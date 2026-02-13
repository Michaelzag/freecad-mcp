from mcp.server.fastmcp import FastMCP

from .runtime import server_lifespan


mcp = FastMCP(
    "FreeCADMCP",
    instructions="FreeCAD integration through the Model Context Protocol",
    lifespan=server_lifespan,
)

