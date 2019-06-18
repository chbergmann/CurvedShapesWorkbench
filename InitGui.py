# -*- coding: utf-8 -*-

__title__="FreeCAD CurvedShapes Workbench - Init file"
__author__ = "Christian Bergmann"
__url__ = ["http://www.freecadweb.org"]


class CurvedShapesWB (Workbench):
    def __init__(self):
        import os
        import CurvedShapes
        self.__class__.MenuText = "Curved Shapes"
        self.__class__.ToolTip = "Creates 3D designs from 2D curves"
        self.__class__.Icon = os.path.join(CurvedShapes.get_module_path(), "Resources", "icons", "curvedArray.svg")

    def Initialize(self):
        "This function is executed when FreeCAD starts"
        # import here all the needed files that create your FreeCAD commands
        import CurvedShapes 
        import CurvedSegment
        import CurvedArray   
        import InterpolatedMiddle 
        import SketchToPython
        import Horten_HIX
        self.list = ["CurvedArray", "CurvedSegment", "InterpolatedMiddle", "SketchToPython", "Horten_HIX"] # A list of command names created in the line above
        self.appendToolbar("Curved Shapes",self.list) # creates a new toolbar with your commands
        self.appendMenu("Curved Shapes",self.list) # creates a new menu

    def Activated(self):
        "This function is executed when the workbench is activated"
        return

    def Deactivated(self):
        "This function is executed when the workbench is deactivated"
        return

    def ContextMenu(self, recipient):
        "This is executed whenever the user right-clicks on screen"
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu("Curved Shapes",self.list) # add commands to the context menu

    def GetClassName(self): 
        # this function is mandatory if this is a full python workbench
        return "Gui::PythonWorkbench"
       
Gui.addWorkbench(CurvedShapesWB())