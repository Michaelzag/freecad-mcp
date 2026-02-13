import json
import logging
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent

from ..connection import get_freecad_connection


logger = logging.getLogger("FreeCADMCPserver")


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def create_sketch(
        ctx: Context,
        doc_name: str,
        sketch_name: str,
        support: str | dict[str, Any] = "XY",
        placement: dict[str, Any] | None = None,
    ) -> list[TextContent]:
        """Create a sketch in a document.

        Sketches are 2D drawing planes where you add geometry (lines, circles, arcs) and
        constraints before applying a 3D feature (pad, pocket, revolve).

        Args:
            doc_name: The document containing the sketch.
            sketch_name: The sketch object name to create.
            support: Where to place the sketch. Options:
                - Plane string: "XY", "XZ", or "YZ" (origin planes, for first sketch).
                - Face reference dict: {"object": "Pad", "face": "Face6"} (to sketch on an existing feature's face).
                - Object name string: "MyDatumPlane" (to sketch on a datum plane).
            placement: Optional placement mapping for initial position/rotation.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.create_sketch(doc_name, sketch_name, support, placement)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [
                TextContent(type="text", text=f"Failed to create sketch: {res['error']}")
            ]
        except Exception as e:
            logger.error(f"Failed to create sketch: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to create sketch: {str(e)}")
            ]

    @mcp.tool()
    def add_sketch_geometry(
        ctx: Context,
        doc_name: str,
        sketch_name: str,
        geometry: dict[str, Any],
    ) -> list[TextContent]:
        """Add geometry to an existing sketch."""
        freecad = get_freecad_connection()
        try:
            res = freecad.add_sketch_geometry(doc_name, sketch_name, geometry)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [
                TextContent(type="text", text=f"Failed to add sketch geometry: {res['error']}")
            ]
        except Exception as e:
            logger.error(f"Failed to add sketch geometry: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to add sketch geometry: {str(e)}")
            ]

    @mcp.tool()
    def add_sketch_constraint(
        ctx: Context,
        doc_name: str,
        sketch_name: str,
        constraint: dict[str, Any],
    ) -> list[TextContent]:
        """Add a sketch constraint to an existing sketch."""
        freecad = get_freecad_connection()
        try:
            res = freecad.add_sketch_constraint(doc_name, sketch_name, constraint)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [
                TextContent(type="text", text=f"Failed to add sketch constraint: {res['error']}")
            ]
        except Exception as e:
            logger.error(f"Failed to add sketch constraint: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to add sketch constraint: {str(e)}")
            ]

    @mcp.tool()
    def get_sketch_info(
        ctx: Context,
        doc_name: str,
        sketch_name: str,
    ) -> list[TextContent]:
        """Get all geometry and constraints from a sketch as structured data.

        Returns the full sketch content including every geometry element (lines, circles, arcs, points,
        bsplines, ellipses) with coordinates, and every constraint with type, references, and values.
        This is the primary way to understand what a sketch contains.

        Args:
            doc_name: The document containing the sketch.
            sketch_name: The sketch object name.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.get_sketch_info(doc_name, sketch_name)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [
                TextContent(type="text", text=f"Failed to get sketch info: {res['error']}")
            ]
        except Exception as e:
            logger.error(f"Failed to get sketch info: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to get sketch info: {str(e)}")
            ]

    @mcp.tool()
    def get_sketch_diagnostics(
        ctx: Context,
        doc_name: str,
        sketch_name: str,
    ) -> list[TextContent]:
        """Get sketch diagnostics such as DoF and conflicts."""
        freecad = get_freecad_connection()
        try:
            res = freecad.get_sketch_diagnostics(doc_name, sketch_name)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [
                TextContent(type="text", text=f"Failed to get sketch diagnostics: {res['error']}")
            ]
        except Exception as e:
            logger.error(f"Failed to get sketch diagnostics: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to get sketch diagnostics: {str(e)}")
            ]

    @mcp.tool()
    def recompute_document(
        ctx: Context,
        doc_name: str,
    ) -> list[TextContent]:
        """Recompute a FreeCAD document and return status."""
        freecad = get_freecad_connection()
        try:
            res = freecad.recompute_document(doc_name)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [
                TextContent(type="text", text=f"Failed to recompute document: {res['error']}")
            ]
        except Exception as e:
            logger.error(f"Failed to recompute document: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to recompute document: {str(e)}")
            ]
