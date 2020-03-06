from FreeCAD import Vector, Rotation, Placement
import FreeCAD
import Sketcher
import Part
import Draft
import BOPTools.SplitFeatures
import CompoundTools.Explode
import math
import FreeCADGui
import CurvedShapes
from importlib import reload

def draw_S800():
    sweep_offset = 210
    wing_span = 820
    midWidth = 150
    midLength = 200
    
    WingInside_height_top = 25
    WingInside_height_bot =  5
    WingInside_length = 260
    
    WingOutside_height_top = 20
    WingOutside_height_bot = 3
    WingOutside_length = 165
    
    Middle_height_top = 40
    Middle_height_bot = 20
    Middle_length = WingInside_length
    
    WingletTop_height_top = 3
    WingletTop_height_bot = 3
    Winglet_angle_y = 10   
    Winglet_angle_z = 10     
    WingletBottom_height_top = WingletTop_height_top
    WingletBottom_height_bot = WingletTop_height_bot
    WingletBottom_length = WingOutside_length
    
    ElevonThickness = 1
    ElevonLeftAngle = 20
    ElevonRightAngle = -20
    
    
    if FreeCAD.ActiveDocument is not None and FreeCAD.ActiveDocument.Name == "S800":
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
        FreeCAD.setActiveDocument("")
        ActiveDocument=None
        FreeCAD.ActiveDocument=None
        
    doc = FreeCAD.newDocument('S800')
    
    
    SplineFoilWingInside = doc.addObject('Sketcher::SketchObject', 'SplineFoilWingInside')
    makeSplineFoilSketch(SplineFoilWingInside, WingInside_length, WingInside_height_top, WingInside_height_bot, ElevonThickness)
    SplineFoilWingInside.ViewObject.Visibility = False
    SplineFoilWingInside.Placement = Placement(Vector (midWidth / 2, 0.0, 1.0), Rotation (0.5, 0.5, 0.5, 0.5))
    SplineFoilWingInside.ViewObject.Visibility = False
    
    SplineFoilWingOutside = doc.addObject('Sketcher::SketchObject', 'SplineFoilWingOutside')
    makeSplineFoilSketch(SplineFoilWingOutside, WingOutside_length, WingOutside_height_top, WingOutside_height_bot, ElevonThickness)
    SplineFoilWingOutside.ViewObject.Visibility = False
    SplineFoilWingOutside.Placement = Placement(Vector (wing_span / 2, sweep_offset, 1.0), Rotation (0.5, 0.5, 0.5, 0.5))
    SplineFoilWingOutside.ViewObject.Visibility = False
    
    SplineFoilWingletBottom = doc.addObject('Sketcher::SketchObject', 'SplineFoilWingletBottom')
    makeSplineFoilSketch(SplineFoilWingletBottom, WingletBottom_length, WingletBottom_height_top, WingletBottom_height_bot, 0.5)
    SplineFoilWingletBottom.ViewObject.Visibility = False
    SplineFoilWingletBottom.Placement.Rotation.Axis = Vector (0.0, 0.0, 0.1)
    SplineFoilWingletBottom.Placement.Rotation.Angle = math.radians(90)
    SplineFoilWingletBottom.Placement.Base.y = sweep_offset
    SplineFoilWingletBottom.Placement.Base.x = wing_span / 2 + WingletTop_height_bot *1.5 
    SplineFoilWingletBottom.Placement.Base.z = WingOutside_height_top
    SplineFoilWingletBottom.ViewObject.Visibility = False
    
    doc.recompute()
    Draft.rotate([SplineFoilWingletBottom], Winglet_angle_y, SplineFoilWingletBottom.Placement.Base, Vector(0, 1, 0), copy=False)
    doc.recompute()
    
    SplineFoilMiddle = doc.addObject('Sketcher::SketchObject', 'SplineFoilMiddle')
    makeSplineFoilSketch(SplineFoilMiddle, Middle_length, Middle_height_top, Middle_height_bot, ElevonThickness)
    SplineFoilMiddle.Placement = Placement(Vector (0.0, 0.0, 0.0), Rotation (0.5, 0.5, 0.5, 0.5))
    SplineFoilMiddle.ViewObject.Visibility = False
    
    MiddleProfile = createSketch_MiddleProfile(doc)
    MiddleProfile.ViewObject.Visibility = False
    
    MiddlePart1 = CurvedShapes.makeCurvedSegment(SplineFoilMiddle, SplineFoilWingInside, [MiddleProfile], Items=4, Surface=True, Solid=True, Distribution='elliptic', DistributionReverse=True)
    MiddlePart1.Label = "MiddlePart1"
    MiddlePart1.ViewObject.Visibility = False
    
    MainWing = doc.addObject('Part::Loft', 'MainWing') 
    MainWing.Sections = [SplineFoilWingInside ,SplineFoilWingOutside]
    MainWing.Solid = True
    
    WingToWinglet = CurvedShapes.makeInterpolatedMiddle(SplineFoilWingOutside, SplineFoilWingletBottom, Surface=True, Solid=True)
    WingToWinglet.Label = "WingToWinglet"
    
    WingletProfile = makeWingletProfile(doc)
    WingletProfile.ViewObject.Visibility = False
    
    doc.recompute()
    Winglet = CurvedShapes.makeCurvedArray(SplineFoilWingletBottom, [WingletProfile], Items=8, OffsetStart=0.01, OffsetEnd=0.01, Surface=True, Solid=True)
    Winglet.Label = "Winget"
    
    doc.recompute()
    Draft.rotate([Winglet], Winglet_angle_y, SplineFoilWingletBottom.Placement.Base, Vector(0, 1, 0), copy=False)
    doc.recompute()
    
    sketchCutout = doc.addObject('Sketcher::SketchObject', 'sketchCutout')
    sketchCutout.addGeometry(Part.LineSegment(Vector (0.0, 400.0, 0.0), Vector (274.99999999950205, 400.0, 0.0)), False)
    sketchCutout.addGeometry(Part.LineSegment(Vector (274.99999999950205, 400.0, 0.0), Vector (75.0, 200.0, 0.0)), False)
    sketchCutout.addGeometry(Part.LineSegment(Vector (75.0, 200.0, 0.0), Vector (0.0, 200.0, 0.0)), False)
    sketchCutout.addGeometry(Part.LineSegment(Vector (0.0, 200.0, 0.0), Vector (0.0, 400.0, 0.0)), False)
    sketchCutout.addConstraint(Sketcher.Constraint('PointOnObject', 0, 1, -2))
    sketchCutout.addConstraint(Sketcher.Constraint('Horizontal', 0))
    sketchCutout.addConstraint(Sketcher.Constraint('Coincident', 0, 2, 1, 1))
    sketchCutout.addConstraint(Sketcher.Constraint('Coincident', 1, 2, 2, 1))
    sketchCutout.addConstraint(Sketcher.Constraint('PointOnObject', 2, 2, -2))
    sketchCutout.addConstraint(Sketcher.Constraint('Horizontal', 2))
    sketchCutout.addConstraint(Sketcher.Constraint('Coincident', 2, 2, 3, 1))
    sketchCutout.addConstraint(Sketcher.Constraint('Coincident', 3, 2, 0, 1))
    sketchCutout.addConstraint(Sketcher.Constraint('Angle', 1, 2, 2, 1, 2.356194))
    sketchCutout.addConstraint(Sketcher.Constraint('DistanceX', 2, 2, 2, 1, midWidth/2))
    sketchCutout.addConstraint(Sketcher.Constraint('DistanceY', 2, 2, midLength))
    sketchCutout.addConstraint(Sketcher.Constraint('DistanceY', 3, 1, 3, 2, midLength))
    sketchCutout.ViewObject.Visibility = False
    
    
    cutout = doc.addObject('Part::Extrusion', 'cutout')
    cutout.Base = sketchCutout
    cutout.DirMode = "Normal"
    cutout.LengthFwd = 100.0
    cutout.LengthRev = 100.0
    cutout.Solid = True
    cutout.Symmetric = True
    cutout.ViewObject.Visibility = False
    
    MiddlePart = doc.addObject('Part::Cut', 'MiddlePart')
    MiddlePart.Base = MiddlePart1
    MiddlePart.Tool = cutout
    
    cutpathPoints = [Vector(midWidth/2 , midLength, -WingInside_height_bot)]
    cutpathPoints.append(Vector(wing_span/2, midLength + sweep_offset - WingInside_length + WingOutside_length, -WingOutside_height_bot))
    cutpath = Draft.makeWire(cutpathPoints)
    cutpath.ViewObject.Visibility = False
    cutExtrude = doc.addObject('Part::Extrusion', 'cutExtrude')
    cutExtrude.Base = cutpath
    cutExtrude.DirMode = "Normal"
    cutExtrude.LengthFwd = WingInside_height_bot + WingInside_height_top
    
    doc.recompute()
    
    Wing = doc.addObject('Part::Cut', 'Wing')
    Wing.Base = MainWing
    Wing.Tool = cutout
    
    doc.recompute()
    
    WingSlice = BOPTools.SplitFeatures.makeSlice(name= 'WingSlice')
    WingSlice.Base = [Wing, cutExtrude][0]
    WingSlice.Tools = [Wing, cutExtrude][1:]
    WingSlice.Mode = 'Split'
    WingSlice.Proxy.execute(WingSlice)
    WingSlice.purgeTouched()
    WingSlice.ViewObject.Visibility = False
    for obj in WingSlice.ViewObject.Proxy.claimChildren():
        obj.ViewObject.hide()
    
    WingAndElevon = CompoundTools.Explode.explodeCompound(WingSlice)
    Wing1 = WingAndElevon[0].Group[0]
    Wing1.Label = "Wing1"
    ElevonLeft = WingAndElevon[0].Group[1]
    ElevonLeft.Label = "ElevonLeft"
    
    
    HalfWing = doc.addObject('Part::Compound', 'HalfWing')
    HalfWing.Links = [MiddlePart, Wing1, WingToWinglet, Winglet]
    
    FullWing = doc.addObject('Part::Mirroring', 'FullWing')
    FullWing.Normal = Vector (1.0, 0.0, 0.0)
    FullWing.Source = HalfWing
    
    ElevonRight1 = Draft.clone(ElevonLeft)
    ElevonRight1.ViewObject.Visibility = False
    
    ElevonRight = doc.addObject('Part::Mirroring', 'ElevonRight')
    ElevonRight.Normal = Vector (1.0, 0.0, 0.0)
    ElevonRight.Source = ElevonRight1
    
    doc.recompute()
    axis=cutpathPoints[1].sub(cutpathPoints[0])
    center = ElevonLeft.Placement.Base.add(Vector(midWidth/2, midLength, ElevonLeft.Shape.BoundBox.ZMax))
    Draft.rotate([ElevonLeft], ElevonLeftAngle, center, axis=axis, copy=False)
    Draft.rotate([ElevonRight1], ElevonRightAngle, center, axis=axis, copy=False)
    
    FreeCADGui.activeDocument().activeView().viewIsometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")
    return
    
    
