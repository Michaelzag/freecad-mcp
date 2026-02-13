import math
from typing import Any

import FreeCAD

from ..serialize import serialize_value


def _import_part_module():
    import Part

    return Part


def _import_sketcher_module():
    import Sketcher

    return Sketcher


def _to_vector(raw: Any, default_z: float = 0.0) -> FreeCAD.Vector:
    if isinstance(raw, FreeCAD.Vector):
        return raw
    if isinstance(raw, dict):
        return FreeCAD.Vector(
            float(raw.get("x", 0.0)),
            float(raw.get("y", 0.0)),
            float(raw.get("z", default_z)),
        )
    if isinstance(raw, (list, tuple)):
        if len(raw) == 2:
            return FreeCAD.Vector(float(raw[0]), float(raw[1]), float(default_z))
        if len(raw) >= 3:
            return FreeCAD.Vector(float(raw[0]), float(raw[1]), float(raw[2]))
    raise ValueError(f"Invalid vector payload: {raw}")


def _to_placement(raw: dict[str, Any] | None) -> FreeCAD.Placement | None:
    if raw is None:
        return None

    base_raw = raw.get("Base", raw.get("Position", {}))
    rot_raw = raw.get("Rotation", {})

    base = _to_vector(base_raw)
    axis = _to_vector(rot_raw.get("Axis", {"x": 0.0, "y": 0.0, "z": 1.0}), default_z=1.0)
    angle = float(rot_raw.get("Angle", 0.0))
    return FreeCAD.Placement(base, FreeCAD.Rotation(axis, angle))


def _attach_support(sketch: Any, support_obj: Any, subelement: str) -> None:
    if hasattr(sketch, "Support"):
        sketch.Support = [(support_obj, subelement)]
    if hasattr(sketch, "AttachmentSupport"):
        sketch.AttachmentSupport = [(support_obj, subelement)]
    if hasattr(sketch, "MapMode"):
        sketch.MapMode = "FlatFace"


def _apply_support(doc: Any, sketch: Any, support: Any) -> None:
    if support is None:
        return

    if isinstance(support, str):
        plane = support.upper()
        if plane == "XY":
            return
        if plane == "XZ":
            sketch.Placement = FreeCAD.Placement(
                FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 90)
            )
            return
        if plane == "YZ":
            sketch.Placement = FreeCAD.Placement(
                FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), -90)
            )
            return

        support_obj = doc.getObject(support)
        if support_obj is None:
            raise ValueError(f"Support object '{support}' not found.")
        _attach_support(sketch, support_obj, "Face1")
        return

    if isinstance(support, dict):
        object_name = support.get("object") or support.get("object_name") or support.get("name")
        if not object_name:
            raise ValueError("Support mapping requires 'object' or 'object_name'.")

        subelement = support.get("subelement") or support.get("sub") or support.get("face") or "Face1"
        support_obj = doc.getObject(str(object_name))
        if support_obj is None:
            raise ValueError(f"Support object '{object_name}' not found.")
        _attach_support(sketch, support_obj, str(subelement))
        return

    raise ValueError("Support must be a plane string (XY/XZ/YZ), object name, or support mapping object.")


def create_sketch_gui(
    doc_name: str,
    sketch_name: str,
    support: Any = "XY",
    placement: dict[str, Any] | None = None,
):
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    if doc.getObject(sketch_name):
        return f"Object '{sketch_name}' already exists in document '{doc_name}'."

    try:
        sketch = doc.addObject("Sketcher::SketchObject", sketch_name)
        _apply_support(doc, sketch, support)

        parsed_placement = _to_placement(placement)
        if parsed_placement is not None:
            sketch.Placement = parsed_placement

        doc.recompute()
        FreeCAD.Console.PrintMessage(
            f"Sketch '{sketch.Name}' created in document '{doc_name}'.\n"
        )
        return {
            "sketch_name": sketch.Name,
            "label": sketch.Label,
            "support": support,
        }
    except Exception as e:
        return str(e)


