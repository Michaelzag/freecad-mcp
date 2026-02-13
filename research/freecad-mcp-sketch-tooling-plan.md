# FreeCAD MCP Sketch Expansion Plan (Two Parts)

## Scope and intent

This plan is intentionally split into two parts:

1. **Modularization first** (reduce risk and file bloat before adding many tools).
2. **Full sketch/constraint endpoint suite** (well-defined contracts and implementation mapping).

Primary evidence sources:

- MCP bootstrap/registration composition in [src/freecad_mcp/server.py](../src/freecad_mcp/server.py:19)
- MCP tool definitions in [src/freecad_mcp/tools/object_tools.py](../src/freecad_mcp/tools/object_tools.py:15) and [src/freecad_mcp/tools/misc_tools.py](../src/freecad_mcp/tools/misc_tools.py:15)
- App/lifecycle/connection split in [src/freecad_mcp/app.py](../src/freecad_mcp/app.py:6), [src/freecad_mcp/runtime.py](../src/freecad_mcp/runtime.py:23), and [src/freecad_mcp/connection.py](../src/freecad_mcp/connection.py:9)
- RPC facade and GUI queue model in [addon/FreeCADMCP/rpc_server/rpc_server.py](../addon/FreeCADMCP/rpc_server/rpc_server.py:244) and [addon/FreeCADMCP/rpc_server/rpc_server.py](../addon/FreeCADMCP/rpc_server/rpc_server.py:144)
- Prior usability analysis and recommended phase-1 tool set in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:133)
- FreeCAD Sketcher tutorial and scripting references:
  - https://wiki.freecad.org/Basic_Sketcher_Tutorial
  - https://wiki.freecad.org/Sketcher_scripting

---

## Part 1 — Modularization Baseline (completed)

## Why this is first

- Historically, the MCP-side file mixed lifecycle, connection, tool definitions, and prompts; after Part 1 it is now a thin bootstrap/registration layer in [src/freecad_mcp/server.py](../src/freecad_mcp/server.py:1).
- The addon RPC file still acts as a broad facade for settings UI, server process, queue wiring, and operation dispatch in [addon/FreeCADMCP/rpc_server/rpc_server.py](../addon/FreeCADMCP/rpc_server/rpc_server.py:1).
- Adding 20+ sketch endpoints directly into those files will increase coupling and regression risk.

## Target modular structure

### MCP side (Python package)

- Keep [src/freecad_mcp/server.py](../src/freecad_mcp/server.py:1) as bootstrap and registration composition only.
- Connection/lifecycle are now split into:
  - `src/freecad_mcp/connection.py`
  - `src/freecad_mcp/runtime.py`
  - `src/freecad_mcp/app.py`
- Tool families currently implemented:
  - `src/freecad_mcp/tools/object_tools.py`
  - `src/freecad_mcp/tools/misc_tools.py` (contains view/code/parts tools)
  - `src/freecad_mcp/tools/common.py` (shared screenshot response helper)
- Planned additions for sketch expansion:
  - `src/freecad_mcp/tools/sketch_tools.py` (new)
  - `src/freecad_mcp/tools/feature_tools.py` (new)
  - `src/freecad_mcp/tools/diagnostic_tools.py` (new)

### Addon RPC side

- Keep [addon/FreeCADMCP/rpc_server/rpc_server.py](../addon/FreeCADMCP/rpc_server/rpc_server.py:1) as RPC facade, queue wiring, and command registration.
- Operation logic currently extracted into:
  - `addon/FreeCADMCP/rpc_server/ops/object_ops.py`
  - `addon/FreeCADMCP/rpc_server/ops/view_ops.py`
  - `addon/FreeCADMCP/rpc_server/ops/code_ops.py`
- Planned additions for sketch expansion:
  - `addon/FreeCADMCP/rpc_server/ops/sketch_ops.py` (new)
  - `addon/FreeCADMCP/rpc_server/ops/feature_ops.py` (new)
  - `addon/FreeCADMCP/rpc_server/ops/diagnostic_ops.py` (new)

## Step-by-step execution

1. **Stabilize interfaces**
   - Define typed request/response dictionaries for current tools before moving logic.
   - Preserve current output compatibility from [src/freecad_mcp/tools/object_tools.py](../src/freecad_mcp/tools/object_tools.py:17) and [src/freecad_mcp/tools/misc_tools.py](../src/freecad_mcp/tools/misc_tools.py:17).

2. **Extract existing tools with no behavior changes**
   - Move create/edit/delete/view/list/code tooling in thin slices.
   - Keep registration names unchanged.

3. **Refactor addon into operation modules**
   - Pull internal methods from [addon/FreeCADMCP/rpc_server/rpc_server.py](../addon/FreeCADMCP/rpc_server/rpc_server.py:385) into ops modules.
   - Keep queue and GUI-thread execution path unchanged per [addon/FreeCADMCP/rpc_server/rpc_server.py](../addon/FreeCADMCP/rpc_server/rpc_server.py:144).