def makeSplineFoilSketch(sketch, length, height_top, height_bottom, back_width = 0):
    print(sketch.Label)
    sketch.Placement = FreeCAD.Placement(FreeCAD.Vector(0.000000,0.000000,0.000000),FreeCAD.Rotation(0.5, 0.5, 0.5, 0.5))
    sketch.MapMode = "Deactivated"
    
    points = []
    conList = []
    points.append(FreeCAD.Vector(length, back_width, 0))
    points.append(FreeCAD.Vector(length * 0.75, height_top * 0.55, 0))
    points.append(FreeCAD.Vector(length * 0.57, height_top * 0.75, 0))
    points.append(FreeCAD.Vector(length * 0.29, height_top * 1, 0))
    points.append(FreeCAD.Vector(length * 0.03, height_top * 0.6, 0))
    points.append(FreeCAD.Vector(0, height_top * 0.2, 0))
    points.append(FreeCAD.Vector(0, 0, 0))
    points.append(FreeCAD.Vector(0, height_bottom * -0.2, 0))
    points.append(FreeCAD.Vector(length * 0.03, height_bottom * -0.6, 0))
    points.append(FreeCAD.Vector(length * 0.29, height_bottom * -1, 0))
    points.append(FreeCAD.Vector(length * 0.57, height_bottom * -0.75, 0))
    points.append(FreeCAD.Vector(length * 0.75, height_bottom * -0.55, 0))
    points.append(FreeCAD.Vector(length, -back_width, 0))
        
    n = 0    
    for p in points:
        circle = sketch.addGeometry(Part.Circle(p,FreeCAD.Vector(0,0,1),10),True)
        sketch.addConstraint(Sketcher.Constraint('Radius',circle, 1)) 
        sketch.addConstraint(Sketcher.Constraint('DistanceX',circle,3, p.x)) 
        sketch.addConstraint(Sketcher.Constraint('DistanceY',circle,3, p.y)) 
        conList.append(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint',circle,3,13,n))
        n = n + 1
    
    bspline = sketch.addGeometry(Part.BSplineCurve(points,None,None,False,3,None,False),False)
    sketch.addConstraint(conList)
    sketch.exposeInternalGeometry(13)
    if back_width > 0:
        line = sketch.addGeometry(Part.LineSegment(points[0], points[12]))
        sketch.addConstraint(Sketcher.Constraint('Coincident', bspline ,1, line, 1))
        sketch.addConstraint(Sketcher.Constraint('Coincident', bspline ,2, line, 2))
    return sketch


def createSketch_MiddleProfile(doc):
    MiddleProfile = doc.addObject('Sketcher::SketchObject', 'MiddleProfile')
    MiddleProfile.addGeometry(Part.Circle(Vector(45.0, 40.0, 0.0), Vector (0.0, 0.0, 1.0), 10.0), True)
    MiddleProfile.addGeometry(Part.Circle(Vector(69.0, 40.0, 0.0), Vector (0.0, 0.0, 1.0), 10.0), True)
    MiddleProfile.addGeometry(Part.Circle(Vector(75.0, 25.0, 0.0), Vector (0.0, 0.0, 1.0), 10.0), True)
    MiddleProfile.addGeometry(Part.BSplineCurve([Vector(45.0, 40.0, 0.0), Vector(69.0, 40.0, 0.0), Vector(75.0, 25.0, 0.0)]), False)
    MiddleProfile.addGeometry(Part.Circle(Vector(45.0, -20.0, 0.0), Vector (0.0, 0.0, 1.0), 10.0), True)
    MiddleProfile.addGeometry(Part.Circle(Vector(69.0, -20.0, 0.0), Vector (0.0, 0.0, 1.0), 10.0), True)
    MiddleProfile.addGeometry(Part.Circle(Vector(75.0, -5.0, 0.0), Vector (0.0, 0.0, 1.0), 10.0), True)
    MiddleProfile.addGeometry(Part.BSplineCurve([Vector(45.0, -20.0, 0.0), Vector(69.0, -20.0, 0.0), Vector(75.0, -5.0, 0.0)]), False)
    MiddleProfile.addGeometry(Part.Point(Vector(45.0,-20.0,0.0)), False)
    MiddleProfile.addGeometry(Part.LineSegment(Vector (75.0, 25.0, 0.0), Vector (75.0, -5.0, 0.0)), False)
    MiddleProfile.addGeometry(Part.LineSegment(Vector (45.0, 40.0, 0.0), Vector (69.0, 40.0, 0.0)), True)
    MiddleProfile.addGeometry(Part.LineSegment(Vector (69.0, -20.0, 0.0), Vector (45.0, -20.0, 0.0)), True)
    MiddleProfile.addGeometry(Part.LineSegment(Vector (45.0, 40.0, 0.0), Vector (0.0, 40.0, 0.0)), False)
    MiddleProfile.addGeometry(Part.LineSegment(Vector (0.0, 40.0, 0.0), Vector (0.0, -20.0, 0.0)), False)
    MiddleProfile.addGeometry(Part.LineSegment(Vector (0.0, -20.0, 0.0), Vector (45.0, -20.0, 0.0)), False)
    MiddleProfile.addConstraint(Sketcher.Constraint('Radius', 0, 10.0))
    MiddleProfile.addConstraint(Sketcher.Constraint('Equal', 0, 1))
    MiddleProfile.addConstraint(Sketcher.Constraint('Equal', 0, 2))
    MiddleProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 0, 3, 3, 0))
    MiddleProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 1, 3, 3, 1))
    MiddleProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 2, 3, 3, 2))
    MiddleProfile.addConstraint(Sketcher.Constraint('Radius', 4, 10.0))
    MiddleProfile.addConstraint(Sketcher.Constraint('Equal', 4, 5))
    MiddleProfile.addConstraint(Sketcher.Constraint('Equal', 4, 6))
    MiddleProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 4, 3, 7, 0))
    MiddleProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 5, 3, 7, 1))
    MiddleProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 6, 3, 7, 2))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 9, 2, 7, 2))
    MiddleProfile.addConstraint(Sketcher.Constraint('Vertical', 9))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 9, 1, 3, 2))
    MiddleProfile.addConstraint(Sketcher.Constraint('DistanceX', 7, 2, 75.0))
    MiddleProfile.addConstraint(Sketcher.Constraint('DistanceY', 3, 2, 25.0))
    MiddleProfile.addConstraint(Sketcher.Constraint('DistanceY', 7, 2, -5.0))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 10, 1, 3, 1))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 10, 2, 1, 3))
    MiddleProfile.addConstraint(Sketcher.Constraint('Horizontal', 10))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 11, 1, 5, 3))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 11, 2, 7, 1))
    MiddleProfile.addConstraint(Sketcher.Constraint('Horizontal', 11))
    MiddleProfile.addConstraint(Sketcher.Constraint('DistanceY', 3, 1, 40.0))
    MiddleProfile.addConstraint(Sketcher.Constraint('DistanceY', 8, 1, -20.0))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 8, 1, 7, 1))
    MiddleProfile.addConstraint(Sketcher.Constraint('Equal', 11, 10))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 12, 1, 3, 1))
    MiddleProfile.addConstraint(Sketcher.Constraint('Horizontal', 12))
    MiddleProfile.addConstraint(Sketcher.Constraint('Vertical', 13))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 13, 2, 14, 1))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 14, 2, 7, 1))
    MiddleProfile.addConstraint(Sketcher.Constraint('Horizontal', 14))
    MiddleProfile.addConstraint(Sketcher.Constraint('Equal', 12, 14))
    MiddleProfile.addConstraint(Sketcher.Constraint('DistanceX', 12, 2, 12, 1, 45.0))
    MiddleProfile.addConstraint(Sketcher.Constraint('PointOnObject', 12, 2, -2))
    MiddleProfile.addConstraint(Sketcher.Constraint('Equal', 11, 10))
    MiddleProfile.addConstraint(Sketcher.Constraint('DistanceX', 10, 1, 10, 2, 24.0))
    MiddleProfile.addConstraint(Sketcher.Constraint('Coincident', 13, 1, 12, 2))
    MiddleProfile.Placement = Placement(Vector(0.0, 0.0, 0.0), Rotation (0.7071067811865475, -0.0, -0.0, 0.7071067811865476))
    MiddleProfile.ViewObject.Visibility = False
    return MiddleProfile


