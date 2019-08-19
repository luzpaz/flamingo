#(c) 2016 R. T. LGPL: part of Flamingo tools w.b. for FreeCAD

__title__="pypeTools dialogs"
__author__="oddtopus"
__url__="github.com/oddtopus/flamingo"
__license__="LGPL 3"

import FreeCAD,FreeCADGui,Part, csv
pq=FreeCAD.Units.parseQuantity
import frameCmd, pipeCmd
#from frameForms import prototypeForm
from os import listdir
from os.path import join, dirname, abspath
from PySide.QtCore import *
from PySide.QtGui import *
from math import degrees
from DraftVecUtils import rounded
from frameForms import prototypeDialog

class protopypeForm(QDialog): #QWidget):
  'prototype dialog for insert pipeFeatures'
  def __init__(self,winTitle='Title', PType='Pipe', PRating='SCH-STD', icon='flamingo.svg'):
    '''
    __init__(self,winTitle='Title', PType='Pipe', PRating='SCH-STD')
      winTitle: the window's title
      PType: the pipeFeature type
      PRating: the pipeFeature pressure rating class
    It lookups in the directory ./tables the file PType+"_"+PRating+".csv",
    imports it's content in a list of dictionaries -> .pipeDictList and
    shows a summary in the QListWidget -> .sizeList
    Also create a property -> PRatingsList with the list of available PRatings for the 
    selected PType.   
    '''
    super(protopypeForm,self).__init__()
    self.move(QPoint(100,250))
    self.PType=PType
    self.PRating=PRating
    self.setWindowFlags(Qt.WindowStaysOnTopHint)
    self.setWindowTitle(winTitle)
    iconPath=join(dirname(abspath(__file__)),"icons",icon)
    from PySide.QtGui import QIcon
    Icon=QIcon()
    Icon.addFile(iconPath)
    self.setWindowIcon(Icon) 
    self.mainHL=QHBoxLayout()
    self.setLayout(self.mainHL)
    self.firstCol=QWidget()
    self.firstCol.setLayout(QVBoxLayout())
    self.mainHL.addWidget(self.firstCol)
    self.currentRatingLab=QLabel('Rating: '+self.PRating)
    self.firstCol.layout().addWidget(self.currentRatingLab)
    self.sizeList=QListWidget()
    self.firstCol.layout().addWidget(self.sizeList)
    self.pipeDictList=[]
    self.fileList=listdir(join(dirname(abspath(__file__)),"tables"))
    self.fillSizes()
    self.PRatingsList=[s.lstrip(PType+"_").rstrip(".csv") for s in self.fileList if s.startswith(PType) and s.endswith('.csv')]
    self.secondCol=QWidget()
    self.secondCol.setLayout(QVBoxLayout())
    self.combo=QComboBox()
    self.combo.addItem('<none>')
    try:
      self.combo.addItems([o.Label for o in FreeCAD.activeDocument().Objects if hasattr(o,'PType') and o.PType=='PypeLine'])
    except:
      None
    self.combo.currentIndexChanged.connect(self.setCurrentPL)
    if FreeCAD.__activePypeLine__ and FreeCAD.__activePypeLine__ in [self.combo.itemText(i) for i in range(self.combo.count())]:
      self.combo.setCurrentIndex(self.combo.findText(FreeCAD.__activePypeLine__))
    self.secondCol.layout().addWidget(self.combo)
    self.ratingList=QListWidget()
    self.ratingList.addItems(self.PRatingsList)
    self.ratingList.itemClicked.connect(self.changeRating)
    self.ratingList.setCurrentRow(0)
    self.secondCol.layout().addWidget(self.ratingList)
    self.btn1=QPushButton('Insert')
    self.secondCol.layout().addWidget(self.btn1)
    self.mainHL.addWidget(self.secondCol)
    self.resize(350,350)
    self.mainHL.setContentsMargins(0,0,0,0)
  def setCurrentPL(self,PLName=None):
    if self.combo.currentText() not in ['<none>','<new>']:
      FreeCAD.__activePypeLine__= self.combo.currentText()
    else:
      FreeCAD.__activePypeLine__=None
  def fillSizes(self):
    self.sizeList.clear()
    for fileName in self.fileList:
      if fileName==self.PType+'_'+self.PRating+'.csv':
        f=open(join(dirname(abspath(__file__)),"tables",fileName),'r')
        reader=csv.DictReader(f,delimiter=';')
        self.pipeDictList=[DNx for DNx in reader]
        f.close()
        for row in self.pipeDictList:
          s=row['PSize']
          if 'OD' in row.keys(): #row.has_key('OD'):
            s+=" - "+row['OD']
          if 'thk' in row.keys(): #row.has_key('thk'):
            s+="x"+row['thk']
          self.sizeList.addItem(s)
        break
  def changeRating(self,item):
    self.PRating=item.text()
    self.currentRatingLab.setText('Rating: '+self.PRating)
    self.fillSizes()
  def findDN(self,DN):
    result=None
    for row in self.pipeDictList:
      if row['PSize']==DN:
        result=row
        break
    return result

class redrawDialog(QDialog):
  def __init__(self):
    super(redrawDialog,self).__init__()
    self.setWindowTitle("Redraw PypeLines")
    self.resize(200, 350)
    self.verticalLayout = QVBoxLayout(self)
    self.scrollArea = QScrollArea(self)
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QWidget()
    self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 190, 338))
    self.formLayout = QFormLayout(self.scrollAreaWidgetContents)
    self.checkBoxes = list()
    self.pypelines = list()
    try:
      self.pypelines=[o.Label for o in FreeCAD.activeDocument().Objects if hasattr(o,'PType') and o.PType=='PypeLine']
      for pl in self.pypelines:
          self.checkBoxes.append(QCheckBox(self.scrollAreaWidgetContents))
          self.checkBoxes[-1].setText(pl)
          self.formLayout.layout().addWidget(self.checkBoxes[-1])
    except:
      None
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.verticalLayout.addWidget(self.scrollArea)
    self.btn1=QPushButton('Redraw')
    self.verticalLayout.addWidget(self.btn1)
    self.btn1.clicked.connect(self.redraw)
    self.brn2=QPushButton('Select all')
    self.verticalLayout.addWidget(self.brn2)
    self.brn2.clicked.connect(self.selectAll)
    self.btn3=QPushButton('Clear all')
    self.verticalLayout.addWidget(self.btn3)
    self.btn3.clicked.connect(self.clearAll)
    self.show()
  def redraw(self):
    FreeCAD.activeDocument().openTransaction('Redraw pype-lines')
    i=0
    for cb in self.checkBoxes:
      if cb.isChecked():
        pl=FreeCAD.ActiveDocument.getObjectsByLabel(cb.text())[0]
        if pl.Base:
          pl.Proxy.purge(pl)
          pl.Proxy.update(pl)
          i+=1
        else:
          FreeCAD.Console.PrintError('%s has no Base: nothing to redraw\n' %cb.text())
    FreeCAD.ActiveDocument.recompute()
    FreeCAD.Console.PrintMessage('Redrawn %i pipelines.\n' %i)
    FreeCAD.activeDocument().commitTransaction()
  def selectAll(self):
    for cb in self.checkBoxes: cb.setChecked(True)
  def clearAll(self):
    for cb in self.checkBoxes: cb.setChecked(False)
        