4. **Add test harness and golden responses**
   - Snapshot response shapes for existing tools to prevent breakage.

5. **Only then add sketch endpoints**
   - Implement new endpoints in isolated `sketch_tools.py` + `sketch_ops.py` modules.

## Acceptance criteria for Part 1

- No user-visible behavior changes for current MCP tools registered from [src/freecad_mcp/tools/object_tools.py](../src/freecad_mcp/tools/object_tools.py:15) and [src/freecad_mcp/tools/misc_tools.py](../src/freecad_mcp/tools/misc_tools.py:15).
- Existing tool names remain stable from [src/freecad_mcp/tools/object_tools.py](../src/freecad_mcp/tools/object_tools.py:17) and [src/freecad_mcp/tools/misc_tools.py](../src/freecad_mcp/tools/misc_tools.py:17).
- New code paths keep GUI-thread safety model in [addon/FreeCADMCP/rpc_server/rpc_server.py](../addon/FreeCADMCP/rpc_server/rpc_server.py:144).

---

## Part 2 — Sketch/Constraint Endpoint Plan (full endpoint suite)

## Design rules used for all endpoints

1. **Sketch-first modeling workflow**: construction geometry, real geometry, geometric constraints, then dimensional constraints (per Basic Sketcher tutorial).
2. **Typed and deterministic contracts**: stable geometry IDs and constraint IDs in every mutating response.
3. **Units as strings** (`"mm"`, `"deg"`) to align with `App.Units.Quantity(...)` conventions in Sketcher scripting docs.
4. **Every mutating endpoint returns diagnostics** (DoF, conflicts, redundancies, open profiles).

## Endpoint conventions

- Every endpoint returns:
  - `success: bool`
  - `data: { ... } | null`
  - `error: str | null`
  - `diagnostics: { dof, conflicting_constraints, redundant_constraints, open_profiles }`
- Every sketch mutation accepts:
  - `doc_name`
  - `sketch_name`
  - `recompute: bool = true`

---

## A) Lifecycle and support endpoints

### 1) `create_sketch`
- **Purpose:** Create sketch on plane/support and return sketch handle.
- **Input:** `doc_name`, `sketch_name`, `support` (XY/XZ/YZ or attachment reference), optional placement.
- **Implementation basis:** sketch object creation pattern from Sketcher scripting docs and recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:137).

### 2) `get_sketch`
- **Purpose:** Return geometry list, constraint list, external geometry list, mapping metadata.
- **Input:** `doc_name`, `sketch_name`.
- **Implementation basis:** extends object introspection pattern in [src/freecad_mcp/tools/object_tools.py](../src/freecad_mcp/tools/object_tools.py:163) and [src/freecad_mcp/tools/object_tools.py](../src/freecad_mcp/tools/object_tools.py:193).

### 3) `delete_sketch`
- **Purpose:** Remove sketch object safely.
- **Input:** `doc_name`, `sketch_name`.
- **Implementation basis:** aligns with delete flow in [src/freecad_mcp/tools/object_tools.py](../src/freecad_mcp/tools/object_tools.py:131).

### 4) `map_sketch_support`
- **Purpose:** Attach/reorient sketch to support face/datums.
- **Input:** `doc_name`, `sketch_name`, `support_ref`, attachment params.
- **Implementation basis:** Sketcher workflow requirement and phase-3 datum guidance in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:155).

---

## B) Geometry creation endpoints

### 5) `add_sketch_geometry`
- **Purpose:** Generic typed geometry add API.
- **Input:** `geometry` union (`line`, `arc_center`, `circle`, `bspline`, `polyline`, `regular_polygon`, `point`).
- **Output:** created geometry IDs.
- **Implementation basis:** phase-1 recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:138) and `SketchObject.addGeometry(...)` from Sketcher scripting docs.

### 6) `add_sketch_geometry_batch`
- **Purpose:** Add multiple geometry items atomically.
- **Input:** ordered list of geometry objects.
- **Implementation basis:** batch recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:149).

### 7) `set_construction_geometry`
- **Purpose:** Toggle geometry between construction and real.
- **Input:** geometry refs, boolean `construction`.
- **Implementation basis:** construction-vs-real modeling method from Basic Sketcher tutorial.

### 8) `update_sketch_geometry`
- **Purpose:** Edit geometry parameters (points, radius, poles/weights where applicable).
- **Input:** geometry ref + patch payload.

### 9) `delete_sketch_geometry`
- **Purpose:** Remove one or many geometry elements and reindex map safely.
- **Input:** geometry refs.

---

## C) Constraint endpoints

