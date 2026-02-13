# FreeCAD MCP Usability Analysis (Revised)

## 1) Scope and Research Method

This document evaluates how usable this repository is for **agent-driven, sketch-first parametric CAD workflows**, especially the workflow style shown in the referenced tutorial video:

- YouTube tutorial: https://www.youtube.com/watch?v=E14m5hf6Pvo

Evidence sources used:

1. Repository implementation in [`src/freecad_mcp/server.py`](../src/freecad_mcp/server.py:1), app/lifecycle wiring in [`src/freecad_mcp/app.py`](../src/freecad_mcp/app.py:6) and [`src/freecad_mcp/runtime.py`](../src/freecad_mcp/runtime.py:23), connection wrapper in [`src/freecad_mcp/connection.py`](../src/freecad_mcp/connection.py:9), tool modules in [`src/freecad_mcp/tools/object_tools.py`](../src/freecad_mcp/tools/object_tools.py:15) and [`src/freecad_mcp/tools/misc_tools.py`](../src/freecad_mcp/tools/misc_tools.py:15), and addon facade in [`addon/FreeCADMCP/rpc_server/rpc_server.py`](../addon/FreeCADMCP/rpc_server/rpc_server.py:1).
2. Project docs in [`README.md`](../README.md:1).
3. FreeCAD docs for scripting model and Sketcher APIs:
   - FreeCAD Scripting Basics: https://wiki.freecad.org/FreeCAD_Scripting_Basics
   - Sketcher scripting: https://wiki.freecad.org/Sketcher_scripting
   - Topological naming problem: https://wiki.freecad.org/Topological_naming_problem
   - PartDesign workbench: https://wiki.freecad.org/PartDesign_Workbench

---

## 2) Executive Assessment

### Bottom line

The project is a strong **MVP integration** between MCP and FreeCAD, but currently exposes only a small high-level tool surface. It is:

- **Good** for object-level CRUD, screenshots, parts-library insertion, and generalized scripting.
- **Not yet first-class** for sketch/constraint-native modeling as a structured tool API.

### Practical implication

An agent can still achieve complex CAD output today by using [`execute_code()`](../src/freecad_mcp/tools/misc_tools.py:17), but that shifts burden to generated Python rather than deterministic domain tools.

---

## 3) Architecture Overview (What Works Well)

### 3.1 Clean split between MCP and FreeCAD runtime

- MCP-facing bootstrap/registration lives in [`src/freecad_mcp/server.py`](../src/freecad_mcp/server.py:1), app/lifecycle in [`src/freecad_mcp/app.py`](../src/freecad_mcp/app.py:6) and [`src/freecad_mcp/runtime.py`](../src/freecad_mcp/runtime.py:23), connection transport in [`src/freecad_mcp/connection.py`](../src/freecad_mcp/connection.py:9), with tool declarations in [`src/freecad_mcp/tools/object_tools.py`](../src/freecad_mcp/tools/object_tools.py:15) and [`src/freecad_mcp/tools/misc_tools.py`](../src/freecad_mcp/tools/misc_tools.py:15).
- FreeCAD-addon XML-RPC server and GUI-thread execution live in [`addon/FreeCADMCP/rpc_server/rpc_server.py`](../addon/FreeCADMCP/rpc_server/rpc_server.py:1), while extracted operation logic lives in [`addon/FreeCADMCP/rpc_server/ops/object_ops.py`](../addon/FreeCADMCP/rpc_server/ops/object_ops.py:1), [`addon/FreeCADMCP/rpc_server/ops/view_ops.py`](../addon/FreeCADMCP/rpc_server/ops/view_ops.py:1), and [`addon/FreeCADMCP/rpc_server/ops/code_ops.py`](../addon/FreeCADMCP/rpc_server/ops/code_ops.py:1).
- Workbench commands are registered in [`addon/FreeCADMCP/InitGui.py`](../addon/FreeCADMCP/InitGui.py:1).

This aligns with FreeCAD’s App/Gui split model documented in FreeCAD Scripting Basics.

### 3.2 GUI-thread execution strategy is appropriate

