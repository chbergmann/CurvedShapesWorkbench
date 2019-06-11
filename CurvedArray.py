# -*- coding: utf-8 -*-

__title__ = "CurvedArray"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Create 3D shapes from 2D curves"

import sys
import os
import FreeCADGui
import FreeCAD
from FreeCAD import Vector
import Part
import Draft
import CompoundTools.Explode
import CurvedShapes

global epsilon
epsilon = CurvedShapes.epsilon
    
class CurvedArrayWorker:
    def __init__(self, 
                 obj,
                 base = None,
                 hullcurves=[], 
                 axis=Vector(0.0,0.0,0.0), items=2, 
                 OffsetStart=0, OffsetEnd=0, 
                 Twist=0.0, 
                 Surface=True, 
                 Solid = False,
                 extract=False):
        obj.addProperty("App::PropertyLink",  "Base",     "CurvedArray",   "The object to make an array from").Base = base
        obj.addProperty("App::PropertyLinkList",  "Hullcurves",   "CurvedArray",   "Bounding curves").Hullcurves = hullcurves        
        obj.addProperty("App::PropertyVector", "Axis",    "CurvedArray",   "Direction axis").Axis = axis
        obj.addProperty("App::PropertyQuantity", "Items", "CurvedArray",   "Nr. of array items").Items = items
        obj.addProperty("App::PropertyFloat", "OffsetStart","CurvedArray",  "Offset of the first part in Axis direction").OffsetStart = OffsetStart
        obj.addProperty("App::PropertyFloat", "OffsetEnd","CurvedArray",  "Offset of the last part from the end in opposite Axis direction").OffsetEnd = OffsetEnd
        obj.addProperty("App::PropertyFloat", "Twist","CurvedArray",  "Offset of the last part from the end in opposite Axis direction").Twist = Twist
        obj.addProperty("App::PropertyBool", "Surface","CurvedArray",  "make a surface").Surface = Surface
        obj.addProperty("App::PropertyBool", "Solid","CurvedArray",  "make a solid").Solid = Solid
        self.obj = obj
        self.extract = extract
        self.compound = None
        self.doScaleXYZ = []
        self.doScaleXYZsum = [False, False, False]
        obj.Proxy = self
        self.execute("Base")
    
    
    def boundbox_from_intersect(self, pos, normal):
        curves = self.obj.Hullcurves
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
                        parm = edge.Curve.parameter(CurvedShapes.PointVec(p))
                        if parm >= edge.FirstParameter and parm <= edge.LastParameter:    
                            ipoints.append(p)
                            found = True
            
            if found == False:
                return None
            
            use_x = True
            use_y = True
            use_z = True
            if len(ipoints) > 1:
                use_x = self.doScaleXYZ[n][0]
                use_y = self.doScaleXYZ[n][1]
                use_z = self.doScaleXYZ[n][2] 
            
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
       

    def makeRibs(self):
        pl = self.obj.Placement
        ribs = []
        curvebox = FreeCAD.BoundBox(float("-inf"), float("-inf"), float("-inf"), float("inf"), float("inf"), float("inf"))
            
        for n in range(0, len(self.obj.Hullcurves)):
            cbbx = self.obj.Hullcurves[n].Shape.BoundBox
            if self.doScaleXYZ[n][0]:
                if cbbx.XMin > curvebox.XMin: curvebox.XMin = cbbx.XMin
                if cbbx.XMax < curvebox.XMax: curvebox.XMax = cbbx.XMax
            if self.doScaleXYZ[n][1]:
                if cbbx.YMin > curvebox.YMin: curvebox.YMin = cbbx.YMin
                if cbbx.YMax < curvebox.YMax: curvebox.YMax = cbbx.YMax
            if self.doScaleXYZ[n][2]:
                if cbbx.ZMin > curvebox.ZMin: curvebox.ZMin = cbbx.ZMin
                if cbbx.ZMax < curvebox.ZMax: curvebox.ZMax = cbbx.ZMax
            
        if curvebox.XMin == float("inf"): 
            curvebox.XMin = self.obj.Hullcurves[0].Shape.BoundBox.XMin
        if curvebox.XMin == float("-inf"): 
            curvebox.XMax = self.obj.Hullcurves[0].Shape.BoundBox.XMax
        if curvebox.YMin == float("inf"): 
            curvebox.YMin = self.obj.Hullcurves[0].Shape.BoundBox.YMin
        if curvebox.YMax == float("-inf"): 
            curvebox.YMax = self.obj.Hullcurves[0].Shape.BoundBox.YMax
        if curvebox.ZMin == float("inf"): 
            curvebox.ZMin = self.obj.Hullcurves[0].Shape.BoundBox.ZMin
        if curvebox.ZMax == float("-inf"): 
            curvebox.ZMax = self.obj.Hullcurves[0].Shape.BoundBox.ZMax
         
        areavec = Vector(curvebox.XLength, curvebox.YLength, curvebox.ZLength)
        deltavec = areavec.scale(self.obj.Axis.x, self.obj.Axis.y ,self.obj.Axis.z) - (self.obj.OffsetStart + self.obj.OffsetEnd) * self.obj.Axis
        sections = int(self.obj.Items)
        startvec = Vector(curvebox.XMin, curvebox.YMin, curvebox.ZMin)
        if self.obj.Axis.x < 0: startvec.x = curvebox.XMax
        if self.obj.Axis.y < 0: startvec.y = curvebox.YMax
        if self.obj.Axis.z < 0: startvec.z = curvebox.ZMax
        pos0 = startvec + (self.obj.OffsetStart * self.obj.Axis)      
            
        for n in range(0, sections):
            if sections > 1:
                posvec = pos0 + (deltavec * n / (sections - 1))
            else:
                posvec = pos0
                
            dolly = self.makeRib(posvec)
            if dolly: 
                if not self.obj.Twist == 0:
                    dolly.rotate(dolly.BoundBox.Center, self.obj.Axis, self.obj.Twist * posvec.Length / areavec.Length)
                ribs.append(dolly)  
        
        if self.extract:
            links = []
            for r in ribs:
                f = FreeCAD.ActiveDocument.addObject("Part::Feature","CurvedArrayElement")
                f.Shape = r
                links.append(f)
            
            self.compound = FreeCAD.ActiveDocument.addObject("Part::Compound","CurvedArrayElements")
            self.compound.Links = links
        
        if (self.obj.Surface or self.obj.Solid) and self.obj.Items > 1:
            self.makeSurfaceSolid(ribs)
        else:
            self.obj.Shape = Part.makeCompound(ribs)
            
        self.obj.Placement = pl
        
            
    def makeSurfaceSolid(self, ribs):
        surfaces = []
        for e in range(0, len(self.obj.Base.Shape.Edges)):
            edge = self.obj.Base.Shape.Edges[e]      
            bs = edge.Curve.toBSpline()
            umults = bs.getMultiplicities()
            uknots = bs.getKnots()
            uperiodic = bs.isPeriodic()
            udegree = bs.Degree
            uweights = bs.getWeights()
            
            weights = []
            poles = []
            for r in ribs:
                weights += uweights
                poles.append(r.Edges[e].Curve.getPoles())
            
            if len(ribs) > 3:
                vmults = [4]
                vknots = [0]
                for i in range(1, len(ribs) - 3):
                    vknots.append(i * 1.0 / (len(ribs) - 1))
                    vmults.append(1)
                vmults.append(4)
                vknots.append(1.0)
            else:
                vmults = [len(ribs), len(ribs)]
                vknots = [0.0, 1.0]
            
        #print("poles:" + str(len(poles)) + "x" + str(len(poles[0])))
        #print("umults:" + str(umults))
        #print("vmults:" + str(vmults))
        #print("uknots:" + str(uknots))
        #print("vknots:" + str(vknots))
        
            try:
                bs = Part.BSplineSurface()
                bs.buildFromPolesMultsKnots(poles, vmults, umults, vknots, uknots, False, uperiodic, udegree, udegree) 
                surfaces.append(bs.toShape())
            except:            
                wiribs = []
                for r in ribs:
                    wiribs.append(Part.Wire(r.Edges))
                                    
                surfaces.append(Part.makeLoft(wiribs))
                    
            if len(surfaces) == 1:
                self.obj.Shape = surfaces[0]
            elif len(surfaces) > 1:
                self.obj.Shape = Part.makeCompound(surfaces)
            
        if self.obj.Solid:  
            face1 = self.makeFace(ribs[0])
            if face1:
                face2 = self.makeFace(ribs[len(ribs)-1])
                shell = Part.makeShell([face1, face2, self.obj.Shape])
                self.obj.Shape = Part.makeSolid(shell)
            
    def makeFace(self, rib):
        wire = Part.Wire(rib.Edges)
        if wire.isClosed():
            return Part.makeFace(wire, "Part::FaceMakerSimple")
        else:
            FreeCAD.Console.PrintError("Base shape is not closed. Cannot draw solid")
        
        
    def makeRib(self, posvec):
        basebbox = self.obj.Base.Shape.BoundBox    
        basepl = self.obj.Base.Placement 
        bbox = self.boundbox_from_intersect(posvec, self.obj.Axis)
        if not bbox:
            return None
          
        #box = Part.makeBox(max(bbox.XLength, 0.1), max(bbox.YLength, 0.1), max(bbox.ZLength, 0.1))
        #box.Placement.Base.x = bbox.XMin
        #box.Placement.Base.y = bbox.YMin
        #box.Placement.Base.z = bbox.ZMin
        #Part.show(box)        
        scalevec = Vector(1, 1, 1)
        if basebbox.XLength > epsilon: scalevec.x = bbox.XLength / basebbox.XLength
        if basebbox.YLength > epsilon: scalevec.y = bbox.YLength / basebbox.YLength
        if basebbox.ZLength > epsilon: scalevec.z = bbox.ZLength / basebbox.ZLength     
        if scalevec.x < epsilon: 
            if self.doScaleXYZsum[0]:
                scalevec.x = epsilon   
            else:
                scalevec.x = 1   
        if scalevec.y < epsilon: 
            if self.doScaleXYZsum[1]:
                scalevec.y = epsilon   
            else:
                scalevec.y = 1
        if scalevec.z < epsilon: 
            if self.doScaleXYZsum[2]:
                scalevec.z = epsilon   
            else:
                scalevec.z = 1
        
        scalevec2 = scalevec
        if abs(self.obj.Axis.x) > 1 - epsilon: scalevec2.x = 1
        if abs(self.obj.Axis.y) > 1 - epsilon: scalevec2.y = 1
        if abs(self.obj.Axis.z) > 1 - epsilon: scalevec2.z = 1
        dolly = CurvedShapes.scale(self.obj.Base, scalevec2)
        
        dolly.Placement = basepl
        if self.doScaleXYZsum[0]:
            dolly.Placement.Base.x += bbox.XMin - basebbox.XMin * scalevec.x  
        if self.doScaleXYZsum[1]:           
            dolly.Placement.Base.y += bbox.YMin - basebbox.YMin * scalevec.y
        if self.doScaleXYZsum[2]:
            dolly.Placement.Base.z += bbox.ZMin - basebbox.ZMin * scalevec.z
        return dolly
    
    
    def execute(self, prop):
        proplist = ["Base", "Hullcurves", "Axis", "Items", "OffsetStart", "OffsetEnd", "Twist", "Surface", "Solid"]
        if prop in proplist:      
            if self.obj.Base and self.obj.Axis == Vector(0.0,0.0,0.0):
                if hasattr(self.obj.Base, 'Dir'):
                    self.obj.Axis = self.obj.Base.Dir
                else:
                    self.obj.Axis = self.obj.Base.Placement.Rotation.multVec(Vector(0, 0, 1))
                return
            
            self.doScaleXYZ = []
            self.doScaleXYZsum = [False, False, False]
            for h in self.obj.Hullcurves:
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
 
            if self.obj.Items > 0 and self.obj.Base and hasattr(self.obj.Base, "Shape") and len(self.obj.Hullcurves) > 0:
                self.makeRibs()
     
     
    def onChanged(self, fp, prop):
        self.execute(prop)  
        
        
    def getObj(self):
        if self.extract:
            return self.compound
        else:
            return self.obj  


class CurvedArrayViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
            
    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "curvedArray.svg"))

    def attach(self, vobj):
        self.Object = vobj.Object
        self.onChanged(vobj,"Base")

    def claimChildren(self):
        return [self.Object.Base] + self.Object.Hullcurves
        
    def onDelete(self, feature, subelements):
        return True
    
    def onChanged(self, fp, prop):
        pass
        
    def __getstate__(self):
        return None
 
    def __setstate__(self,state):
        return None
        

class CurvedArray():
        
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
                'MenuText': "Curved Array",
                'ToolTip' : "Creates an array and resizes the items in the bounds of curves in the XY, XZ or YZ plane." }

FreeCADGui.addCommand('CurvedArray', CurvedArray())
