import os

import FreeCAD
import FreeCADGui


DEFAULT_SCREENSHOT_WIDTH = 800
DEFAULT_SCREENSHOT_HEIGHT = 600

_VIEW_SETTERS = {
    "Isometric": "viewIsometric",
    "Front": "viewFront",
    "Top": "viewTop",
    "Right": "viewRight",
    "Back": "viewBack",
    "Left": "viewLeft",
    "Bottom": "viewBottom",
    "Dimetric": "viewDimetric",
    "Trimetric": "viewTrimetric",
}


def save_active_screenshot(save_path: str, view_name: str = "Current", width: int | None = None, height: int | None = None, focus_object: str | None = None):
    try:
        view = FreeCADGui.ActiveDocument.ActiveView
        if not hasattr(view, 'saveImage'):
            return "Current view does not support screenshots"

        setter = _VIEW_SETTERS.get(view_name)
        if setter:
            getattr(view, setter)()
        elif view_name != "Current":
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

        w = width or DEFAULT_SCREENSHOT_WIDTH
        h = height or DEFAULT_SCREENSHOT_HEIGHT
        view.saveImage(save_path, w, h)
        return True
    except Exception as e:
        return str(e)


def remove_if_exists(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)

