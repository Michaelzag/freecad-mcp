import json
import logging
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ImageContent, TextContent

from ..connection import get_freecad_connection
from .common import add_screenshot_if_available


logger = logging.getLogger("FreeCADMCPserver")


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def create_sketch(
        ctx: Context,
        doc_name: str,
        sketch_name: str,
        support: str | dict[str, Any] = "XY",
        placement: dict[str, Any] | None = None,
    ) -> list[TextContent | ImageContent]:
        """Create a sketch in a document.

        Args:
            doc_name: The document containing the sketch.
            sketch_name: The sketch object name to create.
            support: Sketch support plane/object reference (e.g. "XY", "XZ", "YZ").
            placement: Optional placement mapping for initial position/rotation.

        Returns:
            A success/failure message with optional screenshot.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.create_sketch(doc_name, sketch_name, support, placement)
            screenshot = freecad.get_active_screenshot()
            if res["success"]:
                response = [
                    TextContent(type="text", text=json.dumps(res["data"])),
                ]
                return add_screenshot_if_available(response, screenshot)
            response = [
                TextContent(type="text", text=f"Failed to create sketch: {res['error']}"),
            ]
            return add_screenshot_if_available(response, screenshot)
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
    ) -> list[TextContent | ImageContent]:
        """Add geometry to an existing sketch."""
        freecad = get_freecad_connection()
        try:
            res = freecad.add_sketch_geometry(doc_name, sketch_name, geometry)
            screenshot = freecad.get_active_screenshot()
            if res["success"]:
                response = [
                    TextContent(type="text", text=json.dumps(res["data"])),
                ]
                return add_screenshot_if_available(response, screenshot)
            response = [
                TextContent(type="text", text=f"Failed to add sketch geometry: {res['error']}"),
            ]
            return add_screenshot_if_available(response, screenshot)
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
    ) -> list[TextContent | ImageContent]:
        """Add a sketch constraint to an existing sketch."""
        freecad = get_freecad_connection()
        try:
            res = freecad.add_sketch_constraint(doc_name, sketch_name, constraint)
            screenshot = freecad.get_active_screenshot()
            if res["success"]:
                response = [
                    TextContent(type="text", text=json.dumps(res["data"])),
                ]
                return add_screenshot_if_available(response, screenshot)
            response = [
                TextContent(type="text", text=f"Failed to add sketch constraint: {res['error']}"),
            ]
            return add_screenshot_if_available(response, screenshot)
        except Exception as e:
            logger.error(f"Failed to add sketch constraint: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to add sketch constraint: {str(e)}")
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
    ) -> list[TextContent | ImageContent]:
        """Recompute a FreeCAD document and return status."""
        freecad = get_freecad_connection()
        try:
            res = freecad.recompute_document(doc_name)
            screenshot = freecad.get_active_screenshot()
            if res["success"]:
                response = [
                    TextContent(type="text", text=json.dumps(res["data"])),
                ]
                return add_screenshot_if_available(response, screenshot)
            response = [
                TextContent(type="text", text=f"Failed to recompute document: {res['error']}"),
            ]
            return add_screenshot_if_available(response, screenshot)
        except Exception as e:
            logger.error(f"Failed to recompute document: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to recompute document: {str(e)}")
            ]

