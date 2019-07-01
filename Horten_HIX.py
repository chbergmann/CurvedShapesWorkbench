from FreeCAD import Vector, Placement, Rotation
import FreeCAD
import FreeCADGui
import Part
import Draft
import CurvedShapes
import CurvedSegment
import CurvedArray
import BOPTools.JoinFeatures
from importlib import reload
        
global epsilon
epsilon = CurvedShapes.epsilon

def draw_HortenHIX():
    rib_material_height = 33.0
    baseplate_width = 5.0
    front_width = 20
    reload(CurvedSegment)
    reload(CurvedShapes)
    reload(CurvedArray)

    length = 500
    scaleFactor = length / 85
    

    if FreeCAD.ActiveDocument is not None and FreeCAD.ActiveDocument.Name == "Horten_HIX":
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
        FreeCAD.setActiveDocument("")
        ActiveDocument=None
        FreeCAD.ActiveDocument=None
        
    doc = FreeCAD.newDocument('Horten_HIX')

    wing_sweep = 32.2
    twist = 3
    wing_ribs = 10
    front_part_fraction = 0.97
    
    
    WingTop_parts = []
    line = Draft.makeWire([Vector(0.0, 73.39, 0.0) * scaleFactor, Vector(72.64, 27.65, 0.0) * scaleFactor])
    WingTop_parts.append(line)
    line = Draft.makeWire([Vector(75.22, 11.01, 0.0) * scaleFactor, Vector(35.0, 22.43, 0.0) * scaleFactor])
    WingTop_parts.append(line)
    poles = []
    poles.append(Vector(72.64, 27.65, 0.0) * scaleFactor)
    poles.append(Vector(86.21, 19.11, 0.0) * scaleFactor)
    poles.append(Vector(86.21, 7.88, 0.0) * scaleFactor)
    poles.append(Vector(75.22, 11.01, 0.0) * scaleFactor)
    weights = [1.0, 1.0, 1.0, 1.0]
    knots = [0.0, 1.0]
    mults = [4, 4]
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults, knots, False, 3, weights, False)
    bezier = doc.addObject('Part::Spline', 'BSplineCurve')
    bezier.Shape = bspline.toShape()
    WingTop_parts.append(bezier)
    poles = []
    poles.append(Vector(0.0, 0.0, 0.0) * scaleFactor)
    poles.append(Vector(15.13, 28.07, 0.0) * scaleFactor)
    poles.append(Vector(35.0, 22.43, 0.0) * scaleFactor)
    weights = [1.0, 1.0, 1.0]
    knots = [0.0, 1.0]
    mults = [3, 3]
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults, knots, False, 2, weights, False)
    bezier = doc.addObject('Part::Spline', 'BSplineCurve')
    bezier.Shape = bspline.toShape()
    WingTop_parts.append(bezier)
    WingTop = doc.addObject('Part::Compound', 'WingTop')
    WingTop.Links = WingTop_parts
    WingTop.Placement.Base = Vector(0.0, 0.0, 0.0) * scaleFactor
    WingTop.Placement.Rotation = Rotation (0.0, 0.0, 0.0, 1.0)
    WingTop.ViewObject.LineColor = (1.0 ,0.0 ,0.0 ,0.0)
    WingTop.ViewObject.LineColorArray = [(1.0 ,0.0 ,0.0 ,0.0)]
    
    WingFront_parts = []
    line = Draft.makeWire([Vector(0.0, -4.31, 0.0) * scaleFactor, Vector(77.02, 2.59, 0.0) * scaleFactor])
    WingFront_parts.append(line)
    poles = []
    poles.append(Vector(0.0, 7.35, 0.0) * scaleFactor)
    poles.append(Vector(5.43, 4.71, 0.0) * scaleFactor)
    poles.append(Vector(16.41, 2.6, 0.0) * scaleFactor)
    poles.append(Vector(41.55, 2.77, 0.0) * scaleFactor)
    poles.append(Vector(76.91, 3.93, 0.0) * scaleFactor)
    poles.append(Vector(83.72, 4.28, 0.0) * scaleFactor)
    poles.append(Vector(83.72, 3.38, 0.0) * scaleFactor)
    poles.append(Vector(77.02, 2.59, 0.0) * scaleFactor)
    weights = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    knots = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    mults = [4, 1, 1, 1, 1, 4]
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults, knots, False, 3, weights, False)
    bezier = doc.addObject('Part::Spline', 'BSplineCurve')
    bezier.Shape = bspline.toShape()
    WingFront_parts.append(bezier)
    WingFront = doc.addObject('Part::Compound', 'WingFront')
    WingFront.Links = WingFront_parts
    WingFront.Placement.Base = Vector(0.0, 0.0, 0.0) * scaleFactor
    WingFront.Placement.Rotation = Rotation (0.7071067811865475, -0.0, -0.0, 0.7071067811865476)
    WingFront.ViewObject.LineColor = (1.0 ,0.0 ,0.5 ,0.0)
    WingFront.ViewObject.LineColorArray = [(1.0 ,0.0 ,0.5 ,0.0)]
    
    WingProfile_parts = []
    poles = []
    poles.append(Vector(65.04, 0.0, 0.0) * scaleFactor)
    poles.append(Vector(24.39, -4.45, 0.0) * scaleFactor)
    poles.append(Vector(10.95, -2.98, 0.0) * scaleFactor)
    poles.append(Vector(2.58, -2.28, 0.0) * scaleFactor)
    poles.append(Vector(3.23, 0.0, 0.0) * scaleFactor)
    poles.append(Vector(3.89, 2.3, 0.0) * scaleFactor)
    poles.append(Vector(13.51, 5.94, 0.0) * scaleFactor)
    poles.append(Vector(27.26, 5.54, 0.0) * scaleFactor)
    poles.append(Vector(65.04, 0.0, 0.0) * scaleFactor)
    weights = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    knots = [0.0, 0.1666666666666667, 0.3333333333333333, 0.5, 0.6666666666666666, 0.8333333333333334, 1.0]
    mults = [4, 1, 1, 1, 1, 1, 4]
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults, knots, False, 3, weights, False)
    bezier = doc.addObject('Part::Spline', 'BSplineCurve')
    bezier.Shape = bspline.toShape()
    WingProfile_parts.append(bezier)
    WingProfile = doc.addObject('Part::Compound', 'WingProfile')
    WingProfile.Links = WingProfile_parts
    WingProfile.Placement.Base = Vector(5.0, 73.0, 0.0) * scaleFactor
    WingProfile.Placement.Rotation = Rotation (0.5, -0.5, -0.5, 0.5)
    WingProfile.ViewObject.LineColor = (1.0 ,0.33 ,0.0 ,0.0)
    WingProfile.ViewObject.LineColorArray = [(1.0 ,0.33 ,0.0 ,0.0)]
    # Profiles ^^^
   
    doc.recompute()       
  
    
    WingArray = CurvedShapes.makeCurvedArray(Base=WingProfile, 
                                         Hullcurves=[WingTop, WingFront], 
                                         Axis=Vector(1,0,0), 
                                         Items=11, 
                                         OffsetStart=0, 
                                         OffsetEnd=0,
                                         Twist=twist,
                                         Surface=False,
                                         Solid=False,
                                         extract=False)
    
    WingTopLeft = doc.addObject('Part::Mirroring', 'WingTopLeft')
    WingTopLeft.Normal = Vector(1.0, 0.0, 0.0)
    WingTopLeft.Source = WingTop
    WingTopLeft.ViewObject.hide()
    
    WingFrontLeft = doc.addObject('Part::Mirroring', 'WingFrontLeft')
    WingFrontLeft.Normal = Vector(1.0, 0.0, 0.0)
    WingFrontLeft.Source = WingFront
    WingFrontLeft.ViewObject.hide()
    doc.recompute()
    
    winglength = WingFrontLeft.Shape.BoundBox.XLength
    WingSurface = CurvedShapes.makeCurvedArray(Base=WingProfile, 
                                             Hullcurves=[WingTopLeft, WingFrontLeft], 
                                             Axis=Vector(-1,0,0), 
                                             Items=16, 
                                             OffsetStart=0, 
                                             OffsetEnd=winglength * 0.1,
                                             Twist=-twist,
                                             Surface=True,
                                             Solid=True,
                                             extract=False) 
    
    WingSurfaceEnd = CurvedShapes.makeCurvedArray(Base=WingProfile, 
                                             Hullcurves=[WingTopLeft, WingFrontLeft], 
                                             Axis=Vector(-1,0,0), 
                                             Items=32, 
                                             OffsetStart=winglength * 0.9, 
                                             OffsetEnd=0.2,
                                             Twist=-twist,
                                             Surface=True,
                                             Solid=True,
                                             extract=False) 
    
    WingSurface.Label = "WingSurface"
    WingSurfaceEnd.Label = "WingSurfaceEnd"
    
    Cockpit = drawCockpit(doc, scaleFactor, rib_material_height)
    
    doc.recompute()
    FreeCADGui.activeDocument().activeView().viewIsometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")
    
            
