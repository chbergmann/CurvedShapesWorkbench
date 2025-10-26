# -*- coding: utf-8 -*-
from PySide.QtCore import QT_TRANSLATE_NOOP

__title__ = "NotchConnector"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = QT_TRANSLATE_NOOP("NotchConnector", "Cuts notches into an object to make it connectable other objects with a notch")

import os
import FreeCAD
from FreeCAD import Vector
import Part
import CurvedShapes
if FreeCAD.GuiUp:
    import FreeCADGui

epsilon = 1e-6
translate = FreeCAD.Qt.translate

class NotchConnector:
    def __init__(self, 
                 fp,    # FeaturePython
                 Base,
                 Tools,
                 CutDirection=Vector(0,0,0),
                 CutDepth=50.0,
                 ShiftLength=0):
        fp.addProperty("App::PropertyLink", "Base", "NotchConnector", QT_TRANSLATE_NOOP("App::Property", "Object to cut")).Base = Base
        fp.addProperty("App::PropertyLinkList", "Tools", "NotchConnector", QT_TRANSLATE_NOOP("App::Property", "Object to cut")).Tools = Tools
        fp.addProperty("App::PropertyVector", "CutDirection", "NotchConnector", QT_TRANSLATE_NOOP("App::Property", "The direction of the cut")).CutDirection = CutDirection
        fp.addProperty("App::PropertyFloat", "CutDepth", "NotchConnector", QT_TRANSLATE_NOOP("App::Property", "Length of the cut in percent")).CutDepth = CutDepth
        fp.addProperty("App::PropertyFloat", "ShiftLength", "NotchConnector", QT_TRANSLATE_NOOP("App::Property", "Shift the tools, then cut. Overrides CutDepth if not zero")).ShiftLength = ShiftLength
        fp.Proxy = self


    def onChanged(self, fp, prop):
        proplist = ["Base", "Tools", "CutDirection", "ShiftLength"]

        if prop == "CutDepth" and fp.CutDirection != Vector(0.0,0.0,0.0):
            cdep = 100 - abs(fp.CutDepth)
            fp.CutDirection = fp.CutDirection.normalize() * cdep / 50


    def execute(self, fp):
        if not fp.Base or not fp.Tools:
            return 

        fp.Proxy = None
        if fp.CutDirection == Vector(0.0,0.0,0.0):
            bbox1 = self.extractCompounds([fp.Base])[0].Shape.BoundBox
            bbox2 = self.extractCompounds(fp.Tools)[0].Shape.BoundBox
            v = Vector(1,1,1)

            if abs(bbox1.XLength - bbox2.XLength) > epsilon:
                v.x = 0
            if abs(bbox1.YLength - bbox2.YLength) > epsilon:
                v.y = 0
            if abs(bbox1.ZLength - bbox2.ZLength) > epsilon:
                v.z = 0

            if v.Length < epsilon:
                v = Vector(1,1,1)
                if bbox1.XLength < bbox1.YLength and bbox1.XLength < bbox1.ZLength:
                    v.x = 0
                elif bbox1.YLength <= bbox1.XLength and bbox1.YLength < bbox1.ZLength:
                    v.y = 0
                else:
                    v.z = 0
                    
                if bbox2.XLength < bbox2.YLength and bbox2.XLength < bbox2.ZLength:
                    v.x = 0
                elif bbox2.YLength <= bbox2.XLength and bbox2.YLength < bbox2.ZLength:
                    v.y = 0
                else:
                    v.z = 0            

            fp.CutDirection = v * fp.CutDepth / 50

        fp.Proxy = self
        self.cutNotches(fp)
        fp.Base.ViewObject.hide()


    def extractCompounds(self, obj):
        extracted = []
        for o in obj:
            if o.TypeId == 'Part::Compound':
                extracted += self.extractCompounds(o.Links)
            else:
                extracted.append(o)

        return extracted


    def extractShapes(self, lobj):
        shapes = []
        for obj in lobj:
            if len(obj.Shape.Solids) > 0:
                shapes += obj.Shape.Solids
            else:
                shapes += obj.Shape.Faces

        return shapes


    def cutNotches(self, fp):
        shapes = []
        halfsize = fp.CutDirection / 2
        for obj in self.extractCompounds([fp.Base]):
            useSubPart = obj.TypeId == 'Part::Extrusion' and len(obj.Base.Shape.Faces) > 0
            if useSubPart:
                bShapes = obj.Base
            else:
                bShapes = obj

            for bShape in self.extractShapes([bShapes]):    
                cutcubes = []

                for tool in self.extractShapes(fp.Tools):  
                    if fp.ShiftLength == 0:  
                        tbox = tool.optimalBoundingBox()
                        common = tool.common(bShape)
                        cbox = common.BoundBox
                        if cbox.XLength + cbox.YLength + cbox.ZLength > epsilon:
                            cbox = common.optimalBoundingBox()
                            vSize = Vector(cbox.XLength, cbox.YLength, cbox.ZLength)
                            vPlace = Vector(cbox.XMin, cbox.YMin, cbox.ZMin)
                            if vSize.x < epsilon or vSize.x > tbox.XLength: 
                                vSize.x = tbox.XLength
                                vPlace.x = tbox.XMin
                            if vSize.y < epsilon or vSize.y > tbox.YLength: 
                                vSize.y = tbox.YLength
                                vPlace.y = tbox.YMin
                            if vSize.z < epsilon or vSize.z > tbox.ZLength: 
                                vSize.z = tbox.ZLength   
                                vPlace.z = tbox.ZMin

                            cutcube = Part.makeBox(vSize.x, vSize.y, vSize.z)
                            cutcube.Placement.Base = vPlace           
                            cutcube.Placement.Base.x += cbox.XLength * halfsize.x
                            cutcube.Placement.Base.y += cbox.YLength * halfsize.y
                            cutcube.Placement.Base.z += cbox.ZLength * halfsize.z
                            cutcubes.append(cutcube)
                    else:
                        cutcube = tool.copy()
                        cutcube.Placement.Base = tool.Placement.Base + fp.CutDirection * fp.ShiftLength                        
                        cutcubes.append(cutcube)                            

                if len(cutcubes) > 0:
                    try:
                        cutted = bShape.cut(cutcubes)
                    except Exception as ex:
                        cutted = bShape

                else:
                    cutted = bShape

                if useSubPart:
                    cutted.Placement.Base -= obj.Dir * float(obj.LengthRev)               
                    ext = cutted.extrude(obj.Dir * float(obj.LengthFwd + obj.LengthRev))
                    shapes.append(ext)
                else:
                    shapes.append(cutted)

        fp.Shape = Part.makeCompound(shapes)


