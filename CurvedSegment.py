# -*- coding: utf-8 -*-

__title__ = "CurvedSegment"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Interpolates a 3D shape between two 2D curves and optional hullcurves"

import os
import FreeCADGui
import FreeCAD
from FreeCAD import Vector
import Part
import CurvedShapes

global epsilon
epsilon = CurvedShapes.epsilon
    
class CurvedSegmentWorker:
    def __init__(self, 
                 fp,    # FeaturePython
                 shape1 = None, 
                 shape2 = None, 
                 hullcurves=[], 
                 normalShape1=Vector(0,0,0), 
                 normalShape2=Vector(0,0,0), 
                 items=2, 
                 surface=False, 
                 solid=False,
                 interpol=16):
        fp.addProperty("App::PropertyLink",  "Shape1",     "CurvedSegment",   "The first object of the segment").Shape1 = shape1
        fp.addProperty("App::PropertyLink",  "Shape2",     "CurvedSegment",   "The last object of the segment").Shape2 = shape2
        fp.addProperty("App::PropertyLinkList",  "Hullcurves",   "CurvedSegment",   "Bounding curves").Hullcurves = hullcurves        
        fp.addProperty("App::PropertyVector", "NormalShape1",    "CurvedSegment",   "Direction axis of Shape1").NormalShape1 = normalShape1 
        fp.addProperty("App::PropertyVector", "NormalShape2",    "CurvedSegment",   "Direction axis of Shape2").NormalShape1 = normalShape2
        fp.addProperty("App::PropertyInteger", "Items", "CurvedSegment",   "Nr. of items between the segments").Items = items
        fp.addProperty("App::PropertyBool", "Surface","CurvedSegment",  "make a surface").Surface = surface
        fp.addProperty("App::PropertyBool", "Solid","CurvedSegment",  "make a solid").Solid = solid
        fp.addProperty("App::PropertyInteger", "InterpolationPoints", "CurvedSegment",   "Unequal edges will be splitted into this number of points").InterpolationPoints = interpol
        self.compound = None
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        fp.Proxy = self
 
    
    def execute(self, fp):
        if not fp.Shape1 or not hasattr(fp.Shape1, "Shape"):
            return
        
        if not fp.Shape2 or not hasattr(fp.Shape2, "Shape"):
            return
            
        if fp.NormalShape1 == Vector(0.0,0.0,0.0):
            if hasattr(fp.Shape1, 'Dir'):
                fp.NormalShape1 = fp.Shape1.Dir
            else:
                fp.NormalShape1 = fp.Shape1.Placement.Rotation.multVec(Vector(0, 0, 1))
            return
        
        if fp.NormalShape2 == Vector(0.0,0.0,0.0):
            if hasattr(fp.Shape2, 'Dir'):
                fp.NormalShape2 = fp.Shape2.Dir
            else:
                fp.NormalShape2 = fp.Shape2.Placement.Rotation.multVec(Vector(0, 0, 1))
            return
        
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        for h in fp.Hullcurves:
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
        
        if fp.Items > 0:
            self.makeRibs(fp)
            return
        
    def onChanged(self, fp, prop):
        proplist = ["Shape1", "Shape2", "Hullcurves", "NormalShape1", "NormalShape2", "Items", "Surface", "Solid", "InterpolationPoints"]
        if prop in proplist:      
            self.execute(fp)
            
    def vectorMiddle(self, vec1, vec2, fraction):
        x = vec1.x + (vec2.x - vec1.x) * fraction
        y = vec1.y + (vec2.y - vec1.y) * fraction
        z = vec1.z + (vec2.z - vec1.z) * fraction
        return Vector(x,y,z)
            
            
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
                 
        if interpolate:
            ribs = self.makeRibsInterpolate(fp)
        else:
            ribs = self.makeRibsSameShape(fp)
            
        if fp.Surface or fp.Solid:
            ribs.insert(0, fp.Shape1.Shape)
            ribs.append(fp.Shape2.Shape)
            fp.Shape = CurvedShapes.makeSurfaceSolid(ribs, fp.Solid)
        else:
            fp.Shape = Part.makeCompound(ribs)
        
            
    def makeRibsSameShape(self, fp):
        ribs = []        
        for i in range(1, fp.Items + 1):
            if len(fp.Shape1.Shape.Edges) == len(fp.Shape2.Shape.Edges):
                for e in range(0, len(fp.Shape1.Shape.Edges)):
                    edge1 = fp.Shape1.Shape.Edges[e]
                    edge2 = fp.Shape2.Shape.Edges[e]
                    curve1 = edge1.Curve.toBSpline()
                    curve2 = edge2.Curve.toBSpline()
                    poles1 = curve1.getPoles()
                    poles2 = curve2.getPoles()
                    newcurve = Part.BSplineCurve()
                    
                    newpoles = []
                    for p in range(len(poles1)):
                        newpoles.append(self.vectorMiddle(poles1[p], poles2[p], i / (fp.Items + 1)))
                        
                    newcurve.buildFromPolesMultsKnots(newpoles, 
                                                  curve1.getMultiplicities(), 
                                                  curve1.getKnots(), 
                                                  curve1.isPeriodic(), 
                                                  curve1.Degree,
                                                  curve1.getWeights(), 
                                                  curve1.isRational())
                   
                    ribs.append(newcurve.toShape())
        return ribs
                    
     
    def makeRibsInterpolate(self, fp):
        points1 = []
        points2 = []
        len1 = len(fp.Shape1.Shape.Wires)
        if len(fp.Shape1.Shape.Wires) == 0:
            len1 = len(fp.Shape1.Shape.Edges)
                       
        len2 = len(fp.Shape2.Shape.Wires)
        if len(fp.Shape2.Shape.Wires) == 0:
            len2 = len(fp.Shape2.Shape.Edges)
        
        nr_points = max(len1, len2) * fp.InterpolationPoints
        if len(fp.Shape1.Shape.Wires) == 0:
            for edge1 in fp.Shape1.Shape.Edges:
                points1 += (edge1.discretize(int(nr_points / len(fp.Shape1.Shape.Edges))))
        else:
            for wire1 in fp.Shape1.Shape.Wires:
                points1 += (wire1.discretize(int(nr_points / len(fp.Shape1.Shape.Wires))))
                
        if len(fp.Shape2.Shape.Wires) == 0:
            for edge2 in fp.Shape2.Shape.Edges:
                points2 += (edge2.discretize(int(nr_points / len(fp.Shape2.Shape.Edges))))
        else:
            for wire2 in fp.Shape2.Shape.Wires:
                points2 += (wire2.discretize(int(nr_points / len(fp.Shape2.Shape.Wires))))
        
        ribs = []
        for i in range(1, fp.Items + 1):
            newpoles = []
            for p in range(0, nr_points):
                newpoles.append(self.vectorMiddle(points1[p], points2[p], i / (fp.Items + 1)))
                
            newcurve = Part.BSplineCurve()
            newcurve.buildFromPoles(newpoles)
            ribs.append(newcurve.toShape())
            
        return ribs
        

