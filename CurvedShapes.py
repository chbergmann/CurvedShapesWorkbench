import sys
import os
import FreeCAD
from FreeCAD import Vector
import Part
from importlib import reload

global epsilon
epsilon = 1e-7

def get_module_path():
    """ Returns the current module path.
    Determines where this file is running from, so works regardless of whether
    the module is installed in the app's module directory or the user's app data folder.
    (The second overrides the first.)
    """
    return os.path.dirname(__file__)

    
def scale(obj, delta=Vector(1,1,1), center=Vector(0,0,0)):
    sh = obj.Shape.copy()
    if delta == Vector(1,1,1):
        return sh
    
    #if len(obj.Shape.Solids) > 0:
    #    sh.Placement.Base = Vector(0,0,0)
    #    sh.Placement.Rotation.Angle = -obj.Placement.Rotation.Angle
    #    delta = sh.Placement.Rotation.multVec(delta)
    #    sh.Placement.Rotation.Angle = 0
    
    m = FreeCAD.Matrix()
    m.scale(delta)
    sh = sh.transformGeometry(m)
    corr = Vector(center.x,center.y,center.z)
    corr.scale(delta.x,delta.y,delta.z)
    corr = (corr.sub(center)).negative()
    sh.translate(corr)
    sh.Placement = obj.Placement
    return sh


def PointVec(point):
    """Converts a Part::Point to a FreeCAD::Vector"""
    return Vector(point.X, point.Y, point.Z)

   
def boundbox_from_intersect(curves, pos, normal, doScaleXYZ):        
    if len(curves) == 0:
        return None
    
    plane = Part.Plane(pos, normal)
    xmin = float("inf")
    xmax = float("-inf")
    ymin = float("inf")
    ymax = float("-inf")
    zmin = float("inf")
    zmax = float("-inf")
    found = False
    for n in range(0, len(curves)):
        curve = curves[n]
        ipoints = []
        for edge in curve.Shape.Edges:
            i = plane.intersect(edge.Curve)          
            if i: 
                for p in i[0]:
                    parm = edge.Curve.parameter(PointVec(p))
                    if parm >= edge.FirstParameter and parm <= edge.LastParameter:    
                        ipoints.append(p)
                        found = True
        
        if found == False:
            return None
        
        use_x = True
        use_y = True
        use_z = True
        if len(ipoints) > 1:
            use_x = doScaleXYZ[n][0]
            use_y = doScaleXYZ[n][1]
            use_z = doScaleXYZ[n][2] 
        
        for p in ipoints:
            if use_x and p.X > xmax: xmax = p.X
            if use_x and p.X < xmin: xmin = p.X
            if use_y and p.Y > ymax: ymax = p.Y
            if use_y and p.Y < ymin: ymin = p.Y
            if use_z and p.Z > zmax: zmax = p.Z
            if use_z and p.Z < zmin: zmin = p.Z
      
    if xmin == float("inf") or xmax == float("-inf"):
        xmin = 0
        xmax = 0
    if ymin == float("inf") or ymax == float("-inf"):
        ymin = 0
        ymax = 0
    if zmin == float("inf") or zmax == float("-inf"):
        zmin = 0
        zmax = 0
   
    return FreeCAD.BoundBox(xmin, ymin, zmin, xmax, ymax, zmax)
    
        
def makeCurvedArray(Base = None, 
                    Hullcurves=[], 
                    Axis=Vector(0,0,0), 
                    Items=2, 
                    OffsetStart=0, 
                    OffsetEnd=0, 
                    Twist=0, 
                    Surface=False, 
                    Solid=False, 
                    extract=False):
    import CurvedArray
    reload(CurvedArray)
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","CurvedArray")
    cs = CurvedArray.CurvedArrayWorker(obj, Base, Hullcurves, Axis, Items, OffsetStart, OffsetEnd, Twist, Surface, Solid, extract)
    CurvedArray.CurvedArrayViewProvider(obj.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    return obj


def makeCurvedSegment(Shape1 = None, 
                      Shape2 = None, 
                    Hullcurves=[], 
                    NormalShape1=Vector(0,0,1), 
                    NormalShape2=Vector(0,0,1), 
                    Items=2, 
                    Surface=False, 
                    Solid=False):
    import CurvedSegment
    reload(CurvedSegment)
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","CurvedSegment")
    cs = CurvedSegment.CurvedSegmentWorker(obj, Shape1, Shape2, Hullcurves, NormalShape1, NormalShape2, Items, Surface, Solid)
    CurvedSegment.CurvedSegmentViewProvider(obj.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    return obj
        