#background compatibility
NotchConnectorWorker = NotchConnector

class NotchConnectorViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object


    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "NotchConnector.svg"))


    def attach(self, vobj):
        self.Object = vobj.Object
        self.onChanged(vobj,"Base")


    def claimChildren(self):
        childs = [self.Object.Base] + self.Object.Tools
        for c in childs:
            c.ViewObject.hide()
        return childs


    def onDelete(self, feature, subelements):
        return True


    def onChanged(self, fp, prop):
        pass


    def loads(self, state):
        return None


    def dumps(self):
        return None


    def __getstate__(self):
        return None


    def __setstate__(self,state):
        return None


if FreeCAD.GuiUp:

    class NotchConnectorCommand():
        def Activated(self):
            FreeCADGui.doCommand("import CurvedShapes")
            FreeCADGui.doCommand("import NotchConnector")

            selection = FreeCADGui.Selection.getSelection()
            if len(selection) < 2:
                return;

            for sel in selection:
                if sel == selection[0]:
                    FreeCADGui.doCommand("base = FreeCAD.ActiveDocument.getObject('%s')"%(sel.Name))
                elif sel == selection[1]:
                    FreeCADGui.doCommand("tools = [FreeCAD.ActiveDocument.getObject('%s')]"%(sel.Name))
                else:
                    FreeCADGui.doCommand("tools.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.Name))

            FreeCADGui.doCommand("CurvedShapes.makeNotchConnector(base, tools, CutDepth=50.0)")
            if len(selection) == 2:
                FreeCADGui.doCommand("CurvedShapes.makeNotchConnector(tools[0], [base], CutDepth=-50.0)")            

            FreeCAD.ActiveDocument.recompute()        


        def IsActive(self):
            """Here you can define if the command must be active or not (greyed) if certain conditions
            are met or not. This function is optional."""
            if FreeCAD.ActiveDocument:
                return(True)
            else:
                return(False)


        def GetResources(self):
            return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "NotchConnector.svg"),
                    'Accel' : "", # a default shortcut (optional)
                    'MenuText': QT_TRANSLATE_NOOP("NotchConnector", "Notch Connector"),
                    'ToolTip' : QT_TRANSLATE_NOOP("NotchConnector", __doc__)}


    FreeCADGui.addCommand('NotchConnector', NotchConnectorCommand())