The request/response queues and timed GUI processing in [`process_gui_tasks()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:149) are the right direction for avoiding unsafe direct manipulation from non-GUI threads.

### 3.3 Usable baseline tool set

The server exposes 11 tools (registered from [`register_tools()`](../src/freecad_mcp/tools/object_tools.py:15) and [`register_tools()`](../src/freecad_mcp/tools/misc_tools.py:15)).

| Tool | Type of control |
|---|---|
| [`create_document()`](../src/freecad_mcp/tools/object_tools.py:17) | Document lifecycle |
| [`create_object()`](../src/freecad_mcp/tools/object_tools.py:52) | Object creation (Part/Draft/PartDesign/FEM) |
| [`edit_object()`](../src/freecad_mcp/tools/object_tools.py:95) | Property mutation |
| [`delete_object()`](../src/freecad_mcp/tools/object_tools.py:131) | Object deletion |
| [`get_objects()`](../src/freecad_mcp/tools/object_tools.py:163), [`get_object()`](../src/freecad_mcp/tools/object_tools.py:193) | Introspection |
| [`get_view()`](../src/freecad_mcp/tools/misc_tools.py:48) | Visual feedback |
| [`insert_part_from_library()`](../src/freecad_mcp/tools/misc_tools.py:65), [`get_parts_list()`](../src/freecad_mcp/tools/misc_tools.py:96) | Parts reuse |
| [`list_documents()`](../src/freecad_mcp/tools/object_tools.py:224) | Session introspection |
| [`execute_code()`](../src/freecad_mcp/tools/misc_tools.py:17) | Full escape hatch to Python API |

---

## 4) Coverage Against Sketch/Constraint-Centric Workflows

The tutorial workflow is heavily Sketcher/PartDesign-oriented (constraints, dimensions, expressions, external geometry, pad/pocket/hole iterations).

### 4.1 Current support matrix

| Workflow capability | Direct MCP tool? | Achievable via `execute_code`? |
|---|---:|---:|
| Create/open sketch | ❌ | ✅ |
| Add sketch geometry (line/circle/arc/spline) | ❌ | ✅ |
| Add geometric constraints | ❌ | ✅ |
| Add dimensional constraints with units | ❌ | ✅ |
| Bind expressions/variables to constraints | ❌ | ✅ |
| External geometry projection into sketch | ❌ | ✅ |
| Sketch diagnostics (DoF/conflicts/redundancy) | ❌ | ✅ (if scripted) |
| Feature ops (Pad/Pocket/Hole/Chamfer/Mirror/Pattern) | ❌ | ✅ |
| Assembly constraints workflow | ❌ | ✅ (if scripted and workbench available) |

### 4.2 Important correction from prior draft

The previous draft over-credited [`edit_object()`](../src/freecad_mcp/tools/object_tools.py:95) for constraint operations. In practice, sketch constraints are **not** a first-class path through [`edit_object()`](../src/freecad_mcp/tools/object_tools.py:95); they are primarily done through Python scripting (`Sketcher.Constraint(...)`) via [`execute_code()`](../src/freecad_mcp/tools/misc_tools.py:17).

---

## 5) Why It Feels “Brute Force” for Agents

Even though functionality is technically reachable, usability degrades because:

1. No first-class sketch/constraint tool contract (agent must emit FreeCAD Python).
2. No stable semantic IDs for geometry/constraints in MCP responses.
3. No explicit sketch-state diagnostics (under/over-constrained, conflicting constraints).
4. No dedicated feature tools to represent intent (e.g., “through all pocket”).
5. Heavy dependence on prompt engineering + ad hoc scripts instead of deterministic API steps.

---

## 6) What Is Already Available in FreeCAD API (and Therefore Reachable)

From FreeCAD docs, Sketcher supports scripted geometry and constraints:

```python
import FreeCAD as App
import Part
import Sketcher

doc = App.ActiveDocument
sk = doc.addObject("Sketcher::SketchObject", "Sketch")
g0 = sk.addGeometry(Part.LineSegment(App.Vector(0,0,0), App.Vector(10,0,0)), False)
g1 = sk.addGeometry(Part.Circle(App.Vector(5,5,0), App.Vector(0,0,1), 3), False)

sk.addConstraint(Sketcher.Constraint("Horizontal", g0))
sk.addConstraint(Sketcher.Constraint("Radius", g1, App.Units.Quantity("3 mm")))

doc.recompute()
```

References:

- Sketcher scripting: https://wiki.freecad.org/Sketcher_scripting
- Scripting model (App/Gui/doc): https://wiki.freecad.org/FreeCAD_Scripting_Basics

Implication: the MCP can support tutorial-style workflows today, but through scripted control, not ergonomic tool-level control.

---

## 7) Prioritized Improvements (Usability-Focused)

## Phase 1 — Minimum viable sketch-native MCP (highest ROI)

1. `create_sketch(doc_name, support)`
2. `add_sketch_geometry(doc_name, sketch_name, geometry)`
3. `add_sketch_constraint(doc_name, sketch_name, constraint)`
4. `set_sketch_expression(doc_name, sketch_name, target, expression)`
5. `project_external_geometry(doc_name, sketch_name, refs)`
6. `create_feature(doc_name, type, params)` for Pad/Pocket/Hole/Chamfer
7. `get_sketch_diagnostics(doc_name, sketch_name)`
8. `recompute_document(doc_name)` with structured status

### Phase 2 — Reliability and iteration speed

1. Deterministic geometry/constraint handles in responses
2. Batch operations (add many geometries/constraints atomically)
3. Undo/redo and transaction grouping
4. Better typed error model (e.g., constraint conflict, invalid support)

### Phase 3 — Advanced workflows

1. Datum and attachment tools
2. Pattern/mirror tools with explicit semantic params
3. Assembly helper tools
4. Topology-stability helpers (datum-first suggestions)

---

## 8) Suggested MCP Tool Contract Shape

To reduce LLM brittleness, tool contracts should be explicit and typed.

Example pattern:

```json
{
  "doc_name": "Stem",
  "sketch_name": "Profile",
  "constraint": {
    "type": "Distance",
    "refs": [
      {"geometry": 3, "sub": 1},
      {"geometry": -1, "sub": 0}
    ],
    "value": "47 mm",
    "name": "stem_height"
  }
}
```

Notes:

- Keep unit-bearing values as strings (e.g., `"47 mm"`) to mirror FreeCAD quantity behavior.
- Return stable IDs and include updated DoF/conflict info after each constraint mutation.

---

## 9) FreeCAD-Specific Modeling Guidance to Encode in MCP

The tutorial-style method is strong because it is robust:

1. Fully constrain sketches before feature creation.
2. Prefer datum/origin-based attachments over unstable face chaining where possible.
3. Recompute and validate incrementally.
4. Use expressions/variables for design intent and parametric edits.

References:

- Topological naming and datum guidance: https://wiki.freecad.org/Topological_naming_problem
- Sketcher constraints and indexing model: https://wiki.freecad.org/Sketcher_scripting

---

## 10) Notable Code-Level Observations

1. Screenshot behavior is already thoughtfully handled with fallbacks in [`add_screenshot_if_available()`](../src/freecad_mcp/tools/common.py:6), view checks in [`FreeCADConnection.get_active_screenshot()`](../src/freecad_mcp/connection.py:34), and addon capture logic in [`FreeCADRPC.get_active_screenshot()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:334).
2. Core property mapping is centralized in [`set_object_property()`](../addon/FreeCADMCP/rpc_server/rpc_server.py:166), while object lifecycle GUI operations are now separated in [`create_object_gui()`](../addon/FreeCADMCP/rpc_server/ops/object_ops.py:12), [`edit_object_gui()`](../addon/FreeCADMCP/rpc_server/ops/object_ops.py:75), and [`delete_object_gui()`](../addon/FreeCADMCP/rpc_server/ops/object_ops.py:109).
3. Code execution is routed via [`execute_code_gui()`](../addon/FreeCADMCP/rpc_server/ops/code_ops.py:8), and parts library integration is straightforward via [`insert_part_from_library()`](../addon/FreeCADMCP/rpc_server/parts_library.py:8) and [`get_parts_list()`](../addon/FreeCADMCP/rpc_server/parts_library.py:19).
4. Object serialization compatibility handling is centralized in [`serialize_value()`](../addon/FreeCADMCP/rpc_server/serialize.py:4), [`serialize_view_object()`](../addon/FreeCADMCP/rpc_server/serialize.py:41), and [`serialize_object()`](../addon/FreeCADMCP/rpc_server/serialize.py:56).
5. Cleanup routes through [`reset_freecad_connection()`](../src/freecad_mcp/connection.py:117) from [`server_lifespan()`](../src/freecad_mcp/runtime.py:23), and [`disconnect()`](../src/freecad_mcp/connection.py:90) is defined.

