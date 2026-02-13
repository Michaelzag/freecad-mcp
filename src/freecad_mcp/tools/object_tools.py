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
    def create_document(ctx: Context, name: str) -> list[TextContent]:
        """Create a new document in FreeCAD.

        Args:
            name: The name of the document to create.

        Returns:
            A message indicating the success or failure of the document creation.

        Examples:
            If you want to create a document named "MyDocument", you can use the following data.
            ```json
            {
                "name": "MyDocument"
            }
            ```
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.create_document(name)
            if res["success"]:
                return [
                    TextContent(type="text", text=f"Document '{res['data']['document_name']}' created successfully")
                ]
            else:
                return [
                    TextContent(type="text", text=f"Failed to create document: {res['error']}")
                ]
        except Exception as e:
            logger.error(f"Failed to create document: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to create document: {str(e)}")
            ]

    @mcp.tool()
    def create_object(
        ctx: Context,
        doc_name: str,
        obj_type: str,
        obj_name: str,
        analysis_name: str | None = None,
        obj_properties: dict[str, Any] | None = None,
    ) -> list[TextContent | ImageContent]:
        """Create a new object in FreeCAD.
        Object type is starts with "Part::" or "Draft::" or "PartDesign::" or "Fem::".

        Args:
            doc_name: The name of the document to create the object in.
            obj_type: The type of the object to create (e.g. 'Part::Box', 'Part::Cylinder', 'Draft::Circle', 'PartDesign::Body', etc.).
            obj_name: The name of the object to create.
            obj_properties: The properties of the object to create.

        Returns:
            A message indicating the success or failure of the object creation and a screenshot of the object.
        """
        freecad = get_freecad_connection()
        try:
            obj_data = {"Name": obj_name, "Type": obj_type, "Properties": obj_properties or {}, "Analysis": analysis_name}
            res = freecad.create_object(doc_name, obj_data)
            screenshot = freecad.get_active_screenshot()

            if res["success"]:
                response = [
                    TextContent(type="text", text=f"Object '{res['data']['object_name']}' created successfully"),
                ]
                return add_screenshot_if_available(response, screenshot)
            else:
                response = [
                    TextContent(type="text", text=f"Failed to create object: {res['error']}"),
                ]
                return add_screenshot_if_available(response, screenshot)
        except Exception as e:
            logger.error(f"Failed to create object: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to create object: {str(e)}")
            ]

    @mcp.tool()
    def edit_object(
        ctx: Context, doc_name: str, obj_name: str, obj_properties: dict[str, Any]
    ) -> list[TextContent | ImageContent]:
        """Edit an object in FreeCAD.
        This tool is used when the `create_object` tool cannot handle the object creation.

        Args:
            doc_name: The name of the document to edit the object in.
            obj_name: The name of the object to edit.
            obj_properties: The properties of the object to edit.

        Returns:
            A message indicating the success or failure of the object editing and a screenshot of the object.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.edit_object(doc_name, obj_name, {"Properties": obj_properties})
            screenshot = freecad.get_active_screenshot()

            if res["success"]:
                response = [
                    TextContent(type="text", text=f"Object '{res['data']['object_name']}' edited successfully"),
                ]
                return add_screenshot_if_available(response, screenshot)
            else:
                response = [
                    TextContent(type="text", text=f"Failed to edit object: {res['error']}"),
                ]
                return add_screenshot_if_available(response, screenshot)
        except Exception as e:
            logger.error(f"Failed to edit object: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to edit object: {str(e)}")
            ]

    @mcp.tool()
    def delete_object(ctx: Context, doc_name: str, obj_name: str) -> list[TextContent | ImageContent]:
        """Delete an object in FreeCAD.

        Args:
            doc_name: The name of the document to delete the object from.
            obj_name: The name of the object to delete.

        Returns:
            A message indicating the success or failure of the object deletion and a screenshot of the object.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.delete_object(doc_name, obj_name)
            screenshot = freecad.get_active_screenshot()

            if res["success"]:
                response = [
                    TextContent(type="text", text=f"Object '{res['data']['object_name']}' deleted successfully"),
                ]
                return add_screenshot_if_available(response, screenshot)
            else:
                response = [
                    TextContent(type="text", text=f"Failed to delete object: {res['error']}"),
                ]
                return add_screenshot_if_available(response, screenshot)
        except Exception as e:
            logger.error(f"Failed to delete object: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to delete object: {str(e)}")
            ]

    @mcp.tool()
    def get_objects(ctx: Context, doc_name: str) -> list[TextContent | ImageContent]:
        """Get all objects in a document.
        You can use this tool to get the objects in a document to see what you can check or edit.

        Args:
            doc_name: The name of the document to get the objects from.

        Returns:
            A list of objects in the document and a screenshot of the document.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.get_objects(doc_name)
            screenshot = freecad.get_active_screenshot()
            if res["success"]:
                response = [
                    TextContent(type="text", text=json.dumps(res["data"])),
                ]
                return add_screenshot_if_available(response, screenshot)
            else:
                return [
                    TextContent(type="text", text=f"Failed to get objects: {res['error']}")
                ]
        except Exception as e:
            logger.error(f"Failed to get objects: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to get objects: {str(e)}")
            ]

    @mcp.tool()
    def get_object(ctx: Context, doc_name: str, obj_name: str) -> list[TextContent | ImageContent]:
        """Get an object from a document.
        You can use this tool to get the properties of an object to see what you can check or edit.

        Args:
            doc_name: The name of the document to get the object from.
            obj_name: The name of the object to get.

        Returns:
            The object and a screenshot of the object.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.get_object(doc_name, obj_name)
            screenshot = freecad.get_active_screenshot()
            if res["success"]:
                response = [
                    TextContent(type="text", text=json.dumps(res["data"])),
                ]
                return add_screenshot_if_available(response, screenshot)
            else:
                return [
                    TextContent(type="text", text=f"Failed to get object: {res['error']}")
                ]
        except Exception as e:
            logger.error(f"Failed to get object: {str(e)}")
            return [
                TextContent(type="text", text=f"Failed to get object: {str(e)}")
            ]

    @mcp.tool()
    def list_documents(ctx: Context) -> list[TextContent]:
        """Get the list of open documents in FreeCAD.

        Returns:
            A list of document names.
        """
        freecad = get_freecad_connection()
        res = freecad.list_documents()
        return [TextContent(type="text", text=json.dumps(res["data"]))]
