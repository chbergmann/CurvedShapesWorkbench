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
    return cs.getObj()

        