class insertPipeForm(protopypeForm):
  '''
  Dialog to insert tubes.
  For position and orientation you can select
    - one or more straight edges (centerlines)
    - one or more curved edges (axis and origin across the center)
    - one or more vertexes 
    - nothing 
  Default length = 200 mm.
  Available one button to reverse the orientation of the last or selected tubes.
  '''
  def __init__(self):
    super(insertPipeForm,self).__init__("Insert pipes","Pipe","SCH-STD","pipe.svg")
    self.move(QPoint(75,225))
    self.sizeList.setCurrentRow(0)
    self.ratingList.setCurrentRow(0)
    self.btn1.clicked.connect(self.insert)
    self.edit1=QLineEdit()
    self.edit1.setPlaceholderText('<length>')
    self.edit1.setAlignment(Qt.AlignHCenter)
    self.edit1.setValidator(QDoubleValidator())
    #self.edit1.editingFinished.connect(lambda: self.sli.setValue(100))
    self.secondCol.layout().addWidget(self.edit1)
    self.btn2=QPushButton('Reverse')
    self.secondCol.layout().addWidget(self.btn2)
    self.btn2.clicked.connect(self.reverse)
    self.btn3=QPushButton('Apply')
    self.secondCol.layout().addWidget(self.btn3)
    self.btn3.clicked.connect(self.apply)
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.sli=QSlider(Qt.Vertical)
    self.sli.setMaximum(200)
    self.sli.setMinimum(1)
    self.sli.setValue(100)
    self.mainHL.addWidget(self.sli)
    self.sli.valueChanged.connect(self.changeL)
    self.show()
    self.lastPipe=None
    self.H=200
  def reverse(self):     # revert orientation of selected or last inserted pipe
    selPipes=[p for p in FreeCADGui.Selection.getSelection() if hasattr(p,'PType') and p.PType=='Pipe']
    if len(selPipes):
      for p in selPipes:
        pipeCmd.rotateTheTubeAx(p,FreeCAD.Vector(1,0,0),180)
    else:
      pipeCmd.rotateTheTubeAx(self.lastPipe,FreeCAD.Vector(1,0,0),180)
  def insert(self):      # insert the pipe
    self.lastPipe=None
    d=self.pipeDictList[self.sizeList.currentRow()]
    FreeCAD.activeDocument().openTransaction('Insert pipe')
    if self.edit1.text():
      self.H=float(self.edit1.text())
    self.sli.setValue(100)
    if len(frameCmd.edges())==0: #..no edges selected
      propList=[d['PSize'],float(pq(d['OD'])),float(pq(d['thk'])),self.H]
      vs=[v for sx in FreeCADGui.Selection.getSelectionEx() for so in sx.SubObjects for v in so.Vertexes]
      if len(vs)==0: # ...no vertexes selected
        self.lastPipe=pipeCmd.makePipe(propList)
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastPipe,self.combo.currentText())
      else:
        for v in vs: # ... one or more vertexes
          self.lastPipe=pipeCmd.makePipe(propList,v.Point)
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastPipe,self.combo.currentText())
    else:
      selex=FreeCADGui.Selection.getSelectionEx()
      for objex in selex:
        o=objex.Object # SELECT PROPERTIES ACCORDING OBJECT
        if hasattr(o,'PSize') and hasattr(o,'OD') and hasattr(o,'thk'):
          propList=[o.PSize,o.OD,o.thk,self.H]
        else:
          propList=[d['PSize'],float(pq(d['OD'])),float(pq(d['thk'])),self.H]
        if frameCmd.faces(): # Face selected...
          for face in frameCmd.faces():
            x=(face.ParameterRange[0]+face.ParameterRange[1])/2
            y=(face.ParameterRange[2]+face.ParameterRange[3])/2
            self.lastPipe=pipeCmd.makePipe(propList,face.valueAt(x,y),face.normalAt(x,y))
            if self.combo.currentText()!='<none>':
              pipeCmd.moveToPyLi(self.lastPipe,self.combo.currentText())
          FreeCAD.activeDocument().commitTransaction()
          FreeCAD.activeDocument().recompute()
          return 
        for edge in frameCmd.edges([objex]): # ...one or more edges...
          if edge.curvatureAt(0)==0: # ...straight edges
            pL=propList
            pL[3]=edge.Length
            self.lastPipe=pipeCmd.makePipe(pL,edge.valueAt(0),edge.tangentAt(0))
          else: # ...curved edges
            pos=edge.centerOfCurvatureAt(0)
            Z=edge.tangentAt(0).cross(edge.normalAt(0))
            if pipeCmd.isElbow(o):
              p0,p1=[o.Placement.Rotation.multVec(p) for p in o.Ports]
              if not frameCmd.isParallel(Z,p0):
                Z=p1
            self.lastPipe=pipeCmd.makePipe(propList,pos,Z)
          if self.combo.currentText()!='<none>':
            pipeCmd.moveToPyLi(self.lastPipe,self.combo.currentText())
    self.H=float(self.lastPipe.Height)
    self.edit1.setText(str(float(self.H)))
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()
  def apply(self):
    self.lastPipe=None
    if self.edit1.text():
      self.H=float(self.edit1.text())
    else:
      self.H=200.0
    self.sli.setValue(100)
    for obj in FreeCADGui.Selection.getSelection():
      d=self.pipeDictList[self.sizeList.currentRow()]
      if hasattr(obj,'PType') and obj.PType==self.PType:
        obj.PSize=d['PSize']
        obj.OD=pq(d['OD'])
        obj.thk=pq(d['thk'])
        obj.PRating=self.PRating
        if self.edit1.text():
          obj.Height=self.H
        FreeCAD.activeDocument().recompute()
  def changeL(self):
    if self.edit1.text():
      newL=self.H*self.sli.value()/100
      self.edit1.setText(str(newL))
      if self.lastPipe:
        self.lastPipe.Height=newL
      FreeCAD.ActiveDocument.recompute()

class insertElbowForm(protopypeForm):
  '''
  Dialog to insert one elbow.
  For position and orientation you can select
    - one vertex, 
    - one circular edge 
    - a pair of edges or pipes or beams
    - one pipe at one of its ends
    - nothing.
  In case one pipe is selected, its properties are applied to the elbow and 
  the tube or tubes are trimmed or extended automatically.
  Also available one button to trim/extend one selected pipe to the selected 
  edges, if necessary.
  '''
  def __init__(self):
    super(insertElbowForm,self).__init__("Insert elbows","Elbow","SCH-STD","elbow.svg")
    self.move(QPoint(125,275))
    self.sizeList.setCurrentRow(0)
    self.ratingList.setCurrentRow(0)
    self.btn1.clicked.connect(self.insert)
    self.edit1=QLineEdit()
    self.edit1.setPlaceholderText('<bend angle>')
    self.edit1.setAlignment(Qt.AlignHCenter)
    self.edit1.setValidator(QDoubleValidator())
    self.secondCol.layout().addWidget(self.edit1)
    self.btn2=QPushButton('Trim/Extend')
    self.btn2.clicked.connect(self.trim)
    self.secondCol.layout().addWidget(self.btn2)
    self.btn3=QPushButton('Reverse')
    self.secondCol.layout().addWidget(self.btn3)
    self.btn3.clicked.connect(self.reverse)
    self.btn4=QPushButton('Apply')
    self.secondCol.layout().addWidget(self.btn4)
    self.btn4.clicked.connect(self.apply)
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.screenDial=QWidget()
    self.screenDial.setLayout(QHBoxLayout())
    self.dial=QDial()
    self.dial.setMaximumSize(80,80)
    self.dial.setWrapping(True)
    self.dial.setMaximum(180)
    self.dial.setMinimum(-180)
    self.dial.setNotchTarget(15)
    self.dial.setNotchesVisible(True)
    self.dial.setMaximumSize(70,70)
    self.screenDial.layout().addWidget(self.dial)
    self.lab=QLabel('0 deg')
    self.lab.setAlignment(Qt.AlignCenter)
    #self.connect(self.dial,SIGNAL("valueChanged(int)"),self.lab.setNum)
    self.dial.valueChanged.connect(self.rotatePort)
    self.screenDial.layout().addWidget(self.lab)
    self.firstCol.layout().addWidget(self.screenDial)
    self.show()
    self.lastElbow=None
    self.lastAngle=0
  def insert(self):    # insert the curve
    #self.lastElbow=None
    self.lastAngle=0
    self.dial.setValue(0)
    DN=OD=thk=PRating=None
    d=self.pipeDictList[self.sizeList.currentRow()]
    try:
      if float(self.edit1.text())>180:
        self.edit1.setText("180")
      ang=float(self.edit1.text())
    except:
      ang=float(pq(d['BendAngle']))
    selex=FreeCADGui.Selection.getSelectionEx()
    if len(selex)==0:     # no selection -> insert one elbow at origin
      propList=[d['PSize'],float(pq(d['OD'])),float(pq(d['thk'])),ang,float(pq(d['BendRadius']))]
      FreeCAD.activeDocument().openTransaction('Insert elbow in (0,0,0)')
      self.lastElbow=pipeCmd.makeElbow(propList)
      if self.combo.currentText()!='<none>':
        pipeCmd.moveToPyLi(self.lastElbow,self.combo.currentText())
      FreeCAD.activeDocument().commitTransaction()
    elif len(selex)==1 and len(selex[0].SubObjects)==1:  #one selection -> ...
      if hasattr(selex[0].Object,'PType') and selex[0].Object.PType in ['Pipe','Elbow','Cap','Reduct']:
        DN=selex[0].Object.PSize
        OD=float(selex[0].Object.OD)
        thk=float(selex[0].Object.thk)
        BR=None
        for prop in self.pipeDictList:
          if prop['PSize']==DN:
            BR=float(pq(prop['BendRadius']))
        if BR==None:
          BR=1.5*OD/2
        propList=[DN,OD,thk,ang,BR]
      else:
        propList=[d['PSize'],float(pq(d['OD'])),float(pq(d['thk'])),ang,float(pq(d['BendRadius']))]
      if selex[0].SubObjects[0].ShapeType=="Vertex":   # ...on vertex
        FreeCAD.activeDocument().openTransaction('Insert elbow on vertex')
        self.lastElbow=pipeCmd.makeElbow(propList,selex[0].SubObjects[0].Point)
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastElbow,self.combo.currentText())
        FreeCAD.activeDocument().commitTransaction()
      elif selex[0].SubObjects[0].ShapeType=="Edge" and  selex[0].SubObjects[0].curvatureAt(0)!=0: # ...on center of curved edge
        P=selex[0].SubObjects[0].centerOfCurvatureAt(0)
        N=selex[0].SubObjects[0].normalAt(0).cross(selex[0].SubObjects[0].tangentAt(0)).normalize()
        FreeCAD.activeDocument().openTransaction('Insert elbow on curved edge')
        self.lastElbow=pipeCmd.makeElbow(propList,P) # ,Z)
        if pipeCmd.isPipe(selex[0].Object):
          ax=selex[0].Object.Shape.Solids[0].CenterOfMass-P
          rot=FreeCAD.Rotation(self.lastElbow.Ports[0],ax)
          self.lastElbow.Placement.Rotation=rot.multiply(self.lastElbow.Placement.Rotation)
          Port0=pipeCmd.getElbowPort(self.lastElbow)
          self.lastElbow.Placement.move(P-Port0)
        elif pipeCmd.isElbow(selex[0].Object):
          p0,p1=[selex[0].Object.Placement.Rotation.multVec(p) for p in selex[0].Object.Ports]
          if frameCmd.isParallel(p0,N):
            self.lastElbow.Placement.Rotation=FreeCAD.Rotation(self.lastElbow.Ports[0],p0*-1)
          else:
            self.lastElbow.Placement.Rotation=FreeCAD.Rotation(self.lastElbow.Ports[0],p1*-1)
          self.lastElbow.Placement.move(P-pipeCmd.getElbowPort(self.lastElbow))
        else:
          rot=FreeCAD.Rotation(self.lastElbow.Ports[0],N)
          self.lastElbow.Placement.Rotation=rot.multiply(self.lastElbow.Placement.Rotation)
          self.lastElbow.Placement.move(self.lastElbow.Placement.Rotation.multVec(self.lastElbow.Ports[0])*-1)
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastElbow,self.combo.currentText())
        FreeCAD.activeDocument().recompute()
        FreeCAD.activeDocument().commitTransaction()
    else:       # multiple selection -> insert one elbow at intersection of two edges or beams or pipes ##
      # selection of axes
      things=[]
      for objEx in selex:
        # if the profile is not defined and the selection is one piping object, take its profile for elbow
        if OD==thk==None and hasattr(objEx.Object,'PType') and objEx.Object.PType in ['Pipe','Elbow','Cap','Reduct']: 
          DN=objEx.Object.PSize
          OD=objEx.Object.OD
          thk=objEx.Object.thk
          PRating=objEx.Object.PRating
        # if the object is a beam or pipe, append it to the "things"..
        if len(frameCmd.beams([objEx.Object]))==1:
          things.append(objEx.Object)
        else:
          # ..else append its edges
          for edge in frameCmd.edges([objEx]):
            things.append(edge)
        if len(things)>=2:
          break
      FreeCAD.activeDocument().openTransaction('Insert elbow on intersection')
      try:
        #create the feature
        if None in [DN,OD,thk,PRating]:
          propList=[d['PSize'],float(pq(d['OD'])),float(pq(d['thk'])),ang,float(pq(d['BendRadius']))]
          self.lastElbow=pipeCmd.makeElbowBetweenThings(*things[:2],propList=propList)
          self.lastElbow.PRating=self.ratingList.item(self.ratingList.currentRow()).text()
        else:
          for prop in self.pipeDictList:
            if prop['PSize']==DN:
              BR=float(pq(prop['BendRadius']))
          if BR==None:
            BR=1.5*OD/2
          propList=[DN,OD,thk,ang,BR]
          self.lastElbow=pipeCmd.makeElbowBetweenThings(*things[:2],propList=propList)
          self.lastElbow.PRating=PRating
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastElbow,self.combo.currentText())
      except:
        FreeCAD.Console.PrintError('Creation of elbow is failed\n')
      FreeCAD.activeDocument().commitTransaction()
      ####
    FreeCAD.activeDocument().recompute()
  def trim(self):
    if len(frameCmd.beams())==1:
      pipe=frameCmd.beams()[0]
      comPipeEdges=[e.CenterOfMass for e in pipe.Shape.Edges]
      eds=[e for e in frameCmd.edges() if not e.CenterOfMass in comPipeEdges]
      FreeCAD.activeDocument().openTransaction('Trim pipes')
      for edge in eds:
        frameCmd.extendTheBeam(frameCmd.beams()[0],edge)
      FreeCAD.activeDocument().commitTransaction()
      FreeCAD.activeDocument().recompute()
    else:
      FreeCAD.Console.PrintError("Wrong selection\n")
  def rotatePort(self):
    if self.lastElbow:
      pipeCmd.rotateTheElbowPort(self.lastElbow,0,self.lastAngle*-1)
      self.lastAngle=self.dial.value()
      pipeCmd.rotateTheElbowPort(self.lastElbow,0,self.lastAngle)
    self.lab.setText(str(self.dial.value())+' deg')
  def apply(self):
    for obj in FreeCADGui.Selection.getSelection():
      d=self.pipeDictList[self.sizeList.currentRow()]
      if hasattr(obj,'PType') and obj.PType==self.PType:
        obj.PSize=d['PSize']
        obj.OD=pq(d['OD'])
        obj.thk=pq(d['thk'])
        try:
          obj.BendAngle=float(self.edit1.text())
        except:
          pass
        obj.BendRadius=pq(d['BendRadius'])
        obj.PRating=self.PRating
        FreeCAD.activeDocument().recompute()
  def reverse(self):
    if self.lastElbow:
      pipeCmd.rotateTheTubeAx(self.lastElbow,angle=180)
      self.lastElbow.Placement.move(self.lastElbow.Placement.Rotation.multVec(self.lastElbow.Ports[0])*-2)