def drawCockpit(doc, scaleFactor, rib_material_height):
    CockpitFront_parts = []
    poles = []
    poles.append(Vector(0.0, 7.92, 0.0) * scaleFactor)
    poles.append(Vector(1.41, 7.92, 0.0) * scaleFactor)
    poles.append(Vector(2.8, 6.04, 0.0) * scaleFactor)
    weights = [1.0, 1.0, 1.0]
    knots = [0.0, 1.0]
    mults = [3, 3]
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults, knots, False, 2, weights, False)
    bezier = doc.addObject('Part::Spline', 'BSplineCurve')
    bezier.Shape = bspline.toShape()
    CockpitFront_parts.append(bezier)
    CockpitFront = doc.addObject('Part::Compound', 'CockpitFront')
    CockpitFront.Links = CockpitFront_parts
    CockpitFront.Placement.Base = Vector(0.0, 0.0, 0.0) * scaleFactor
    CockpitFront.Placement.Rotation = Rotation (-0.7071067811865475, 0.0, 0.0, -0.7071067811865475)
    
    CockpitTop_parts = []
    poles = []
    poles.append(Vector(0.0, 66.8, 0.0) * scaleFactor)
    poles.append(Vector(3.46, 66.16, 0.0) * scaleFactor)
    poles.append(Vector(5.2, 61.61, 0.0) * scaleFactor)
    poles.append(Vector(3.99, 46.46, 0.0) * scaleFactor)
    poles.append(Vector(0.0, 33.85, 0.0) * scaleFactor)
    weights = [1.0, 1.0, 1.0, 1.0, 1.0]
    knots = [0.0, 0.5, 1.0]
    mults = [4, 1, 4]
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults, knots, False, 3, weights, False)
    bezier = doc.addObject('Part::Spline', 'BSplineCurve')
    bezier.Shape = bspline.toShape()
    CockpitTop_parts.append(bezier)
    CockpitTop = doc.addObject('Part::Compound', 'CockpitTop')
    CockpitTop.Links = CockpitTop_parts
    CockpitTop.Placement.Base = Vector(0.0, 0.0, 4.0) * scaleFactor
    CockpitTop.Placement.Rotation = Rotation (0.0, 0.0, 0.0, 1.0)
    
    CockpitSide_parts = []
    poles = []
    poles.append(Vector(33.9, 5.23, 0.0) * scaleFactor)
    poles.append(Vector(64.33, 11.8, 0.0) * scaleFactor)
    poles.append(Vector(67.07, 5.18, 0.0) * scaleFactor)
    weights = [1.0, 1.0, 1.0]
    knots = [0.0, 1.0]
    mults = [3, 3]
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults, knots, False, 2, weights, False)
    bezier = doc.addObject('Part::Spline', 'BSplineCurve')
    bezier.Shape = bspline.toShape()
    CockpitSide_parts.append(bezier)
    CockpitSide = doc.addObject('Part::Compound', 'CockpitSide')
    CockpitSide.Links = CockpitSide_parts
    CockpitSide.Placement.Base = Vector(0.0, 0.0, 0.0) * scaleFactor
    CockpitSide.Placement.Rotation = Rotation (0.5, 0.5, 0.5, 0.5)
    
    doc.recompute() 
   
    CockpitFront.ViewObject.Visibility = False
    CockpitSide.ViewObject.Visibility = False
    CockpitTop.ViewObject.Visibility = False
    
    doc.recompute()
    CockpitRight = CurvedShapes.makeCurvedArray(Base=CockpitFront, 
                                             Hullcurves=[CockpitSide, CockpitTop], 
                                             Axis=Vector(0,1,0), 
                                             Items=16, 
                                             OffsetStart=0, 
                                             OffsetEnd=0,
                                             Surface=False,
                                             extract=False) 

    CockpitTopLeft = doc.addObject('Part::Mirroring', 'CockpitTopLeft')
    CockpitTopLeft.Normal = Vector(1.0, 0.0, 0.0)
    CockpitTopLeft.Source = CockpitTop
    CockpitTopLeft.ViewObject.hide()
    
    CockpitFrontLeft = doc.addObject('Part::Mirroring', 'CockpitFrontLeft')
    CockpitFrontLeft.Normal = Vector(1.0, 0.0, 0.0)
    CockpitFrontLeft.Source = CockpitFront
    CockpitFrontLeft.ViewObject.hide()
    doc.recompute()
    
    CockpitLeft = CurvedShapes.makeCurvedArray(Base=CockpitFrontLeft, 
                                             Hullcurves=[CockpitSide, CockpitTopLeft], 
                                             Axis=Vector(0,1,0), 
                                             Items=16, 
                                             OffsetStart=0, 
                                             OffsetEnd=0,
                                             Surface=True,
                                             extract=False) 
    CockpitLeft.ViewObject.Transparency = 50
    
    Cockpit = doc.addObject('Part::Compound', 'Cockpit')
    Cockpit.Links = [CockpitRight, CockpitLeft]
    Cockpit.ViewObject.Transparency = 50
    
    return Cockpit
    

        
class Horten_HIX():
    def Activated(self):
        import Horten_HIX
        reload(Horten_HIX)
        draw_HortenHIX()
        
    def GetResources(self):
        import CurvedShapes
        import os
        return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "Horten_HIX.svg"),
                'MenuText': "Horten H IX",
                'ToolTip' : "Example shape of a stealth fighter from WW2" }


FreeCADGui.addCommand('Horten_HIX', Horten_HIX())
