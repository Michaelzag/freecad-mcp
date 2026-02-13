import os

import FreeCAD
import FreeCADGui


def save_active_screenshot(save_path: str, view_name: str = "Isometric", width: int | None = None, height: int | None = None, focus_object: str | None = None):
    try:
        view = FreeCADGui.ActiveDocument.ActiveView
        if not hasattr(view, 'saveImage'):
            return "Current view does not support screenshots"

        if view_name == "Isometric":
            view.viewIsometric()
        elif view_name == "Front":
            view.viewFront()
        elif view_name == "Top":
            view.viewTop()
        elif view_name == "Right":
            view.viewRight()
        elif view_name == "Back":
            view.viewBack()
        elif view_name == "Left":
            view.viewLeft()
        elif view_name == "Bottom":
            view.viewBottom()
        elif view_name == "Dimetric":
            view.viewDimetric()
        elif view_name == "Trimetric":
            view.viewTrimetric()
        else:
            raise ValueError(f"Invalid view name: {view_name}")

        if focus_object:
            doc = FreeCAD.ActiveDocument
            obj = doc.getObject(focus_object) if doc else None
            if obj:
                FreeCADGui.Selection.clearSelection()
                FreeCADGui.Selection.addSelection(obj)
                FreeCADGui.SendMsgToActiveView("ViewSelection")
            else:
                view.fitAll()
        else:
            view.fitAll()

        if width is not None and height is not None:
            view.saveImage(save_path, width, height)
        else:
            view.saveImage(save_path)
        return True
    except Exception as e:
        return str(e)


def remove_if_exists(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)

