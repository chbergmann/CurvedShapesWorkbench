# -*- coding: utf-8 -*-

__title__ = "CurvedArray"
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

global epsilon
epsilon = CurvedShapes.epsilon
    
class CurvedArrayWorker:
    def __init__(self, 
                 obj,
                 base = None,
                 hullcurves=[], 
                 axis=Vector(0.0,0.0,0.0), items=2, ExtraRibs = [],
                 OffsetStart=0, OffsetEnd=0, 
                 Twist=0.0, 
                 Surface=True, 
                 Solid = False,
                 extract=False):
        obj.addProperty("App::PropertyLink",  "Base",     "CurvedArray",   "The object to make an array from").Base = base
        obj.addProperty("App::PropertyLinkList",  "Hullcurves",   "CurvedArray",   "Bounding curves").Hullcurves = hullcurves        
        obj.addProperty("App::PropertyVector", "Axis",    "CurvedArray",   "Direction axis").Axis = axis
        obj.addProperty("App::PropertyQuantity", "Items", "CurvedArray",   "Nr. of array items").Items = items
        obj.addProperty("App::PropertyFloatList","ExtraRibs", "CurvedArray","Positions for extra ribs (as floats from 0.0 to 1.0)").ExtraRibs = []
        obj.addProperty("App::PropertyFloat", "OffsetStart","CurvedArray",  "Offset of the first part in Axis direction").OffsetStart = OffsetStart
        obj.addProperty("App::PropertyFloat", "OffsetEnd","CurvedArray",  "Offset of the last part from the end in opposite Axis direction").OffsetEnd = OffsetEnd
        obj.addProperty("App::PropertyFloat", "Twist","CurvedArray",  "Offset of the last part from the end in opposite Axis direction").Twist = Twist
        obj.addProperty("App::PropertyBool", "Surface","CurvedArray",  "make a surface").Surface = Surface
        obj.addProperty("App::PropertyBool", "Solid","CurvedArray",  "make a solid").Solid = Solid
        self.extract = extract
        self.compound = None
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
         
        areavec = Vector(curvebox.XLength, curvebox.YLength, curvebox.ZLength)
        deltavec = areavec.scale(obj.Axis.x, obj.Axis.y ,obj.Axis.z) - (obj.OffsetStart + obj.OffsetEnd) * obj.Axis
        sections = int(obj.Items)
        startvec = Vector(curvebox.XMin, curvebox.YMin, curvebox.ZMin)
        if obj.Axis.x < 0: startvec.x = curvebox.XMax
        if obj.Axis.y < 0: startvec.y = curvebox.YMax
        if obj.Axis.z < 0: startvec.z = curvebox.ZMax
        pos0 = startvec + (obj.OffsetStart * obj.Axis)      
            

        for n in range(0, sections):
            if sections > 1:
                posvec = pos0 + (deltavec * n / (sections - 1))
            else:
                posvec = pos0
                
            dolly = self.makeRib(obj, posvec)
            if dolly: 
                if not obj.Twist == 0:
                    dolly.rotate(dolly.BoundBox.Center, obj.Axis, obj.Twist * posvec.Length / areavec.Length)
                ribs.append(dolly)

        if (hasattr(obj,"ExtraRibs")):
            for p in obj.ExtraRibs:
                posvec = pos0 + (deltavec * p)
                dolly = self.makeRib(obj, posvec)

                if dolly: 
                    if not obj.Twist == 0:
                        dolly.rotate(dolly.BoundBox.Center, obj.Axis, obj.Twist * posvec.Length / areavec.Length)
                    ribs.append(dolly)  
        
        if self.extract:
            links = []
            for r in ribs:
                f = FreeCAD.ActiveDocument.addObject("Part::Feature","CurvedArrayElement")
                f.Shape = r
                links.append(f)
            
            self.compound = FreeCAD.ActiveDocument.addObject("Part::Compound","CurvedArrayElements")
            self.compound.Links = links
        
        if ((hasattr(obj,"Surface") and obj.Surface) or (hasattr(obj,"Solid") and obj.Solid)) and (obj.Items > 1 or (hasattr(obj,"ExtraRibs") and len(obj.ExtraRibs)>1)):
            obj.Shape = CurvedShapes.makeSurfaceSolid(ribs, obj.Solid)
        else:
            obj.Shape = Part.makeCompound(ribs)
            
        obj.Placement = pl
        

        
        
    def makeRib(self, obj, posvec):
        basebbox = obj.Base.Shape.BoundBox    
        basepl = obj.Base.Placement 
        bbox = CurvedShapes.boundbox_from_intersect(obj.Hullcurves, posvec, obj.Axis, self.doScaleXYZ)
        if not bbox:
            return None
          
        #box = Part.makeBox(max(bbox.XLength, 0.1), max(bbox.YLength, 0.1), max(bbox.ZLength, 0.1))
        #box.Placement.Base.x = bbox.XMin
        #box.Placement.Base.y = bbox.YMin
        #box.Placement.Base.z = bbox.ZMin
        #Part.show(box)        
        
        return CurvedShapes.scaleByBoundbox(obj.Base.Shape, bbox, self.doScaleXYZsum, copy=True)
    
    
    def execute(self, prop):
        if prop.Base and prop.Axis == Vector(0.0,0.0,0.0):
            if hasattr(prop.Base, 'Dir'):
                prop.Axis = prop.Base.Dir
            else:
                prop.Axis = prop.Base.Placement.Rotation.multVec(Vector(0, 0, 1))
            return
        
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
        
        if (hasattr(prop,"ExtraRibs") and len(prop.ExtraRibs) != 0) or (prop.Items and prop.Base and hasattr(prop.Base, "Shape") and len(prop.Hullcurves) > 0):
            self.makeRibs(prop)
            return
        
    def onChanged(self, fp, prop):
        proplist = ["Base", "Hullcurves", "Axis", "Items", "ExtraRibs", "OffsetStart", "OffsetEnd", "Twist", "Surface", "Solid"]
        if prop in proplist:
            if "ExtraRibs" in prop and len(fp.ExtraRibs) != 0:
                outOfBounds = False
                for p in fp.ExtraRibs:
                    if (p < 0.0 or p > 1.0):
                        outOfBounds = True
                        break
                if outOfBounds:
                    FreeCAD.Console.PrintWarning("Some extra rib positions are out of bounds, should all be between 0.0 and 1.0, inclusive\n")
            self.execute(fp)


class CurvedArrayViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
            
    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "curvedArray.svg"))

    def attach(self, vobj):
        self.Object = vobj.Object
        self.onChanged(vobj,"Base")

    def claimChildren(self):
        return [self.Object.Base] + self.Object.Hullcurves
        
    def onDelete(self, feature, subelements):
        return True
    
    def onChanged(self, fp, prop):
        pass
        
    def __getstate__(self):
        return None
 
    def __setstate__(self,state):
        return None
        

class CurvedArray():
        
    def Activated(self):
        FreeCADGui.doCommand("import CurvedShapes")
        
        selection = FreeCADGui.Selection.getSelectionEx()
        options = ""
        for sel in selection:
            if sel == selection[0]:
                options += "Base=base, "
                FreeCADGui.doCommand("base = FreeCAD.ActiveDocument.getObject('%s')"%(selection[0].ObjectName))
                FreeCADGui.doCommand("hullcurves = []");
                options += "Hullcurves=hullcurves, "
            else:
                FreeCADGui.doCommand("hullcurves.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))
        
        FreeCADGui.doCommand("CurvedShapes.makeCurvedArray(%sItems=4, OffsetStart=0, OffsetEnd=0, Surface=False)"%(options))
        FreeCAD.ActiveDocument.recompute()        

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        #if FreeCAD.ActiveDocument:
        return(True)
        #else:
        #    return(False)
        
    def GetResources(self):
        return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "curvedArray.svg"),
                'Accel' : "", # a default shortcut (optional)
                'MenuText': "Curved Array",
                'ToolTip' : "Creates an array and resizes the items in the bounds of curves in the XY, XZ or YZ plane." }

FreeCADGui.addCommand('CurvedArray', CurvedArray())
