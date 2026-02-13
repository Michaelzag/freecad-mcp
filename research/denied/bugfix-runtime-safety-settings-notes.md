# Branch Notes: `bugfix/runtime-safety-settings`

## Context

This branch records preparatory runtime-safety work for the FreeCAD addon RPC layer in [`addon/FreeCADMCP/rpc_server/rpc_server.py`](../addon/FreeCADMCP/rpc_server/rpc_server.py:1).

The goal was to leave **inline implementation hooks** for a future settings-menu GUI merge, without changing runtime behavior yet.

---

## Problem Findings (Error / Risk Analysis)

### 1) Unbounded execution path for user Python

The current execution path in [`FreeCADRPC.execute_code()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:292) runs arbitrary code via `exec`, with no runtime timeout or output-size limits.

Potential impact:

- Extremely heavy geometry scripts (e.g., high-complexity spline/constraint workloads) may overconsume CPU/RAM.
- Verbose scripts can grow captured output significantly.

### 2) Blocking queue waits with no timeout policy

Multiple RPC methods block on queue responses (e.g. `rpc_response_queue.get()` in methods around [`FreeCADRPC`](../addon/FreeCADMCP/rpc_server/rpc_server.py:244)).

Potential impact:

- Callers can hang indefinitely if a response is delayed or never arrives.

### 3) Heavy GUI task processing can hurt responsiveness

GUI tasks are processed in [`process_gui_tasks()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:149) without an explicit runtime-safety policy yet.

Potential impact:

- Expensive task bursts can degrade UI responsiveness.

### 4) Missing explicit integration points for future settings UI

A settings persistence mechanism already exists (`_DEFAULT_SETTINGS`, `load_settings`, `save_settings`), but runtime-safety knobs were not yet documented in-place for the upcoming GUI settings merge.

---

## What Was Added on This Branch

Only inline comments and hook annotations were added (no functional behavior changes).

### A) Settings-key placeholders

Added comment placeholders near [`_DEFAULT_SETTINGS`](../addon/FreeCADMCP/rpc_server/rpc_server.py:38) for future keys such as:

- `rpc_response_timeout_seconds`
- `execute_code_timeout_seconds`
- `execute_code_max_output_bytes`
- `complexity_soft_limit_enabled`

### B) Compatibility hook note for settings evolution

Added migration/compatibility guidance near [`load_settings()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:50), where default keys are backfilled.

### C) Queue-timeout policy hook

Added note near queue declarations around [`rpc_response_queue`](../addon/FreeCADMCP/rpc_server/rpc_server.py:146) to centralize timeout behavior via a shared helper in future implementation.

### D) GUI-task safety hook

Added note in [`process_gui_tasks()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:149) suggesting try/except wrapping and per-tick budget strategy for heavy workloads.

### E) RPC class-level blocking-wait hook

Added note in [`FreeCADRPC`](../addon/FreeCADMCP/rpc_server/rpc_server.py:244) that current methods block on queue waits and should eventually use a shared timeout policy.

### F) Execution safety hook in code execution path

Added notes in [`FreeCADRPC.execute_code()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:292) documenting where timeout/output-cap/complexity warnings should be wired.

### G) Toolbar/settings command integration hook

Added note near command registration after [`FreeCADGui.addCommand("Configure_Allowed_IPs", ...)`](../addon/FreeCADMCP/rpc_server/rpc_server.py:717) identifying a good insertion point for a future Runtime Safety settings dialog.

---

## Validation Performed

- Syntax check on addon module passed (`python -m py_compile` on [`addon/FreeCADMCP/rpc_server/rpc_server.py`](../addon/FreeCADMCP/rpc_server/rpc_server.py:1)).
- CLI entrypoint check passed (`freecad-mcp --help` via [`main()`](../src/freecad_mcp/server.py:72)).
- `pytest` was not available in this repository environment at time of validation.

---

## Scope Clarification

This branch does **not** yet implement runtime-enforced limits. It only documents exact code locations to implement them once the settings-menu GUI work is merged.