class CurvedSegmentViewProvider:
    def __init__(self, vfp):
        vfp.Proxy = self
        self.Object = vfp.Object
            
    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "curvedSegment.svg"))

    def attach(self, vfp):
        self.Object = vfp.Object
        self.onChanged(vfp,"Shape1")

    def claimChildren(self):
        return [self.Object.Shape1, self.Object.Shape2] + self.Object.Hullcurves
        
    def onDelete(self, feature, subelements):
        return True
    
    def onChanged(self, fp, prop):
        pass
        
    def __getstate__(self):
        return None
 
    def __setstate__(self,state):
        return None
        

class CurvedSegment():
        
    def Activated(self):
        FreeCADGui.doCommand("import CurvedShapes")
        
        selection = FreeCADGui.Selection.getSelectionEx()
        options = ""
        for sel in selection:
            if sel == selection[0]:
                FreeCADGui.doCommand("shape1 = FreeCAD.ActiveDocument.getObject('%s')"%(selection[0].ObjectName))
                options += "Shape1=shape1, "
            elif sel == selection[1]:
                FreeCADGui.doCommand("shape2 = FreeCAD.ActiveDocument.getObject('%s')"%(selection[1].ObjectName))
                options += "Shape2=shape2, "
                FreeCADGui.doCommand("hullcurves = []");
                options += "Hullcurves=hullcurves, "
            else:
                FreeCADGui.doCommand("hullcurves.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))
        
        FreeCADGui.doCommand("CurvedShapes.makeCurvedSegment(%sItems=4, Surface=False, Solid=False)"%(options))
        FreeCAD.ActiveDocument.recompute()        

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        #if FreeCAD.ActiveDocument:
        return(True)
        #else:
        #    return(False)
        
    def GetResources(self):
        return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "curvedSegment.svg"),
                'Accel' : "", # a default shortcut (optional)
                'MenuText': "Curved Segment",
                'ToolTip' : __doc__ }

FreeCADGui.addCommand('CurvedSegment', CurvedSegment())
