import json
import logging
from typing import Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ImageContent, TextContent

from ..connection import get_freecad_connection


logger = logging.getLogger("FreeCADMCPserver")


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def execute_code(ctx: Context, code: str) -> list[TextContent]:
        """Execute arbitrary Python code in FreeCAD.

        Args:
            code: The Python code to execute.

        Returns:
            A message indicating the success or failure of the code execution and its output.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.execute_code(code)

            if res["success"]:
                return [
                    TextContent(type="text", text=f"Code executed successfully.\nOutput: {res['data']['output']}"),
                ]
            else:
                return [
                    TextContent(type="text", text=f"Failed to execute code: {res['error']}"),
                ]
        except Exception as e:
            logger.error(f"Failed to execute code: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to execute code: {str(e)}")
            ]

    @mcp.tool()
    def get_view(
        ctx: Context,
        view_name: Literal["Current", "Isometric", "Front", "Top", "Right", "Back", "Left", "Bottom", "Dimetric", "Trimetric"] = "Current",
        width: int | None = None,
        height: int | None = None,
        focus_object: str | None = None,
    ) -> list[ImageContent | TextContent]:
        """Get a screenshot of the active view.

        Args:
            view_name: The camera angle. Use "Current" (default) to capture without changing the user's view.
            width: Image width in pixels (default 800).
            height: Image height in pixels (default 600).
            focus_object: Optional object name to focus/zoom on.
        """
        freecad = get_freecad_connection()
        screenshot = freecad.get_active_screenshot(view_name, width, height, focus_object)

        if screenshot is not None:
            return [ImageContent(type="image", data=screenshot, mimeType="image/png")]
        else:
            return [TextContent(type="text", text="Cannot get screenshot in the current view type (such as TechDraw or Spreadsheet)")]

    @mcp.tool()
    def insert_part_from_library(ctx: Context, relative_path: str) -> list[TextContent]:
        """Insert a part from the parts library addon.

        Args:
            relative_path: The relative path of the part to insert.

        Returns:
            A message indicating the success or failure of the part insertion.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.insert_part_from_library(relative_path)

            if res["success"]:
                return [
                    TextContent(type="text", text="Part inserted from library successfully"),
                ]
            else:
                return [
                    TextContent(type="text", text=f"Failed to insert part from library: {res['error']}"),
                ]
        except Exception as e:
            logger.error(f"Failed to insert part from library: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to insert part from library: {str(e)}")
            ]

    @mcp.tool()
    def get_parts_list(ctx: Context) -> list[TextContent]:
        """Get the list of parts in the parts library addon."""
        freecad = get_freecad_connection()
        res = freecad.get_parts_list()
        if res["success"] and res["data"]:
            return [
                TextContent(type="text", text=json.dumps(res["data"]))
            ]
        else:
            return [
                TextContent(type="text", text="No parts found in the parts library. You must add parts_library addon.")
            ]
