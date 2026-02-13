from mcp.types import ImageContent, TextContent

from ..runtime import get_only_text_feedback


def add_screenshot_if_available(response, screenshot):
    """Safely add screenshot to response only if it's available."""
    if screenshot is not None and not get_only_text_feedback():
        response.append(ImageContent(type="image", data=screenshot, mimeType="image/png"))
    elif not get_only_text_feedback():
        response.append(
            TextContent(
                type="text",
                text=(
                    "Note: Visual preview is unavailable in the current view type "
                    "(such as TechDraw or Spreadsheet). Switch to a 3D view to see visual feedback."
                ),
            )
        )
    return response

