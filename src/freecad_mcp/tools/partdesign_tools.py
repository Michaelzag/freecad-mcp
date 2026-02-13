import json
import logging
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent

from ..connection import get_freecad_connection


logger = logging.getLogger("FreeCADMCPserver")


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def pad(
        ctx: Context,
        doc_name: str,
        body_name: str,
        sketch_name: str,
        length: float = 10.0,
        type: int = 0,
        reversed: bool = False,
        symmetric: bool = False,
        length2: float = 0.0,
        taper_angle: float = 0.0,
        taper_angle2: float = 0.0,
        name: str | None = None,
    ) -> list[TextContent]:
        """Pad (extrude) a sketch to create a solid feature. This is the primary way to go from 2D sketch to 3D solid.

        The sketch must be a closed profile. The pad extrudes along the sketch's normal direction.

        Args:
            doc_name: The document name.
            body_name: The PartDesign Body to add the pad to.
            sketch_name: The sketch to extrude.
            length: Extrusion distance in mm (default 10).
            type: Pad type — 0=Dimension (use length), 1=ToLast, 2=ToFirst, 3=UpToFace, 4=TwoDimensions, 5=UpToShape.
            reversed: Reverse extrusion direction.
            symmetric: Extrude symmetrically about the sketch plane (Midplane).
            length2: Second length for TwoDimensions mode (type=4).
            taper_angle: Draft/taper angle in degrees.
            taper_angle2: Taper angle for opposite direction.
            name: Optional custom name for the feature.
        """
        freecad = get_freecad_connection()
        try:
            params: dict[str, Any] = {}
            if length != 10.0:
                params["length"] = length
            if type != 0:
                params["type"] = type
            if reversed:
                params["reversed"] = reversed
            if symmetric:
                params["symmetric"] = symmetric
            if length2:
                params["length2"] = length2
            if taper_angle:
                params["taper_angle"] = taper_angle
            if taper_angle2:
                params["taper_angle2"] = taper_angle2
            if name:
                params["name"] = name

            res = freecad.pad(doc_name, body_name, sketch_name, params or None)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [TextContent(type="text", text=f"Failed to pad: {res['error']}")]
        except Exception as e:
            logger.error(f"Failed to pad: {str(e)}")
            return [TextContent(type="text", text=f"Failed to pad: {str(e)}")]

    @mcp.tool()
    def pocket(
        ctx: Context,
        doc_name: str,
        body_name: str,
        sketch_name: str,
        length: float = 10.0,
        type: int = 0,
        reversed: bool = False,
        symmetric: bool = False,
        name: str | None = None,
    ) -> list[TextContent]:
        """Pocket (cut) into a solid using a sketch profile. The sketch must be on a face of the existing solid.

        Args:
            doc_name: The document name.
            body_name: The PartDesign Body to cut from.
            sketch_name: The sketch defining the cut profile.
            length: Cut depth in mm (default 10).
            type: Pocket type — 0=Dimension, 1=ThroughAll, 2=ToFirst, 3=UpToFace, 4=TwoDimensions.
            reversed: Reverse cut direction.
            symmetric: Cut symmetrically about the sketch plane.
            name: Optional custom name for the feature.
        """
        freecad = get_freecad_connection()
        try:
            params: dict[str, Any] = {}
            if length != 10.0:
                params["length"] = length
            if type != 0:
                params["type"] = type
            if reversed:
                params["reversed"] = reversed
            if symmetric:
                params["symmetric"] = symmetric
            if name:
                params["name"] = name

            res = freecad.pocket(doc_name, body_name, sketch_name, params or None)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [TextContent(type="text", text=f"Failed to pocket: {res['error']}")]
        except Exception as e:
            logger.error(f"Failed to pocket: {str(e)}")
            return [TextContent(type="text", text=f"Failed to pocket: {str(e)}")]

    @mcp.tool()
    def revolve(
        ctx: Context,
        doc_name: str,
        body_name: str,
        sketch_name: str,
        axis: str = "V_Axis",
        axis_object: str | None = None,
        angle: float = 360.0,
        type: int = 0,
        reversed: bool = False,
        symmetric: bool = False,
        name: str | None = None,
    ) -> list[TextContent]:
        """Revolve a sketch around an axis to create a solid of revolution (e.g. cylinders, cones, donuts).

        Args:
            doc_name: The document name.
            body_name: The PartDesign Body.
            sketch_name: The sketch to revolve. The sketch profile must not cross the axis.
            axis: Axis sub-element — "V_Axis" or "H_Axis" (sketch axes), "N_Axis" (construction line in sketch).
            axis_object: Object providing the axis. Defaults to the sketch itself. Can be a body origin axis name.
            angle: Revolution angle in degrees (default 360 for full revolution).
            type: Revolution type — 0=Angle, 1=ToLast, 2=ToFirst, 3=UpToFace, 4=TwoAngles.
            reversed: Reverse revolution direction.
            symmetric: Revolve symmetrically about the sketch plane.
            name: Optional custom name for the feature.
        """
        freecad = get_freecad_connection()
        try:
            params: dict[str, Any] = {}
            if axis != "V_Axis":
                params["axis"] = axis
            if axis_object:
                params["axis_object"] = axis_object
            if angle != 360.0:
                params["angle"] = angle
            if type != 0:
                params["type"] = type
            if reversed:
                params["reversed"] = reversed
            if symmetric:
                params["symmetric"] = symmetric
            if name:
                params["name"] = name

            res = freecad.revolve(doc_name, body_name, sketch_name, params or None)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [TextContent(type="text", text=f"Failed to revolve: {res['error']}")]
        except Exception as e:
            logger.error(f"Failed to revolve: {str(e)}")
            return [TextContent(type="text", text=f"Failed to revolve: {str(e)}")]

    @mcp.tool()
    def fillet(
        ctx: Context,
        doc_name: str,
        body_name: str,
        feature_name: str,
        edges: list[str],
        radius: float = 1.0,
        name: str | None = None,
    ) -> list[TextContent]:
        """Fillet (round) edges on an existing feature. Use get_body_features to find edge names.

        Args:
            doc_name: The document name.
            body_name: The PartDesign Body.
            feature_name: The feature whose edges to fillet (e.g. "Pad", "Pocket").
            edges: List of edge sub-element names, e.g. ["Edge1", "Edge3", "Edge5"].
            radius: Fillet radius in mm (default 1).
            name: Optional custom name for the feature.
        """
        freecad = get_freecad_connection()
        try:
            params: dict[str, Any] = {}
            if radius != 1.0:
                params["radius"] = radius
            if name:
                params["name"] = name

            res = freecad.fillet(doc_name, body_name, feature_name, edges, params or None)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [TextContent(type="text", text=f"Failed to fillet: {res['error']}")]
        except Exception as e:
            logger.error(f"Failed to fillet: {str(e)}")
            return [TextContent(type="text", text=f"Failed to fillet: {str(e)}")]

    @mcp.tool()
    def chamfer(
        ctx: Context,
        doc_name: str,
        body_name: str,
        feature_name: str,
        edges: list[str],
        size: float = 1.0,
        name: str | None = None,
    ) -> list[TextContent]:
        """Chamfer (bevel) edges on an existing feature.

        Args:
            doc_name: The document name.
            body_name: The PartDesign Body.
            feature_name: The feature whose edges to chamfer.
            edges: List of edge sub-element names, e.g. ["Edge1", "Edge3"].
            size: Chamfer distance in mm (default 1).
            name: Optional custom name for the feature.
        """
        freecad = get_freecad_connection()
        try:
            params: dict[str, Any] = {}
            if size != 1.0:
                params["size"] = size
            if name:
                params["name"] = name

            res = freecad.chamfer(doc_name, body_name, feature_name, edges, params or None)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [TextContent(type="text", text=f"Failed to chamfer: {res['error']}")]
        except Exception as e:
            logger.error(f"Failed to chamfer: {str(e)}")
            return [TextContent(type="text", text=f"Failed to chamfer: {str(e)}")]

    @mcp.tool()
    def get_body_features(
        ctx: Context,
        doc_name: str,
        body_name: str,
    ) -> list[TextContent]:
        """Get the ordered feature tree for a PartDesign Body.

        Returns every feature in the body with its type, sketch/profile references, key properties
        (length, radius, angle, etc.), and shape info (volume, face/edge counts). This is the
        primary way to understand what an existing model contains.

        Args:
            doc_name: The document name.
            body_name: The PartDesign Body to inspect.
        """
        freecad = get_freecad_connection()
        try:
            res = freecad.get_body_features(doc_name, body_name)
            if res["success"]:
                return [TextContent(type="text", text=json.dumps(res["data"]))]
            return [TextContent(type="text", text=f"Failed to get body features: {res['error']}")]
        except Exception as e:
            logger.error(f"Failed to get body features: {str(e)}")
            return [TextContent(type="text", text=f"Failed to get body features: {str(e)}")]
