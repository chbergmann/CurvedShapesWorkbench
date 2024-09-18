# coding=utf-8
import os
import FreeCAD
from FreeCAD import Vector
import Part
import math
import CompoundTools.Explode

epsilon = 1e-7


def addObjectProperty(obj, ptype, pname, *args, init_val=None):
    """
    Adds a property to the object if it does not exist yet - important for upgrading CAD files from older versions of the plugin
    """
    added = False
    if pname not in obj.PropertiesList:
        added = obj.addProperty(ptype, pname, *args)
    if init_val is None:
        return obj
    if added:
        setattr(obj, pname, init_val)
    return obj

def get_module_path():
    """ Returns the current module path.
    Determines where this file is running from, so works regardless of whether
    the module is installed in the app's module directory or the user's app data folder.
    (The second overrides the first.)
    """
    return os.path.dirname(__file__)

    
def scale(shape, delta=Vector(1,1,1), center=Vector(0,0,0), copy=True):
    if copy:
        sh = shape.copy()
    else:
        sh = shape
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
    sh.Placement = shape.Placement
    return sh


def PointVec(point):
    """Converts a Part::Point to a FreeCAD::Vector"""
    return Vector(point.X, point.Y, point.Z)

   
def boundbox_from_intersect(curves, pos, normal, doScaleXYZ, nearestpoints=True):        
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
                    vert=Part.Vertex(p)
                    if vert.distToShape(edge)[0] < epsilon:              
                        if len(ipoints) < 2: 
                            ipoints.append(p) 
                        else:    
                            if nearestpoints:
                                distp = (pos - PointVec(p)).Length
                                dist0 = (pos - PointVec(ipoints[0])).Length
                                dist1 = (pos - PointVec(ipoints[1])).Length
                            
                                if distp < dist0 or distp < dist1:
                                    if dist1 < dist0:
                                        ipoints[0] = p
                                    else:
                                        ipoints[1] = p
                            else:
                                distp = (PointVec(ipoints[0]) - PointVec(ipoints[1])).Length
                                dist0 = (PointVec(p) - PointVec(ipoints[0])).Length
                                dist1 = (PointVec(p) - PointVec(ipoints[1])).Length
                                if distp < dist0 or distp < dist1:
                                    if dist1 > dist0:
                                        ipoints[0] = p
                                    else:
                                        ipoints[1] = p
                         
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


def scaleByBoundbox(shape, boundbox, doScaleXYZ, copy=True):
    basebbox = shape.BoundBox   
      
    scalevec = Vector(1, 1, 1)
    if doScaleXYZ[0] and basebbox.XLength > epsilon: scalevec.x = boundbox.XLength / basebbox.XLength
    if doScaleXYZ[1] and basebbox.YLength > epsilon: scalevec.y = boundbox.YLength / basebbox.YLength
    if doScaleXYZ[2] and basebbox.ZLength > epsilon: scalevec.z = boundbox.ZLength / basebbox.ZLength     
    if scalevec.x < epsilon: 
        if doScaleXYZ[0]:
            scalevec.x = epsilon   
        else:
            scalevec.x = 1   
    if scalevec.y < epsilon: 
        if doScaleXYZ[1]:
            scalevec.y = epsilon   
        else:
            scalevec.y = 1
    if scalevec.z < epsilon: 
        if doScaleXYZ[2]:
            scalevec.z = epsilon   
        else:
            scalevec.z = 1
    
    dolly = scale(shape, scalevec, basebbox.Center, copy)    
    dolly.Placement = shape.Placement
    
    if doScaleXYZ[0]:
        dolly.Placement.Base.x += boundbox.XMin - basebbox.XMin * scalevec.x  
    if doScaleXYZ[1]:           
        dolly.Placement.Base.y += boundbox.YMin - basebbox.YMin * scalevec.y
    if doScaleXYZ[2]:
        dolly.Placement.Base.z += boundbox.ZMin - basebbox.ZMin * scalevec.z
        
    return dolly
    
            
def makeSurfaceSolid(ribs, solid, maxDegree=5):
    surfaces = []

    wiribs = []
    for r in ribs:
        if len(r.Wires) > 0:
            wiribs += r.Wires
        else:
            try:
                wiribs.append(Part.Wire(r.Edges))
            except Exception as ex:
                FreeCAD.Console.PrintError("Cannot make a wire. Creation of surface is not possible !\n")
                return
          
    try:
        loft = Part.makeLoft(wiribs,False,False,False,maxDegree)
        surfaces += loft.Faces
    except Exception as ex:      
        FreeCAD.Console.PrintError("Creation of surface is not possible !\n")
        return Part.makeCompound(wiribs)
         
    if solid:  
        face1 = makeFace(ribs[0])
        if face1:
            surfaces.append(face1)
        face2 = makeFace(ribs[len(ribs)-1])
        if face2:
            surfaces.append(face2)

        try:
            shell = Part.makeShell(surfaces)
            if face1 and face2:
                try:
                    return Part.makeSolid(shell)
                except Exception as ex:
                    FreeCAD.Console.PrintError("Creating solid failed !\n")
                    
        except Exception as ex:
            FreeCAD.Console.PrintError("Creating shell failed !\n")
               
    if len(surfaces) == 1:
        return surfaces[0]
    elif len(surfaces) > 1:
        return Part.makeCompound(surfaces) 

        
        