class insertFlangeForm(protopypeForm):
  '''
  Dialog to insert flanges.
  For position and orientation you can select
    - one or more circular edges,
    - one or more vertexes,
    - nothing.
  In case one pipe is selected, its properties are applied to the flange.
  Available one button to reverse the orientation of the last or selected 
  flanges.
  '''
  def __init__(self):
    super(insertFlangeForm,self).__init__("Insert flanges","Flange","DIN-PN16","flange.svg")
    self.sizeList.setCurrentRow(0)
    self.ratingList.setCurrentRow(0)
    self.btn1.clicked.connect(self.insert)
    self.btn2=QPushButton('Reverse')
    self.secondCol.layout().addWidget(self.btn2)
    self.btn2.clicked.connect(self.reverse) #lambda: pipeCmd.rotateTheTubeAx(self.lastFlange,FreeCAD.Vector(1,0,0),180))
    self.btn3=QPushButton('Apply')
    self.secondCol.layout().addWidget(self.btn3)
    self.btn3.clicked.connect(self.apply)
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.show()
    self.lastFlange=None
  def reverse(self):
    selFlanges=[f for f in FreeCADGui.Selection.getSelection() if hasattr(f,'PType') and f.PType=='Flange']
    if len(selFlanges):
      for f in selFlanges:
        pipeCmd.rotateTheTubeAx(f,FreeCAD.Vector(1,0,0),180)
    else:
      pipeCmd.rotateTheTubeAx(self.lastFlange,FreeCAD.Vector(1,0,0),180)
  def insert(self):
    tubes=[t for t in frameCmd.beams() if hasattr(t,'PSize')]
    if len(tubes)>0 and tubes[0].PSize in [prop['PSize'] for prop in self.pipeDictList]:
      for prop in self.pipeDictList:
        if prop['PSize']==tubes[0].PSize:
          d=prop
          break
    else:
      d=self.pipeDictList[self.sizeList.currentRow()]
    propList=[d['PSize'],d['FlangeType'],float(pq(d['D'])),float(pq(d['d'])),float(pq(d['df'])),float(pq(d['f'])),float(pq(d['t'])),int(d['n'])]
    try: # for raised-face
      propList.append(float(d['trf']))
      propList.append(float(d['drf']))
    except:
      pass
    try: # for welding-neck
      propList.append(float(d['twn']))
      propList.append(float(d['dwn']))
      propList.append(float(d['ODp']))
    except:
      pass
    FreeCAD.activeDocument().openTransaction('Insert flange')
    if len(frameCmd.edges())==0:
      vs=[v for sx in FreeCADGui.Selection.getSelectionEx() for so in sx.SubObjects for v in so.Vertexes]
      if len(vs)==0:
        self.lastFlange=pipeCmd.makeFlange(propList)
        self.lastFlange.PRating=self.PRating
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastFlange,self.combo.currentText())
      else:
        for v in vs:
          self.lastFlange=pipeCmd.makeFlange(propList,v.Point)
          self.lastFlange.PRating=self.PRating
          if self.combo.currentText()!='<none>':
            pipeCmd.moveToPyLi(self.lastFlange,self.combo.currentText())
    elif tubes:
      selex=FreeCADGui.Selection.getSelectionEx()
      for sx in selex:
        if hasattr(sx.Object,'PType') and sx.Object.PType=='Pipe' and frameCmd.edges([sx]):
          for edge in frameCmd.edges([sx]):
            if edge.curvatureAt(0)!=0:
              self.lastFlange=pipeCmd.makeFlange(propList,edge.centerOfCurvatureAt(0),sx.Object.Shape.Solids[0].CenterOfMass-edge.centerOfCurvatureAt(0))
              self.lastFlange.PRating=self.PRating
              if self.combo.currentText()!='<none>':
                pipeCmd.moveToPyLi(self.lastFlange,self.combo.currentText())
      FreeCAD.activeDocument().commitTransaction()
      FreeCAD.activeDocument().recompute()
      return
    else:
      for edge in frameCmd.edges():
        if edge.curvatureAt(0)!=0:
          self.lastFlange=pipeCmd.makeFlange(propList,edge.centerOfCurvatureAt(0),edge.tangentAt(0).cross(edge.normalAt(0)))
          self.lastFlange.PRating=self.PRating
          if self.combo.currentText()!='<none>':
            pipeCmd.moveToPyLi(self.lastFlange,self.combo.currentText())
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()
  def apply(self):
    for obj in FreeCADGui.Selection.getSelection():
      d=self.pipeDictList[self.sizeList.currentRow()]
      if hasattr(obj,'PType') and obj.PType==self.PType:
        obj.PSize=d['PSize']
        obj.FlangeType=d['FlangeType']
        obj.D=float(pq(d['D']))
        obj.d=float(pq(d['d']))
        obj.df=float(pq(d['df']))
        obj.f=float(pq(d['f']))
        obj.t=float(pq(d['t']))
        obj.n=int(pq(d['n']))
        obj.PRating=self.PRating
        FreeCAD.activeDocument().recompute()

