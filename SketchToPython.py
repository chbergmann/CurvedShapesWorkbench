# -*- coding: utf-8 -*-

__Name__ = 'Sketch To Python'
__Comment__ = 'Exports the geometry from a FreeCAD sketch to a python script'
__Author__ = 'Christi'
__Version__ = '0.1'
__Date__ = '2019-03-02'
__License__ = 'LGPL-3.0-or-later'
__Web__ = ''
__Wiki__ = 'README.md'
__Icon__ = ''
__Help__ = ''
__Status__ = ''
__Requires__ = 'FreeCAD >= 0.17'
__Communication__ = ''
__Files__ = ''

VERSION_STRING = __Name__ + ' Macro v' + __Version__


import FreeCAD
import FreeCADGui
import Part
import Sketcher
import sys


class SketchToPython:

    def Activated(self):
        doc =FreeCAD.ActiveDocument
        addScript("from FreeCAD import Vector, Placement");
        addScript("import Draft");
        addScript("import Part");
        addScript("doc = App.ActiveDocument")
        addScript("scaleFactor = 1")
        addScript("")
        
        selection = FreeCADGui.Selection.getSelection() 
        if not selection:
            selection = doc.Objects
    
        for obj in selection:
            if 'Geometry' in obj.PropertiesList:
                addSketch(doc.getObject(obj.Name), varname(obj)) 
                addScript("")
        
    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        if not FreeCAD.ActiveDocument:
            return(False)        
                
        selection = FreeCADGui.Selection.getSelection()       
        if not selection:
            selection = FreeCAD.ActiveDocument.Objects
    
        for obj in selection:
            if 'Geometry' in obj.PropertiesList:
                return True
            
        return False
                
    def GetResources(self):
        import CurvedShapes
        import os
        return {'Pixmap'  : os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "SketcherToConsole.svg"),
                'MenuText': __Name__,
                'ToolTip' : __Comment__ }     
 
 
def addScript(line):
    FreeCAD.Console.PrintMessage("\t" + line)
    FreeCAD.Console.PrintMessage("\n")
  
def varname(obj):
    return obj.Label.replace(" ", "_")  
         
def floatstr2(f):
    return str(float("{0:.2f}".format(f)))
    
def floatstr(f):
    return floatstr2(f) + " * scaleFactor"
     
def vecstr(v):
    #return "Vector(" + floatstr(v.x) + ", " + floatstr(v.y) + ", " + floatstr(v.z) + ")"
    return "Vector(" + floatstr2(v.x) + ", " + floatstr2(v.y) + ", " + floatstr2(v.z) + ") * scaleFactor"
            
    
def addSketch(sketch, objname): 
    prop = sketch.getPropertyByName('Geometry') 
    comp = objname + "_parts"
    addScript(comp + " = []")
    skipPoints = 0
    for geo in prop: 
        if geo.Construction == False:
            if isinstance(geo, Part.Point):
                if skipPoints > 0:
                    skipPoints = skipPoints - 1
                else:
                    addScript("point = Draft.makePoint(Vector(%s,%s,%s))"%(floatstr(geo.X), floatstr(geo.Y), floatstr(geo.Z)))
                    addScript(comp + ".append(point)")
        
            if isinstance(geo, Part.Circle):
                addScript("circle = Draft.makeCircle(radius=%f, face=False, support=None)"%(floatstr(geo.Radius)))
                addScript("circle.Placement.Base = " + vecstr(geo.Center))
                addScript(comp + ".append(circle)")
            
            if isinstance(geo, Part.LineSegment):
                addScript("line = Draft.makeWire([%s, %s])"%(vecstr(geo.StartPoint), vecstr(geo.EndPoint)))
                addScript(comp + ".append(line)")
                       
            if isinstance(geo, Part.ArcOfCircle):
                addScript("arc = Draft.makeCircle(radius=%f, face=False,startangle=%f ,endangle=%f, support=None)"%(geo.Radius, geo.FirstParameter, geo.LastParameter))
                addScript("arc.Placement.Base = " + vecstr(geo.Center))
                addScript(comp + ".append(arc)")
                
            if isinstance(geo, Part.Ellipse):
                addScript("ellipse = Draft.makeEllipse(%f, %f, face=False, support=None)"%(geo.MajorRadius, geo.MinorRadius))
                addScript("ellipse.Placement.Base = " + vecstr(geo.Center))
                addScript(comp + ".append(ellipse)")
            
            if isinstance(geo, Part.BSplineCurve):  
                addScript("poles = []")
                for p in geo.getPoles():                    
                    addScript("poles.append(" + vecstr(p) + ")")
                    
                addScript("weights = " + str(geo.getWeights()))
                addScript("knots = " + str(geo.getKnots()))
                addScript("mults = " + str(geo.getMultiplicities()))
                addScript("bspline = Part.BSplineCurve()")
                addScript("bspline.buildFromPolesMultsKnots(poles, mults, knots, %s, %d, weights, %s)"%(geo.isPeriodic(), geo.Degree, geo.isRational()))
                addScript("bezier = doc.addObject('Part::Spline', 'BSplineCurve')") 
                addScript("bezier.Shape = bspline.toShape()")            
                addScript(comp + ".append(bezier)")
                skipPoints = geo.NbPoles - 2
                
    addScript(objname + " = doc.addObject('Part::Compound', '" + objname + "')")
    addScript(objname + ".Links = " + comp)
    addScript(objname + ".Placement.Base = " + vecstr(sketch.Placement.Base))
    addScript(objname + ".Placement.Rotation = " + str(sketch.Placement.Rotation))
    

FreeCADGui.addCommand('SketchToPython', SketchToPython())
