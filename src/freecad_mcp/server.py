import logging

from .app import mcp
from .connection import set_rpc_host
from .tools.misc_tools import register_tools as register_misc_tools
from .tools.object_tools import register_tools as register_object_tools
from .tools.partdesign_tools import register_tools as register_partdesign_tools
from .tools.sketch_tools import register_tools as register_sketch_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FreeCADMCPserver")


register_object_tools(mcp)
register_misc_tools(mcp)
register_sketch_tools(mcp)
register_partdesign_tools(mcp)


@mcp.prompt()
def asset_creation_strategy() -> str:
    return """
PartDesign Workflow for FreeCAD MCP

Follow the standard PartDesign iterative loop to create parts:

1. SETUP:
   - create_document() to make a new document.
   - create_object() with type "PartDesign::Body" to create a Body (the container for your part).

2. SKETCH (2D):
   - create_sketch() on a plane ("XY", "XZ", "YZ") or on a face of an existing feature
     (use support={"object": "Pad", "face": "Face6"} for face attachment).
   - add_sketch_geometry() to draw lines, circles, arcs, polylines.
   - add_sketch_constraint() to constrain the sketch (Coincident, Horizontal, Vertical, Distance, Radius, etc.).
   - Use get_sketch_diagnostics() to verify 0 degrees of freedom (fully constrained).

3. FEATURE (2D → 3D):
   - pad() to extrude a sketch into a solid (first feature creates the base shape).
   - pocket() to cut into an existing solid using a sketch profile.
   - revolve() to create solids of revolution.

4. REPEAT:
   - Create a new sketch on a face of the result (e.g. support={"object": "Pad", "face": "Face6"}).
   - Add geometry and constraints.
   - Apply another feature (pad, pocket, revolve).

5. DRESS-UP:
   - fillet() to round edges.
   - chamfer() to bevel edges.

6. INSPECT:
   - get_body_features() to see the full feature tree of a Body.
   - get_sketch_info() to read a sketch's geometry and constraints.
   - get_sketch_diagnostics() to check degrees of freedom and constraint conflicts.
   - get_object() / get_objects() for detailed object properties.

Use execute_code() as an escape hatch for operations not covered by the tools above.
"""


def _validate_host(value: str) -> str:
    """Validate that *value* is a valid IP address or hostname.

    Used as the ``type`` callback for the ``--host`` argparse argument.
    Raises ``argparse.ArgumentTypeError`` on invalid input.
    """
    import argparse

    import validators

    if validators.ipv4(value) or validators.ipv6(value) or validators.hostname(value):
        return value
    raise argparse.ArgumentTypeError(
        f"Invalid host: '{value}'. Must be a valid IP address or hostname."
    )


def main():
    """Run the MCP server"""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=_validate_host, default="localhost", help="Host address of the FreeCAD RPC server to connect to (default: localhost)")
    args = parser.parse_args()

    set_rpc_host(args.host)
    logger.info(f"Connecting to FreeCAD RPC server at: {args.host}")
    mcp.run()
