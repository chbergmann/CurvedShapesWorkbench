# -*- coding: utf-8 -*-

__title__ = "CurvedArray"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Create 3D shapes from 2D curves"

import os
import FreeCADGui
import FreeCAD
from FreeCAD import Vector
import Part
import CompoundTools.Explode
import CurvedShapes

epsilon = CurvedShapes.epsilon
    
class CurvedArrayWorker:
    def __init__(self, 
                 obj,
                 base = None,
                 hullcurves=[], 
                 axis=Vector(0.0,0.0,0.0), 
                 items=2, 
                 Positions = [],
                 OffsetStart=0, OffsetEnd=0, 
                 Twist=0.0, 
                 Surface=True, 
                 Solid = False,
                 Distribution = 'linear',
                 DistributionReverse = False,
                 extract=False,
                 Twists = []):
        obj.addProperty("App::PropertyLink",  "Base",     "CurvedArray",   "The object to make an array from").Base = base
        obj.addProperty("App::PropertyLinkList",  "Hullcurves",   "CurvedArray",   "Bounding curves").Hullcurves = hullcurves        
        obj.addProperty("App::PropertyVector", "Axis",    "CurvedArray",   "Direction axis").Axis = axis
        obj.addProperty("App::PropertyQuantity", "Items", "CurvedArray",   "Nr. of array items").Items = items
        obj.addProperty("App::PropertyFloatList","Positions", "CurvedArray","Positions for ribs (as floats from 0.0 to 1.0) -- overrides Items").Positions = Positions
        obj.addProperty("App::PropertyFloat", "OffsetStart","CurvedArray",  "Offset of the first part in Axis direction").OffsetStart = OffsetStart
        obj.addProperty("App::PropertyFloat", "OffsetEnd","CurvedArray",  "Offset of the last part from the end in opposite Axis direction").OffsetEnd = OffsetEnd
        obj.addProperty("App::PropertyFloat", "Twist","CurvedArray",  "Rotate around Axis in degrees").Twist = Twist
        obj.addProperty("App::PropertyFloatList","Twists", "CurvedArray","Rotate around Axis in degrees for each item -- overrides Twist").Twists = Twists
        obj.addProperty("App::PropertyBool", "Surface","CurvedArray",  "Make a surface").Surface = Surface
        obj.addProperty("App::PropertyBool", "Solid","CurvedArray",  "Make a solid").Solid = Solid
        obj.addProperty("App::PropertyEnumeration", "Distribution", "CurvedArray",  "Algorithm for distance between elements")
        obj.addProperty("App::PropertyBool", "DistributionReverse", "CurvedArray",  "Reverses direction of Distribution algorithm").DistributionReverse = DistributionReverse
        obj.Distribution = ['linear', 'parabolic', 'x³', 'sinusoidal', 'elliptic']
        obj.Distribution = Distribution
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
            
        if (not hasattr(obj,"Positions") or len(obj.Positions) == 0):
            for x in range(0, sections):            
                if sections > 1:
                    d = CurvedShapes.distribute(x / (sections - 1), obj.Distribution, obj.DistributionReverse)
                                 
                    posvec = pos0 + (deltavec * d)                
                else:
                    posvec = pos0
                		
                rib = self.makeRibRotate(obj, posvec, x, areavec.Length, ribs)
        else:
            x = 0
            for p in obj.Positions:
                posvec = pos0 + (deltavec * p) 
            
                rib = self.makeRibRotate(obj, posvec, x, areavec.Length, ribs)
                x = x + 1       

        
        if (obj.Surface or obj.Solid) and obj.Items > 1:
            obj.Shape = CurvedShapes.makeSurfaceSolid(ribs, obj.Solid)
        else:
            obj.Shape = Part.makeCompound(ribs)
            
        obj.Placement = pl
        
        if self.extract:
            CompoundTools.Explode.explodeCompound(obj)
            obj.ViewObject.hide()
    
    
    def makeRibRotate(self, obj, posvec, x, maxlen, ribs):
        dolly = self.makeRib(obj, posvec)
        if dolly:
            if x < len(obj.Twists):
                dolly.rotate(dolly.BoundBox.Center, obj.Axis, obj.Twists[x])
            elif not obj.Twist == 0:
                dolly.rotate(dolly.BoundBox.Center, obj.Axis, obj.Twist * posvec.Length / maxlen) 
        
            ribs.append(dolly)            
        
    def makeRib(self, obj, posvec):
        bbox = CurvedShapes.boundbox_from_intersect(obj.Hullcurves, posvec, obj.Axis, self.doScaleXYZ, False)
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
            prop.Axis = CurvedShapes.getNormal(prop.Base)
            return
        
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        sumbbox=None   #Define the variable other wise it causes error 
        for h in prop.Hullcurves:
            bbox = h.Shape.BoundBox
            if h == prop.Hullcurves[0]:
                sumbbox = bbox
            else:
                sumbbox.add(bbox)    
                
            doScale = [False, False, False]
            
            if bbox.XLength > epsilon: 
                doScale[0] = True 
        
            if bbox.YLength > epsilon: 
                doScale[1] = True 
        
            if bbox.ZLength > epsilon: 
                doScale[2] = True 
        
            self.doScaleXYZ.append(doScale)
            
        if sumbbox:
            if sumbbox.XLength > epsilon: 
                self.doScaleXYZsum[0] = True 
        
            if sumbbox.YLength > epsilon: 
                self.doScaleXYZsum[1] = True 
        
            if sumbbox.ZLength > epsilon: 
                self.doScaleXYZsum[2] = True          
        
        if (hasattr(prop,"Positions") and len(prop.Positions) != 0) or (prop.Items and prop.Base and hasattr(prop.Base, "Shape") and len(prop.Hullcurves) > 0):
            self.makeRibs(prop)
            return
        
    def onChanged(self, fp, prop):
        proplist = ["Base", "Hullcurves", "Axis", "Items", "Positions", "OffsetStart", "OffsetEnd", "Twist", "Surface", "Solid", "Distribution", "DistributionReverse"]
        for p in proplist:
            if not hasattr(fp, p):
                return

        if prop in proplist:                
            if "Positions" in prop and len(fp.Positions) != 0:
                setattr(fp,"Items",str(len(fp.Positions)))
                outOfBounds = False
                for p in fp.Positions:
                    if (p < 0.0 or p > 1.0):
                        outOfBounds = True
                        break
                if outOfBounds:
                    FreeCAD.Console.PrintWarning("Some positions are out of bounds, should all be between 0.0 and 1.0, inclusive\n")

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
