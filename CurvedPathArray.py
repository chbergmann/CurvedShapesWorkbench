# -*- coding: utf-8 -*-

__title__ = "CurvedPathArray"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Create 3D shapes from 2D curves"

import os
import FreeCAD
from FreeCAD import Vector
import Part
import CompoundTools.Explode
import CurvedShapes
import math
if FreeCAD.GuiUp:
    import FreeCADGui

epsilon = CurvedShapes.epsilon
    
class CurvedPathArray:
    def __init__(self, 
                 obj,
                 base = None,
                 path = None,
                 hullcurves=[], 
                 items=4, 
                 OffsetStart=0, OffsetEnd=0, 
                 Twist=0.0, 
                 Surface=True, 
                 Solid = False,
                 doScale = [],
                 extract=False,
                 LoftMaxDegree=5):
        CurvedShapes.addObjectProperty(obj,"App::PropertyLink",  "Base",     "CurvedPathArray",   "The object to make an array from").Base = base
        CurvedShapes.addObjectProperty(obj,"App::PropertyLink",  "Path",     "CurvedPathArray",   "Sweep path").Path = path
        CurvedShapes.addObjectProperty(obj,"App::PropertyLinkList",  "Hullcurves",   "CurvedPathArray",   "Bounding curves").Hullcurves = hullcurves   
        CurvedShapes.addObjectProperty(obj,"App::PropertyQuantity", "Items", "CurvedPathArray",   "Nr. of array items").Items = items
        CurvedShapes.addObjectProperty(obj,"App::PropertyFloat", "OffsetStart","CurvedPathArray",  "Offset of the first part").OffsetStart = OffsetStart
        CurvedShapes.addObjectProperty(obj,"App::PropertyFloat", "OffsetEnd","CurvedPathArray",  "Offset of the last part from the end in opposite direction").OffsetEnd = OffsetEnd
        CurvedShapes.addObjectProperty(obj,"App::PropertyFloat", "Twist","CurvedPathArray",  "Rotate in degrees around the sweep path").Twist = Twist
        CurvedShapes.addObjectProperty(obj,"App::PropertyBool", "Surface","CurvedPathArray",  "Make a surface").Surface = Surface
        CurvedShapes.addObjectProperty(obj,"App::PropertyBool", "Solid","CurvedPathArray",  "Make a solid").Solid = Solid
        CurvedShapes.addObjectProperty(obj,"App::PropertyBool", "ScaleX","CurvedPathArray",  "Scale by hullcurves in X direction").ScaleX = True
        CurvedShapes.addObjectProperty(obj,"App::PropertyBool", "ScaleY","CurvedPathArray",  "Scale by hullcurves in Y direction").ScaleY = True
        CurvedShapes.addObjectProperty(obj,"App::PropertyBool", "ScaleZ","CurvedPathArray",  "Scale by hullcurves in Z direction").ScaleZ = True
        CurvedShapes.addObjectProperty(obj,"App::PropertyInteger", "LoftMaxDegree", "CurvedPathArray",   "Max Degree for Surface or Solid").LoftMaxDegree = LoftMaxDegree
        self.doScaleXYZsum = [False, False, False]
        if len(doScale) == 3:
            obj.ScaleX = doScale[0]
            obj.ScaleY = doScale[1]
            obj.ScaleZ = doScale[2]
            
        self.extract = extract
        self.doScaleXYZ = []
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
        
        if len(obj.Hullcurves) > 0: 
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
         
        maxlen = 0   
        edgelen = []
        edges = Part.__sortEdges__(obj.Path.Shape.Edges)
        for edge in edges:
            maxlen += edge.Length
            edgelen.append(edge.Length)
        
        for n in range(0, int(obj.Items)):
            plen = obj.OffsetStart
            if obj.Items > 1:
                plen += (maxlen - obj.OffsetStart - obj.OffsetEnd) * n / (float(obj.Items) - 1)
                
            for edge in edges:
                if plen > edge.Length: 
                    plen -= edge.Length
                else:
                    param = edge.getParameterByLength(plen)
                    direction = edge.tangentAt(param) 
                    posvec = edge.valueAt(param) 
                    normal = CurvedShapes.getNormal(obj.Base)
                    rotaxis = normal.cross(direction)
                    angle = math.degrees(normal.getAngle(direction))
            
                    #dolly = self.makeRib(obj, posvec, direction)
                    dolly = obj.Base.Shape.copy()
                    if rotaxis.Length > epsilon:
                        dolly = dolly.rotate(dolly.BoundBox.Center, rotaxis, angle)

                    dolly.Placement.Base = posvec
                    if dolly: 
                        if not obj.Twist == 0 and n > 0:
                            dolly = dolly.rotate(posvec, direction, obj.Twist * n / int(obj.Items))
                            
                        if len(obj.Hullcurves) > 0:
                            if not obj.ScaleX: direction = Vector(1, 0, 0)
                            if not obj.ScaleY: direction = Vector(0, 1, 0)
                            if not obj.ScaleZ: direction = Vector(0, 0, 1)
                            
                            bbox = CurvedShapes.boundbox_from_intersect(obj.Hullcurves, posvec, direction, self.doScaleXYZ)
                            if bbox:
                                dolly = CurvedShapes.scaleByBoundbox(dolly, bbox, self.doScaleXYZsum, copy=True)
                            
                        ribs.append(dolly) 
                        
                    break
        
        
        if (obj.Surface or obj.Solid) and obj.Items > 1:
            obj.Shape = CurvedShapes.makeSurfaceSolid(ribs, obj.Solid, maxDegree=obj.LoftMaxDegree)
        else:
            obj.Shape = Part.makeCompound(ribs)
            
        obj.Placement = pl
        
        if self.extract:
            CompoundTools.Explode.explodeCompound(obj)
            obj.ViewObject.hide()

    
    def execute(self, prop):        
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        bbox = None
        for h in prop.Hullcurves:
            bbox = h.Shape.BoundBox
            doScale = [False, False, False]
            
            if bbox.XLength > epsilon: 
                doScale[0] = True 
        
            if bbox.YLength > epsilon: 
                doScale[1] = True 
        
            if bbox.ZLength > epsilon: 
                doScale[2] = True 
        
            self.doScaleXYZ.append(doScale)
            
        if bbox:    
            for h in prop.Hullcurves:
                bbox.add(h.Shape.BoundBox)
                      
            if bbox.XLength > epsilon: 
                self.doScaleXYZsum[0] = prop.ScaleX
        
            if bbox.YLength > epsilon: 
                self.doScaleXYZsum[1] = prop.ScaleY
        
            if bbox.ZLength > epsilon: 
                self.doScaleXYZsum[2] = prop.ScaleZ
        
        if prop.Items > 0 and prop.Base and hasattr(prop.Base, "Shape") and prop.Path and hasattr(prop.Path, "Shape") and len(prop.Path.Shape.Edges) > 0:
            self.makeRibs(prop)
            return
        
    def onChanged(self, fp, prop):
        if not hasattr(fp, 'LoftMaxDegree'):
            CurvedShapes.addObjectProperty(fp, "App::PropertyInteger", "LoftMaxDegree", "CurvedPathArray",   "Max Degree for Surface or Solid", init_val=5) # backwards compatibility - this upgrades older documents
            
