# -*- coding: utf-8 -*-

__title__ = "CurvedSegment"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Interpolates a 3D shape between two 2D curves and optional hullcurves"

import os
import FreeCAD
from FreeCAD import Vector
import Part
import CurvedShapes
import math
if FreeCAD.GuiUp:
    import FreeCADGui

from PySide.QtCore import QT_TRANSLATE_NOOP

epsilon = CurvedShapes.epsilon
translate = FreeCAD.Qt.translate

class CurvedSegment:
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
                 InterpolationPoints=16,
                 Twist = 0.0,
                 TwistReverse = False,
                 Distribution = 'linear',
                 DistributionReverse = False,
                 LoftMaxDegree=5,
                 MaxLoftSize=16,
                 Path=None,
                 ForceInterpolated = False):
        CurvedShapes.addObjectProperty(fp,"App::PropertyLink", "Shape1", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "The first object of the segment")).Shape1 = shape1
        CurvedShapes.addObjectProperty(fp,"App::PropertyLink", "Shape2", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "The last object of the segment")).Shape2 = shape2
        CurvedShapes.addObjectProperty(fp,"App::PropertyLinkList", "Hullcurves", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Bounding curves")).Hullcurves = hullcurves        
        CurvedShapes.addObjectProperty(fp,"App::PropertyVector", "NormalShape1", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Direction axis of Shape1")).NormalShape1 = normalShape1 
        CurvedShapes.addObjectProperty(fp,"App::PropertyVector", "NormalShape2", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Direction axis of Shape2")).NormalShape1 = normalShape2
        CurvedShapes.addObjectProperty(fp,"App::PropertyInteger", "Items", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Nr. of items between the segments")).Items = items
        CurvedShapes.addObjectProperty(fp,"App::PropertyBool", "makeSurface","CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Make a surface")).makeSurface = surface
        CurvedShapes.addObjectProperty(fp,"App::PropertyBool", "makeSolid","CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Make a solid")).makeSolid = solid
        CurvedShapes.addObjectProperty(fp,"App::PropertyInteger", "InterpolationPoints", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Unequal edges will be split into this number of points")).InterpolationPoints = InterpolationPoints
        CurvedShapes.addObjectProperty(fp,"App::PropertyFloat", "Twist","CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Compensates a rotation between Shape1 and Shape2")).Twist = Twist
        CurvedShapes.addObjectProperty(fp,"App::PropertyBool", "TwistReverse","CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Reverses the rotation of one Shape")).TwistReverse = TwistReverse
        CurvedShapes.addObjectProperty(fp,"App::PropertyEnumeration", "Distribution", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Algorithm for distance between elements"))
        CurvedShapes.addObjectProperty(fp,"App::PropertyBool", "DistributionReverse", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Reverses direction of Distribution algorithm")).DistributionReverse = DistributionReverse
        CurvedShapes.addObjectProperty(fp,"App::PropertyInteger", "LoftMaxDegree", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Max Degree for Surface or Solid")).LoftMaxDegree = LoftMaxDegree
        CurvedShapes.addObjectProperty(fp,"App::PropertyInteger", "MaxLoftSize", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Max Size of a Loft in Segments.")).MaxLoftSize = MaxLoftSize
        CurvedShapes.addObjectProperty(fp,"App::PropertyLink", "Path", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Sweep path")).Path = Path
        CurvedShapes.addObjectProperty(fp,"App::PropertyBool", "ForceInterpolated", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Force Interpolation of sketches")).ForceInterpolated = ForceInterpolated
        fp.Distribution = ['linear', 'parabolic', 'x³', 'sinusoidal', 'asinusoidal', 'elliptic']
        fp.Distribution = Distribution
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        self.update = True
        fp.Proxy = self


    def execute(self, fp):
        if not self.update:
            return 

        if not fp.Shape1 or not hasattr(fp.Shape1, "Shape") or len(fp.Shape1.Shape.Edges) == 0:
            return

        if not fp.Shape2 or not hasattr(fp.Shape2, "Shape") or len(fp.Shape2.Shape.Edges) == 0:
            return

        if fp.InterpolationPoints <= 1:
            return

        try:
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
        except Exception as ex:
            self.update = True
            raise ex


    def onChanged(self, fp, prop):   
        if not hasattr(fp, 'LoftMaxDegree'):
            CurvedShapes.addObjectProperty(fp, "App::PropertyInteger", "LoftMaxDegree", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Max Degree for Surface or Solid"), init_val=5) # backwards compatibility - this upgrades older documents
        if not hasattr(fp, 'MaxLoftSize'):
            CurvedShapes.addObjectProperty(fp, "App::PropertyInteger", "MaxLoftSize", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Max Size of a Loft in Segments."), init_val=-1) # backwards compatibility - this upgrades older documents
        if not hasattr(fp, 'Path'):
            CurvedShapes.addObjectProperty(fp, "App::PropertyLink", "Path", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Sweep path"), init_val=None) # backwards compatibility - this upgrades older documents
        if not hasattr(fp, 'ForceInterpolated'):
            CurvedShapes.addObjectProperty(fp, "App::PropertyBool", "ForceInterpolated", "CurvedSegment", QT_TRANSLATE_NOOP("App::Property", "Force Interpolation of sketches"), init_val=False) # backwards compatibility - this upgrades older documents


    def makeRibs(self, fp):
        interpolate = False
        if fp.ForceInterpolated or len(fp.Shape1.Shape.Edges) != len(fp.Shape2.Shape.Edges):
            interpolate = True
        else:
            for e in range(0, len(fp.Shape1.Shape.Edges)):
                edge1 = fp.Shape1.Shape.Edges[e]
                edge2 = fp.Shape2.Shape.Edges[e]
                curve1 = edge1.Curve.toBSpline(edge1.FirstParameter, edge1.LastParameter)
                curve2 = edge2.Curve.toBSpline(edge2.FirstParameter, edge2.LastParameter)
                poles1 = curve1.getPoles()
                poles2 = curve2.getPoles()
                if len(poles1) != len(poles2):
                    interpolate = True
                    break

        makeStartEnd = fp.makeSurface or fp.makeSolid
        if interpolate:
            ribs = makeRibsInterpolate(fp, fp.Items, False, makeStartEnd)
        else:
            ribs = makeRibsSameShape(fp, fp.Items, False, makeStartEnd)

        self.rescaleRibs(fp, ribs)

        if fp.makeSurface or fp.makeSolid:
            fp.Shape = CurvedShapes.makeSurfaceSolid(ribs, fp.makeSolid, maxDegree=fp.LoftMaxDegree, maxLoftSize=fp.MaxLoftSize)
        else:
            fp.Shape = Part.makeCompound(ribs)


    def rescaleRibs(self, fp, ribs):
        if (fp.makeSurface or fp.makeSolid) and fp.Path is None and abs(fp.Twist)<=epsilon:
            start = 1
            end = len(ribs) - 1
            items = fp.Items + 3
        else:   
            start = 0
            end = len(ribs) 
            items = fp.Items + 1

        maxlen = 0   
        edgelen = []
        if fp.Path is not None:
            edges = Part.__sortEdges__(fp.Path.Shape.Edges)
            for edge in edges:
                maxlen += edge.Length
                edgelen.append(edge.Length)

        bc0=fp.Shape1.Shape.Placement.Base
        bc1=fp.Shape2.Shape.Placement.Base # makes rotating assymetric shapes easier - taking sketch origin into account
        for i in range(start, end):
            d = CurvedShapes.distribute(i / items, fp.Distribution, fp.DistributionReverse)
            normal = CurvedShapes.vectorMiddle(fp.NormalShape1, fp.NormalShape2, d)
            #Draft.makeLine(ribs[i].BoundBox.Center, ribs[i].BoundBox.Center + normal)
            ribs[i] = ribs[i].rotate(bc0+d*(bc1-bc0), normal, fp.Twist * d)
            direction = normal
            if maxlen>0:
                plen = d * maxlen
                for edge in edges:
                    if plen > edge.Length: 
                        plen -= edge.Length
                    else:
                        param = edge.getParameterByLength(plen)
                        direction = edge.tangentAt(param) 
                        posvec = edge.valueAt(param) 
                        rotaxis = normal.cross(direction)
                        angle = math.degrees(normal.getAngle(direction))
                        if rotaxis.Length>epsilon:
                            ribs[i] = ribs[i].rotate(bc0+d*(bc1-bc0), rotaxis, angle)
                        ribs[i].Placement.Base = posvec

            if len(fp.Hullcurves) > 0:
                bbox = CurvedShapes.boundbox_from_intersect(fp.Hullcurves, ribs[i].BoundBox.Center, direction, self.doScaleXYZ)
                if bbox:
                    ribs[i] = CurvedShapes.scaleByBoundbox(ribs[i], bbox, self.doScaleXYZsum, copy=False)


#background compatibility
CurvedSegmentWorker = CurvedSegment

def vectorMiddlePlane(vec1, vec2, fraction, plane):
    line = Part.makeLine(vec1, vec2)

    isec = plane.intersect(line.Curve)
    if not isec or len(isec[0]) != 1:
        return CurvedShapes.vectorMiddle(vec1, vec2, fraction)

    return CurvedShapes.PointVec(isec[0][0]) 


def vectorMiddlePlaneNormal1(vec1, vec2, normalShape1, normalShape2):
    rota90 = FreeCAD.Rotation(normalShape1.cross(normalShape2), 90)
    normal90 = rota90.multVec(normalShape1)
    plane1 = Part.Plane(vec1, normal90)
    line2 = Part.makeLine(vec2, vec2 + normalShape2)

    p1 = vec1
    isec = plane1.intersect(line2.Curve)
    if isec and len(isec[0]) == 1:
        p1 = CurvedShapes.PointVec(isec[0][0])

    return p1


def vectorMiddlePlaneNormal(vec1, vec2, fraction, normalShape1, normalShape2):
    if fraction == 0:
        return vec1
    if fraction == 1:
        return vec2

    p1 = vectorMiddlePlaneNormal1(vec1, vec2, normalShape1, normalShape2)  
    p2 = vectorMiddlePlaneNormal1(vec2, vec1, normalShape2, normalShape1)  
    return CurvedShapes.vectorMiddle(p1, p2, 0.5)


def getMidPlane(fp, fraction):
    midvec = CurvedShapes.vectorMiddle(fp.Shape1.Shape.BoundBox.Center, fp.Shape2.Shape.BoundBox.Center, fraction)
    midnorm = CurvedShapes.vectorMiddle(fp.NormalShape1, fp.NormalShape2, fraction)
    return Part.Plane(midvec, midnorm)


def makeRibsSameShape(fp, items, alongNormal, makeStartEnd = False):
    ribs = []

    base1=fp.Shape1.Placement.Base
    base2=fp.Shape2.Placement.Base
    offset=base2-base1
    if makeStartEnd and ((fp.Path is not None) or (abs(fp.Twist)>epsilon)):
        start=0
        end=items+2
    else:
        start=1
        end=items+1
    for i in range(start, end): 
        if hasattr(fp, "Distribution"):
            fraction = CurvedShapes.distribute(i / (items + 1), fp.Distribution, fp.DistributionReverse)
        else:
            fraction = i / (items + 1)

        plane = getMidPlane(fp, fraction)

        edges = []
        curves = []
        edges2 = fp.Shape2.Shape.Edges.copy()
        if fp.TwistReverse:
            edges2.reverse()

        for e in range(0, len(fp.Shape1.Shape.Edges)):
            edge1 = fp.Shape1.Shape.Edges[e]
            edge2 = edges2[e]
            curve1 = edge1.Curve.toBSpline(edge1.FirstParameter, edge1.LastParameter)
            curve2 = edge2.Curve.toBSpline(edge2.FirstParameter, edge2.LastParameter)
            poles1 = curve1.getPoles()
            poles2 = curve2.getPoles()

            newpoles = []
            for p in range(len(poles1)):
                if alongNormal:
                    newpoles.append(vectorMiddlePlaneNormal(poles1[p], poles2[p], fraction, fp.NormalShape1, fp.NormalShape2)-fraction*offset)
                else:
                    newpoles.append(vectorMiddlePlane(poles1[p], poles2[p], fraction, plane)-fraction*offset)
                # coordinate has fraction*offset substracted to force the shape to be centered on itself, important for later rotation on path

            newcurve = Part.BSplineCurve()
            newcurve.buildFromPolesMultsKnots(newpoles, 
                                      curve1.getMultiplicities(), 
                                      curve1.getKnots(), 
                                      curve1.isPeriodic(), 
                                      curve1.Degree,
                                      curve1.getWeights(), 
                                      curve1.isRational())

            rib = newcurve.toShape()
            curves.append(rib)
            edges += rib.Edges

        try:
            wire = Part.Wire(edges)
            ribs.append(wire)
        except Exception as ex:
            if len(curves) == 1:
                ribs.append(curves[0]) 
            else:
                ribs.append(Part.makeCompound(curves))
        ribs[-1].Placement.Base=fraction*offset #place the whole rib in the right place instead

    if makeStartEnd and fp.Path is None and abs(fp.Twist)<=epsilon:
        ribs.insert(0, fp.Shape1.Shape)
        ribs.append(fp.Shape2.Shape)

    return ribs


def makeRibsInterpolate(fp, items, alongNormal, makeStartEnd = False):
    s1=fp.Shape1.Shape.toNurbs()
    s2=fp.Shape2.Shape.toNurbs()
    len1 = len(s1.Edges)
    len2 = len(s2.Edges)

    nr_edges = int(len1 * len2 / math.gcd(len1, len2))

    pointslist1 = EdgesToPoints(s1, int(nr_edges / len1), int(fp.InterpolationPoints))
    pointslist2 = EdgesToPoints(s2, int(nr_edges / len2), int(fp.InterpolationPoints), fp.TwistReverse)

    ribs = []
    if makeStartEnd:
        start = 0
        end = items + 2 
    else:   
        start = 1
        end = items + 1 

    base1=s1.Placement.Base
    base2=s2.Placement.Base
    offset=base2-base1
    for i in range(start, end):
        if hasattr(fp, "Distribution"):
            fraction = CurvedShapes.distribute(i / (items + 1), fp.Distribution, fp.DistributionReverse)
        else:
            fraction = i / (items + 1)

        plane = getMidPlane(fp, fraction)
        newshape = []
        for l in range(0, len(pointslist1)):
            points1 = pointslist1[l]
            points2 = pointslist2[l]
            if(fp.TwistReverse):
                points2.reverse()

            newpoles = []
            for p in range(0, fp.InterpolationPoints):
                if alongNormal:
                    newpoles.append(vectorMiddlePlaneNormal(points1[p], points2[p], fraction, fp.NormalShape1, fp.NormalShape2) - fraction * offset)
                else:
                    newpoles.append(vectorMiddlePlane(points1[p], points2[p], fraction, plane)-fraction*offset)
                # coordinate has fraction*offset substracted to force the shape to be centered on itself, important for later rotation on path

            bc = Part.BSplineCurve()
            bc.approximate(newpoles)
            newshape.append(bc)

        if len(newshape) == 1:
            sh = newshape[0].toShape()
            try:
                wire = Part.Wire(sh.Edges)
                ribs.append(wire)
            except Exception as ex:
                ribs.append(sh)
        else:
            shapes = []
            for n in newshape:
                shapes.append(n.toShape())

            comp = Part.makeCompound(shapes)

            try:
                wire = Part.Wire(comp.Edges)
                ribs.append(wire)
            except Exception as ex:
                ribs.append(comp)
        ribs[-1].Placement.Base=fraction*offset #place the whole rib in the right place instead
    return ribs


def EdgesToPoints(shape, nr_frac, points_per_edge, twistReverse = False):
    edges = [] 
    sortedEdges=sum(Part.sortEdges(shape.Edges),[])
    if twistReverse:
        sortedEdges.reverse()

    if nr_frac == 1:
        edges = sortedEdges
    else:
        for edge in sortedEdges:
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
        if self.Object.Path:
            return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CurvedPathSegment.svg"))
        else:
            return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "curvedSegment.svg"))


    def attach(self, vfp):
        self.Object = vfp.Object
        self.onChanged(vfp,"Shape1")


    def claimChildren(self):
        return [self.Object.Shape1, self.Object.Shape2, self.Object.Path] + self.Object.Hullcurves


    def onDelete(self, feature, subelements):
        return True


    def onChanged(self, fp, prop):
        pass


    def loads(self, state):
        return None


    def dumps(self):
        return None


    def __getstate__(self):
        return None


    def __setstate__(self,state):
        return None


if FreeCAD.GuiUp:

    class CurvedSegmentCommand():
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

            FreeCADGui.doCommand("CurvedShapes.makeCurvedSegment(%sItems=16, Surface=False, Solid=False)"%(options))
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
                    'MenuText': QT_TRANSLATE_NOOP("CurvedSegment", "Curved Segment"),
                    'ToolTip' : QT_TRANSLATE_NOOP("CurvedSegment", __doc__)}


    class CurvedPathSegmentCommand():
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
                elif sel == selection[2]:
                    FreeCADGui.doCommand("path = FreeCAD.ActiveDocument.getObject('%s')"%(selection[2].ObjectName))
                    options += "Path=path, "
                    FreeCADGui.doCommand("hullcurves = []");
                    options += "Hullcurves=hullcurves, "
                else:
                    FreeCADGui.doCommand("hullcurves.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))

            FreeCADGui.doCommand("CurvedShapes.makeCurvedSegment(%sItems=16, Surface=False, Solid=False)"%(options))
            FreeCAD.ActiveDocument.recompute()


        def IsActive(self):
            """Here you can define if the command must be active or not (greyed) if certain conditions
            are met or not. This function is optional."""
            #if FreeCAD.ActiveDocument:
            return(True)
            #else:
            #    return(False)


        def GetResources(self):
            return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CurvedPathSegment.svg"),
                    'Accel' : "", # a default shortcut (optional)
                    'MenuText': QT_TRANSLATE_NOOP("CurvedPathSegment", "Curved Path Segment"),
                    'ToolTip' : QT_TRANSLATE_NOOP("CurvedPathSegment", __doc__ + " along a path")}


    FreeCADGui.addCommand('CurvedSegment', CurvedSegmentCommand())
    FreeCADGui.addCommand('CurvedPathSegment', CurvedPathSegmentCommand())
