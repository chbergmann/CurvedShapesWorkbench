# -*- coding: utf-8 -*-

__title__ = "NotchConnector"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Cuts notches into an object to make it connectable other objects with a notch"

import os
import FreeCADGui
import FreeCAD
from FreeCAD import Vector
import Part
import CurvedShapes

global epsilon
epsilon = CurvedShapes.epsilon
    
class NotchConnectorWorker:
    def __init__(self, 
                 fp,    # FeaturePython
                 Base,
                 Tools,
                 CutDirection=Vector(0,0,0),
                 Reverse=False):
        fp.addProperty("App::PropertyLink",  "Base",   "NotchConnector",   "Object to cut").Base = Base  
        fp.addProperty("App::PropertyLinkList",  "Tools",   "NotchConnector",   "Object to cut").Tools = Tools        
        fp.addProperty("App::PropertyVector", "CutDirection", "NotchConnector",  "The direction of the cut").CutDirection = CutDirection     
        fp.addProperty("App::PropertyBool", "Reverse", "NotchConnector",  "Reverses the direction of the cut").Reverse = Reverse   
        fp.Proxy = self
        
        
    def onChanged(self, fp, prop):
        proplist = ["Base", "Tools", "CutDirection"]
        if prop in proplist:      
            self.execute(fp)
            
    def execute(self, fp):
        if not fp.Base or not fp.Tools:
            return 
        
        if fp.CutDirection == Vector(0.0,0.0,0.0):
            bbox = self.extractCompounds([fp.Base])[0].Shape.BoundBox
            v = Vector(1,1,1)
            if bbox.XLength < bbox.YLength and bbox.XLength < bbox.ZLength:
                v.x = 0
            elif bbox.YLength < bbox.XLength and bbox.YLength < bbox.ZLength:
                v.y = 0
            else:
                v.z = 0
                
            bbox = self.extractCompounds(fp.Tools)[0].Shape.BoundBox
            if bbox.XLength < bbox.YLength and bbox.XLength < bbox.ZLength:
                v.x = 0
            elif bbox.YLength < bbox.XLength and bbox.YLength < bbox.ZLength:
                v.y = 0
            else:
                v.z = 0
            
            if fp.Reverse:
                v = v * -1
                
            fp.CutDirection = v
            return
            
        self.cutNotches(fp)
        
        
    def extractCompounds(self, obj):
        extracted = []
        for o in obj:
            if hasattr(o, 'Links'):
                extracted += self.extractCompounds(o.Links)
            else:
                extracted.append(o)
                
        return extracted
        
    
    def cutNotches(self, fp):
        shapes = []
        halfsize = fp.CutDirection / 2
        for obj in self.extractCompounds([fp.Base]):
            isExtrude = hasattr(obj, "LengthFwd") and hasattr(obj, "Base")
            if isExtrude:
                bShape = obj.Base.Shape
            else:
                bShape = obj.Shape
                
            cutcubes = []
            for tool in self.extractCompounds(fp.Tools):  
                if len(tool.Shape.Solids) > 0:
                    tbox = tool.Shape.BoundBox
                    common = tool.Shape.common(bShape)
                    cbox = common.BoundBox
                    if cbox.XLength + cbox.YLength + cbox.ZLength > epsilon:
                        vSize = Vector(cbox.XLength, cbox.YLength, cbox.ZLength)
                        vPlace = Vector(cbox.XMin, cbox.YMin, cbox.ZMin)
                        if vSize.x < epsilon: 
                            vSize.x = tbox.XLength
                            vPlace.x = tbox.XMin
                        if vSize.y < epsilon: 
                            vSize.y = tbox.YLength
                            vPlace.y = tbox.YMin
                        if vSize.z < epsilon: 
                            vSize.z = tbox.ZLength   
                            vPlace.z = tbox.ZMin
                            
                        cutcube = Part.makeBox(vSize.x, vSize.y, vSize.z)
                        cutcube.Placement.Base = vPlace
                        cutcube.Placement.Base.x += cbox.XLength * halfsize.x
                        cutcube.Placement.Base.y += cbox.YLength * halfsize.y
                        cutcube.Placement.Base.z += cbox.ZLength * halfsize.z
                        cutcubes.append(cutcube)  
                    
            if len(cutcubes) > 0:
                cutted = bShape.cut(cutcubes)
                if isExtrude:
                    ext = cutted.extrude(obj.Dir * float(obj.LengthFwd + obj.LengthRev))
                    ext.Placement.Base -= obj.Dir * float(obj.LengthRev)                    
                    shapes.append(ext)
                else:
                    shapes.append(cutted)
                
        if len(shapes) == 1:
            fp.Shape = shapes[0]
        elif len(shapes) > 1:
            fp.Shape = Part.makeCompound(shapes)
        
        
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
        
    def __getstate__(self):
        return None
 
    def __setstate__(self,state):
        return None
        

class NotchConnector():
        
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
        
        FreeCADGui.doCommand("CurvedShapes.makeNotchConnector(base, tools, Reverse=False)")
        if len(selection) == 2:
            FreeCADGui.doCommand("CurvedShapes.makeNotchConnector(tools[0], [base], Reverse=True)")            
            
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
                'MenuText': "Notch Connector",
                'ToolTip' : __doc__ }

FreeCADGui.addCommand('NotchConnector', NotchConnector())
