# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FreeCAD MCP is a Model Context Protocol server that enables AI agents (Claude Desktop, LangChain, Google ADK) to control FreeCAD, an open-source 3D parametric CAD application. It uses a two-process architecture connected via XML-RPC.

## Build & Run

**Package manager:** `uv` (Astral). Python >= 3.12 required.

```bash
# Install dependencies
uv sync

# Run the MCP server directly
uv run freecad-mcp

# Run with options
uv run freecad-mcp --only-text-feedback --host 192.168.1.100
```

No test suite or linter is currently configured.

## Architecture

Three-layer communication model:

```
AI Client (Claude Desktop / LangChain / ADK)
  ↓ MCP protocol (stdio)
MCP Server (src/freecad_mcp/)
  ↓ XML-RPC on port 9875
FreeCAD Addon RPC Server (addon/FreeCADMCP/rpc_server/)
  ↓ GUI task queue
FreeCAD Core
```

### MCP Server (`src/freecad_mcp/`)

Modular FastMCP-based server:

- **`server.py`** — Entrypoint (`main()`). Imports and calls `register_tools()` from each tool module, defines the `asset_creation_strategy` prompt, parses CLI args (`--only-text-feedback`, `--host`).
- **`app.py`** — Creates the `FastMCP` instance (`mcp`) with server lifespan.
- **`connection.py`** — `FreeCADConnection` class wrapping XML-RPC proxy to FreeCAD. Module-level singleton via `get_freecad_connection()` (lazy init, pings on first connect). `set_rpc_host()` / `reset_freecad_connection()` manage lifecycle.
- **`runtime.py`** — Global `only_text_feedback` flag and `server_lifespan` async context manager.
- **`tools/`** — Tool registration split by domain:
  - `object_tools.py` — `create_document`, `create_object`, `edit_object`, `delete_object`, `get_objects`, `get_object`, `list_documents`
  - `misc_tools.py` — `execute_code`, `get_view`, `insert_part_from_library`, `get_parts_list`
  - `sketch_tools.py` — `create_sketch`, `add_sketch_geometry`, `add_sketch_constraint`, `get_sketch_diagnostics`, `recompute_document`
  - `common.py` — `add_screenshot_if_available()` helper shared by all tool modules

Each tool module exports `register_tools(mcp: FastMCP)` which defines tools as closures via `@mcp.tool()`.

### FreeCAD Addon (`addon/FreeCADMCP/`)

Installed into FreeCAD's `Mod/` directory, registers a workbench with toolbar commands.

- **`rpc_server/rpc_server.py`** — `FreeCADRPC` class implements XML-RPC methods. All mutating FreeCAD operations are queued to the GUI thread via `rpc_request_queue`/`rpc_response_queue` pair, polled by `process_gui_tasks()` (500ms QTimer). Read-only methods (`get_objects`, `get_object`, `list_documents`, `get_parts_list`) run directly. Also contains `set_object_property()`, settings persistence, `FilteredXMLRPCServer` (IP/CIDR filtering), and all workbench UI commands.
- **`rpc_server/ops/`** — GUI-thread operation functions extracted from rpc_server:
  - `object_ops.py` — `create_document_gui`, `create_object_gui`, `edit_object_gui`, `delete_object_gui`
  - `sketch_ops.py` — `create_sketch_gui`, `add_sketch_geometry_gui`, `add_sketch_constraint_gui`, `get_sketch_diagnostics_gui`, `recompute_document_gui`
  - `code_ops.py` — `execute_code_gui`
  - `view_ops.py` — `save_active_screenshot`
- **`rpc_server/serialize.py`** — Converts FreeCAD types (Vector, Placement, Rotation, Color, Shape) to JSON-serializable dicts
- **`rpc_server/parts_library.py`** — Discovers `.FCStd` files from the parts_library addon
- Settings persisted to `~/.FreeCAD/freecad_mcp_settings.json`

### Key Patterns

- **RPC response envelope:** All RPC methods return `{"success": bool, "data": Any, "error": str}`. GUI-thread ops return `True` on success or an error string on failure; the RPC method wraps this into the envelope.
- **Adding a new tool:** (1) Add method to `FreeCADConnection` in `connection.py`, (2) create or extend a tool module in `tools/` with a `register_tools(mcp)` function containing `@mcp.tool()` closures, (3) if the operation mutates FreeCAD state, add a `_*_gui` function in `addon/.../ops/` and queue it through the RPC server.
- **Property setting:** `set_object_property()` in `rpc_server.py` handles type coercion (dicts → Placement/Vector, strings → object references, nested dicts → ViewObject properties).
- **Thread safety:** FreeCAD's GUI is single-threaded. All mutating operations must go through the `rpc_request_queue` → `process_gui_tasks()` → `rpc_response_queue` pipeline. Never call FreeCAD GUI APIs directly from the RPC thread.
- **Addon code runs inside FreeCAD's embedded Python** — it can import `FreeCAD`, `FreeCADGui`, `Part`, `Sketcher`, `ObjectsFem` etc. but cannot use external packages not bundled with FreeCAD.
