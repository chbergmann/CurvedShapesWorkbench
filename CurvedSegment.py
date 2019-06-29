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
import Draft
import math

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
        fp.addProperty("App::PropertyBool", "makeSurface","CurvedSegment",  "make a surface").makeSurface = surface
        fp.addProperty("App::PropertyBool", "makeSolid","CurvedSegment",  "make a solid").makeSolid = solid
        fp.addProperty("App::PropertyInteger", "InterpolationPoints", "CurvedSegment",   "Unequal edges will be splitted into this number of points").InterpolationPoints = interpol
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
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
        
        self.update = True
        
        
    def onChanged(self, fp, prop):
        proplist = ["Shape1", "Shape2", "Hullcurves", "NormalShape1", "NormalShape2", "Items", "makeSurface", "makeSolid", "InterpolationPoints"]
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
            ribs = makeRibsInterpolate(fp, fp.Items, False)
        else:
            ribs = makeRibsSameShape(fp, fp.Items, False)
            
        if len(fp.Hullcurves) > 0:
            self.rescaleRibs(fp, ribs)
            
        if fp.makeSurface or fp.makeSolid:
            fp.Shape = CurvedShapes.makeSurfaceSolid(ribs, fp.makeSolid)
        else:
            fp.Shape = Part.makeCompound(ribs)
        
        
    def rescaleRibs(self, fp, ribs):
        if fp.makeSurface or fp.makeSolid:
            start = 1
            end = len(ribs) - 1
            items = fp.Items + 3
        else:   
            start = 0
            end = len(ribs) 
            items = fp.Items + 1
            
        for i in range(start, end):
            normal = CurvedShapes.vectorMiddle(fp.NormalShape1, fp.NormalShape2, (i + 1) / items)
            #Draft.makeLine(ribs[i].BoundBox.Center, ribs[i].BoundBox.Center + normal)
            bbox = CurvedShapes.boundbox_from_intersect(fp.Hullcurves, ribs[i].BoundBox.Center, normal, self.doScaleXYZ)
            if bbox:              
                ribs[i] = CurvedShapes.scaleByBoundbox(ribs[i], bbox, self.doScaleXYZsum, copy=False)
           
             
             
             
def vectorMiddlePlane(vec1, vec2, fraction, plane):
    line = Part.makeLine(vec1, vec2)
        
    isec = plane.intersect(line.Curve)
    if not isec or len(isec[0]) != 1:
        return CurvedShapes.vectorMiddle(vec1, vec2, fraction)
    
    return CurvedShapes.PointVec(isec[0][0]) 


def vectorMiddlePlaneNormal1(vec1, normalShape1, plane):
    line1 = Part.makeLine(vec1, vec1 + normalShape1)
        
    p1 = vec1
    isec = plane.intersect(line1.Curve)
    if isec and len(isec[0]) == 1:
        p1 = CurvedShapes.PointVec(isec[0][0])
        
    return p1
        
def vectorMiddlePlaneNormal(vec1, vec2, plane, normalShape1, normalShape2):
    p1 = vectorMiddlePlaneNormal1(vec1, normalShape1, plane)
    p2 = vectorMiddlePlaneNormal1(vec2, normalShape2, plane)
        
    return CurvedShapes.vectorMiddle(p1, p2, 0.5)  


def getMidPlane(fp, fraction):
    midvec = CurvedShapes.vectorMiddle(fp.Shape1.Shape.BoundBox.Center, fp.Shape2.Shape.BoundBox.Center, fraction)
    midnorm = CurvedShapes.vectorMiddle(fp.NormalShape1, fp.NormalShape2, fraction)
    return Part.Plane(midvec, midnorm)
        
        
def makeRibsSameShape(fp, items, alongNormal):
    ribs = []        
    for i in range(1, items + 1):  
        plane = getMidPlane(fp, i / (items + 1))
        
        for e in range(0, len(fp.Shape1.Shape.Edges)):
            edge1 = fp.Shape1.Shape.Edges[e]
            edge2 = fp.Shape2.Shape.Edges[e]
            curve1 = edge1.Curve.toBSpline(edge1.FirstParameter, edge1.LastParameter)
            curve2 = edge2.Curve.toBSpline(edge2.FirstParameter, edge2.LastParameter)
            poles1 = curve1.getPoles()
            poles2 = curve2.getPoles()
            newcurve = Part.BSplineCurve()
            
            newpoles = []
            for p in range(len(poles1)):
                if alongNormal:
                    newpoles.append(vectorMiddlePlaneNormal(poles1[p], poles2[p], plane, fp.NormalShape1, fp.NormalShape2))
                else:
                    newpoles.append(vectorMiddlePlane(poles1[p], poles2[p], plane))
                    
                
            newcurve.buildFromPolesMultsKnots(newpoles, 
                                          curve1.getMultiplicities(), 
                                          curve1.getKnots(), 
                                          curve1.isPeriodic(), 
                                          curve1.Degree,
                                          curve1.getWeights(), 
                                          curve1.isRational())
           
            ribs.append(newcurve.toShape())
            
    if fp.makeSurface or fp.makeSolid:
        ribs.insert(0, fp.Shape1.Shape)
        ribs.append(fp.Shape2.Shape)
        
    return ribs
                
 
def makeRibsInterpolate(fp, items, alongNormal):
    len1 = len(fp.Shape1.Shape.Edges)
    len2 = len(fp.Shape2.Shape.Edges)
    
    nr_edges = int(len1 * len2 / math.gcd(len1, len2))

    pointslist1 = EdgesToPoints(fp.Shape1.Shape, int(nr_edges / len1), int(fp.InterpolationPoints))
    pointslist2 = EdgesToPoints(fp.Shape2.Shape, int(nr_edges / len2), int(fp.InterpolationPoints))
            
    ribs = []
    if fp.makeSurface or fp.makeSolid:
        start = 0
        end = items + 2 
    else:   
        start = 1
        end = items + 1 
        
    for i in range(start, end):
        plane = getMidPlane(fp, i / (items + 1))
        newshape = []
        for l in range(0, len(pointslist1)):
            points1 = pointslist1[l]
            points2 = pointslist2[l]
            newpoles = []
            for p in range(0, fp.InterpolationPoints):
                if alongNormal:
                    newpoles.append(vectorMiddlePlaneNormal(points1[p], points2[p], plane, fp.NormalShape1, fp.NormalShape2))
                else:
                    newpoles.append(vectorMiddlePlane(points1[p], points2[p], plane))     
            
            bc = Part.BSplineCurve()
            bc.approximate(newpoles)
            newshape.append(bc)
        
        if len(newshape) == 1:
            ribs.append(newshape[0].toShape())
        else:
            shapes = []
            for n in newshape:
                shapes.append(n.toShape())
                
            comp = Part.makeCompound(shapes)
                
            try:
                wire = Part.Wire(comp.Edges)
                ribs.append(wire)
            except:
                ribs.append(comp)
        
    return ribs


def EdgesToPoints(shape, nr_frac, points_per_edge):   
    edges = []
    if nr_frac == 1:
        edges = shape.Edges
    else:
        for edge in shape.Edges:
            edge1 = edge
            for f in range(0, nr_frac - 1):
                wires1 = edge1.split(edge1.FirstParameter + (edge1.LastParameter - edge1.FirstParameter) / nr_frac)
                edges.append(wires1.Edges[0])
                edge1 = wires1.Edges[1]
            
            edges.append(wires1.Edges[1])
                
    llpoints = []
    for edge in edges:
        edge.Placement = shape.Placement
        llpoints.append(edge.discretize(points_per_edge))
        
    return llpoints

        

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
