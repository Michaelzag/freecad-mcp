from typing import Any

import FreeCAD


def pad_gui(
    doc_name: str,
    body_name: str,
    sketch_name: str,
    length: float = 10.0,
    type: int = 0,
    reversed: bool = False,
    symmetric: bool = False,
    length2: float = 0.0,
    taper_angle: float = 0.0,
    taper_angle2: float = 0.0,
    name: str | None = None,
):
    """Pad (extrude) a sketch to create a solid feature.

    Type values: 0=Dimension, 1=ToLast, 2=ToFirst, 3=UpToFace, 4=TwoDimensions, 5=UpToShape
    """
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    body = doc.getObject(body_name)
    if not body:
        return f"Body '{body_name}' not found."

    sketch = doc.getObject(sketch_name)
    if not sketch:
        return f"Sketch '{sketch_name}' not found."

    try:
        pad_name = name or "Pad"
        pad = doc.addObject("PartDesign::Pad", pad_name)
        body.addObject(pad)
        pad.Profile = sketch
        pad.Length = length
        pad.Type = type
        pad.Reversed = reversed
        pad.Midplane = symmetric

        if length2:
            pad.Length2 = length2
        if taper_angle:
            pad.TaperAngle = taper_angle
        if taper_angle2:
            pad.TaperAngle2 = taper_angle2

        doc.recompute()
        FreeCAD.Console.PrintMessage(f"Pad '{pad.Name}' created in body '{body_name}'.\n")
        return {
            "feature_name": pad.Name,
            "body_name": body_name,
            "sketch_name": sketch_name,
            "length": pad.Length.Value if hasattr(pad.Length, "Value") else float(pad.Length),
        }
    except Exception as e:
        return str(e)


def pocket_gui(
    doc_name: str,
    body_name: str,
    sketch_name: str,
    length: float = 10.0,
    type: int = 0,
    reversed: bool = False,
    symmetric: bool = False,
    name: str | None = None,
):
    """Pocket (cut) using a sketch profile.

    Type values: 0=Dimension, 1=ThroughAll, 2=ToFirst, 3=UpToFace, 4=TwoDimensions
    """
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    body = doc.getObject(body_name)
    if not body:
        return f"Body '{body_name}' not found."

    sketch = doc.getObject(sketch_name)
    if not sketch:
        return f"Sketch '{sketch_name}' not found."

    try:
        pocket_name = name or "Pocket"
        pocket = doc.addObject("PartDesign::Pocket", pocket_name)
        body.addObject(pocket)
        pocket.Profile = sketch
        pocket.Length = length
        pocket.Type = type
        pocket.Reversed = reversed
        pocket.Midplane = symmetric

        doc.recompute()
        FreeCAD.Console.PrintMessage(f"Pocket '{pocket.Name}' created in body '{body_name}'.\n")
        return {
            "feature_name": pocket.Name,
            "body_name": body_name,
            "sketch_name": sketch_name,
            "length": pocket.Length.Value if hasattr(pocket.Length, "Value") else float(pocket.Length),
        }
    except Exception as e:
        return str(e)


def revolve_gui(
    doc_name: str,
    body_name: str,
    sketch_name: str,
    axis: str = "V_Axis",
    axis_object: str | None = None,
    angle: float = 360.0,
    type: int = 0,
    reversed: bool = False,
    symmetric: bool = False,
    name: str | None = None,
):
    """Revolve a sketch around an axis.

    axis: Sub-element name like "V_Axis", "H_Axis", "N_Axis" (sketch axes),
          or "X_Axis", "Y_Axis", "Z_Axis" (with axis_object as the body origin axis object name).
    axis_object: If provided, the object name to use as axis reference (e.g. the sketch name, or a body origin axis).
                 If not provided, defaults to the sketch.
    Type values: 0=Angle, 1=ToLast, 2=ToFirst, 3=UpToFace, 4=TwoAngles
    """
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    body = doc.getObject(body_name)
    if not body:
        return f"Body '{body_name}' not found."

    sketch = doc.getObject(sketch_name)
    if not sketch:
        return f"Sketch '{sketch_name}' not found."

    try:
        rev_name = name or "Revolution"
        rev = doc.addObject("PartDesign::Revolution", rev_name)
        body.addObject(rev)
        rev.Profile = sketch
        rev.Angle = angle
        rev.Type = type
        rev.Reversed = reversed
        rev.Midplane = symmetric

        # Set the reference axis
        if axis_object:
            axis_obj = doc.getObject(axis_object)
            if not axis_obj:
                return f"Axis object '{axis_object}' not found."
            rev.ReferenceAxis = (axis_obj, [axis])
        else:
            rev.ReferenceAxis = (sketch, [axis])

        doc.recompute()
        FreeCAD.Console.PrintMessage(f"Revolution '{rev.Name}' created in body '{body_name}'.\n")
        return {
            "feature_name": rev.Name,
            "body_name": body_name,
            "sketch_name": sketch_name,
            "angle": rev.Angle.Value if hasattr(rev.Angle, "Value") else float(rev.Angle),
        }
    except Exception as e:
        return str(e)


