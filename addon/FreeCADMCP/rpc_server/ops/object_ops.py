import FreeCAD
import ObjectsFem


def create_document_gui(name):
    doc = FreeCAD.newDocument(name)
    doc.recompute()
    FreeCAD.Console.PrintMessage(f"Document '{name}' created via RPC.\n")
    return True


def create_object_gui(doc_name, obj, set_object_property):
    doc = FreeCAD.getDocument(doc_name)
    if doc:
        try:
            if obj.type == "Fem::FemMeshGmsh" and obj.analysis:
                from femmesh.gmshtools import GmshTools

                res = getattr(doc, obj.analysis).addObject(ObjectsFem.makeMeshGmsh(doc, obj.name))[0]
                if "Part" in obj.properties:
                    target_obj = doc.getObject(obj.properties["Part"])
                    if target_obj:
                        res.Part = target_obj
                    else:
                        raise ValueError(f"Referenced object '{obj.properties['Part']}' not found.")
                    del obj.properties["Part"]
                else:
                    raise ValueError("'Part' property not found in properties.")

                for param, value in obj.properties.items():
                    if hasattr(res, param):
                        setattr(res, param, value)
                doc.recompute()

                gmsh_tools = GmshTools(res)
                gmsh_tools.create_mesh()
                FreeCAD.Console.PrintMessage(
                    f"FEM Mesh '{res.Name}' generated successfully in '{doc_name}'.\n"
                )
            elif obj.type.startswith("Fem::"):
                fem_make_methods = {
                    "MaterialCommon": ObjectsFem.makeMaterialSolid,
                    "AnalysisPython": ObjectsFem.makeAnalysis,
                }
                obj_type_short = obj.type.split("::")[1]
                method_name = "make" + obj_type_short
                make_method = fem_make_methods.get(obj_type_short, getattr(ObjectsFem, method_name, None))

                if callable(make_method):
                    res = make_method(doc, obj.name)
                    set_object_property(doc, res, obj.properties)
                    FreeCAD.Console.PrintMessage(
                        f"FEM object '{res.Name}' created with '{method_name}'.\n"
                    )
                else:
                    raise ValueError(f"No creation method '{method_name}' found in ObjectsFem.")
                if obj.type != "Fem::AnalysisPython" and obj.analysis:
                    getattr(doc, obj.analysis).addObject(res)
            else:
                res = doc.addObject(obj.type, obj.name)
                set_object_property(doc, res, obj.properties)
                FreeCAD.Console.PrintMessage(
                    f"{res.TypeId} '{res.Name}' added to '{doc_name}' via RPC.\n"
                )

            doc.recompute()
            return True
        except Exception as e:
            return str(e)
    else:
        FreeCAD.Console.PrintError(f"Document '{doc_name}' not found.\n")
        return f"Document '{doc_name}' not found.\n"


def edit_object_gui(doc_name, obj, set_object_property):
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        FreeCAD.Console.PrintError(f"Document '{doc_name}' not found.\n")
        return f"Document '{doc_name}' not found.\n"

    obj_ins = doc.getObject(obj.name)
    if not obj_ins:
        FreeCAD.Console.PrintError(f"Object '{obj.name}' not found in document '{doc_name}'.\n")
        return f"Object '{obj.name}' not found in document '{doc_name}'.\n"

    try:
        if hasattr(obj_ins, "References") and "References" in obj.properties:
            refs = []
            for ref_name, face in obj.properties["References"]:
                ref_obj = doc.getObject(ref_name)
                if ref_obj:
                    refs.append((ref_obj, face))
                else:
                    raise ValueError(f"Referenced object '{ref_name}' not found.")
            obj_ins.References = refs
            FreeCAD.Console.PrintMessage(
                f"References updated for '{obj.name}' in '{doc_name}'.\n"
            )
            del obj.properties["References"]

        set_object_property(doc, obj_ins, obj.properties)
        doc.recompute()
        FreeCAD.Console.PrintMessage(f"Object '{obj.name}' updated via RPC.\n")
        return True
    except Exception as e:
        return str(e)


def delete_object_gui(doc_name, obj_name):
    doc = FreeCAD.getDocument(doc_name)
    if not doc:
        FreeCAD.Console.PrintError(f"Document '{doc_name}' not found.\n")
        return f"Document '{doc_name}' not found.\n"

    try:
        doc.removeObject(obj_name)
        doc.recompute()
        FreeCAD.Console.PrintMessage(f"Object '{obj_name}' deleted via RPC.\n")
        return True
    except Exception as e:
        return str(e)

