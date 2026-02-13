import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

from .connection import get_freecad_connection, reset_freecad_connection


logger = logging.getLogger("FreeCADMCPserver")

_only_text_feedback = False


def set_only_text_feedback(value: bool) -> None:
    global _only_text_feedback
    _only_text_feedback = value


def get_only_text_feedback() -> bool:
    return _only_text_feedback


@asynccontextmanager
async def server_lifespan(_server) -> AsyncIterator[Dict[str, Any]]:
    try:
        logger.info("FreeCADMCP server starting up")
        try:
            _ = get_freecad_connection()
            logger.info("Successfully connected to FreeCAD on startup")
        except Exception as e:
            logger.warning(f"Could not connect to FreeCAD on startup: {str(e)}")
            logger.warning(
                "Make sure the FreeCAD addon is running before using FreeCAD resources or tools"
            )
        yield {}
    finally:
        logger.info("Disconnecting from FreeCAD on shutdown")
        reset_freecad_connection()
        logger.info("FreeCADMCP server shut down")

