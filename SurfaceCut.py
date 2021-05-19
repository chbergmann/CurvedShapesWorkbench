# -*- coding: utf-8 -*-
__title__ = "SurfaceCut"
__author__ = "Christian Bergmann"
__license__ = "LGPL 2.1"
__doc__ = "Create 3D shapes from 2D curves"

import os
import FreeCADGui
import FreeCAD
from FreeCAD import Vector
import Part
import CurvedShapes
    
epsilon = CurvedShapes.epsilon

class SurfaceCutWorker:
    def __init__(self, obj, Surfaces=[], Normal=Vector(0, 0, 1), Position=0, Face=False, Simplify=0): 
        obj.addProperty("App::PropertyLinkList",  "Surfaces",   "SurfaceCut",   "List of objects with a surface").Surfaces = Surfaces
        obj.addProperty("App::PropertyVector",  "Normal",   "SurfaceCut",   "Normal vector of the cut plane").Normal = Normal
        obj.addProperty("App::PropertyVector",  "Position",   "SurfaceCut",   "Position of the cut plane relative to Surfaces").Position = Position
        obj.addProperty("App::PropertyBool",  "Face",   "SurfaceCut",   "make a face").Face = Face
        obj.addProperty("App::PropertyQuantity",  "Simplify",   "SurfaceCut",   "if >0, discretize each edge to this number of poles and approximate.").Simplify = Simplify
        self.update = True
        obj.Proxy = self  
    

    def execute(self, fp):       
        self.cutSurfaces(fp)
        self.makeFace(fp)
        
    def makeFace(self, fp):
        if fp.Face and len(fp.Shape.Wires) > 0:
            face = Part.makeFace(fp.Shape.Wires, "Part::FaceMakerSimple")
            fp.Shape = face
         
     
    def onChanged(self, fp, prop):
        props = ["Surfaces", "Position", "Normal", "Simplify"]
        if prop in props:
            self.execute(fp)  
            
        if prop == "Face":
            if fp.Face == True:
                self.makeFace(fp)
            else:
                fp.Shape = Part.Compound(fp.Shape.Wires)
                

    def cutSurfaces(self, fp):
        edges=list()
        
        if len(fp.Surfaces) == 1:
            vOffset = fp.Surfaces[0].Placement.Base
        else:
            bbox = None
            for obj in fp.Surfaces:
                if not bbox:
                    bbox = obj.Shape.BoundBox
                else:
                    bbox = bbox.united(obj.Shape.BoundBox)
                
            vOffset = Vector(bbox.XMin, bbox.YMin, bbox.ZMin)
            
        vOffset += fp.Position
        origin = Vector(0,0,0)
        off = origin.distanceToPlane(vOffset, fp.Normal) * -1
            
        for obj in fp.Surfaces:
            for wire in obj.Shape.slice(fp.Normal, off):
                edges += wire.Edges
        
        if fp.Simplify > 0:    
            edges = self.removeEdgeComplexity(fp, edges) 
            
        edges = self.removeDoubles(edges)
            
        comp = Part.Compound(edges)
        comp.connectEdgesToWires(False, 1e-7)  
        fp.Shape = comp
        
    
    def removeEdgeComplexity(self, fp, edges):
        newedges = []
        for e in edges:
            if fp.Simplify > 0 and type(e.Curve) == Part.BSplineCurve and e.Curve.NbPoles > fp.Simplify:         
                poles = e.discretize(Deflection = 1.0)
                bc = Part.BSplineCurve()
                bc.approximate(poles)
                
                newedges.append(bc.toShape().Edges[0])            
            else:
                newedges.append(e)
                
        return newedges
    
    
    def removeDoubles(self, edges):
        newedges = []
        for e in edges:
            found = False
            for e2 in edges:                
                if e != e2 and self.isSameEdge(e, e2):
                    found = True
                    break
                    
            if not found:
                newedges.append(e)
                
        return newedges
                    
                    
    def isSameEdge(self, e1, e2):
        pol1 = e1.discretize(Deflection = 1.0)
        pol2 = e2.discretize(Deflection = 1.0)
        if len(pol1) != len(pol2): return False
        
        equal = True
        for n in range(len(pol1)):
            v = pol1[n] - pol2[n]
            if v.Length > epsilon: equal = False
            
        if equal: return True
        
        for n in range(len(pol1)):
            v = pol1[n] - pol2[len(pol1) - n - 1]
            if v.Length > epsilon: return False
            
        return True
        
        

class SurfaceCutViewProvider:
    def __init__(self, vfp):
        vfp.Proxy = self
        self.Object = vfp.Object
       
    def getIcon(self):
        return (os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "surfaceCut.svg"))

    def attach(self, vobj):
        self.Object = vobj.Object

    def claimChildren(self):
        return self.Object.Surfaces
        
    def onDelete(self, feature, subelements):
        return True
    
    def onChanged(self, fp, prop):
        pass
        

class SurfaceCut():
        
    def Activated(self):
        import SurfaceCut
        FreeCADGui.doCommand("import CurvedShapes")
        
        selection = FreeCADGui.Selection.getSelectionEx()
        FreeCADGui.doCommand("curves = []")
        for sel in selection:
            FreeCADGui.doCommand("curves.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))
        
        FreeCADGui.doCommand("CurvedShapes.cutSurfaces(curves, Normal = FreeCAD.Vector(0, 0, 1), Position=FreeCAD.Vector(0,0,0), Face=False, Simplify=False)")
        FreeCAD.ActiveDocument.recompute()        

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)
        
    def GetResources(self):
        return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "surfaceCut.svg"),
                'Accel' : "", # a default shortcut (optional)
                'MenuText': "Surface Cut",
                'ToolTip' : "Creates a wire by cutting through surfaces" }


FreeCADGui.addCommand('SurfaceCut', SurfaceCut())