def makeWingletProfile(doc):
    WingletProfile = doc.addObject('Sketcher::SketchObject', 'WingletProfile') 
    print(WingletProfile.Label)
    WingletProfile.addGeometry(Part.LineSegment(Vector (210.0, 20.0, 0.0), Vector (375.0, 20.0, 0.0)), False)
    WingletProfile.addGeometry(Part.LineSegment(Vector (375.0, 20.0, 0.0), Vector (385.0, 100.0, 0.0)), False)
    WingletProfile.addGeometry(Part.LineSegment(Vector (385.0, 100.0, 0.0), Vector (305.0, 100.0, 0.0)), False)
    WingletProfile.addGeometry(Part.Circle(Vector(305.0, 100.0, 0.0), Vector (0.0, 0.0, 1.0), 0.8), True)
    WingletProfile.addGeometry(Part.Circle(Vector(295.0, 100.0, 0.0), Vector (0.0, 0.0, 1.0), 0.8), True)
    WingletProfile.addGeometry(Part.Circle(Vector(210.0, 20.0, 0.0), Vector (0.0, 0.0, 1.0), 0.8), True)
    WingletProfile.addGeometry(Part.BSplineCurve([Vector(305.0, 100.0, 0.0), Vector(295.0, 100.0, 0.0), Vector(210.0, 20.0, 0.0)]), False)
    WingletProfile.addGeometry(Part.Point(Vector(305.0,100.0,0.0)), False)
    WingletProfile.addGeometry(Part.Point(Vector(210.0,20.0,0.0)), False)
    WingletProfile.addConstraint(Sketcher.Constraint('Horizontal', 0))
    WingletProfile.addConstraint(Sketcher.Constraint('Distance', 0, 165.0))
    WingletProfile.addConstraint(Sketcher.Constraint('Coincident', 1, 1, 0, 2))
    WingletProfile.addConstraint(Sketcher.Constraint('Coincident', 2, 1, 1, 2))
    WingletProfile.addConstraint(Sketcher.Constraint('Horizontal', 2))
    WingletProfile.addConstraint(Sketcher.Constraint('Radius', 3, 0.8))
    WingletProfile.addConstraint(Sketcher.Constraint('Equal', 3, 4))
    WingletProfile.addConstraint(Sketcher.Constraint('Equal', 3, 5))
    WingletProfile.addConstraint(Sketcher.Constraint('Coincident', 6, 2, 0, 1))
    WingletProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 3, 3, 6, 0))
    WingletProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 4, 3, 6, 1))
    WingletProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 5, 3, 6, 2))
    #WingletProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 7, 3, 6, 3))
    #WingletProfile.addConstraint(Sketcher.Constraint('InternalAlignment:Sketcher::BSplineControlPoint', 8, 3, 6, 4))
    WingletProfile.addConstraint(Sketcher.Constraint('DistanceY', 0, 2, 1, 2, 80.0))
    WingletProfile.addConstraint(Sketcher.Constraint('Coincident', 2, 2, 6, 1))
    WingletProfile.addConstraint(Sketcher.Constraint('DistanceX', 0, 2, 1, 2, 10.0))
    WingletProfile.addConstraint(Sketcher.Constraint('DistanceX', 4, 3, 1, 2, 90.0))
    WingletProfile.addConstraint(Sketcher.Constraint('PointOnObject', 4, 3, 2))
    WingletProfile.addConstraint(Sketcher.Constraint('DistanceY', 0, 1, 20.0))
    WingletProfile.addConstraint(Sketcher.Constraint('DistanceX', 0, 1, 210.0))
    WingletProfile.addConstraint(Sketcher.Constraint('DistanceX', 4, 3, 2, 2, 10.0))
    WingletProfile.Placement = Placement(Vector(0.0, 0.0, 0.0), Rotation (0.5, 0.5, 0.5, 0.5))
    return WingletProfile

 
class FlyingWingS800():
    def Activated(self):
        import FlyingWingS800
        reload(FlyingWingS800)
        draw_S800()
        
    def GetResources(self):
        import CurvedShapes
        import os
        return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "FlyingWingS800.svg"),
                'MenuText': "S800",
                'ToolTip' : "A cheap flying wing" }


FreeCADGui.addCommand('FlyingWingS800', FlyingWingS800())
