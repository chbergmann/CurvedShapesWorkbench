# -*- coding: utf-8 -*-

__title__ = "CurvedArray"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Creates an array and resizes the items in the bounds of curves in the XY, XZ or YZ plane."

import os
import FreeCAD
from FreeCAD import Vector
import Part
import CompoundTools.Explode
import CurvedShapes
if FreeCAD.GuiUp:
    import FreeCADGui

epsilon = CurvedShapes.epsilon
translate = FreeCAD.Qt.translate

class CurvedArray:
    def __init__(self, 
                 obj,
                 base = None,
                 hullcurves=[], 
                 axis=Vector(0.0,0.0,0.0), 
                 items=2, 
                 Positions = [],
                 OffsetStart=0, OffsetEnd=0, 
                 Twist=0.0, 
                 Surface=True, 
                 Solid = False,
                 Distribution = 'linear',
                 DistributionReverse = False,
                 extract=False,
                 Twists = [],
                 LoftMaxDegree=5,
                 MaxLoftSize=16,
                 KeepBase='None'):
        CurvedShapes.addObjectProperty(obj, "App::PropertyLink", "Base", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "The object to make an array from")).Base = base
        CurvedShapes.addObjectProperty(obj, "App::PropertyLinkList", "Hullcurves", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Bounding curves")).Hullcurves = hullcurves
        CurvedShapes.addObjectProperty(obj, "App::PropertyVector", "Axis", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Direction axis")).Axis = axis
        CurvedShapes.addObjectProperty(obj, "App::PropertyQuantity", "Items", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Nr. of array items")).Items = items
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloatList", "Positions", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Positions for ribs (as floats from 0.0 to 1.0) -- overrides Items")).Positions = Positions
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloat", "OffsetStart", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Offset of the first part in Axis direction")).OffsetStart = OffsetStart
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloat", "OffsetEnd", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Offset of the last part from the end in opposite Axis direction")).OffsetEnd = OffsetEnd
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloat", "Twist", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Rotate around Axis in degrees")).Twist = Twist
        CurvedShapes.addObjectProperty(obj, "App::PropertyFloatList", "Twists", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Rotate around Axis in degrees for each item -- overrides Twist")).Twists = Twists
        CurvedShapes.addObjectProperty(obj, "App::PropertyEnumeration", "KeepBase", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Include the base shape unmodified and where"))
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "Surface", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Make a surface")).Surface = Surface
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "Solid", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Make a solid")).Solid = Solid
        CurvedShapes.addObjectProperty(obj, "App::PropertyEnumeration", "Distribution", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Algorithm for distance between elements"))
        CurvedShapes.addObjectProperty(obj, "App::PropertyBool", "DistributionReverse", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Reverses direction of Distribution algorithm")).DistributionReverse = DistributionReverse
        CurvedShapes.addObjectProperty(obj, "App::PropertyInteger", "LoftMaxDegree", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Max Degree for Surface or Solid")).LoftMaxDegree = LoftMaxDegree
        CurvedShapes.addObjectProperty(obj, "App::PropertyInteger", "MaxLoftSize", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Max Size of a Loft in Segments.")).MaxLoftSize = MaxLoftSize
        obj.Distribution = ['linear', 'parabolic', 'x³', 'sinusoidal', 'asinusoidal', 'elliptic']
        obj.Distribution = Distribution
        obj.KeepBase = ['None', 'First', 'Last']
        obj.KeepBase = KeepBase
        self.extract = extract
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        obj.Proxy = self


    def makeRibs(self, obj):
        pl = obj.Placement
        ribs = []
        curvebox = FreeCAD.BoundBox(float("-inf"), float("-inf"), float("-inf"), float("inf"), float("inf"), float("inf"))

        for n in range(0, len(obj.Hullcurves)):
            cbbx = obj.Hullcurves[n].Shape.BoundBox
            if self.doScaleXYZ[n][0]:
                if cbbx.XMin > curvebox.XMin: curvebox.XMin = cbbx.XMin
                if cbbx.XMax < curvebox.XMax: curvebox.XMax = cbbx.XMax
            if self.doScaleXYZ[n][1]:
                if cbbx.YMin > curvebox.YMin: curvebox.YMin = cbbx.YMin
                if cbbx.YMax < curvebox.YMax: curvebox.YMax = cbbx.YMax
            if self.doScaleXYZ[n][2]:
                if cbbx.ZMin > curvebox.ZMin: curvebox.ZMin = cbbx.ZMin
                if cbbx.ZMax < curvebox.ZMax: curvebox.ZMax = cbbx.ZMax

        if curvebox.XMin == float("-inf"): 
            curvebox.XMin = obj.Hullcurves[0].Shape.BoundBox.XMin
        if curvebox.XMax == float("inf"): 
            curvebox.XMax = obj.Hullcurves[0].Shape.BoundBox.XMax
        if curvebox.YMin == float("-inf"): 
            curvebox.YMin = obj.Hullcurves[0].Shape.BoundBox.YMin
        if curvebox.YMax == float("inf"): 
            curvebox.YMax = obj.Hullcurves[0].Shape.BoundBox.YMax
        if curvebox.ZMin == float("-inf"): 
            curvebox.ZMin = obj.Hullcurves[0].Shape.BoundBox.ZMin
        if curvebox.ZMax == float("inf"): 
            curvebox.ZMax = obj.Hullcurves[0].Shape.BoundBox.ZMax

        areavec = Vector(curvebox.XLength, curvebox.YLength, curvebox.ZLength)
        deltavec = areavec.scale(obj.Axis.x, obj.Axis.y ,obj.Axis.z) - (obj.OffsetStart + obj.OffsetEnd) * obj.Axis
        sections = int(obj.Items)
        startvec = Vector(curvebox.XMin, curvebox.YMin, curvebox.ZMin)
        if obj.Axis.x < 0: startvec.x = curvebox.XMax
        if obj.Axis.y < 0: startvec.y = curvebox.YMax
        if obj.Axis.z < 0: startvec.z = curvebox.ZMax
        pos0 = startvec + (obj.OffsetStart * obj.Axis)

        if (not hasattr(obj,"Positions") or len(obj.Positions) == 0):
            for x in range(0, sections):
                if sections > 1:
                    d = CurvedShapes.distribute(x / (sections - 1), obj.Distribution, obj.DistributionReverse)

                    posvec = pos0 + (deltavec * d)
                else:
                    posvec = pos0

                rib = self.makeRibRotate(obj, posvec, x, d, ribs)
        else:
            x = 0
            for p in obj.Positions:
                posvec = pos0 + (deltavec * p) 

                rib = self.makeRibRotate(obj, posvec, x, x / len(obj.Positions), ribs)
                x = x + 1

        if (obj.KeepBase == 'First'):
            ribs[0] = obj.Base.Shape.copy()
        elif (obj.KeepBase == 'Last'):
            ribs[-1] = obj.Base.Shape.copy()
        
        if (obj.Surface or obj.Solid) and obj.Items > 1:
            obj.Shape = CurvedShapes.makeSurfaceSolid(ribs, obj.Solid, maxDegree=obj.LoftMaxDegree, maxLoftSize=obj.MaxLoftSize)
        else:
            obj.Shape = Part.makeCompound(ribs)

        obj.Placement = pl

        if self.extract:
            CompoundTools.Explode.explodeCompound(obj)
            obj.ViewObject.hide()


    def makeRibRotate(self, obj, posvec, x, d, ribs):
        dolly = self.makeRib(obj, posvec)
        if dolly:
            if x < len(obj.Twists):
                dolly = dolly.rotate(dolly.BoundBox.Center, obj.Axis, obj.Twists[x])
            elif not obj.Twist == 0:
                dolly = dolly.rotate(dolly.BoundBox.Center, obj.Axis, obj.Twist * d)

            ribs.append(dolly)


    def makeRib(self, obj, posvec):
        bbox = CurvedShapes.boundbox_from_intersect(obj.Hullcurves, posvec, obj.Axis, self.doScaleXYZ, False)
        if not bbox:
            return None

        #box = Part.makeBox(max(bbox.XLength, 0.1), max(bbox.YLength, 0.1), max(bbox.ZLength, 0.1))
        #box.Placement.Base.x = bbox.XMin
        #box.Placement.Base.y = bbox.YMin
        #box.Placement.Base.z = bbox.ZMin
        #Part.show(box)

        return CurvedShapes.scaleByBoundbox(obj.Base.Shape, bbox, self.doScaleXYZsum, copy=True)


    def execute(self, prop):
        if prop.Base and prop.Axis == Vector(0.0,0.0,0.0):
            prop.Axis = CurvedShapes.getNormal(prop.Base)
            return

        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        sumbbox=None   #Define the variable other wise it causes error 
        for h in prop.Hullcurves:
            bbox = h.Shape.BoundBox
            if h == prop.Hullcurves[0]:
                sumbbox = bbox
            else:
                sumbbox.add(bbox)

            doScale = [False, False, False]

            if bbox.XLength > epsilon: 
                doScale[0] = True 

            if bbox.YLength > epsilon: 
                doScale[1] = True 

            if bbox.ZLength > epsilon: 
                doScale[2] = True 

            self.doScaleXYZ.append(doScale)

        if sumbbox:
            if sumbbox.XLength > epsilon: 
                self.doScaleXYZsum[0] = True 

            if sumbbox.YLength > epsilon: 
                self.doScaleXYZsum[1] = True 

            if sumbbox.ZLength > epsilon: 
                self.doScaleXYZsum[2] = True

        if (hasattr(prop,"Positions") and len(prop.Positions) != 0) or (prop.Items and prop.Base and hasattr(prop.Base, "Shape") and len(prop.Hullcurves) > 0):
            self.makeRibs(prop)
            return


    def onChanged(self, fp, prop):
        if not hasattr(fp, 'LoftMaxDegree'):
            CurvedShapes.addObjectProperty(fp, "App::PropertyInteger", "LoftMaxDegree", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Max Degree for Surface or Solid"), init_val=5) # backwards compatibility - this upgrades older documents
        if not hasattr(fp, 'MaxLoftSize'):
            CurvedShapes.addObjectProperty(fp, "App::PropertyInteger", "MaxLoftSize", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Max Size of a Loft in Segments."), init_val=-1) # backwards compatibility - this upgrades older documents
        if not hasattr(fp, 'KeepBase'):
            CurvedShapes.addObjectProperty(fp, "App::PropertyEnumeration", "KeepBase", "CurvedArray", QT_TRANSLATE_NOOP("App::Property", "Include the base shape unmodified and where"))
            fp.KeepBase = ['None', 'First', 'Last']
            fp.KeepBase = 'None'
           
        if "Positions" in prop and len(fp.Positions) != 0:
            setattr(fp,"Items",str(len(fp.Positions)))
            outOfBounds = False
            for p in fp.Positions:
                if (p < 0.0 or p > 1.0):
                    outOfBounds = True
                    break
            if outOfBounds:
                FreeCAD.Console.PrintWarning(translate("Curved Shapes", "Some positions are out of bounds, should all be between 0.0 and 1.0, inclusive\n"))


#background compatibility
CurvedArrayWorker = CurvedArray

class CurvedArrayViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object


    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "curvedArray.svg"))


    def attach(self, vobj):
        self.Object = vobj.Object
        self.onChanged(vobj, "Base")


    def claimChildren(self):
        return [self.Object.Base] + self.Object.Hullcurves


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
    class CurvedArrayCommand():
        def QT_TRANSLATE_NOOP(context, text):
            return text


        def Activated(self):
            FreeCADGui.doCommand("import CurvedShapes")


            selection = FreeCADGui.Selection.getSelectionEx()
            options = ""
            for sel in selection:
                if sel == selection[0]:
                    options += "Base=base, "
                    FreeCADGui.doCommand("base = FreeCAD.ActiveDocument.getObject('%s')"%(selection[0].ObjectName))
                    FreeCADGui.doCommand("hullcurves = []");
                    options += "Hullcurves=hullcurves, "
                else:
                    FreeCADGui.doCommand("hullcurves.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))

            FreeCADGui.doCommand("CurvedShapes.makeCurvedArray(%sItems=4, OffsetStart=0, OffsetEnd=0, Surface=False)"%(options))
            FreeCAD.ActiveDocument.recompute()


        def IsActive(self):
            """Here you can define if the command must be active or not (greyed) if certain conditions
            are met or not. This function is optional."""
            #if FreeCAD.ActiveDocument:
            return(True)
            #else:
            #    return(False)


        def GetResources(self):
            return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "curvedArray.svg"),
                    'Accel' : "", # a default shortcut (optional)
                    'MenuText': QT_TRANSLATE_NOOP("CurvedArray", "Curved Array"),
                    'ToolTip' : QT_TRANSLATE_NOOP("CurvedArray", __doc__)}


    FreeCADGui.addCommand('CurvedArray', CurvedArrayCommand())