def makeFace(rib):
    if len(rib.Wires) == 1:
        wire = rib.Wires[0]
    else:
        wire = Part.Wire(rib.Edges)
        
    if wire.isClosed():
        try:
            return Part.makeFace(wire, "Part::FaceMakerSimple")
        except  Exception as ex:
            FreeCAD.Console.PrintError("Cannot make face from Base shape. Cannot draw solid\n") 

    else:
        FreeCAD.Console.PrintError("Base shape is not closed. Cannot draw solid\n")  
         
    return None
     

def getNormal(obj):
    if hasattr(obj, 'Dir'):
        return obj.Dir
    else:
        bbox = obj.Shape.BoundBox
        if bbox.XLength < epsilon: return Vector(1.0,0.0,0.0)
        elif bbox.YLength < epsilon: return Vector(0.0,1.0,0.0)
        elif bbox.ZLength < epsilon: return Vector(0.0,0.0,1.0)
        return obj.Placement.Rotation.multVec(Vector(0, 0, 1))
 

def vectorMiddle(vec1, vec2, fraction):
    x = vec1.x + (vec2.x - vec1.x) * fraction
    y = vec1.y + (vec2.y - vec1.y) * fraction
    z = vec1.z + (vec2.z - vec1.z) * fraction
    return Vector(x,y,z)   


# x is in range 0 to 1. result mut be in range 0 to 1.
def distribute(x, distribution, reverse = False): 
    d = x   # default = 'linear'   
        
    if distribution == 'parabolic':
        d = x*x
    
    if distribution == 'x³':
        d = x*x*x
    
    if distribution == 'sinusoidal':
        d = (math.cos(x * math.pi) + 1) / 2
    
    if distribution == 'asinusoidal':
        d = math.acos(x * 2 - 1) / math.pi
        
    if distribution == 'elliptic':
        d = math.sqrt(1 - x*x)
    
    if reverse:
        d = 1 - d
        
    return d  
        
        
def makeCurvedArray(Base = None, 
                    Hullcurves=[], 
                    Axis=Vector(0,0,0), 
                    Items=2,
                    Position=[],
                    OffsetStart=0, 
                    OffsetEnd=0, 
                    Twist=0, 
                    Surface=False, 
                    Solid=False, 
                    Distribution = 'linear',
                    DistributionReverse = False,
                    extract=False,
                    Twists = []):
    import CurvedArray
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","CurvedArray")
    CurvedArray.CurvedArrayWorker(obj, Base, Hullcurves, Axis, Items, Position, OffsetStart, OffsetEnd, Twist, Surface, Solid, Distribution, DistributionReverse, False, Twists)
    CurvedArray.CurvedArrayViewProvider(obj.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    if not extract:     
        return obj
        
    bang = CompoundTools.Explode.explodeCompound(obj)
    obj.ViewObject.hide()
    return bang[1]


def makeCurvedPathArray(Base = None, 
                    Path = None,
                    Hullcurves=[], 
                    Items=2, 
                    OffsetStart=0, 
                    OffsetEnd=0, 
                    Twist=0, 
                    Surface=False, 
                    Solid=False, 
                    doScale = [True, True, True],
                    extract=False):
    import CurvedPathArray
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","CurvedPathArray")
    CurvedPathArray.CurvedPathArrayWorker(obj, Base, Path, Hullcurves, Items, OffsetStart, OffsetEnd, Twist, Surface, Solid, doScale, extract)
    CurvedPathArray.CurvedPathArrayViewProvider(obj.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    return obj


def makeCurvedSegment(Shape1 = None, 
                      Shape2 = None, 
                    Hullcurves=[], 
                    NormalShape1=Vector(0,0,0), 
                    NormalShape2=Vector(0,0,0), 
                    Items=2, 
                    Surface=False, 
                    Solid=False,
                    InterpolationPoints=16,
                    Twist = 0.0,
                    TwistReverse = False,
                    Distribution = 'linear',
                    DistributionReverse = False):
    import CurvedSegment
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","CurvedSegment")
    CurvedSegment.CurvedSegmentWorker(obj, Shape1, Shape2, Hullcurves, NormalShape1, NormalShape2, Items, Surface, Solid, InterpolationPoints, Twist, TwistReverse, Distribution, DistributionReverse)
    CurvedSegment.CurvedSegmentViewProvider(obj.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    return obj


def makeInterpolatedMiddle(Shape1 = None, 
                    Shape2 = None, 
                    NormalShape1=Vector(0,0,0), 
                    NormalShape2=Vector(0,0,0), 
                    Surface=False, 
                    Solid=False,
                    InterpolationPoints=16,
                    Twist = 0.0,
                    TwistReverse = False):
    import InterpolatedMiddle
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","InterpolatedMiddle")
    InterpolatedMiddle.InterpolatedMiddleWorker(obj, Shape1, Shape2, NormalShape1, NormalShape2, Surface, Solid, InterpolationPoints, Twist, TwistReverse)
    InterpolatedMiddle.InterpolatedMiddleViewProvider(obj.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    return obj     

def cutSurfaces(Surfaces=[], Normal = Vector(1, 0, 0), Position=Vector(0,0,0), Face=False, Simplify=0):    
    import SurfaceCut                  
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","SurfaceCut")
    SurfaceCut.SurfaceCutWorker(obj, Surfaces, Normal, Position, Face, Simplify)
    SurfaceCut.SurfaceCutViewProvider(obj.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    return obj


def makeNotchConnector(Base, Tools, CutDirection=Vector(0,0,0), CutDepth=50.0, ShiftLength=0):
    import NotchConnector                  
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","NotchConnector")
    NotchConnector.NotchConnectorWorker(obj, Base, Tools, CutDirection, CutDepth, ShiftLength)
    NotchConnector.NotchConnectorViewProvider(obj.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    return obj
    
                 
                 
