# RPC Response Standardization

## Goal

Normalize all `FreeCADRPC` method return shapes into two well-defined patterns. No transport change required — this is a contract cleanup over the existing XML-RPC layer.

## Patterns

### Pattern 1: Envelope

For any method that carries application semantics (commands and queries).

```python
{"success": bool, "data": Any, "error": str | None}
```

- `success` — whether the operation completed without error.
- `data` — the payload on success, `None` on failure.
- `error` — human-readable error string on failure, `None` on success.

### Pattern 2: Bare value

For infrastructure probes and raw data fetches that don't carry application semantics.

```python
value  # no wrapping
```

## Method assignments

### Envelope methods

| Method | Current return (success) | Current return (failure) | New `data` shape |
|---|---|---|---|
| `create_document` | `{"success", "document_name"}` | `{"success", "error"}` | `{"document_name": str}` |
| `create_object` | `{"success", "object_name"}` | `{"success", "error"}` | `{"object_name": str}` |
| `edit_object` | `{"success", "object_name"}` | `{"success", "error"}` | `{"object_name": str}` |
| `delete_object` | `{"success", "object_name"}` | `{"success", "error"}` | `{"object_name": str}` |
| `execute_code` | `{"success", "message"}` | `{"success", "error"}` | `{"output": str}` |
| `insert_part_from_library` | `{"success", "message"}` | `{"success", "error"}` | `None` |
| `get_objects` | raw `list` | `[]` (silent) | `list[dict]` |
| `get_object` | raw `dict` | `None` (silent) | `dict` |
| `list_documents` | raw `list` | (no failure path) | `list[str]` |
| `get_parts_list` | raw `list` | (no failure path) | `list[str]` |

### Bare methods

| Method | Returns | Notes |
|---|---|---|
| `ping` | `True` | Connectivity probe only |
| `get_active_screenshot` | `str \| None` | Large base64 payload; caller already branches on `None` |

## What changes

### Addon side (`FreeCADRPC`)

1. **Commands** (`create_document`, `create_object`, `edit_object`, `delete_object`, `execute_code`, `insert_part_from_library`): move ad hoc keys into `data` dict, add `error: None` on success.

   Before:
   ```python
   return {"success": True, "document_name": name}
   ```

   After:
   ```python
   return {"success": True, "data": {"document_name": name}, "error": None}
   ```

2. **Queries** (`get_objects`, `get_object`, `list_documents`, `get_parts_list`): wrap raw returns in envelope, add explicit failure for missing documents.

   Before:
   ```python
   def get_objects(self, doc_name):
       doc = FreeCAD.getDocument(doc_name)
       if doc:
           return [serialize_object(obj) for obj in doc.Objects]
       else:
           return []
   ```

   After:
   ```python
   def get_objects(self, doc_name):
       doc = FreeCAD.getDocument(doc_name)
       if not doc:
           return {"success": False, "data": None, "error": f"Document '{doc_name}' not found"}
       return {"success": True, "data": [serialize_object(obj) for obj in doc.Objects], "error": None}
   ```

3. **`execute_code`**: rename `message` to `output` for clarity.

   Before:
   ```python
   return {"success": True, "message": "Python code execution scheduled. \nOutput: " + output_buffer.getvalue()}
   ```

   After:
   ```python
   return {"success": True, "data": {"output": output_buffer.getvalue()}, "error": None}
   ```

### Client side (`FreeCADConnection` / MCP tools)

Update all response consumers to read from `res["data"]` instead of ad hoc keys:

- `res["document_name"]` → `res["data"]["document_name"]`
- `res["object_name"]` → `res["data"]["object_name"]`
- `res["message"]` → `res["data"]["output"]`
- Raw list/dict returns → `res["data"]`

### No changes

- `ping` — stays as bare `True`.
- `get_active_screenshot` — stays as bare `str | None`.
- GUI task queue, IP filtering, settings — untouched.
- All `_*_gui` private methods — untouched (they return `True` or error string to the internal queue, not to RPC clients).
