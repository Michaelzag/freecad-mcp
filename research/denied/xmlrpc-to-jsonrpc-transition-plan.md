# XML-RPC → JSON-RPC Transition Plan (Fork-First)

## Context

This fork is intentionally optimized for forward progress, not legacy compatibility. The goal is to replace XML-RPC transport with a modern JSON-RPC stack and add strict typed contracts for stability.

Current XML-RPC usage is explicit in:

- client import and proxy creation in [`src/freecad_mcp/connection.py`](../src/freecad_mcp/connection.py:2) and [`FreeCADConnection.__init__()`](../src/freecad_mcp/connection.py:10)
- server import and implementation in [`addon/FreeCADMCP/rpc_server/rpc_server.py`](../addon/FreeCADMCP/rpc_server/rpc_server.py:15) and [`FilteredXMLRPCServer`](../addon/FreeCADMCP/rpc_server/rpc_server.py:77)

## Why change

### Main benefits

1. **Standardized error envelope**
   - JSON-RPC gives stable `result`/`error` semantics instead of ad hoc response dicts.
2. **Cleaner protocol evolution**
   - versioned request/response models are easier to maintain.
3. **Batch and notification support**
   - useful for grouped operations.
4. **Better observability**
   - JSON payloads are easier to log, diff, and replay.

### What does *not* magically improve

- FreeCAD compute-heavy operations (recompute/meshing) still dominate runtime.
- GUI-thread constraints still require queue-based scheduling via [`process_gui_tasks()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:149).

## Foundation choice

## 1) Protocol

- Adopt **JSON-RPC 2.0** as the only RPC protocol.

## 2) Validation

- Add **Pydantic models** at transport boundaries immediately.
- Validate incoming requests before execution and validate outgoing responses before sending.

## 3) Libraries (recommended shortlist)

Use an existing library, not a custom protocol implementation.

- **`jsonrpcserver` / `jsonrpcclient`**
  - straightforward JSON-RPC processing; good fit for simple request/response architecture.
- **`python-lsp-jsonrpc`**
  - battle-tested framing/JSON-RPC core from LSP ecosystem; stronger if stream-based framing becomes desirable.

If minimal complexity is preferred, start with `jsonrpcserver` + an HTTP transport.

## Target architecture

Keep the same high-level split:

- MCP-facing orchestration in [`src/freecad_mcp/server.py`](../src/freecad_mcp/server.py:1)
- FreeCAD execution in [`addon/FreeCADMCP/rpc_server/rpc_server.py`](../addon/FreeCADMCP/rpc_server/rpc_server.py:1)

Replace only transport and contract boundaries.

### Proposed layers

1. **Contract layer (Pydantic)**
   - request/response/error models for every RPC method.
2. **Transport adapter layer**
   - one client adapter in MCP process.
   - one server adapter in FreeCAD addon.
3. **Execution layer (existing logic)**
   - retain queue and FreeCAD operations (`_create_object_gui`, `_edit_object_gui`, etc.).

## Migration plan (no backward compatibility required)

### Phase 0 — Freeze current behavior

- Snapshot existing RPC method behavior from [`FreeCADRPC`](../addon/FreeCADMCP/rpc_server/rpc_server.py:244).
- Record current response shapes for:
  - `create_document`, `create_object`, `edit_object`, `delete_object`, `execute_code`, `get_objects`, `get_object`, `insert_part_from_library`, `list_documents`, `get_parts_list`, `get_active_screenshot`.

### Phase 1 — Add typed models first

- Add Pydantic dependency to [`pyproject.toml`](../pyproject.toml:11).
- Define strict models for each RPC request/response and unified error model.
- Validate data before entering execution methods.

### Phase 2 — Implement JSON-RPC server in addon

- Replace [`SimpleXMLRPCServer`](../addon/FreeCADMCP/rpc_server/rpc_server.py:15) usage.
- Keep IP filtering logic currently in [`verify_request()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:84) by reusing `allowed_ips` checks in new server request path.
- Keep GUI queue scheduling unchanged.

### Phase 3 — Implement JSON-RPC client in MCP process

- Replace [`xmlrpc.client.ServerProxy`](../src/freecad_mcp/connection.py:11) with JSON-RPC client adapter.
- Keep existing MCP tool method signatures initially; swap internals only.

### Phase 4 — Remove XML-RPC code

- Delete XML-RPC imports and server/client code paths.
- Remove XML-specific helpers and dead config.

## Contract guidelines

### Request/response shape

- Use explicit request models (no loose `dict[str, Any]` in public boundary).
- Use explicit result models with `success`, `data`, and typed `error` object.
- Preserve stable method names and predictable response schemas.

### Error model

- `code` (stable machine code)
- `message` (human readable)
- `details` (typed optional context)

### Units and geometry references

- encode dimensions as strings with units (e.g., `"25 mm"`).
- keep stable object/geometry handles where possible.

## Risk register

1. **FreeCAD embedded Python environment constraints**
   - ensure chosen JSON-RPC + Pydantic versions install cleanly in your FreeCAD runtime.
2. **Qt/event-loop interaction**
   - avoid async model conflicts; maintain queue-driven execution flow.
3. **Large payload behavior**
   - screenshots may require payload limits/compression strategy.

## Test strategy

### Unit

- model validation tests for every request/response schema.
- serialization/deserialization round-trip tests.

### Integration

- start server from FreeCAD addon and run full RPC method smoke tests.
- verify parity for method results relative to baseline snapshot.

### Stability

- repeated create/edit/delete loops.
- repeated screenshot calls from supported and unsupported views.
- long-running `execute_code` workload stability.

## Done criteria

- XML-RPC removed from both:
  - [`src/freecad_mcp/server.py`](../src/freecad_mcp/server.py:1)
  - [`addon/FreeCADMCP/rpc_server/rpc_server.py`](../addon/FreeCADMCP/rpc_server/rpc_server.py:1)
- All RPC boundaries validated by Pydantic.
- Integration suite passes against JSON-RPC server/client only.
- Manual FreeCAD workflow smoke tests pass end-to-end.

## Short recommendation

For this fork: do **Pydantic + JSON-RPC together** in one migration project, but keep execution logic and GUI queue architecture intact. This gives you a stronger foundation without rewriting core CAD behavior.