class insertReductForm(protopypeForm):
  '''
  Dialog to insert concentric reductions.
  For position and orientation you can select
    - two pipes parallel (possibly co-linear)
    - one pipe at one of its ends
    - one pipe
    - one circular edge
    - one straight edge
    - one vertex
    - nothing (created at origin)
  In case one pipe is selected, its properties are applied to the reduction.
  Available one button to reverse the orientation of the last or selected 
  reductions.
  '''
  def __init__(self):
    super(insertReductForm,self).__init__("Insert reductions","Reduct","SCH-STD","reduct.svg")
    self.sizeList.setCurrentRow(0)
    self.ratingList.setCurrentRow(0)
    self.ratingList.itemClicked.connect(self.changeRating2)
    self.sizeList.currentItemChanged.connect(self.fillOD2)
    self.ratingList.setCurrentRow(0)
    self.ratingList.setMaximumHeight(50)
    self.OD2list=QListWidget()
    self.OD2list.setMaximumHeight(80)
    self.secondCol.layout().addWidget(self.OD2list)
    self.btn2=QPushButton('Reverse')
    self.secondCol.layout().addWidget(self.btn2)
    self.btn3=QPushButton('Apply')
    self.secondCol.layout().addWidget(self.btn3)
    self.btn1.clicked.connect(self.insert)
    self.btn2.clicked.connect(self.reverse)
    self.btn3.clicked.connect(self.applyProp)
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.cb1=QCheckBox(' Eccentric')
    self.secondCol.layout().addWidget(self.cb1)
    self.fillOD2()
    self.show()
    self.lastReduct=None
  def applyProp(self):
    r=self.pipeDictList[self.sizeList.currentRow()]
    DN=r['PSize']
    OD1=float(pq(r['OD']))
    OD2=float(pq(self.OD2list.currentItem().text()))
    thk1=float(pq(r['thk']))
    try:
      thk2=float(pq(r['thk2'].split('>')[self.OD2list.currentRow()]))
    except:
      thk2=thk1
    H=pq(r['H'])
    reductions=[red for red in FreeCADGui.Selection.getSelection() if hasattr(red,'PType') and red.PType=='Reduct']
    if len(reductions):
      for reduct in reductions:
        reduct.PSize=DN
        reduct.PRating=self.PRating
        reduct.OD=OD1
        reduct.OD2=OD2
        reduct.thk=thk1
        reduct.thk2=thk2
        reduct.Height=H
    elif self.lastReduct:
      self.lastReduct.PSize=DN
      self.lastReduct.PRating=self.PRating
      self.lastReduct.OD=OD1
      self.lastReduct.OD2=OD2
      self.lastReduct.thk=thk1
      self.lastReduct.thk2=thk2
      self.lastReduct.Height=H
    FreeCAD.activeDocument().recompute()
  def fillOD2(self):
    self.OD2list.clear()
    self.OD2list.addItems(self.pipeDictList[self.sizeList.currentRow()]['OD2'].split('>'))
    self.OD2list.setCurrentRow(0)
  def reverse(self):
    selRed=[r for r in FreeCADGui.Selection.getSelection() if hasattr(r,'PType') and r. PType=='Reduct']
    if len(selRed):
      for r in selRed:
        pipeCmd.rotateTheTubeAx(r,FreeCAD.Vector(1,0,0),180)
    elif self.lastReduct:
      pipeCmd.rotateTheTubeAx(self.lastReduct,FreeCAD.Vector(1,0,0),180)
  def insert(self):
    r=self.pipeDictList[self.sizeList.currentRow()]
    pos=Z=H=None
    selex=FreeCADGui.Selection.getSelectionEx()
    pipes=[p.Object for p in selex if hasattr(p.Object,'PType') and p.Object.PType=='Pipe']
    if len(pipes)>1 and frameCmd.isParallel(frameCmd.beamAx(pipes[0]),frameCmd.beamAx(pipes[1])):  # if at least 2 pipes are selected...
      if pipes[0].OD>=pipes[1].OD:
        p1,p2=pipes[:2]
      else:
        p2,p1=pipes[:2]
      DN=p1.PSize
      OD1=float(p1.OD)
      OD2=float(p2.OD)
      thk1=float(p1.thk)
      thk2=float(p2.thk)
      H=float(pq(self.findDN(DN)['H']))
      Z=p2.Shape.Solids[0].CenterOfMass-p1.Shape.Solids[0].CenterOfMass
      Z.normalize()
      pos=p1.Shape.Solids[0].CenterOfMass+Z*float(p1.Height/2)
    elif len(pipes)>0:            # if 1 pipe is selected...
      DN=pipes[0].PSize
      OD1=float(pipes[0].OD)
      OD2=float(pq(self.OD2list.currentItem().text()))
      thk1=float(pipes[0].thk)
      thk2=float(pq(r['thk2'].split('>')[self.OD2list.currentRow()]))
      H=float(pq(self.findDN(DN)['H']))
      curves=[e for e in frameCmd.edges() if e.curvatureAt(0)>0]
      if len(curves): #...and 1 curve is selected...
        pos=curves[0].centerOfCurvatureAt(0)
      else: #...or no curve is selected...
        pos=pipes[0].Placement.Base
      Z= pos-pipes[0].Shape.Solids[0].CenterOfMass
    else:                         # if no pipe is selected...
      DN=r['PSize']
      OD1=float(pq(r['OD']))
      OD2=float(pq(self.OD2list.currentItem().text()))
      thk1=float(pq(r['thk']))
      try:
        thk2=float(pq(r['thk2'].split('>')[self.OD2list.currentRow()]))
      except:
        thk2=thk1
      H=pq(r['H'])
      if frameCmd.edges():    #...but 1 curve is selected...
        edge=frameCmd.edges()[0]
        if edge.curvatureAt(0)>0:
          pos=edge.centerOfCurvatureAt(0)
          Z=edge.tangentAt(0).cross(edge.normalAt(0))
        else:
          pos=edge.valueAt(0)
          Z=edge.tangentAt(0)
      elif selex and selex[0].SubObjects[0].ShapeType=="Vertex": #...or 1 vertex..
        pos=selex[0].SubObjects[0].Point
    if not H: # calculate length if it's not defined
      H=float(3*(OD1-OD2))
    propList=[DN,OD1,OD2,thk1,thk2,H]
    FreeCAD.activeDocument().openTransaction('Insert reduction')
    if self.cb1.isChecked():
      self.lastReduct=pipeCmd.makeReduct(propList,pos,Z,False)
    else:
      self.lastReduct=pipeCmd.makeReduct(propList,pos,Z)
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()
    if self.combo.currentText()!='<none>':
      pipeCmd.moveToPyLi(self.lastReduct,self.combo.currentText())
  def changeRating2(self,item):
    self.PRating=item.text()
    self.fillSizes()
    self.sizeList.setCurrentRow(0)
    self.fillOD2()

class insertUboltForm(protopypeForm):
  '''
  Dialog to insert U-bolts.
  For position and orientation you can select
    - one or more circular edges,
    - nothing.
  In case one pipe is selected, its properties are applied to the U-bolt.
  Available one button to reverse the orientation of the last or selected tubes.
  '''
  def __init__(self):
    super(insertUboltForm,self).__init__("Insert U-bolt","Clamp","DIN-UBolt","clamp.svg")
    self.sizeList.setCurrentRow(0)
    self.ratingList.setCurrentRow(0)
    self.lab1=QLabel('- no ref. face -')
    self.lab1.setAlignment(Qt.AlignHCenter)
    self.firstCol.layout().addWidget(self.lab1)
    self.btn1.clicked.connect(self.insert)
    self.btn2=QPushButton('Ref. face')
    self.secondCol.layout().addWidget(self.btn2)
    self.btn2.clicked.connect(self.getReference)
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.cb1=QCheckBox(' Head')
    self.cb1.setChecked(True)
    self.cb2=QCheckBox(' Middle')
    self.cb3=QCheckBox(' Tail')
    self.checkb=QWidget()
    self.checkb.setLayout(QFormLayout())
    self.checkb.layout().setAlignment(Qt.AlignHCenter)
    self.checkb.layout().addRow(self.cb1)
    self.checkb.layout().addRow(self.cb2)
    self.checkb.layout().addRow(self.cb3)
    self.secondCol.layout().addWidget(self.checkb)
    self.show()
    self.refNorm=None
    self.getReference()
  def getReference(self):
    selex=FreeCADGui.Selection.getSelectionEx()
    for sx in selex:
      if sx.SubObjects:
        planes=[f for f in frameCmd.faces([sx]) if type(f.Surface)==Part.Plane]
        if len(planes)>0:
          self.refNorm=rounded(planes[0].normalAt(0,0))
          self.lab1.setText("ref. Face on "+sx.Object.Label)
  def insert(self):
    selex=FreeCADGui.Selection.getSelectionEx()
    if len(selex)==0:
      d=self.pipeDictList[self.sizeList.currentRow()]
      propList=[d['PSize'],self.PRating,float(pq(d['C'])),float(pq(d['H'])),float(pq(d['d']))]
      FreeCAD.activeDocument().openTransaction('Insert clamp in (0,0,0)')
      ub=pipeCmd.makeUbolt(propList)
      if self.combo.currentText()!='<none>':
        pipeCmd.moveToPyLi(ub,self.combo.currentText())
      FreeCAD.activeDocument().commitTransaction()
      FreeCAD.activeDocument().recompute()
    else:
      FreeCAD.activeDocument().openTransaction('Insert clamp on tube')
      for objex in selex:
        if hasattr(objex.Object,'PType') and objex.Object.PType=='Pipe':
          d=[typ for typ in self.pipeDictList if typ['PSize']==objex.Object.PSize]
          if len(d)>0:
            d=d[0]
          else:
            d=self.pipeDictList[self.sizeList.currentRow()]
          propList=[d['PSize'],self.PRating,float(pq(d['C'])),float(pq(d['H'])),float(pq(d['d']))]
          H=float(objex.Object.Height)
          gap=H-float(pq(d['C']))
          steps=[gap*self.cb1.isChecked(),H/2*self.cb2.isChecked(),(H-gap)*self.cb3.isChecked()]
          for s in steps:
            if s:
              ub=pipeCmd.makeUbolt(propList,pos=objex.Object.Placement.Base, Z=frameCmd.beamAx(objex.Object))
              ub.Placement.move(frameCmd.beamAx(objex.Object).multiply(s))
              if self.refNorm:
                pipeCmd.rotateTheTubeAx(obj=ub,angle=degrees(self.refNorm.getAngle((frameCmd.beamAx(ub,FreeCAD.Vector(0,1,0))))))
              if self.combo.currentText()!='<none>':
                pipeCmd.moveToPyLi(ub,self.combo.currentText())
      FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()

