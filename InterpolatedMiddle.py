# -*- coding: utf-8 -*-

__title__ = "InterpolatedMiddle"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Interpolates a 2D shape into the middle between two 2D curves"

import os
import FreeCADGui
import FreeCAD
from FreeCAD import Vector
import Part
import CurvedShapes
import CurvedSegment
from importlib import reload

global epsilon
epsilon = CurvedShapes.epsilon
    
class InterpolatedMiddleWorker:
    def __init__(self, 
                 fp,    # FeaturePython
                 shape1 = None, 
                 shape2 = None, 
                 normalShape1=Vector(0,0,0), 
                 normalShape2=Vector(0,0,0), 
                 surface=False, 
                 solid=False,
                 interpol=16):
        fp.addProperty("App::PropertyLink",  "Shape1",     "InterpolatedMiddle",   "The first object of the segment").Shape1 = shape1
        fp.addProperty("App::PropertyLink",  "Shape2",     "InterpolatedMiddle",   "The last object of the segment").Shape2 = shape2     
        fp.addProperty("App::PropertyVector", "NormalShape1",    "InterpolatedMiddle",   "Direction axis of Shape1").NormalShape1 = normalShape1 
        fp.addProperty("App::PropertyVector", "NormalShape2",    "InterpolatedMiddle",   "Direction axis of Shape2").NormalShape1 = normalShape2
        fp.addProperty("App::PropertyBool", "makeSurface","InterpolatedMiddle",  "make a surface").makeSurface = surface
        fp.addProperty("App::PropertyBool", "makeSolid","InterpolatedMiddle",  "make a solid").makeSolid = solid
        fp.addProperty("App::PropertyInteger", "InterpolationPoints", "CurvedSegment",   "Unequal edges will be splitted into this number of points").InterpolationPoints = interpol
        self.update = True
        fp.Proxy = self
 
    
    def execute(self, fp):
        if not self.update:
            return 
        
        if not fp.Shape1 or not hasattr(fp.Shape1, "Shape"):
            return
        
        if not fp.Shape2 or not hasattr(fp.Shape2, "Shape"):
            return
            
        self.update = False
        if fp.NormalShape1 == Vector(0,0,0):        
            fp.NormalShape1 = CurvedShapes.getNormal(fp.Shape1)
        
        if fp.NormalShape2 == Vector(0,0,0):    
            fp.NormalShape2 = CurvedShapes.getNormal(fp.Shape2)
        
        self.makeRibs(fp)
        
        self.update = True
        
        
    def onChanged(self, fp, prop):
        proplist = ["Shape1", "Shape2", "NormalShape1", "NormalShape2", "makeSurface", "makeSolid"]
        for p in proplist:
            if not hasattr(fp, p):
                return
            
        if prop in proplist:  
            self.execute(fp)
                      
            
    def makeRibs(self, fp):
        interpolate = False
        if len(fp.Shape1.Shape.Edges) != len(fp.Shape2.Shape.Edges):
            interpolate = True
        else:
            for e in range(0, len(fp.Shape1.Shape.Edges)):
                edge1 = fp.Shape1.Shape.Edges[e]
                edge2 = fp.Shape2.Shape.Edges[e]
                curve1 = edge1.Curve.toBSpline()
                curve2 = edge2.Curve.toBSpline()
                poles1 = curve1.getPoles()
                poles2 = curve2.getPoles()
                if len(poles1) != len(poles2):
                    interpolate = True
                    break              
        
        if interpolate:
            ribs = CurvedSegment.makeRibsInterpolate(fp, 1, True)
        else:
            ribs = CurvedSegment.makeRibsSameShape(fp, 1, True)
            
        if fp.makeSurface or fp.makeSolid:
            rib1 = [ribs[0], ribs[1]]
            shape1 = CurvedShapes.makeSurfaceSolid(rib1, fp.makeSolid)
            rib2 = [ribs[1], ribs[2]]
            shape2 = CurvedShapes.makeSurfaceSolid(rib2, fp.makeSolid)
            
            shape = Part.makeCompound([shape1, shape2])
        else:
            shape = Part.makeCompound(ribs)
        
        if shape:
            fp.Shape = shape
                            

class InterpolatedMiddleViewProvider:
    def __init__(self, vfp):
        vfp.Proxy = self
        self.Object = vfp.Object
            
    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CornerShape.svg"))

    def attach(self, vfp):
        self.Object = vfp.Object
        self.onChanged(vfp,"Shape1")

    def claimChildren(self):
        return [self.Object.Shape1, self.Object.Shape2]
        
    def onDelete(self, feature, subelements):
        return True
    
    def onChanged(self, fp, prop):
        pass
        
    def __getstate__(self):
        return None
 
    def __setstate__(self,state):
        return None
        

class InterpolatedMiddle():
        
    def Activated(self):
        FreeCADGui.doCommand("import CurvedShapes")
        reload(CurvedShapes)
        
        selection = FreeCADGui.Selection.getSelectionEx()
        for sel in selection:
            if sel == selection[0]:
                FreeCADGui.doCommand("shape1 = FreeCAD.ActiveDocument.getObject('%s')"%(selection[0].ObjectName))
            elif sel == selection[1]:
                FreeCADGui.doCommand("shape2 = FreeCAD.ActiveDocument.getObject('%s')"%(selection[1].ObjectName))
        
        FreeCADGui.doCommand("CurvedShapes.makeInterpolatedMiddle(shape1, shape2, Surface=False, Solid=False)")
        FreeCAD.ActiveDocument.recompute()        

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        #if FreeCAD.ActiveDocument:
        return(True)
        #else:
        #    return(False)
        
    def GetResources(self):
        return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CornerShape.svg"),
                'Accel' : "", # a default shortcut (optional)
                'MenuText': "Interpolated Middle",
                'ToolTip' : __doc__ }

FreeCADGui.addCommand('InterpolatedMiddle', InterpolatedMiddle())
