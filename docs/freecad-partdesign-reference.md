# FreeCAD PartDesign Reference for MCP Server Development

## The PartDesign Workflow

The core loop a human (and agent) follows:

1. Create document
2. Create a Body (`PartDesign::Body`) — the container for a single contiguous solid
3. Create a sketch on a plane (XY, XZ, YZ from Body's Origin)
4. Add 2D geometry (lines, arcs, circles)
5. Add constraints until fully constrained (0 DoF)
6. Apply a feature (Pad, Pocket, Revolve) that references the sketch → 2D becomes 3D
7. Select a face on the result (or create a DatumPlane)
8. Create a new sketch on that face/datum
9. Repeat steps 4-8
10. Apply dress-up features (Fillet, Chamfer) to edges/faces
11. Apply transformation features (Mirror, LinearPattern, PolarPattern) if needed

## Body Structure

```
Body (PartDesign::Body)
├── Origin (auto-created)
│   ├── XY_Plane, XZ_Plane, YZ_Plane
│   ├── X_Axis, Y_Axis, Z_Axis
│   └── Origin_Point
├── Sketch (on origin plane)
├── Pad (references Sketch → first solid)
├── Sketch001 (on face of Pad)
├── Pocket (references Sketch001 → cuts from solid)
├── Fillet (references edges of Pocket result)
└── ... (Tip points to last solid feature)
```

Key properties:
- `Body.Tip` — the feature whose shape is the Body's output
- `Body.Group` — ordered list of all features
- Features chain via `BaseFeature` links: Pocket.BaseFeature = Pad, Fillet.BaseFeature = Pocket, etc.
- Sketches and datums do NOT participate in the BaseFeature chain

## Python API Patterns

### Creating Body + Sketch on Plane

```python
doc = App.newDocument("MyDoc")
body = doc.addObject("PartDesign::Body", "Body")

sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
body.addObject(sketch)
sketch.AttachmentSupport = (doc.XY_Plane, [""])  # or body.Origin.OriginFeatures[3]
sketch.MapMode = "FlatFace"
```

### Sketch on a Face of Existing Feature

```python
sketch2 = doc.addObject("Sketcher::SketchObject", "Sketch001")
body.addObject(sketch2)
sketch2.AttachmentSupport = (pad, ["Face6"])  # e.g. top face
sketch2.MapMode = "FlatFace"
```

### Pad (Additive Extrusion)

```python
pad = doc.addObject("PartDesign::Pad", "Pad")
body.addObject(pad)
pad.Profile = sketch
pad.Length = 10.0
# pad.Type: 0=Dimension, 1=ToLast, 2=ToFirst, 3=UpToFace, 4=TwoDimensions, 5=UpToShape
# pad.Reversed, pad.Midplane, pad.TaperAngle, pad.Length2
doc.recompute()
```

### Pocket (Subtractive Extrusion)

```python
pocket = doc.addObject("PartDesign::Pocket", "Pocket")
body.addObject(pocket)
pocket.Profile = sketch2
pocket.Length = 5.0
# pocket.Type: 0=Dimension, 1=ThroughAll, 2=ToFirst, 3=UpToFace, 4=TwoDimensions
doc.recompute()
```

### Revolution / Groove

```python
rev = doc.addObject("PartDesign::Revolution", "Revolution")
body.addObject(rev)
rev.Profile = sketch
rev.ReferenceAxis = (sketch, ["V_Axis"])  # or ["H_Axis"], ["N_Axis"], or body origin axis
rev.Angle = 360.0
doc.recompute()
```

### Fillet / Chamfer

```python
fillet = doc.addObject("PartDesign::Fillet", "Fillet")
body.addObject(fillet)
fillet.Base = (pocket, ["Edge1", "Edge2"])
fillet.Radius = 2.0
doc.recompute()

chamfer = doc.addObject("PartDesign::Chamfer", "Chamfer")
body.addObject(chamfer)
chamfer.Base = (pad, ["Edge1"])
chamfer.Size = 1.0
# chamfer.ChamferType: "Equal distance", "Two distances", "Distance and Angle"
doc.recompute()
```

### Navigating the Feature Tree

```python
body = doc.getObject("Body")
for feature in body.Group:
    print(f"{feature.Name} ({feature.TypeId})")
    if hasattr(feature, "Profile") and feature.Profile:
        print(f"  Profile: {feature.Profile[0].Name}")
    if hasattr(feature, "Base") and feature.Base:
        print(f"  Base: {feature.Base[0].Name} {feature.Base[1]}")
```

## All PartDesign Feature Types

### Sketch-Based Additive
| Feature | Type String | Key Properties |
|---------|-------------|----------------|
| Pad | `PartDesign::Pad` | Profile, Length, Type, Reversed, Midplane, TaperAngle |
| Revolution | `PartDesign::Revolution` | Profile, ReferenceAxis, Angle, Type |
| Additive Loft | `PartDesign::AdditiveLoft` | Sections, Ruled, Closed |
| Additive Pipe | `PartDesign::AdditivePipe` | Profile, Spine, Mode |
| Additive Helix | `PartDesign::AdditiveHelix` | Profile, Pitch, Height, Turns |

### Sketch-Based Subtractive
| Feature | Type String | Key Properties |
|---------|-------------|----------------|
| Pocket | `PartDesign::Pocket` | Profile, Length, Type, Reversed |
| Hole | `PartDesign::Hole` | Profile, Threaded, Diameter, Depth |
| Groove | `PartDesign::Groove` | Profile, ReferenceAxis, Angle |
| Subtractive Loft | `PartDesign::SubtractiveLoft` | (same as additive) |
| Subtractive Pipe | `PartDesign::SubtractivePipe` | (same as additive) |
| Subtractive Helix | `PartDesign::SubtractiveHelix` | (same as additive) |

### Additive Primitives (no sketch needed)
`PartDesign::AdditiveBox`, `AdditiveCylinder`, `AdditiveSphere`, `AdditiveCone`, `AdditiveEllipsoid`, `AdditiveTorus`, `AdditivePrism`, `AdditiveWedge`

### Subtractive Primitives
`PartDesign::SubtractiveBox`, `SubtractiveCylinder`, `SubtractiveSphere`, `SubtractiveCone`, etc.

### Dress-Up (modify edges/faces, no sketch)
| Feature | Type String | Key Properties |
|---------|-------------|----------------|
| Fillet | `PartDesign::Fillet` | Base (edges/faces), Radius, UseAllEdges |
| Chamfer | `PartDesign::Chamfer` | Base, Size, ChamferType, Angle |
| Draft | `PartDesign::Draft` | Angle, NeutralPlane |
| Thickness | `PartDesign::Thickness` | Value, Mode, faces to open |

### Transformation (pattern features)
| Feature | Type String | Key Properties |
|---------|-------------|----------------|
| Mirrored | `PartDesign::Mirrored` | MirrorPlane, Originals |
| Linear Pattern | `PartDesign::LinearPattern` | Direction, Length, Occurrences |
| Polar Pattern | `PartDesign::PolarPattern` | Axis, Angle, Occurrences |
| MultiTransform | `PartDesign::MultiTransform` | Transformations, Originals |

### Datum/Helper Objects
| Object | Type String | Purpose |
|--------|-------------|---------|
| DatumPlane | `PartDesign::Plane` | Reference plane (avoids topological naming issues) |
| DatumLine | `PartDesign::Line` | Reference line |
| DatumPoint | `PartDesign::Point` | Reference point |
| ShapeBinder | `PartDesign::ShapeBinder` | External geometry reference |
| Boolean | `PartDesign::Boolean` | Fuse/Cut/Common between Bodies |

## Key Rules

- A Body must contain a single contiguous solid
- Features form a linear chain (no branching)
- Sketches must be closed profiles for Pad/Pocket/Revolution
- Fully constrained sketches (0 DoF) are best practice
- `doc.recompute()` must be called after modifications
- Face/edge numbering can change when earlier features change (topological naming problem)
- DatumPlanes are more stable references than faces
- Close sketch editing: `FreeCADGui.ActiveDocument.resetEdit()` (GUI only, not needed for API scripting)
