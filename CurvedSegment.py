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
        for i in range(0, len(ribs)):
            normal = self.vectorMiddle(fp.NormalShape1, fp.NormalShape2, (i + 1) / (fp.Items + 1))
            #Draft.makeLine(ribs[i].BoundBox.Center, ribs[i].BoundBox.Center + normal)
            bbox = CurvedShapes.boundbox_from_intersect(fp.Hullcurves, ribs[i].BoundBox.Center, normal, self.doScaleXYZ)
            if bbox:              
                ribs[i] = CurvedShapes.scaleByBoundbox(ribs[i], bbox, self.doScaleXYZsum, copy=False)
           
            
def vectorMiddle(vec1, vec2, fraction):
    x = vec1.x + (vec2.x - vec1.x) * fraction
    y = vec1.y + (vec2.y - vec1.y) * fraction
    z = vec1.z + (vec2.z - vec1.z) * fraction
    return Vector(x,y,z)    
             
             
def vectorMiddlePlane(vec1, vec2, fraction, plane, normalShape1):
    if normalShape1:
        line = Part.makeLine(vec1, vec1 + normalShape1)
    else:
        line = Part.makeLine(vec1, vec2)
        
    isec = plane.intersect(line.Curve)
    if not isec or len(isec[0]) != 1:
        return vectorMiddle(vec1, vec2, fraction)
    
    return CurvedShapes.PointVec(isec[0][0])  


def getMidPlane(fp, fraction):
    midvec = vectorMiddle(fp.Shape1.Shape.BoundBox.Center, fp.Shape2.Shape.BoundBox.Center, fraction)
    midnorm = vectorMiddle(fp.NormalShape1, fp.NormalShape2, fraction)
    return Part.Plane(midvec, midnorm)
        
        
def makeRibsSameShape(fp, items, alongNormal):
    ribs = []        
    for i in range(1, items + 1):  
        plane = getMidPlane(fp, i / (items + 1))
        
        if alongNormal:
            normalShape1 = fp.NormalShape1
        else:
            normalShape1 = None
        
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
                newpoles.append(vectorMiddlePlane(poles1[p], poles2[p], i / (items + 1), plane, normalShape1))
                
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


def getLengthPoles(shape):
    poles = []
    length = 0
    for edge in shape.Edges:
        length += edge.Length
        curve1= edge.Curve.toBSpline(edge.FirstParameter, edge.LastParameter)
        poles1 = curve1.getPoles()
        for p in poles1:
            if not p in poles:
                poles.append(p)
                
    return (length, poles)


def polesShape1to2(shape1, shape2):
    length1 = 0
    for e1 in shape1.Edges:
        length1 += e1.Length
        
    length2 = 0
    for e2 in shape2.Edges:
        length2 += e2.Length
        
    nr_edges = int(len(shape1.Edges) * len(shape2.Edges) / math.gcd(len(shape1.Edges), len(shape2.Edges)))
    nr_frac = int(nr_edges / len(shape2.Edges))
        
    lengthfrac = length2 / length1
    newpoles = []
    print("length1 " + str(length1) + ", length2 " + str(length2))
    
    offedge2 = 0
    l2 = 0
    
    for edge2 in shape2.Edges:
        for e in range(0, nr_frac):
            edge2len = edge2.Length / nr_frac
            l2 += edge2len
            lparam2 = edge2.LastParameter - edge2.FirstParameter 
            firstparam2 = edge2.FirstParameter + lparam2 * e / nr_frac
            lastparam2 = edge2.FirstParameter + lparam2 * (e + 1) / nr_frac
            curve2 = edge2.Curve.toBSpline(firstparam2, lastparam2)
            poles2 = curve2.getPoles()  
            
            offedge1 = 0  
            for edge1 in shape1.Edges:
                curve1 = edge1.Curve.toBSpline(edge1.FirstParameter, edge1.LastParameter)
                poles1 = curve1.getPoles()
            
                for p1 in poles1:
                    offsetp1 = (offedge1 + (edge1.Length * curve1.parameter(p1) / (curve1.LastParameter - curve1.FirstParameter))) * lengthfrac
                    if offsetp1 >= offedge2 and offsetp1 <= offedge2 + edge2len:    
                        newparam1 = (offsetp1 - offedge2) * (lastparam2 - firstparam2) / lparam2
                        pnt = edge2.valueAt(newparam1)
                        #print(pnt)
                        #Draft.makePoint(pnt.x, pnt.y, pnt.z)
                 
                        found = False
                        for i in range (0, len(poles2)):
                            try:
                                param2 = curve2.parameter(poles2[i])
                                if newparam1 >= param2 and newparam1 <= lastparam2:
                                    poles2.insert(i, pnt)
                                    found = True
                                    break
                            except: 
                                print("except " + str(i))
                                del poles2[i]
                        
                        if not found:
                            poles2.append(pnt)   
                                                   
                offedge1 += edge1.Length    
                
            offedge2 += edge2len
            newpoles.append(poles2)
         
    return newpoles


def removeDoubles(points):
    newpoints = []
    for p in points:
        found = False
        for n in newpoints:
            if (p - n).Length < epsilon:
                found = True
                break
            
        if not found:
            newpoints.append(p)
            
    return newpoints

               
 
def makeRibsInterpolate(fp, items, alongNormal):   
    ribs = []                        
    newpoles1 = polesShape1to2(fp.Shape1.Shape, fp.Shape2.Shape)
    newpoles2 = polesShape1to2(fp.Shape2.Shape, fp.Shape1.Shape)
    
    for n in newpoles1:
        for pnt in n:
            Draft.makePoint(pnt.x, pnt.y, pnt.z)
    
    for n in newpoles2:
        for pnt in n:
            Draft.makePoint(pnt.x, pnt.y, pnt.z)
   
    for i in range(1, items + 1):     
        plane = getMidPlane(fp, i / (items + 1))
        
        if alongNormal:
            normalShape1 = fp.NormalShape1
        else:
            normalShape1 = None
            
        for i in range(0, len(newpoles1)):
            interpoles = []
            for p in range(0, len(newpoles1[i])):
                pnt = vectorMiddlePlane(newpoles1[i][p], newpoles2[i][p], i / (items + 1), plane, normalShape1)
                Draft.makePoint(pnt.x, pnt.y, pnt.z)
                interpoles.append(pnt)
            
            newcurve = Part.BSplineCurve()
            newcurve.buildFromPolesMultsKnots(interpoles)
            ribs.append(newcurve.toShape())
            
    if fp.makeSurface or fp.makeSolid:
        ribs.insert(0, fp.Shape1.Shape)
        ribs.append(fp.Shape2.Shape)
        
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
        
        FreeCADGui.doCommand("CurvedShapes.makeCurvedSegment(%sItems=1, Surface=False, Solid=False)"%(options))
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