def fillet_gui(
    doc_name: str,
    body_name: str,
    feature_name: str,
    edges: list[str],
    radius: float = 1.0,
    name: str | None = None,
):
    """Fillet (round) edges on a feature.

    edges: List of edge sub-element names, e.g. ["Edge1", "Edge3", "Edge5"].
    """
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    body = doc.getObject(body_name)
    if not body:
        return f"Body '{body_name}' not found."

    feature = doc.getObject(feature_name)
    if not feature:
        return f"Feature '{feature_name}' not found."

    try:
        fillet_name = name or "Fillet"
        fillet = doc.addObject("PartDesign::Fillet", fillet_name)
        body.addObject(fillet)
        fillet.Base = (feature, edges)
        fillet.Radius = radius

        doc.recompute()
        FreeCAD.Console.PrintMessage(f"Fillet '{fillet.Name}' created in body '{body_name}'.\n")
        return {
            "feature_name": fillet.Name,
            "body_name": body_name,
            "base_feature": feature_name,
            "edges": edges,
            "radius": radius,
        }
    except Exception as e:
        return str(e)


def chamfer_gui(
    doc_name: str,
    body_name: str,
    feature_name: str,
    edges: list[str],
    size: float = 1.0,
    name: str | None = None,
):
    """Chamfer (bevel) edges on a feature.

    edges: List of edge sub-element names, e.g. ["Edge1", "Edge3"].
    """
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    body = doc.getObject(body_name)
    if not body:
        return f"Body '{body_name}' not found."

    feature = doc.getObject(feature_name)
    if not feature:
        return f"Feature '{feature_name}' not found."

    try:
        chamfer_name = name or "Chamfer"
        chamfer = doc.addObject("PartDesign::Chamfer", chamfer_name)
        body.addObject(chamfer)
        chamfer.Base = (feature, edges)
        chamfer.Size = size

        doc.recompute()
        FreeCAD.Console.PrintMessage(f"Chamfer '{chamfer.Name}' created in body '{body_name}'.\n")
        return {
            "feature_name": chamfer.Name,
            "body_name": body_name,
            "base_feature": feature_name,
            "edges": edges,
            "size": size,
        }
    except Exception as e:
        return str(e)


def get_body_features_gui(doc_name: str, body_name: str):
    """Return the feature tree for a Body as structured data."""
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        return f"Document '{doc_name}' not found."

    body = doc.getObject(body_name)
    if not body:
        return f"Body '{body_name}' not found."

    try:
        features = []
        for feature in body.Group:
            entry = {
                "name": feature.Name,
                "label": feature.Label,
                "type": feature.TypeId,
            }

            # Sketch-based features — include profile reference
            if hasattr(feature, "Profile") and feature.Profile:
                profile = feature.Profile
                if isinstance(profile, (list, tuple)):
                    entry["profile"] = profile[0].Name if profile[0] else None
                else:
                    entry["profile"] = profile.Name if profile else None

            # Dress-up features — include base + sub-element references
            if hasattr(feature, "Base") and feature.Base:
                base = feature.Base
                if isinstance(base, (list, tuple)) and len(base) >= 1:
                    if isinstance(base[0], str):
                        # (feature, ["Edge1", ...]) format after resolution
                        entry["base_feature"] = base[0]
                        entry["sub_elements"] = list(base[1]) if len(base) > 1 else []
                    else:
                        entry["base_feature"] = base[0].Name if base[0] else None
                        entry["sub_elements"] = list(base[1]) if len(base) > 1 else []

            # Revolution/Groove — include axis reference
            if hasattr(feature, "ReferenceAxis") and feature.ReferenceAxis:
                ref_axis = feature.ReferenceAxis
                if isinstance(ref_axis, (list, tuple)) and len(ref_axis) >= 1:
                    entry["axis_object"] = ref_axis[0].Name if ref_axis[0] else None
                    entry["axis_sub"] = list(ref_axis[1]) if len(ref_axis) > 1 else []

            # Key numeric properties
            for prop in ("Length", "Length2", "Radius", "Size", "Angle", "Angle2"):
                if hasattr(feature, prop):
                    val = getattr(feature, prop)
                    if hasattr(val, "Value"):
                        entry[prop.lower()] = val.Value
                    elif isinstance(val, (int, float)):
                        entry[prop.lower()] = float(val)

            # Shape info (volume, face/edge counts)
            shape = getattr(feature, "Shape", None)
            if shape and getattr(shape, "isValid", lambda: False)():
                entry["shape"] = {
                    "volume": shape.Volume,
                    "face_count": len(shape.Faces),
                    "edge_count": len(shape.Edges),
                }

            features.append(entry)

        tip_name = body.Tip.Name if body.Tip else None
        return {
            "body_name": body.Name,
            "tip": tip_name,
            "feature_count": len(features),
            "features": features,
        }
    except Exception as e:
        return str(e)