class insertCapForm(protopypeForm):
  '''
  Dialog to insert caps.
  For position and orientation you can select
    - one or more curved edges (axis and origin across the center)
    - one or more vertexes 
    - nothing 
  Available one button to reverse the orientation of the last or selected tubes.
  '''
  def __init__(self):
    super(insertCapForm,self).__init__("Insert caps","Cap","SCH-STD","cap.svg")
    self.sizeList.setCurrentRow(0)
    self.ratingList.setCurrentRow(0)
    self.btn1.clicked.connect(self.insert)
    self.btn2=QPushButton('Reverse')
    self.secondCol.layout().addWidget(self.btn2)
    self.btn2.clicked.connect(self.reverse)
    self.btn3=QPushButton('Apply')
    self.secondCol.layout().addWidget(self.btn3)
    self.btn3.clicked.connect(self.apply)
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.show()
    self.lastPipe=None
  def reverse(self):
    selCaps=[p for p in FreeCADGui.Selection.getSelection() if hasattr(p,'PType') and p.PType=='Cap']
    if len(selCaps):
      for p in selCaps:
        pipeCmd.rotateTheTubeAx(p,FreeCAD.Vector(1,0,0),180)
    else:
      pipeCmd.rotateTheTubeAx(self.lastCap,FreeCAD.Vector(1,0,0),180)
  def insert(self):
    d=self.pipeDictList[self.sizeList.currentRow()]
    FreeCAD.activeDocument().openTransaction('Insert cap')
    if len(frameCmd.edges())==0:
      propList=[d['PSize'],float(pq(d['OD'])),float(pq(d['thk']))]
      vs=[v for sx in FreeCADGui.Selection.getSelectionEx() for so in sx.SubObjects for v in so.Vertexes]
      if len(vs)==0:   # nothing is selected
        self.lastCap=pipeCmd.makeCap(propList)
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastCap,self.combo.currentText())
      else:
        for v in vs:   # vertexes are selected
          self.lastCap=pipeCmd.makeCap(propList,v.Point)
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastCap,self.combo.currentText())
    else:
      for edge in frameCmd.edges():
        if edge.curvatureAt(0)!=0:   # curved edges are selected...
          objs=[o for o in FreeCADGui.Selection.getSelection() if hasattr(o,'PSize') and hasattr(o,'OD') and hasattr(o,'thk')]
          Z=None
          if len(objs)>0:  # ...pype objects are selected
            propList=[objs[0].PSize,objs[0].OD,objs[0].thk]
            Z=edge.centerOfCurvatureAt(0)-objs[0].Shape.Solids[0].CenterOfMass
          else:            # ...no pype objects are selected
            propList=[d['PSize'],float(pq(d['OD'])),float(pq(d['thk']))]
            Z=edge.tangentAt(0).cross(edge.normalAt(0))
          self.lastCap=pipeCmd.makeCap(propList,edge.centerOfCurvatureAt(0),Z)
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastCap,self.combo.currentText())
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()
  def apply(self):
    for obj in FreeCADGui.Selection.getSelection():
      d=self.pipeDictList[self.sizeList.currentRow()]
      if hasattr(obj,'PType') and obj.PType==self.PType:
        obj.PSize=d['PSize']
        obj.OD=pq(d['OD'])
        obj.thk=pq(d['thk'])
        obj.PRating=self.PRating
        FreeCAD.activeDocument().recompute()

class insertPypeLineForm(protopypeForm):
  '''
  Dialog to insert pypelines.
  Note: Elbow created within this dialog have a standard bending radius of 
  3/4 x OD, corresponding to a 3D curve. If you aim to have 5D curve or any
  other custom bending radius, you shall apply it in the "Insert Elbow"
  dialog or change it manually. 
  '''
  def __init__(self):
    super(insertPypeLineForm,self).__init__("PypeLine Manager","Pipe","SCH-STD","pypeline.svg")
    self.sizeList.setCurrentRow(0)
    self.ratingList.setCurrentRow(0)
    self.btn1.clicked.connect(self.insert)
    self.combo.activated[str].connect(self.summary)
    self.edit1=QLineEdit()
    self.edit1.setPlaceholderText('<name>')
    self.edit1.setAlignment(Qt.AlignHCenter)
    self.secondCol.layout().addWidget(self.edit1)
    self.btn4=QPushButton('Redraw')
    self.secondCol.layout().addWidget(self.btn4)
    self.btn4.clicked.connect(self.redraw)
    self.btn2=QPushButton('Part list')
    self.secondCol.layout().addWidget(self.btn2)
    self.btn2.clicked.connect(self.partList)
    self.btn3=QPushButton('Color')
    self.secondCol.layout().addWidget(self.btn3)
    self.btn3.clicked.connect(self.changeColor)
    self.btn5=QPushButton('Get Path')
    self.firstCol.layout().addWidget(self.btn5)
    self.btn5.clicked.connect(self.getBase)
    self.btnX=QPushButton('Get Profile')
    self.firstCol.layout().addWidget(self.btnX)
    self.btnX.clicked.connect(self.apply)
    self.color=0.8,0.8,0.8
    self.combo.setItemText(0,'<new>')
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.lastPypeLine=None
    self.show()
  def summary(self,pl=None):
    if self.combo.currentText()!="<new>":
      pl=FreeCAD.ActiveDocument.getObjectsByLabel(self.combo.currentText())[0]
      FreeCAD.Console.PrintMessage("\n%s: %s - %s\nProfile: %.1fx%.1f\nRGB color: %.3f, %.3f, %.3f\n"%(pl.Label, pl.PSize, pl.PRating, pl.OD, pl.thk, pl.ViewObject.ShapeColor[0], pl.ViewObject.ShapeColor[1], pl.ViewObject.ShapeColor[2]))
      if pl.Base:
        FreeCAD.Console.PrintMessage('Path: %s\n'%pl.Base.Label)
      else:
        FreeCAD.Console.PrintMessage('Path not defined\n')
  def apply(self):
    d=self.pipeDictList[self.sizeList.currentRow()]
    if self.combo.currentText()!="<new>":                                           
      pl=FreeCAD.ActiveDocument.getObjectsByLabel(self.combo.currentText())[0]
      pl.PSize=d["PSize"]
      pl.PRating=self.PRating
      pl.OD=float(d["OD"])
      pl.thk=float(d["thk"])
      self.summary()
    else:
      FreeCAD.Console.PrintError('Select a PypeLine to apply first\n')
  def insert(self):
    d=self.pipeDictList[self.sizeList.currentRow()]
    FreeCAD.activeDocument().openTransaction('Insert pype-line')
    if self.combo.currentText()=='<new>':
      plLabel=self.edit1.text()
      if not plLabel: plLabel="Tubatura"
      a=pipeCmd.makePypeLine2(DN=d["PSize"],PRating=self.PRating,OD=float(d["OD"]),thk=float(d["thk"]), lab=plLabel, color=self.color)
      self.combo.addItem(a.Label)
    else:
      plname=self.combo.currentText()
      plcolor=FreeCAD.activeDocument().getObjectsByLabel(plname)[0].ViewObject.ShapeColor
      pipeCmd.makePypeLine2(DN=d["PSize"],PRating=self.PRating,OD=float(d["OD"]),thk=float(d["thk"]), pl=plname, color=plcolor)
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.ActiveDocument.recompute()
    FreeCAD.ActiveDocument.recompute()
  def getBase(self):
    if self.combo.currentText()!="<new>":                                           
      pl=FreeCAD.ActiveDocument.getObjectsByLabel(self.combo.currentText())[0]    
      sel=FreeCADGui.Selection.getSelection()
      if sel:
        base=sel[0]
        isWire=hasattr(base,'Shape') and base.Shape.Edges #type(base.Shape)==Part.Wire
        isSketch=hasattr(base,'TypeId') and base.TypeId=='Sketcher::SketchObject'
        if isWire or isSketch:
          FreeCAD.activeDocument().openTransaction('Assign Base')
          pl.Base=base
          if isWire:
            pipeCmd.drawAsCenterLine(pl.Base)
            pipeCmd.moveToPyLi(pl.Base,self.combo.currentText())
          FreeCAD.activeDocument().commitTransaction()
        else:
          FreeCAD.Console.PrintError('Not valid Base: select a Wire or a Sketch.\n')
      else:
        pl.Base=None
        FreeCAD.Console.PrintWarning(pl.Label+'-> deleted Base\n')
    else:
      FreeCAD.Console.PrintError('Please choose or create a PypeLine first\n')
  def redraw(self):
    self.rd=redrawDialog()
  def changeColor(self):
    self.hide()
    col=QColorDialog.getColor()
    if col.isValid():
      self.color=tuple([c/255.0 for c in col.toTuple()[:3]])
      if self.combo.currentText()!="<new>":
        pl=FreeCAD.ActiveDocument.getObjectsByLabel(self.combo.currentText())[0]
        pl.ViewObject.ShapeColor=self.color
        pipeCmd.updatePLColor([pl])
    self.show()
  def partList(self):
    from PySide.QtGui import QFileDialog as qfd
    f=None
    f=qfd.getSaveFileName()[0]
    if f:
      if self.combo.currentText()!='<new>':
        group=FreeCAD.activeDocument().getObjectsByLabel(FreeCAD.__activePypeLine__+'_pieces')[0]
        fields=['Label','PType','PSize','Volume','Height']
        rows=list()
        for o in group.OutList:
          if hasattr(o,'PType'):
            if o.PType in ['Pipe','Elbow','Flange','Clamp','Reduct','Cap']:
              data=[o.Label,o.PType,o.PSize,o.Shape.Volume,'-']
              if o.PType=='Pipe':
                data[4]=o.Height
              rows.append(dict(zip(fields,data)))
            elif o.PType in ['PypeBranch']:
              for name in o.Tubes+o.Curves:
                pype=FreeCAD.ActiveDocument.getObject(name)
                data=[pype.Label,pype.PType,pype.PSize,pype.Shape.Volume,'-']
                if pype.PType=='Pipe':
                  data[4]=pype.Height
                rows.append(dict(zip(fields,data)))
        plist=open(abspath(f),'w')
        w=csv.DictWriter(plist,fields,restval='-',delimiter=';')
        w.writeheader()
        w.writerows(rows)
        plist.close()
        FreeCAD.Console.PrintMessage('Data saved in %s.\n' %f)
    