def add_sketch_geometry_gui(doc_name: str, sketch_name: str, geometry: dict[str, Any]):
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    sketch = doc.getObject(sketch_name)
    if not sketch:
        return f"Sketch '{sketch_name}' not found in document '{doc_name}'."

    try:
        Part = _import_part_module()

        g_type = str(geometry.get("type", "")).lower()
        construction = bool(geometry.get("construction", False))
        geometry_ids: list[int] = []

        if g_type == "line":
            start = _to_vector(geometry.get("start"))
            end = _to_vector(geometry.get("end"))
            geo = Part.LineSegment(start, end)
            geometry_ids = [int(sketch.addGeometry(geo, construction))]

        elif g_type == "circle":
            center = _to_vector(geometry.get("center"))
            normal = _to_vector(geometry.get("normal", {"x": 0.0, "y": 0.0, "z": 1.0}), default_z=1.0)
            radius = float(geometry.get("radius", 0.0))
            if radius <= 0:
                raise ValueError("Circle radius must be > 0.")
            geo = Part.Circle(center, normal, radius)
            geometry_ids = [int(sketch.addGeometry(geo, construction))]

        elif g_type == "arc_center":
            center = _to_vector(geometry.get("center"))
            normal = _to_vector(geometry.get("normal", {"x": 0.0, "y": 0.0, "z": 1.0}), default_z=1.0)
            radius = float(geometry.get("radius", 0.0))
            if radius <= 0:
                raise ValueError("Arc radius must be > 0.")

            start_angle_deg = float(geometry.get("start_angle_deg", 0.0))
            end_angle_deg = float(geometry.get("end_angle_deg", 90.0))
            start_angle = math.radians(start_angle_deg)
            end_angle = math.radians(end_angle_deg)
            circle = Part.Circle(center, normal, radius)
            geo = Part.ArcOfCircle(circle, start_angle, end_angle)
            geometry_ids = [int(sketch.addGeometry(geo, construction))]

        elif g_type == "point":
            point = _to_vector(geometry.get("point"))
            geo = Part.Point(point)
            geometry_ids = [int(sketch.addGeometry(geo, construction))]

        elif g_type == "polyline":
            raw_points = geometry.get("points", [])
            if not isinstance(raw_points, list) or len(raw_points) < 2:
                raise ValueError("Polyline requires at least two points.")

            points = [_to_vector(p) for p in raw_points]
            segments = [
                Part.LineSegment(points[i], points[i + 1])
                for i in range(len(points) - 1)
            ]
            if geometry.get("closed", False):
                segments.append(Part.LineSegment(points[-1], points[0]))

            added = sketch.addGeometry(segments, construction)
            if isinstance(added, int):
                geometry_ids = [added]
            else:
                geometry_ids = [int(v) for v in added]

        elif g_type == "bspline":
            raw_points = geometry.get("points", [])
            if not isinstance(raw_points, list) or len(raw_points) < 2:
                raise ValueError("BSpline requires at least two points.")

            points = [_to_vector(p) for p in raw_points]
            periodic = bool(geometry.get("closed", False))

            curve = Part.BSplineCurve()
            curve.interpolate(points, PeriodicFlag=periodic)
            geometry_ids = [int(sketch.addGeometry(curve, construction))]

        else:
            raise ValueError(
                "Unsupported geometry type. Supported: line, circle, arc_center, point, polyline, bspline"
            )

        doc.recompute()
        return {
            "sketch_name": sketch.Name,
            "geometry_ids": geometry_ids,
            "geometry_count": len(getattr(sketch, "Geometry", [])),
        }
    except Exception as e:
        return str(e)


def _normalize_constraint_refs(refs: Any) -> list[int]:
    if not isinstance(refs, list):
        raise ValueError("Constraint 'refs' must be a list.")

    normalized: list[int] = []
    for ref in refs:
        if isinstance(ref, dict):
            geom = ref.get("geometry", ref.get("g", ref.get("index")))
            if geom is None:
                raise ValueError(f"Constraint ref missing geometry index: {ref}")
            normalized.append(int(geom))
            if "sub" in ref and ref["sub"] is not None:
                normalized.append(int(ref["sub"]))
            elif "point" in ref and ref["point"] is not None:
                normalized.append(int(ref["point"]))
        elif isinstance(ref, (list, tuple)):
            normalized.extend(int(v) for v in ref)
        else:
            normalized.append(int(ref))
    return normalized