### 10) `add_sketch_constraint`
- **Purpose:** Generic typed constraint add.
- **Input:** `constraint: { type, refs, value? }`.
- **Implementation basis:** phase-1 recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:139), plus `Sketcher.Constraint(...)` usage from Sketcher scripting docs.

### 11) `add_geometric_constraint`
- **Purpose:** Convenience endpoint for geometric constraints.
- **Supported:** Coincident, PointOnObject, Horizontal, Vertical, Parallel, Perpendicular, Tangent, Equal, Symmetric, Block.
- **Implementation basis:** documented type list from Sketcher scripting docs.

### 12) `add_dimensional_constraint`
- **Purpose:** Convenience endpoint for dimensional constraints.
- **Supported:** DistanceX, DistanceY, Distance, Radius, Diameter, Angle, AngleViaPoint.
- **Input value:** unit-bearing string (e.g., `"37 mm"`, `"72 deg"`).
- **Implementation basis:** dimensional constraint + quantity usage from Sketcher scripting docs.

### 13) `add_constraints_batch`
- **Purpose:** Apply multiple constraints in single solve transaction.
- **Implementation basis:** batch reliability recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:149).

### 14) `update_constraint`
- **Purpose:** Change value/active/driving state for constraint by stable ID.

### 15) `delete_constraint`
- **Purpose:** Remove a constraint by stable ID.

### 16) `toggle_constraint_active`
- **Purpose:** Enable/disable constraint for diagnostics and what-if solving.

---

## D) Expression and reference endpoints

### 17) `set_sketch_expression`
- **Purpose:** Bind expression to constraint or geometry property.
- **Input:** `target`, `expression`.
- **Implementation basis:** phase-1 recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:140).

### 18) `project_external_geometry`
- **Purpose:** Project external edges/vertices into sketch.
- **Input:** refs to external objects/sub-elements.
- **Implementation basis:** phase-1 recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:141).

### 19) `list_external_geometry`
- **Purpose:** Return projected geometry map and stable reference IDs.

---

## E) Diagnostics and solve endpoints

### 20) `get_sketch_diagnostics`
- **Purpose:** Return DoF, conflict/redundancy info, open profile details.
- **Implementation basis:** phase-1 recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:143).

### 21) `validate_sketch`
- **Purpose:** Run sketch validity checks and suggest repairs.
- **Implementation basis:** Sketcher validation workflow and phase-2 error typing guidance in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:151).

### 22) `solve_sketch`
- **Purpose:** Explicit solve/recompute with structured solver status.

### 23) `recompute_document`
- **Purpose:** Recompute doc and return structured status object.
- **Implementation basis:** phase-1 recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:144).

---

## F) Feature creation endpoints (post-sketch)

### 24) `create_feature`
- **Purpose:** Generic feature creation from sketch profile.
- **Supported initial types:** Pad, Pocket, Hole, Chamfer.
- **Implementation basis:** phase-1 recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:142).

### 25) `pad_from_sketch`
- **Purpose:** Explicit pad convenience endpoint.

### 26) `pocket_from_sketch`
- **Purpose:** Explicit pocket convenience endpoint.

### 27) `hole_from_sketch`
- **Purpose:** Explicit hole convenience endpoint.

---

## G) Transactions and reliability endpoints

### 28) `begin_transaction`
- **Purpose:** Start grouped sketch edit transaction.

### 29) `commit_transaction`
- **Purpose:** Commit grouped edits atomically.

### 30) `rollback_transaction`
- **Purpose:** Roll back grouped edits.
- **Implementation basis:** transaction recommendation in [research/freecad-mcp-usability-analysis.md](./freecad-mcp-usability-analysis.md:150).

---

## Implementation mapping (where each endpoint goes)

- MCP wrapper and schema validation:
  - `src/freecad_mcp/tools/sketch_tools.py`
  - `src/freecad_mcp/tools/feature_tools.py`
  - `src/freecad_mcp/tools/diagnostic_tools.py`
- RPC execution logic (GUI-thread safe):
  - `addon/FreeCADMCP/rpc_server/ops/sketch_ops.py`
  - `addon/FreeCADMCP/rpc_server/ops/feature_ops.py`
  - `addon/FreeCADMCP/rpc_server/ops/diagnostic_ops.py`
- Queue/facade remains in [addon/FreeCADMCP/rpc_server/rpc_server.py](../addon/FreeCADMCP/rpc_server/rpc_server.py:144).

---

## Delivery order (recommended)

1. Complete Part 1 modularization.
2. Deliver endpoints 1, 5, 10, 20, 23 first (smallest usable vertical slice).
3. Deliver geometry/constraint batch endpoints.
4. Deliver expression/external geometry endpoints.
5. Deliver feature helpers.
6. Deliver transaction/reliability endpoints.

This order gives immediate value for your star/arm/tangent sketch workflows while minimizing risk.