#background compatibility
CurvedPathArrayWorker = CurvedPathArray

class CurvedPathArrayViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
            
    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CurvedPathArray.svg"))

    def attach(self, vobj):
        self.Object = vobj.Object
        self.onChanged(vobj,"Base")

    def claimChildren(self):
        return [self.Object.Base, self.Object.Path] + self.Object.Hullcurves
        
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

    class CurvedPathArrayCommand():
            
        def Activated(self):
            FreeCADGui.doCommand("import CurvedShapes")
            
            selection = FreeCADGui.Selection.getSelectionEx()
            options = ""
            for sel in selection:
                if sel == selection[0]:
                    options += "Base=base, "
                    FreeCADGui.doCommand("base = FreeCAD.ActiveDocument.getObject('%s')"%(selection[0].ObjectName))
                elif sel == selection[1]:
                    options += "Path=path, "
                    FreeCADGui.doCommand("path = FreeCAD.ActiveDocument.getObject('%s')"%(selection[1].ObjectName))
                    options += "Hullcurves=hullcurves, "
                    FreeCADGui.doCommand("hullcurves = []");
                else:
                    FreeCADGui.doCommand("hullcurves.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))
            
            FreeCADGui.doCommand("CurvedShapes.makeCurvedPathArray(%sItems=4, OffsetStart=0, OffsetEnd=0, Surface=False, Solid=False)"%(options))
            FreeCAD.ActiveDocument.recompute()        

        def IsActive(self):
            """Here you can define if the command must be active or not (greyed) if certain conditions
            are met or not. This function is optional."""
            #if FreeCAD.ActiveDocument:
            return(True)
            #else:
            #    return(False)
            
        def GetResources(self):
            return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "CurvedPathArray.svg"),
                    'Accel' : "", # a default shortcut (optional)
                    'MenuText': "Curved Path Array",
                    'ToolTip' : "Creates an array, sweeps the elements around a path curve, and resizes the items in the bounds of optional hullcurves." }

    FreeCADGui.addCommand('CurvedPathArray', CurvedPathArrayCommand())