class insertBranchForm(protopypeForm):
  '''
  Dialog to insert branches.
  Note: Elbow created within this dialog have a standard bending radius of 
  3/4 x OD, corresponding to a 3D curve.  
  '''
  def __init__(self):
    super(insertBranchForm,self).__init__("Insert a branch","Pipe","SCH-STD","branch.svg")
    self.sizeList.setCurrentRow(0)
    self.ratingList.setCurrentRow(0)
    self.btn1.clicked.connect(self.insert)
    self.combo.activated[str].connect(self.summary)
    self.edit1=QLineEdit()
    self.edit1.setPlaceholderText('<name>')
    self.edit1.setAlignment(Qt.AlignHCenter)
    self.secondCol.layout().addWidget(self.edit1)
    self.edit2=QLineEdit()
    self.edit2.setPlaceholderText('<bend radius>')
    self.edit2.setAlignment(Qt.AlignHCenter)
    self.edit2.setValidator(QDoubleValidator())
    self.secondCol.layout().addWidget(self.edit2)
    self.color=0.8,0.8,0.8
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.show()
  def summary(self,pl=None):
    if self.combo.currentText()!="<none>":
      pl=FreeCAD.ActiveDocument.getObjectsByLabel(self.combo.currentText())[0]
      FreeCAD.Console.PrintMessage("\n%s: %s - %s\nProfile: %.1fx%.1f\nRGB color: %.3f, %.3f, %.3f\n"%(pl.Label, pl.PSize, pl.PRating, pl.OD, pl.thk, pl.ViewObject.ShapeColor[0], pl.ViewObject.ShapeColor[1], pl.ViewObject.ShapeColor[2]))
      if pl.Base:
        FreeCAD.Console.PrintMessage('Path: %s\n'%pl.Base.Label)
      else:
        FreeCAD.Console.PrintMessage('Path not defined\n')
  #def apply(self):
    #d=self.pipeDictList[self.sizeList.currentRow()]
    #if self.combo.currentText()!="<new>":                                           
      #pl=FreeCAD.ActiveDocument.getObjectsByLabel(self.combo.currentText())[0]
      #pl.PSize=d["PSize"]
      #pl.PRating=self.PRating
      #pl.OD=float(d["OD"])
      #pl.thk=float(d["thk"])
      #self.summary()
    #else:
      #FreeCAD.Console.PrintError('Select a PypeLine to apply first\n')
  def insert(self):
    d=self.pipeDictList[self.sizeList.currentRow()]
    FreeCAD.activeDocument().openTransaction('Insert pype-branch')
    plLabel=self.edit1.text()
    if not plLabel: plLabel="Traccia"
    if not self.edit2.text(): bendRad=0.75*float(d["OD"])
    else: bendRad=float(self.edit2.text())
    a=pipeCmd.makeBranch(DN=d["PSize"],PRating=self.PRating,OD=float(d["OD"]),thk=float(d["thk"]), BR=bendRad, lab=plLabel, color=self.color)
    if self.combo.currentText()!='<none>':
      pipeCmd.moveToPyLi(a,self.combo.currentText())
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.ActiveDocument.recompute()
    FreeCAD.ActiveDocument.recompute()
    
class breakForm(QDialog):
  '''
  Dialog to break one pipe and create a gap.
  '''
  def __init__(self,winTitle='Break the pipes', PType='Pipe', PRating='SCH-STD', icon='break.svg'):
    self.refL=0.0
    super(breakForm,self).__init__()
    self.move(QPoint(100,250))
    self.PType=PType
    self.PRating=PRating
    self.setWindowFlags(Qt.WindowStaysOnTopHint)
    self.setWindowTitle(winTitle)
    iconPath=join(dirname(abspath(__file__)),"icons",icon)
    from PySide.QtGui import QIcon
    Icon=QIcon()
    Icon.addFile(iconPath)
    self.setWindowIcon(Icon) 
    self.grid=QGridLayout()
    self.setLayout(self.grid)
    self.btn0=QPushButton('Length')
    self.btn0.clicked.connect(self.getL)
    self.lab0=QLabel('<reference>')
    self.lab1=QLabel('PypeLine:')
    self.combo=QComboBox()
    self.combo.addItem('<none>')
    try:
      self.combo.addItems([o.Label for o in FreeCAD.activeDocument().Objects if hasattr(o,'PType') and o.PType=='PypeLine'])
    except:
      None
    self.combo.currentIndexChanged.connect(self.setCurrentPL)
    if FreeCAD.__activePypeLine__ and FreeCAD.__activePypeLine__ in [self.combo.itemText(i) for i in range(self.combo.count())]:
      self.combo.setCurrentIndex(self.combo.findText(FreeCAD.__activePypeLine__))
    self.edit1=QLineEdit('0')
    self.edit1.setAlignment(Qt.AlignCenter)
    self.edit1.editingFinished.connect(self.updateSlider)
    self.edit2=QLineEdit('0')
    self.edit2.setAlignment(Qt.AlignCenter)
    self.edit2.editingFinished.connect(self.calcGapPercent)
    rx=QRegExp('[0-9,.%]*')
    val=QRegExpValidator(rx)
    self.edit1.setValidator(val)
    self.edit2.setValidator(val)
    self.lab2=QLabel('Point:')
    self.btn1=QPushButton('Break')
    self.btn1.clicked.connect(self.breakPipe)
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.lab3=QLabel('Gap:')
    self.btn2=QPushButton('Get gap')
    self.btn2.clicked.connect(self.changeGap)
    self.slider=QSlider(Qt.Horizontal)
    self.slider.valueChanged.connect(self.changePoint)
    self.slider.setMaximum(100)
    self.grid.addWidget(self.btn0,4,0)
    self.grid.addWidget(self.lab0,4,1,1,1,Qt.AlignCenter)
    self.grid.addWidget(self.lab1,0,0,1,1,Qt.AlignCenter)
    self.grid.addWidget(self.combo,0,1,1,1,Qt.AlignCenter)
    self.grid.addWidget(self.lab2,1,0,1,1,Qt.AlignCenter)
    self.grid.addWidget(self.edit1,1,1)
    self.grid.addWidget(self.lab3,2,0,1,1,Qt.AlignCenter)
    self.grid.addWidget(self.edit2,2,1)
    self.grid.addWidget(self.btn1,3,0)
    self.grid.addWidget(self.btn2,3,1)
    self.grid.addWidget(self.slider,5,0,1,2)
    self.show()
  def setCurrentPL(self,PLName=None):
    if self.combo.currentText() not in ['<none>','<new>']:
      FreeCAD.__activePypeLine__= self.combo.currentText()
    else:
      FreeCAD.__activePypeLine__=None
  def getL(self):
    l=[p.Height for p in frameCmd.beams() if pipeCmd.isPipe(p)]
    if l:
      refL=min(l)
      self.lab0.setText(str(refL))
      self.refL=float(refL)
      self.edit1.setText("%.2f" %(self.refL*self.slider.value()/100.0))
    else:
      self.lab0.setText('<reference>')
      self.refL=0.0
      self.edit1.setText(str(self.slider.value())+'%')
  def changePoint(self):
    if self.refL:
      self.edit1.setText("%.2f" %(self.refL*self.slider.value()/100.0))
    else:
      self.edit1.setText(str(self.slider.value())+'%')
  def changeGap(self):
    shapes=[y for x in FreeCADGui.Selection.getSelectionEx() for y in x.SubObjects if hasattr(y,'ShapeType')]
    if len(shapes)==1:
      sub=shapes[0]
      if sub.ShapeType=='Edge':
        if sub.curvatureAt(0)==0:
          gapL=float(sub.Length)
      else:
        gapL=0
    elif len(shapes)>1:
      gapL=shapes[0].distToShape(shapes[1])[0]
    else:
      gapL=0
    self.edit2.setText("%.2f" %gapL)
  def updateSlider(self):
    if self.edit1.text() and self.edit1.text()[-1]=='%':
      self.slider.setValue(int(float(self.edit1.text().rstrip('%').strip())))
    elif self.edit1.text() and float(self.edit1.text().strip())<self.refL:
      self.slider.setValue(int(float(self.edit1.text().strip())/self.refL*100))
  def calcGapPercent(self):
    if self.edit2.text() and self.edit2.text()[-1]=='%':
      if self.refL:
        self.edit2.setText('%.2f' %(float(self.edit2.text().rstrip('%').strip())/100*self.refL))
      else:
        self.edit2.setText('0')
        FreeCAD.Console.PrintError('No reference length defined yet\n')
  def breakPipe(self):
    p2nd=None
    FreeCAD.activeDocument().openTransaction('Break pipes')
    if self.edit1.text()[-1]=='%':
      pipes=[p for p in frameCmd.beams() if pipeCmd.isPipe(p)]
      for p in pipes:
        p2nd=pipeCmd.breakTheTubes(float(p.Height)*float(self.edit1.text().rstrip('%').strip())/100,pipes=[p],gap=float(self.edit2.text()))
        if p2nd and self.combo.currentText()!='<none>':
          for p in p2nd:
            pipeCmd.moveToPyLi(p,self.combo.currentText())
    else:
      p2nd=pipeCmd.breakTheTubes(float(self.edit1.text()),gap=float(self.edit2.text()))
      if p2nd and self.combo.currentText()!='<none>':
        for p in p2nd:
          pipeCmd.moveToPyLi(p,self.combo.currentText())
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()

import pipeObservers as po

