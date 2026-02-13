import contextlib
import io
from typing import Any

import FreeCAD


def execute_code_gui(code: str, global_ns: dict[str, Any]) -> tuple[bool, str, str | None]:
    """Execute Python code in GUI thread.

    Returns:
        (success, stdout_output, error_message)
    """
    output_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(code, global_ns)
        FreeCAD.Console.PrintMessage("Python code executed successfully.\n")
        return True, output_buffer.getvalue(), None
    except Exception as e:
        err = f"Error executing Python code: {e}\n"
        FreeCAD.Console.PrintError(err)
        return False, output_buffer.getvalue(), err

