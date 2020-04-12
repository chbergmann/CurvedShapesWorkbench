# -*- coding: utf-8 -*-

__title__ = "CurvedPathArray"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Create 3D shapes from 2D curves"

import sys
import os
import FreeCADGui
import FreeCAD
from FreeCAD import Vector
import Part
import Draft
import CompoundTools.Explode
import CurvedShapes
import math

global epsilon
epsilon = CurvedShapes.epsilon
    
class CurvedPathArrayWorker:
    def __init__(self, 
                 obj,
                 base = None,
                 path = None,
                 hullcurves=[], 
                 items=4, 
                 OffsetStart=0, OffsetEnd=0, 
                 Twist=0.0, 
                 Surface=True, 
                 Solid = False,
                 extract=False):
        obj.addProperty("App::PropertyLink",  "Base",     "CurvedPathArray",   "The object to make an array from").Base = base
        obj.addProperty("App::PropertyLink",  "Path",     "CurvedPathArray",   "Sweep path").Path = path
        obj.addProperty("App::PropertyLinkList",  "Hullcurves",   "CurvedPathArray",   "Bounding curves").Hullcurves = hullcurves   
        obj.addProperty("App::PropertyQuantity", "Items", "CurvedPathArray",   "Nr. of array items").Items = items
        obj.addProperty("App::PropertyFloat", "OffsetStart","CurvedPathArray",  "Offset of the first part").OffsetStart = OffsetStart
        obj.addProperty("App::PropertyFloat", "OffsetEnd","CurvedPathArray",  "Offset of the last part from the end in opposite direction").OffsetEnd = OffsetEnd
        obj.addProperty("App::PropertyFloat", "Twist","CurvedPathArray",  "Rotate in degrees around the sweep path").Twist = Twist
        obj.addProperty("App::PropertyBool", "Surface","CurvedPathArray",  "Make a surface").Surface = Surface
        obj.addProperty("App::PropertyBool", "Solid","CurvedPathArray",  "Make a solid").Solid = Solid
        self.extract = extract
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        obj.Proxy = self
       

    def makeRibs(self, obj):
        pl = obj.Placement
        ribs = []
        curvebox = FreeCAD.BoundBox(float("-inf"), float("-inf"), float("-inf"), float("inf"), float("inf"), float("inf"))
           
        for n in range(0, len(obj.Hullcurves)):
            cbbx = obj.Hullcurves[n].Shape.BoundBox
            if self.doScaleXYZ[n][0]:
                if cbbx.XMin > curvebox.XMin: curvebox.XMin = cbbx.XMin
                if cbbx.XMax < curvebox.XMax: curvebox.XMax = cbbx.XMax
            if self.doScaleXYZ[n][1]:
                if cbbx.YMin > curvebox.YMin: curvebox.YMin = cbbx.YMin
                if cbbx.YMax < curvebox.YMax: curvebox.YMax = cbbx.YMax
            if self.doScaleXYZ[n][2]:
                if cbbx.ZMin > curvebox.ZMin: curvebox.ZMin = cbbx.ZMin
                if cbbx.ZMax < curvebox.ZMax: curvebox.ZMax = cbbx.ZMax
        
        if len(obj.Hullcurves) > 0: 
            if curvebox.XMin == float("-inf"): 
                curvebox.XMin = obj.Hullcurves[0].Shape.BoundBox.XMin
            if curvebox.XMax == float("inf"): 
                curvebox.XMax = obj.Hullcurves[0].Shape.BoundBox.XMax
            if curvebox.YMin == float("-inf"): 
                curvebox.YMin = obj.Hullcurves[0].Shape.BoundBox.YMin
            if curvebox.YMax == float("inf"): 
                curvebox.YMax = obj.Hullcurves[0].Shape.BoundBox.YMax
            if curvebox.ZMin == float("-inf"): 
                curvebox.ZMin = obj.Hullcurves[0].Shape.BoundBox.ZMin
            if curvebox.ZMax == float("inf"): 
                curvebox.ZMax = obj.Hullcurves[0].Shape.BoundBox.ZMax
         
        maxlen = 0   
        edgelen = []     
        for edge in obj.Path.Shape.Edges:
            maxlen += edge.Length
            edgelen.append(edge.Length)
        
        for n in range(0, int(obj.Items)):
            plen = obj.OffsetStart
            if obj.Items > 1:
                plen += (maxlen - obj.OffsetStart - obj.OffsetEnd) * n / (obj.Items - 1)
                
            for edge in obj.Path.Shape.Edges:
                if plen > edge.Length: 
                    plen -= edge.Length
                else:
                    param = edge.getParameterByLength(plen)
                    direction = edge.tangentAt(param) 
                    posvec = edge.valueAt(param) 
                    normal = CurvedShapes.getNormal(obj.Base)
                    rotaxis = normal.cross(direction)
                    angle = math.degrees(normal.getAngle(direction))
            
                    #dolly = self.makeRib(obj, posvec, direction)
                    dolly = obj.Base.Shape.copy()
                    dolly.rotate(dolly.BoundBox.Center, rotaxis, angle)
                    dolly.Placement.Base = posvec
                    if dolly: 
                        if not obj.Twist == 0 and n > 0:
                            dolly.rotate(dolly.BoundBox.Center, direction, obj.Twist * n / int(obj.Items))
                            
                        if len(obj.Hullcurves) > 0:
                            bbox = CurvedShapes.boundbox_from_intersect(obj.Hullcurves, posvec, direction, self.doScaleXYZ)
                            if bbox:
                                dolly = CurvedShapes.scaleByBoundbox(dolly, bbox, self.doScaleXYZsum, copy=True)
                            
                        ribs.append(dolly) 
                        
                    break
        
        
        if (obj.Surface or obj.Solid) and obj.Items > 1:
            obj.Shape = CurvedShapes.makeSurfaceSolid(ribs, obj.Solid)
        else:
            obj.Shape = Part.makeCompound(ribs)
            
        obj.Placement = pl
        
        if self.extract:
            CompoundTools.Explode.explodeCompound(obj)
            obj.ViewObject.hide()

    
    def execute(self, prop):        
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        for h in prop.Hullcurves:
            bbox = h.Shape.BoundBox
            doScale = [False, False, False]
            
            if bbox.XLength > epsilon: 
                doScale[0] = True 
                self.doScaleXYZsum[0] = True
        
            if bbox.YLength > epsilon: 
                doScale[1] = True 
                self.doScaleXYZsum[1] = True
        
            if bbox.ZLength > epsilon: 
                doScale[2] = True 
                self.doScaleXYZsum[2] = True
        
            self.doScaleXYZ.append(doScale)
        
        if prop.Items > 0 and prop.Base and hasattr(prop.Base, "Shape") and prop.Path and hasattr(prop.Path, "Shape") and len(prop.Path.Shape.Edges) > 0:
            self.makeRibs(prop)
            return
        
    def onChanged(self, fp, prop):
        proplist = ["Base", "Hullcurves", "Path", "Items", "OffsetStart", "OffsetEnd", "Twist", "Surface", "Solid"]
        for p in proplist:
            if not hasattr(fp, p):
                return 
            
        if prop in proplist:      
            self.execute(fp)


class CurvedPathArrayViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
            
    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CurvedPathArray.svg"))

    def attach(self, vobj):
        self.Object = vobj.Object
        self.onChanged(vobj,"Base")

    def claimChildren(self):
        return [self.Object.Base, self.Object.Path] + self.Object.Hullcurves
        
    def onDelete(self, feature, subelements):
        return True
    
    def onChanged(self, fp, prop):
        pass
        
    def __getstate__(self):
        return None
 
    def __setstate__(self,state):
        return None
        

class CurvedPathArray():
        
    def Activated(self):
        FreeCADGui.doCommand("import CurvedShapes")
        
        selection = FreeCADGui.Selection.getSelectionEx()
        options = ""
        for sel in selection:
            if sel == selection[0]:
                options += "Base=base, "
                FreeCADGui.doCommand("base = FreeCAD.ActiveDocument.getObject('%s')"%(selection[0].ObjectName))
            elif sel == selection[1]:
                options += "Path=path, "
                FreeCADGui.doCommand("path = FreeCAD.ActiveDocument.getObject('%s')"%(selection[1].ObjectName))
                options += "Hullcurves=hullcurves, "
                FreeCADGui.doCommand("hullcurves = []");
            else:
                FreeCADGui.doCommand("hullcurves.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))
        
        FreeCADGui.doCommand("CurvedShapes.makeCurvedPathArray(%sItems=4, OffsetStart=0, OffsetEnd=0, Surface=False, Solid=False)"%(options))
        FreeCAD.ActiveDocument.recompute()        

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        #if FreeCAD.ActiveDocument:
        return(True)
        #else:
        #    return(False)
        
    def GetResources(self):
        return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CurvedPathArray.svg"),
                'Accel' : "", # a default shortcut (optional)
                'MenuText': "Curved Path Array",
                'ToolTip' : "Creates an array, sweeps the elements around a path curve, and resizes the items in the bounds of optional hullcurves." }

FreeCADGui.addCommand('CurvedPathArray', CurvedPathArray())