---

## 11) Final Verdict

This repository is a well-structured FreeCAD MCP base with a practical initial tool set, but it is currently **object-centric** rather than **sketch/constraint-centric**.

For agents, that means:

- **Can fully control FreeCAD in principle** (through [`execute_code()`](../src/freecad_mcp/tools/misc_tools.py:17)).
- **Cannot yet do it ergonomically/reliably as first-class CAD intent operations** without additional sketch-native MCP tools.

If Phase 1 is implemented, this can move from “script-driven brute force” to a robust CAD-native agent interface matching modern parametric workflows.

---

## 12) References

### Repository references

- MCP server bootstrap/composition: [`src/freecad_mcp/server.py`](../src/freecad_mcp/server.py:1)
- MCP entrypoint: [`main()`](../src/freecad_mcp/server.py:72)
- MCP app/lifespan composition: [`src/freecad_mcp/app.py`](../src/freecad_mcp/app.py:6), [`server_lifespan()`](../src/freecad_mcp/runtime.py:23)
- MCP transport connection wrapper: [`src/freecad_mcp/connection.py`](../src/freecad_mcp/connection.py:9)
- Tool definition modules: [`src/freecad_mcp/tools/object_tools.py`](../src/freecad_mcp/tools/object_tools.py:15), [`src/freecad_mcp/tools/misc_tools.py`](../src/freecad_mcp/tools/misc_tools.py:15)
- Shared tool helper: [`src/freecad_mcp/tools/common.py`](../src/freecad_mcp/tools/common.py:6)
- FreeCAD addon RPC server: [`addon/FreeCADMCP/rpc_server/rpc_server.py`](../addon/FreeCADMCP/rpc_server/rpc_server.py:1)
- RPC ops modules: [`addon/FreeCADMCP/rpc_server/ops/object_ops.py`](../addon/FreeCADMCP/rpc_server/ops/object_ops.py:1), [`addon/FreeCADMCP/rpc_server/ops/view_ops.py`](../addon/FreeCADMCP/rpc_server/ops/view_ops.py:1), [`addon/FreeCADMCP/rpc_server/ops/code_ops.py`](../addon/FreeCADMCP/rpc_server/ops/code_ops.py:1)
- Workbench registration: [`addon/FreeCADMCP/InitGui.py`](../addon/FreeCADMCP/InitGui.py:1)
- Parts library helpers: [`addon/FreeCADMCP/rpc_server/parts_library.py`](../addon/FreeCADMCP/rpc_server/parts_library.py:1)
- Object serialization: [`addon/FreeCADMCP/rpc_server/serialize.py`](../addon/FreeCADMCP/rpc_server/serialize.py:1)
- Project readme/tools list: [`README.md`](../README.md:154)

### External references

- Tutorial video: https://www.youtube.com/watch?v=E14m5hf6Pvo
- FreeCAD Scripting Basics: https://wiki.freecad.org/FreeCAD_Scripting_Basics
- Sketcher scripting: https://wiki.freecad.org/Sketcher_scripting
- Topological naming problem: https://wiki.freecad.org/Topological_naming_problem
- PartDesign workbench: https://wiki.freecad.org/PartDesign_Workbench