def _normalize_constraint_value(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return FreeCAD.Units.Quantity(value)
        except Exception:
            return float(value)
    return value


def add_sketch_constraint_gui(doc_name: str, sketch_name: str, constraint: dict[str, Any]):
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    sketch = doc.getObject(sketch_name)
    if not sketch:
        return f"Sketch '{sketch_name}' not found in document '{doc_name}'."

    try:
        Sketcher = _import_sketcher_module()

        constraint_type = constraint.get("type")
        if not constraint_type:
            raise ValueError("Constraint payload requires 'type'.")

        refs = _normalize_constraint_refs(constraint.get("refs", []))
        args: list[Any] = list(refs)

        if "value" in constraint:
            args.append(_normalize_constraint_value(constraint["value"]))

        c = Sketcher.Constraint(str(constraint_type), *args)
        constraint_id = int(sketch.addConstraint(c))

        doc.recompute()
        return {
            "sketch_name": sketch.Name,
            "constraint_id": constraint_id,
            "constraint_count": len(getattr(sketch, "Constraints", [])),
        }
    except Exception as e:
        return str(e)


def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def get_sketch_diagnostics_gui(doc_name: str, sketch_name: str):
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    sketch = doc.getObject(sketch_name)
    if not sketch:
        return f"Sketch '{sketch_name}' not found in document '{doc_name}'."

    try:
        dof = None
        if hasattr(sketch, "solve"):
            try:
                dof = sketch.solve()
            except Exception:
                pass

        conflicting: list[Any] = []
        redundant: list[Any] = []
        open_profiles: list[Any] = []

        if hasattr(sketch, "getConflictingConstraints"):
            conflicting = _safe_list(sketch.getConflictingConstraints())
        if hasattr(sketch, "getRedundantConstraints"):
            redundant = _safe_list(sketch.getRedundantConstraints())
        if hasattr(sketch, "getOpenVertices"):
            open_profiles = [str(v) for v in _safe_list(sketch.getOpenVertices())]
        elif hasattr(sketch, "hasOpenVertices") and bool(sketch.hasOpenVertices()):
            open_profiles = ["open"]

        return {
            "sketch_name": sketch.Name,
            "dof": dof,
            "conflicting_constraints": [int(v) for v in conflicting if isinstance(v, (int, float))],
            "redundant_constraints": [int(v) for v in redundant if isinstance(v, (int, float))],
            "open_profiles": open_profiles,
            "geometry_count": len(getattr(sketch, "Geometry", [])),
            "constraint_count": len(getattr(sketch, "Constraints", [])),
        }
    except Exception as e:
        return str(e)


def _serialize_geometry(geo: Any, index: int) -> dict[str, Any]:
    Part = _import_part_module()
    construction = getattr(geo, "Construction", False)
    base: dict[str, Any] = {"id": index, "construction": bool(construction)}

    if isinstance(geo, Part.LineSegment):
        base["type"] = "line"
        base["start"] = serialize_value(geo.StartPoint)
        base["end"] = serialize_value(geo.EndPoint)
    elif isinstance(geo, Part.ArcOfCircle):
        base["type"] = "arc"
        base["center"] = serialize_value(geo.Center)
        base["radius"] = geo.Radius
        base["start_angle_deg"] = math.degrees(geo.FirstParameter)
        base["end_angle_deg"] = math.degrees(geo.LastParameter)
        base["start_point"] = serialize_value(geo.StartPoint)
        base["end_point"] = serialize_value(geo.EndPoint)
    elif isinstance(geo, Part.Circle):
        base["type"] = "circle"
        base["center"] = serialize_value(geo.Center)
        base["radius"] = geo.Radius
    elif isinstance(geo, Part.ArcOfEllipse):
        base["type"] = "arc_of_ellipse"
        base["center"] = serialize_value(geo.Center)
        base["major_radius"] = geo.MajorRadius
        base["minor_radius"] = geo.MinorRadius
        base["start_angle_deg"] = math.degrees(geo.FirstParameter)
        base["end_angle_deg"] = math.degrees(geo.LastParameter)
    elif isinstance(geo, Part.Ellipse):
        base["type"] = "ellipse"
        base["center"] = serialize_value(geo.Center)
        base["major_radius"] = geo.MajorRadius
        base["minor_radius"] = geo.MinorRadius
    elif isinstance(geo, Part.Point):
        base["type"] = "point"
        vec = getattr(geo, "Point", None) or FreeCAD.Vector(geo.X, geo.Y, geo.Z)
        base["point"] = serialize_value(vec)
    elif isinstance(geo, Part.BSplineCurve):
        base["type"] = "bspline"
        base["degree"] = geo.Degree
        base["poles"] = [serialize_value(p) for p in geo.getPoles()]
        base["knots"] = list(geo.getKnots())
    else:
        base["type"] = "unknown"
        base["description"] = str(type(geo).__name__)

    return base


_CONSTRAINT_UNUSED_REF = -2000


def _serialize_constraint(con: Any, index: int) -> dict[str, Any]:
    first = getattr(con, "First", _CONSTRAINT_UNUSED_REF)
    second = getattr(con, "Second", _CONSTRAINT_UNUSED_REF)
    third = getattr(con, "Third", _CONSTRAINT_UNUSED_REF)

    return {
        "id": index,
        "type": getattr(con, "Type", "Unknown"),
        "first": first if first != _CONSTRAINT_UNUSED_REF else None,
        "first_pos": getattr(con, "FirstPos", 0),
        "second": second if second != _CONSTRAINT_UNUSED_REF else None,
        "second_pos": getattr(con, "SecondPos", 0),
        "third": third if third != _CONSTRAINT_UNUSED_REF else None,
        "third_pos": getattr(con, "ThirdPos", 0),
        "value": getattr(con, "Value", None),
        "name": getattr(con, "Name", ""),
    }


def get_sketch_info_gui(doc_name: str, sketch_name: str):
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    sketch = doc.getObject(sketch_name)
    if not sketch:
        return f"Sketch '{sketch_name}' not found in document '{doc_name}'."

    try:
        dof = None
        if hasattr(sketch, "solve"):
            try:
                dof = sketch.solve()
            except Exception:
                pass

        geometry_list = getattr(sketch, "Geometry", [])
        constraint_list = getattr(sketch, "Constraints", [])

        return {
            "sketch_name": sketch.Name,
            "placement": serialize_value(sketch.Placement),
            "dof": dof,
            "geometry_count": len(geometry_list),
            "constraint_count": len(constraint_list),
            "geometry": [_serialize_geometry(g, i) for i, g in enumerate(geometry_list)],
            "constraints": [_serialize_constraint(c, i) for i, c in enumerate(constraint_list)],
        }
    except Exception as e:
        return str(e)


def recompute_document_gui(doc_name: str):
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    try:
        doc.recompute()
        return {
            "document_name": doc.Name,
            "object_count": len(doc.Objects),
            "recomputed": True,
        }
    except Exception as e:
        return str(e)
