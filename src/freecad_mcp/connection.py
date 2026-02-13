import logging
import xmlrpc.client
from typing import Any, cast


logger = logging.getLogger("FreeCADMCPserver")


class FreeCADConnection:
    def __init__(self, host: str = "localhost", port: int = 9875):
        self.server: Any = xmlrpc.client.ServerProxy(f"http://{host}:{port}", allow_none=True)

    def ping(self) -> bool:
        return cast(bool, self.server.ping())

    def create_document(self, name: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.create_document(name))

    def create_object(self, doc_name: str, obj_data: dict[str, Any]) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.create_object(doc_name, obj_data))

    def create_sketch(
        self,
        doc_name: str,
        sketch_name: str,
        support: str | dict[str, Any] = "XY",
        placement: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self.server.create_sketch(doc_name, sketch_name, support, placement),
        )

    def add_sketch_geometry(
        self, doc_name: str, sketch_name: str, geometry: dict[str, Any]
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self.server.add_sketch_geometry(doc_name, sketch_name, geometry),
        )

    def add_sketch_constraint(
        self, doc_name: str, sketch_name: str, constraint: dict[str, Any]
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self.server.add_sketch_constraint(doc_name, sketch_name, constraint),
        )

    def get_sketch_diagnostics(
        self, doc_name: str, sketch_name: str
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self.server.get_sketch_diagnostics(doc_name, sketch_name),
        )

    def get_sketch_info(
        self, doc_name: str, sketch_name: str
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self.server.get_sketch_info(doc_name, sketch_name),
        )

    def recompute_document(self, doc_name: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.recompute_document(doc_name))

    def pad(
        self, doc_name: str, body_name: str, sketch_name: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.pad(doc_name, body_name, sketch_name, params))

    def pocket(
        self, doc_name: str, body_name: str, sketch_name: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.pocket(doc_name, body_name, sketch_name, params))

    def revolve(
        self, doc_name: str, body_name: str, sketch_name: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.revolve(doc_name, body_name, sketch_name, params))

    def fillet(
        self, doc_name: str, body_name: str, feature_name: str, edges: list[str], params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.fillet(doc_name, body_name, feature_name, edges, params))

    def chamfer(
        self, doc_name: str, body_name: str, feature_name: str, edges: list[str], params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.chamfer(doc_name, body_name, feature_name, edges, params))

    def get_body_features(self, doc_name: str, body_name: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.get_body_features(doc_name, body_name))

    def edit_object(self, doc_name: str, obj_name: str, obj_data: dict[str, Any]) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.edit_object(doc_name, obj_name, obj_data))

    def delete_object(self, doc_name: str, obj_name: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.delete_object(doc_name, obj_name))

    def insert_part_from_library(self, relative_path: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.insert_part_from_library(relative_path))

    def execute_code(self, code: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.execute_code(code))

    def get_active_screenshot(
        self,
        view_name: str = "Current",
        width: int | None = None,
        height: int | None = None,
        focus_object: str | None = None,
    ) -> str | None:
        try:
            result = cast(
                dict[str, Any],
                self.server.execute_code(
                """
import FreeCAD
import FreeCADGui

if FreeCAD.Gui.ActiveDocument and FreeCAD.Gui.ActiveDocument.ActiveView:
    view_type = type(FreeCAD.Gui.ActiveDocument.ActiveView).__name__

    unsupported_views = ['SpreadsheetGui::SheetView', 'DrawingGui::DrawingView', 'TechDrawGui::MDIViewPage']

    if view_type in unsupported_views or not hasattr(FreeCAD.Gui.ActiveDocument.ActiveView, 'saveImage'):
        print('Current view does not support screenshots')
        False
    else:
        print(f'Current view supports screenshots: {view_type}')
        True
else:
    print('No active view')
    False
"""
                ),
            )

            if not result.get("success", False) or "Current view does not support screenshots" in (
                result.get("data") or {}
            ).get("output", ""):
                logger.info("Screenshot unavailable in current view (likely Spreadsheet or TechDraw view)")
                return None

            return cast(str | None, self.server.get_active_screenshot(view_name, width, height, focus_object))
        except Exception as e:
            logger.error(f"Error getting screenshot: {e}")
            return None

    def get_objects(self, doc_name: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.get_objects(doc_name))

    def get_object(self, doc_name: str, obj_name: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.get_object(doc_name, obj_name))

    def get_parts_list(self) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.get_parts_list())

    def list_documents(self) -> dict[str, Any]:
        return cast(dict[str, Any], self.server.list_documents())

    def disconnect(self) -> None:
        # ServerProxy has no formal disconnect API; clear reference for GC/cleanup.
        self.server = None


_rpc_host = "localhost"
_freecad_connection: FreeCADConnection | None = None


def set_rpc_host(host: str) -> None:
    global _rpc_host, _freecad_connection
    if _rpc_host != host:
        _rpc_host = host
        _freecad_connection = None


def get_freecad_connection() -> FreeCADConnection:
    global _freecad_connection
    if _freecad_connection is None:
        _freecad_connection = FreeCADConnection(host=_rpc_host, port=9875)
        if not _freecad_connection.ping():
            logger.error("Failed to ping FreeCAD")
            _freecad_connection = None
            raise Exception("Failed to connect to FreeCAD. Make sure the FreeCAD addon is running.")
    return _freecad_connection


def reset_freecad_connection() -> None:
    global _freecad_connection
    if _freecad_connection and hasattr(_freecad_connection, "disconnect"):
        _freecad_connection.disconnect()  # pragma: no cover
    _freecad_connection = None
