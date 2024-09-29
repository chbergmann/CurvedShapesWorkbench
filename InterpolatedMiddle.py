# -*- coding: utf-8 -*-

__title__ = "InterpolatedMiddle"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Interpolates a 2D shape into the middle between two 2D curves"

import os
import FreeCAD
from FreeCAD import Vector
import Part
import CurvedShapes
import CurvedSegment
if FreeCAD.GuiUp:
    import FreeCADGui

epsilon = CurvedShapes.epsilon
    
class InterpolatedMiddle:
    def __init__(self, 
                 fp,    # FeaturePython
                 shape1 = None, 
                 shape2 = None, 
                 normalShape1=Vector(0,0,0), 
                 normalShape2=Vector(0,0,0), 
                 surface=False, 
                 solid=False,
                 InterpolationPoints=16,
                 Twist = 0.0,
                 TwistReverse = False,
                 LoftMaxDegree=5,
                 MaxLoftSize=16):
        CurvedShapes.addObjectProperty(fp,"App::PropertyLink",  "Shape1",     "InterpolatedMiddle",   "The first object of the segment").Shape1 = shape1
        CurvedShapes.addObjectProperty(fp,"App::PropertyLink",  "Shape2",     "InterpolatedMiddle",   "The last object of the segment").Shape2 = shape2     
        CurvedShapes.addObjectProperty(fp,"App::PropertyVector", "NormalShape1",    "InterpolatedMiddle",   "Direction axis of Shape1").NormalShape1 = normalShape1 
        CurvedShapes.addObjectProperty(fp,"App::PropertyVector", "NormalShape2",    "InterpolatedMiddle",   "Direction axis of Shape2").NormalShape1 = normalShape2
        CurvedShapes.addObjectProperty(fp,"App::PropertyBool", "makeSurface","InterpolatedMiddle",  "make a surface").makeSurface = surface
        CurvedShapes.addObjectProperty(fp,"App::PropertyBool", "makeSolid","InterpolatedMiddle",  "make a solid").makeSolid = solid
        CurvedShapes.addObjectProperty(fp,"App::PropertyInteger", "InterpolationPoints", "InterpolatedMiddle",   "Unequal edges will be split into this number of points").InterpolationPoints = InterpolationPoints
        CurvedShapes.addObjectProperty(fp,"App::PropertyFloat", "Twist","InterpolatedMiddle",  "Compensates a rotation between Shape1 and Shape2").Twist = Twist
        CurvedShapes.addObjectProperty(fp,"App::PropertyBool", "TwistReverse","InterpolatedMiddle",  "Reverses the rotation of one Shape").TwistReverse = TwistReverse
        CurvedShapes.addObjectProperty(fp,"App::PropertyInteger", "LoftMaxDegree", "InterpolatedMiddle",   "Max Degree for Surface or Solid").LoftMaxDegree = LoftMaxDegree
        CurvedShapes.addObjectProperty(fp,"App::PropertyInteger", "MaxLoftSize", "InterpolatedMiddle",   "Max Size of a Loft in Segments.").MaxLoftSize = MaxLoftSize
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
            
        self.update = False
        if fp.NormalShape1 == Vector(0,0,0):        
            fp.NormalShape1 = CurvedShapes.getNormal(fp.Shape1)
        
        if fp.NormalShape2 == Vector(0,0,0):    
            fp.NormalShape2 = CurvedShapes.getNormal(fp.Shape2)
        
        self.makeRibs(fp)
        
        self.update = True
        
        
    def onChanged(self, fp, prop):
        if not hasattr(fp, 'LoftMaxDegree'):
            CurvedShapes.addObjectProperty(fp, "App::PropertyInteger", "LoftMaxDegree", "InterpolatedMiddle",   "Max Degree for Surface or Solid", init_val=5) # backwards compatibility - this upgrades older documents
        if not hasattr(fp, 'MaxLoftSize'):
            CurvedShapes.addObjectProperty(fp,"App::PropertyInteger", "MaxLoftSize", "InterpolatedMiddle",   "Max Size of a Loft in Segments.", init_val=-1) # backwards compatibility - this upgrades older documents


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
            ribs = CurvedSegment.makeRibsInterpolate(fp, 1, True, False)
        else:
            ribs = CurvedSegment.makeRibsSameShape(fp, 1, True, False)
            
        if (fp.makeSurface or fp.makeSolid) and len(ribs) == 1:
            rib1 = [fp.Shape1.Shape, ribs[0]]
            shape1 = CurvedShapes.makeSurfaceSolid(rib1, False, maxDegree=fp.LoftMaxDegree, maxLoftSize=fp.MaxLoftSize)
            rib2 = [ribs[0], fp.Shape2.Shape]
            shape2 = CurvedShapes.makeSurfaceSolid(rib2, False, maxDegree=fp.LoftMaxDegree, maxLoftSize=fp.MaxLoftSize)
            
            shape = Part.makeCompound([shape1, shape2])
            
            if fp.makeSolid:
                surfaces = shape1.Faces + shape2.Faces
                
                face1 = CurvedShapes.makeFace(fp.Shape1.Shape)
                if face1:
                    surfaces.append(face1)
                face2 = CurvedShapes.makeFace(fp.Shape2.Shape)
                if face2:
                    surfaces.append(face2)
        
                try:
                    shell = Part.makeShell(surfaces)
                    if face1 and face2:
                        try:
                            shape = Part.makeSolid(shell)
                        except Exception as ex:
                            FreeCAD.Console.PrintError("Creating solid failed ! " + ex + "\n")
                            
                except Exception as ex:
                    FreeCAD.Console.PrintError("Creating shell failed ! " + ex + "\n")
            
        else:
            shape = Part.makeCompound(ribs)
        
        if shape:
            fp.Shape = shape
                            
#background compatibility
InterpolatedMiddleWorker = InterpolatedMiddle

class InterpolatedMiddleViewProvider:
    def __init__(self, vfp):
        vfp.Proxy = self
        self.Object = vfp.Object
            
    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CornerShape.svg"))

    def attach(self, vfp):
        self.Object = vfp.Object
        self.onChanged(vfp,"Shape1")

    def claimChildren(self):
        return [self.Object.Shape1, self.Object.Shape2]
        
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

    class InterpolatedMiddleCommand():
            
        def Activated(self):
            FreeCADGui.doCommand("import CurvedShapes")
            
            selection = FreeCADGui.Selection.getSelectionEx()
            if len(selection) < 1:
                FreeCADGui.doCommand('shape1 = None')
            else:
                FreeCADGui.doCommand("shape1 = FreeCAD.ActiveDocument.getObject('%s')"%(selection[0].ObjectName))
            
            if len(selection) < 2:
                FreeCADGui.doCommand('shape2 = None')
            else:
                FreeCADGui.doCommand("shape2 = FreeCAD.ActiveDocument.getObject('%s')"%(selection[1].ObjectName))
            
            FreeCADGui.doCommand("CurvedShapes.makeInterpolatedMiddle(shape1, shape2, Surface=True, Solid=False)")
            FreeCAD.ActiveDocument.recompute()        

        def IsActive(self):
            """Here you can define if the command must be active or not (greyed) if certain conditions
            are met or not. This function is optional."""
            #if FreeCAD.ActiveDocument:
            return(True)
            #else:
            #    return(False)
            
        def GetResources(self):
            return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CornerShape.svg"),
                    'Accel' : "", # a default shortcut (optional)
                    'MenuText': "Interpolated Middle",
                    'ToolTip' : __doc__ }

    FreeCADGui.addCommand('InterpolatedMiddle', InterpolatedMiddleCommand())
