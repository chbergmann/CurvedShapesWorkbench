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
from importlib import reload
    
global epsilon
epsilon = CurvedShapes.epsilon

class SurfaceCutWorker:
    def __init__(self, obj, Surfaces=[], Normal=Vector(0, 0, 1), Offset=0, Face=False, Simplify=False): 
        obj.addProperty("App::PropertyLinkList",  "Surfaces",   "SurfaceCut",   "List of objects with a surface").Surfaces = Surfaces
        obj.addProperty("App::PropertyVector",  "Normal",   "SurfaceCut",   "Normal vector of the cut plane").Normal = Normal
        obj.addProperty("App::PropertyFloat",  "Offset",   "SurfaceCut",   "Position of the cut plane").Offset = Offset
        obj.addProperty("App::PropertyBool",  "Face",   "SurfaceCut",   "make a face").Face = Face
        obj.addProperty("App::PropertyBool",  "Simplify",   "SurfaceCut",   "reduce the number of poles in complex curves").Simplify = Simplify
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
        props = ["Surfaces", "Offset", "Normal", "Simplify"]
        if prop in props:
            self.execute(fp)  
            
        if prop == "Face":
            if fp.Face == True:
                self.makeFace(fp)
            else:
                fp.Shape = Part.Compound(fp.Shape.Wires)
                

    def cutSurfaces(self, fp):
        edges=list()
        
        bbox = None
        for obj in fp.Surfaces:
            if not bbox:
                bbox = obj.Shape.BoundBox
            else:
                bbox = bbox.united(obj.Shape.BoundBox)
            
        vOffset = Vector(bbox.XMin * fp.Normal.x, bbox.YMin * fp.Normal.y, bbox.ZMin * fp.Normal.z)
        if vOffset.x < 0 or vOffset.y < 0 or vOffset.z < 0:
            off = -vOffset.Length
        else:
            off = vOffset.Length
            
        for obj in fp.Surfaces:
            for wire in obj.Shape.slice(fp.Normal, off + fp.Offset):
                edges += wire.Edges
        
        if fp.Simplify:    
            edges = self.removeEdgeComplexity(edges) 
            
        comp = Part.Compound(edges)
        comp.connectEdgesToWires(False, 1e-7)  
        fp.Shape = comp
        
    
    def removeEdgeComplexity(self, edges):
        newedges = []
        for e in edges:
            if type(e.Curve) == Part.BSplineCurve and e.Curve.NbPoles > 16:         
                poles = e.discretize(Deflection = 1.0)
                bc = Part.BSplineCurve()
                bc.approximate(poles)
                newedges.append(bc.toShape().Edges[0])            
            else:
                newedges.append(e)
                
        return newedges
    

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
        reload(SurfaceCut)
        
        selection = FreeCADGui.Selection.getSelectionEx()
        FreeCADGui.doCommand("curves = []")
        for sel in selection:
            FreeCADGui.doCommand("curves.append(FreeCAD.ActiveDocument.getObject('%s'))"%(sel.ObjectName))
        
        FreeCADGui.doCommand("CurvedShapes.cutSurfaces(curves, Normal = FreeCAD.Vector(0, 0, 1), Offset=0, Face=False, Simplify=False)")
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