class joinForm(prototypeDialog):
  def __init__(self):
    super(joinForm,self).__init__('joinPypes.ui')
    self.form.btn1.clicked.connect(self.reset)
    self.observer=po.joinObserver()
    FreeCADGui.Selection.addObserver(self.observer)
  def reject(self): #redefined to remove the observer
    info=dict()
    info["State"]="DOWN"
    info["Key"]="ESCAPE"
    self.observer.goOut(info)
    #try: self.view.removeEventCallback('SoEvent',self.call)
    #except: pass
    #FreeCADGui.Control.closeDialog()
    super(joinForm,self).reject()
  def accept(self):
    self.reject()
  def selectAction(self):
    self.reset()
  def reset(self):
    po.pipeCmd.o1=None
    po.pipeCmd.o2=None
    for a in po.pipeCmd.arrows1+po.pipeCmd.arrows2:
      a.closeArrow()
    po.pipeCmd.arrows1=[]
    po.pipeCmd.arrows2=[]

class insertValveForm(protopypeForm):
  '''
  Dialog to insert Valves.
  For position and orientation you can select
    - one or more straight edges (centerlines)
    - one or more curved edges (axis and origin across the center)
    - one or more vertexes 
    - nothing 
  Default valve = DN50 ball valve.
  Available one button to reverse the orientation of the last or selected valves.
  '''
  def __init__(self):
    self.PType='Valve'
    self.PRating=''
    #super(insertValveForm,self).__init__("valves.ui")
    super(insertValveForm,self).__init__("Insert valves","Valve","ball","valve.svg")
    self.move(QPoint(75,225))
    self.sizeList.setCurrentRow(0)
    self.ratingList.setCurrentRow(0)
    self.btn1.clicked.connect(self.insert)
    self.btn2=QPushButton('Reverse')
    self.secondCol.layout().addWidget(self.btn2)
    self.btn2.clicked.connect(self.reverse)
    self.btn3=QPushButton('Apply')
    self.secondCol.layout().addWidget(self.btn3)
    self.btn3.clicked.connect(self.apply)
    self.btn1.setDefault(True)
    self.btn1.setFocus()
    self.sli=QSlider(Qt.Vertical)
    self.sli.setMaximum(100)
    self.sli.setMinimum(1)
    self.sli.setValue(50)
    self.mainHL.addWidget(self.sli)
    self.cb1=QCheckBox(' Insert in pipe')
    self.secondCol.layout().addWidget(self.cb1)
    #self.sli.valueChanged.connect(self.changeL)
    self.show()
    #########
    self.lastValve=None
  def reverse(self): 
      selValves=[p for p in FreeCADGui.Selection.getSelection() if hasattr(p,'PType') and p.PType=='Valve']
      if len(selValves):
        for p in selValves:
          pipeCmd.rotateTheTubeAx(p,FreeCAD.Vector(1,0,0),180)
      else:
        pipeCmd.rotateTheTubeAx(self.lastValve,FreeCAD.Vector(1,0,0),180)
  def insert(self):      
    self.lastValve=None
    color=0.05,0.3,0.75
    d=self.pipeDictList[self.sizeList.currentRow()]
    FreeCAD.activeDocument().openTransaction('Insert valve')
    propList=[d['PSize'],d['VType'],float(pq(d['OD'])),float(pq(d['ID'])),float(pq(d['H'])),float(pq(d['Kv']))]
    if self.cb1.isChecked(): # ..place the valve in the middle of pipe(s)
      pipes=[p for p in FreeCADGui.Selection.getSelection() if hasattr(p,'PType') and p.PType=='Pipe']
      if pipes:
        for p1 in pipes:
          self.lastValve=pipeCmd.makeValve(propList)
          p2=pipeCmd.breakTheTubes(float(p1.Height)*self.sli.value()/100, pipes=[p1], gap=float(self.lastValve.Height))[0]
          if p2 and self.combo.currentText()!='<none>': pipeCmd.moveToPyLi(p2,self.combo.currentText())
          self.lastValve.Placement=p1.Placement
          self.lastValve.Placement.move(pipeCmd.portsDir(p1)[1]*float(p1.Height))
          self.lastValve.ViewObject.ShapeColor=color
          if self.combo.currentText()!='<none>':
            pipeCmd.moveToPyLi(self.lastValve,self.combo.currentText())  
        FreeCAD.ActiveDocument.recompute()
    elif len(frameCmd.edges())==0: #..no edges selected
      vs=[v for sx in FreeCADGui.Selection.getSelectionEx() for so in sx.SubObjects for v in so.Vertexes]
      if len(vs)==0: # ...no vertexes selected
        self.lastValve=pipeCmd.makeValve(propList)
        self.lastValve.ViewObject.ShapeColor=color
        if self.combo.currentText()!='<none>':
          pipeCmd.moveToPyLi(self.lastValve,self.combo.currentText())  
      else:
        for v in vs: # ... one or more vertexes
          self.lastValve=pipeCmd.makeValve(propList,v.Point)
          self.lastValve.ViewObject.ShapeColor=color
          if self.combo.currentText()!='<none>':
            pipeCmd.moveToPyLi(self.lastValve,self.combo.currentText())  
    else:
      selex=FreeCADGui.Selection.getSelectionEx()
      for objex in selex:
        o=objex.Object
        for edge in frameCmd.edges([objex]): # ...one or more edges...
          if edge.curvatureAt(0)==0: # ...straight edges
            self.lastValve=pipeCmd.makeValve(propList,edge.valueAt(edge.LastParameter/2-propList[4]/2),edge.tangentAt(0))
            if self.combo.currentText()!='<none>':
              pipeCmd.moveToPyLi(self.lastValve,self.combo.currentText())  
          else: # ...curved edges
            pos=edge.centerOfCurvatureAt(0) # SNIPPET TO ALIGN WITH THE PORTS OF Pype SELECTED: BEGIN...
            if hasattr(o,'PType') and len(o.Ports)==2:
              p0,p1=pipeCmd.portsPos(o) 
              if (p0-pos).Length<(p1-pos).Length:
                Z=pipeCmd.portsDir(o)[0]
              else:
                Z=pipeCmd.portsDir(o)[1]
            else:
              Z=edge.tangentAt(0).cross(edge.normalAt(0)) # ...END
            self.lastValve=pipeCmd.makeValve(propList,pos,Z)
            if self.combo.currentText()!='<none>':
              pipeCmd.moveToPyLi(self.lastValve,self.combo.currentText())  
          self.lastValve.ViewObject.ShapeColor=color
    FreeCAD.activeDocument().commitTransaction()
    FreeCAD.activeDocument().recompute()
  def apply(self):
    for obj in FreeCADGui.Selection.getSelection():
      d=self.pipeDictList[self.sizeList.currentRow()]
      if hasattr(obj,'PType') and obj.PType==self.PType:
        obj.PSize=d['PSize']
        obj.PRating=self.PRating
        obj.OD=pq(d['OD'])
        obj.ID=pq(d['ID'])
        obj.Height=pq(d['H'])
        obj.Kv=float(d['Kv'])
        FreeCAD.activeDocument().recompute()

import DraftTools,Draft,qForms, polarUtilsCmd
from PySide.QtGui import *
class point2pointPipe(DraftTools.Line):
  '''
  Draw pipes by sequence point.
  '''    
  def __init__(self, wireFlag=True):
    DraftTools.Line.__init__(self,wireFlag)
    self.Activated()
    self.pform=insertPipeForm()
    self.pform.btn1.setText('Reset')
    self.pform.btn1.clicked.disconnect(self.pform.insert)
    self.pform.btn1.clicked.connect(self.rset)
    self.pform.btn3.hide()
    self.pform.edit1.hide()
    self.pform.sli.hide()
    self.pform.cb1=QCheckBox(' Move WP on click ')
    self.pform.cb1.setChecked(True)
    self.pform.firstCol.layout().addWidget(self.pform.cb1)
    dialogPath=join(dirname(abspath(__file__)),"dialogs","hackedline.ui")
    self.hackedUI=FreeCADGui.PySideUic.loadUi(dialogPath)
    self.hackedUI.btnRot.clicked.connect(self.rotateWP)
    self.hackedUI.btnOff.clicked.connect(self.offsetWP)
    self.hackedUI.btnXY.clicked.connect(lambda: self.alignWP(FreeCAD.Vector(0,0,1)))
    self.hackedUI.btnXZ.clicked.connect(lambda: self.alignWP(FreeCAD.Vector(0,1,0)))
    self.hackedUI.btnYZ.clicked.connect(lambda: self.alignWP(FreeCAD.Vector(1,0,0)))
    self.ui.layout.addWidget(self.hackedUI)
    self.start=None
    self.lastPipe=None
    self.nodes=list()
  def alignWP(self, norm):
      FreeCAD.DraftWorkingPlane.alignToPointAndAxis(self.nodes[-1],norm)
      FreeCADGui.Snapper.setGrid()
  def offsetWP(self):
    if hasattr(FreeCAD,'DraftWorkingPlane') and hasattr(FreeCADGui,'Snapper'):
      s=FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").GetInt("gridSize")
      sc=[float(x*s) for x in [1,1,.2]]
      varrow =polarUtilsCmd.arrow(FreeCAD.DraftWorkingPlane.getPlacement(),scale=sc,offset=s)
      offset=QInputDialog.getInteger(None,'Offset Work Plane','Offset: ')
      if offset[1]:
        polarUtilsCmd.offsetWP(offset[0])
      FreeCADGui.ActiveDocument.ActiveView.getSceneGraph().removeChild(varrow.node)
  def rotateWP(self):
    self.form=qForms.rotWPForm()
  def rset(self):
    self.start=None
    self.lastPipe=None
  def action(self,arg): #re-defintition of the method of parent
    "scene event handler"
    if arg["Type"] == "SoKeyboardEvent" and arg["State"]=='DOWN':
      # key detection
      if arg["Key"] == "ESCAPE":
        self.pform.close()
        self.finish()
    elif arg["Type"] == "SoLocation2Event":
      # mouse movement detection
      self.point,ctrlPoint,info = DraftTools.getPoint(self,arg)
    elif arg["Type"] == "SoMouseButtonEvent":
      FreeCAD.activeDocument().openTransaction('point-to-point')
      # mouse button detection
      if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
        if (arg["Position"] == self.pos):
          self.finish(False,cont=True)
        else:
          if (not self.node) and (not self.support):
            DraftTools.getSupport(arg)
            self.point,ctrlPoint,info = DraftTools.getPoint(self,arg)
          if self.point:
            self.ui.redraw()
            self.pos = arg["Position"]
            self.nodes.append(self.point)
            #try:
              #print(arg)
              #print(self.point)
              #print(ctrlPoint)
              #print(info)
            #except:
              #pass
            if not self.start:
              self.start=self.point
            else:
              if self.lastPipe:
                prev=self.lastPipe
              else:
                prev=None
              d=self.pform.pipeDictList[self.pform.sizeList.currentRow()]
              v=self.point-self.start
              propList=[d['PSize'],float(pq(d['OD'])),float(pq(d['thk'])),float(v.Length)]
              self.lastPipe=pipeCmd.makePipe(propList,self.start,v)
              if self.pform.combo.currentText()!='<none>':
                pipeCmd.moveToPyLi(self.lastPipe,self.pform.combo.currentText())
              self.start=self.point
              FreeCAD.ActiveDocument.recompute()
              if prev:
                c= pipeCmd.makeElbowBetweenThings(prev,self.lastPipe, [d['PSize'],float(pq(d['OD'])),float(pq(d['thk'])),90,float(pq(d['OD'])*.75)])
                #c= pipeCmd.makeElbow([d['PSize'],float(pq(d['OD'])),float(pq(d['thk'])),90,float(pq(d['OD'])*.75)])
                #pipeCmd.placeTheElbow(c,pipeCmd.portsDir(prev)[1], pipeCmd.portsDir(self.lastPipe)[1], pipeCmd.portsPos(self.lastPipe)[0])
                #portA, portB = pipeCmd.portsPos(c)
                #frameCmd.extendTheBeam(prev,portA)
                #frameCmd.extendTheBeam(self.lastPipe,portB)
                if c and self.pform.combo.currentText()!='<none>':
                  pipeCmd.moveToPyLi(c,self.pform.combo.currentText())
                FreeCAD.ActiveDocument.recompute()
            if self.pform.cb1.isChecked():
              rot=FreeCAD.DraftWorkingPlane.getPlacement().Rotation
              normal=rot.multVec(FreeCAD.Vector(0,0,1))
              FreeCAD.DraftWorkingPlane.alignToPointAndAxis(self.point,normal)
              FreeCADGui.Snapper.setGrid()
            if (not self.isWire and len(self.node) == 2):
              self.finish(False,cont=True)
            if (len(self.node) > 2):
              if ((self.point-self.node[0]).Length < Draft.tolerance()):
                self.undolast()
                self.finish(True,cont=True)
      FreeCAD.activeDocument().commitTransaction()
  #def finish(self, closed=False, cont=False):
    #self.pform.close()
    #super(point2pointPipe,self).finish(closed,cont)

