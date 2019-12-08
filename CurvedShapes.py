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
                    vert=Part.Vertex(p)
                    if vert.distToShape(edge)[0] < epsilon:    
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


def scaleByBoundbox(shape, boundbox, doScaleXYZ, copy=True):
    basebbox = shape.BoundBox   
      
    scalevec = Vector(1, 1, 1)
    if basebbox.XLength > epsilon: scalevec.x = boundbox.XLength / basebbox.XLength
    if basebbox.YLength > epsilon: scalevec.y = boundbox.YLength / basebbox.YLength
    if basebbox.ZLength > epsilon: scalevec.z = boundbox.ZLength / basebbox.ZLength     
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
    
            
def makeSurfaceSolid(ribs, solid):
    surfaces = []

    wiribs = []
    for r in ribs:
        if len(r.Wires) > 0:
            wiribs += r.Wires
        else:
            try:
                wiribs.append(Part.Wire(r.Edges))
            except:
                FreeCAD.Console.PrintError("Cannot make a wire. Creation of surface is not possible !\n")
                return
          
    try: 
        loft = Part.makeLoft(wiribs)
        surfaces += loft.Faces
    except:      
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
                except:
                    FreeCAD.Console.PrintError("Creating solid failed !\n")
        except:
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
        except:
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
                    NormalShape1=Vector(0,0,0), 
                    NormalShape2=Vector(0,0,0), 
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


def makeInterpolatedMiddle(Shape1 = None, 
                    Shape2 = None, 
                    NormalShape1=Vector(0,0,0), 
                    NormalShape2=Vector(0,0,0), 
                    Surface=False, 
                    Solid=False):
    import InterpolatedMiddle
    reload(InterpolatedMiddle)
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","InterpolatedMiddle")
    cs = InterpolatedMiddle.InterpolatedMiddleWorker(obj, Shape1, Shape2, NormalShape1, NormalShape2, Surface, Solid)
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


def makeNotchConnector(Base, Tools, CutDirection=Vector(0,0,0), CutDepth=50.0):
    import NotchConnector                  
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","NotchConnector")
    NotchConnector.NotchConnectorWorker(obj, Base, Tools, CutDirection, CutDepth)
    NotchConnector.NotchConnectorViewProvider(obj.ViewObject)
    FreeCAD.ActiveDocument.recompute()
    return obj
    
                 
                 