class insertTankForm(prototypeDialog):
  def __init__(self):
    self.nozzles=list()
    super(insertTankForm,self).__init__('tank.ui')
    tables=listdir(join(dirname(abspath(__file__)),"tables"))
    self.pipeRatings=[s.lstrip("Pipe_").rstrip(".csv") for s in tables if s.startswith("Pipe") and s.endswith('.csv')]
    self.flangeRatings=[s.lstrip("Flange_").rstrip(".csv") for s in tables if s.startswith("Flange") and s.endswith('.csv')]
    self.form.comboPipe.addItems(self.pipeRatings)
    self.form.comboFlange.addItems(self.flangeRatings)
    self.form.btn1.clicked.connect(self.addNozzle)
    self.form.editLength.setValidator(QDoubleValidator())
    self.form.editX.setValidator(QDoubleValidator())
    self.form.editY.setValidator(QDoubleValidator())
    self.form.editZ.setValidator(QDoubleValidator())
    self.form.comboPipe.currentIndexChanged.connect(self.combine)
    self.form.comboFlange.currentIndexChanged.connect(self.combine)
  def accept(self):
    dims=list()
    for lineEdit in [self.form.editX, self.form.editY, self.form.editZ]:
      if lineEdit.text(): 
        dims.append(float(lineEdit.text()))
      else:
        dims.append(1000)
    t=pipeCmd.makeShell(*dims)
    so=None
    if FreeCADGui.Selection.getSelectionEx(): so=FreeCADGui.Selection.getSelectionEx()[0].SubObjects
    if so:
      so0=so[0]
      if so0.Faces:
        t.Placement.Base=so0.Faces[0].CenterOfMass
      elif so0.Edges:
        t.Placement.Base=so0.Edges[0].CenterOfMass
      elif so0.Vertexes:
        t.Placement.Base=so0.Vertexes[0].Point
  def addNozzle(self):
    DN=self.form.listSizes.currentItem().text()
    args=self.nozzles[DN]
    FreeCAD.ActiveDocument.openTransaction('Add nozzles')
    pipeCmd.makeNozzle(DN, float(self.form.editLength.text()), *args)
    FreeCAD.ActiveDocument.commitTransaction()
  def combine(self):
    self.form.listSizes.clear()
    try:
      fileName="Pipe_"+self.form.comboPipe.currentText()+".csv"
      f=open(join(dirname(abspath(__file__)),"tables",fileName),'r')
      reader=csv.DictReader(f,delimiter=';')
      pipes=dict([[line['PSize'],[float(line['OD']),float(line['thk'])]] for line in reader])
      f.close()
      fileName="Flange_"+self.form.comboFlange.currentText()+".csv"
      f=open(join(dirname(abspath(__file__)),"tables",fileName),'r')
      reader=csv.DictReader(f,delimiter=';')
      flanges=dict([[line['PSize'],[float(line['D']), float(line['d']), float(line['df']), float(line['f']), float(line['t']), int(line['n'])]] for line in reader])
      f.close()
    except:
      return
    listNozzles=[[p[0],p[1]+flanges[p[0]]] for p in pipes.items() if p[0] in flanges.keys()]
    self.nozzles=dict(listNozzles)
    self.form.listSizes.addItems(self.nozzles.keys())
    #self.form.listSizes.sortItems()

class insertRouteForm(prototypeDialog):
  '''
  Dialog for makeRoute().
  '''
  def __init__(self):
    FreeCADGui.Selection.clearSelection()
    super(insertRouteForm,self).__init__('route.ui')
    self.normal=FreeCAD.Vector(0,0,1)
    self.L=0
    self.obj=None
    self.edge=None
    self.form.edit1.setValidator(QDoubleValidator())
    self.form.btn1.clicked.connect(self.selectAction)
    self.form.btn2.clicked.connect(self.mouseActionB1)
    self.form.btnX.clicked.connect(lambda: self.getPrincipalAx('X'))
    self.form.btnY.clicked.connect(lambda: self.getPrincipalAx('Y'))
    self.form.btnZ.clicked.connect(lambda: self.getPrincipalAx('Z'))
    self.form.slider.valueChanged.connect(self.changeOffset) #lambda:self.form.edit1.setText(str(self.form.dial.value())))
    #self.form.edit1.editingFinished.connect(self.moveSlider) #lambda:self.form.dial.setValue(int(round(self.form.edit1.text()))))
  def changeOffset(self):
    if self.L:
      offset=self.L*self.form.slider.value()/100
      self.form.edit1.setText('%.1f' %offset)
  def getPrincipalAx(self, ax):
    if ax=='X': self.normal=FreeCAD.Vector(1,0,0)
    elif ax=='Y': self.normal=FreeCAD.Vector(0,1,0)
    elif ax=='Z': self.normal=FreeCAD.Vector(0,0,1)
    self.form.lab1.setText("global "+ax)
  def accept(self, ang=None):
    FreeCAD.ActiveDocument.openTransaction('Make pipe route')
    if frameCmd.edges():
      e=frameCmd.edges()[0]
      if e.curvatureAt(0):
        pipeCmd.makeRoute(self.normal)
      else:
        s=FreeCAD.ActiveDocument.addObject('Sketcher::SketchObject','pipeRoute')
        s.MapMode = "NormalToEdge"
        s.Support = [(self.obj,self.edge)]
        s.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(0,0,-1*float(self.form.edit1.text())),FreeCAD.Rotation(FreeCAD.Vector(0,0,1),0))
        FreeCADGui.activeDocument().setEdit(s.Name)
    FreeCAD.ActiveDocument.commitTransaction()
  def selectAction(self):
    if frameCmd.faces(): 
      self.normal=frameCmd.faces()[0].normalAt(0,0)
    elif frameCmd.edges():
      self.normal=frameCmd.edges()[0].tangentAt(0)
    else:
      self.normal=FreeCAD.Vector(0,0,1)
    self.form.lab1.setText("%.1f,%.1f,%.1f " %(self.normal.x,self.normal.y,self.normal.z))
  def mouseActionB1(self, CtrlAltShift=[False,False,False]):
    v = FreeCADGui.ActiveDocument.ActiveView
    infos = v.getObjectInfo(v.getCursorPos())
    self.form.slider.setValue(0)
    if infos and infos['Component'][:4]=='Edge':
      self.obj=FreeCAD.ActiveDocument.getObject(infos['Object'])
      self.edge=infos['Component']
      i=int(self.edge[4:])-1
      e=self.obj.Shape.Edges[i]
      if e.curvatureAt(0)==0: 
        self.L=e.Length
      else: 
        self.L=0
      self.form.lab2.setText(infos['Object']+': '+self.edge)
    elif frameCmd.edges():
      selex=FreeCADGui.Selection.getSelectionEx()[0]
      self.obj=selex.Object
      e=frameCmd.edges()[0]
      self.edge=frameCmd.edgeName(e)[1]
      self.L=float(e.Length)
      self.form.lab2.setText(self.edge+' of '+self.obj.Label)
    else: 
      self.L=0
      self.obj=None
      self.edge=None
      self.form.lab2.setText('<select an edge>')
      
    
