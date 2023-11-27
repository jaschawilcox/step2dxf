import os
import argparse
from OCC.Extend.DataExchange import read_step_file
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.TopoDS import topods_Face
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop_SurfaceProperties
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.BRepTools import breptools_UVBounds
from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_WIRE
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.GeomAbs import GeomAbs_Line

from OCC.Display.SimpleGui import init_display
# from OCC.Core.Quantity import Quantity_NOC_RED
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import AIS_Shape
# from OCC.Core.Aspect import Aspect_TOM_NONE

from math import isclose
import ezdxf

import math
from math import degrees
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Ax1, gp_Ax2, gp_Ax3, gp_Trsf, gp_Dir
from OCC.Core.TopoDS import topods
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

def parse_arguments():
    """
    Parses command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Process a STEP file to find faces with specified thickness.')
    parser.add_argument('step_file', type=str, help='Path to the STEP file')
    parser.add_argument('-t', '--thickness', type=float, default=6, help='Thickness to find (default: 6)')
    return parser.parse_args()

def find_faces_with_thickness(step_filename, thickness, min_area=300, tolerance=1e-6):
    """
    Finds faces in a STEP file with a specified thickness.

    Args:
        step_filename (str): Path to the STEP file.
        thickness (float): Thickness to search for.
        min_area (float): Minimum area of faces to consider.
        tolerance (float): Tolerance for comparing thicknesses.

    Returns:
        list: List of faces with specified thickness.
    """
    print(f"Reading STEP file: {step_filename}")
    shape = read_step_file(step_filename)

    # Collect face data in the first pass, including their areas
    faces = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = topods_Face(exp.Current())
        surf = BRepAdaptor_Surface(face)
        if surf.GetType() == 0:
            # Calculate the face area
            props = GProp_GProps()
            brepgprop_SurfaceProperties(face, props)
            area = props.Mass()
            if area >= min_area:
                faces.append({
                    "face": face,
                    "normal": surf.Plane().Axis().Direction(),
                    "area": area,
                    "processed": False
                })
        exp.Next()

    # Find plates with the specified thickness
    plates = []
    for i, data in enumerate(faces):
        if data["processed"]:
            continue
        for j, other_data in enumerate(faces):
            if i == j or other_data["processed"]:
                continue
            if data["normal"].IsParallel(other_data["normal"], tolerance):
                dist_shape_shape = BRepExtrema_DistShapeShape(data["face"], other_data["face"])
                face_thickness = dist_shape_shape.Value()
                if isclose(face_thickness, thickness, rel_tol=tolerance):
                    plates.append(data["face"])
                    data["processed"] = other_data["processed"] = True
                    print(f"Found face pair with thickness {thickness}: Faces {i+1} and {j+1}, Area: {data['area']}")
                    break

    if not plates:
        print("No plates found with the specified thickness.")
    return plates

def get_face_centroid(face):
    """
    Calculates the centroid of a given face.

    Args:
        face (TopoDS_Face): The face whose centroid is to be calculated.

    Returns:
        gp_Pnt: The centroid of the face.
    """
    props = GProp_GProps()
    brepgprop_SurfaceProperties(face, props)
    return props.CentreOfMass()

def faces_are_equal(face1, face2, thickness, tolerance=1e-6):
    """
    Determines if two faces are equal based on their centroids and a specified thickness.

    Args:
        face1 (TopoDS_Face): The first face to compare.
        face2 (TopoDS_Face): The second face to compare.
        thickness (float): Expected thickness between faces.
        tolerance (float): Tolerance for comparison.

    Returns:
        bool: True if faces are considered equal, False otherwise.
    """
    centroid1 = get_face_centroid(face1)
    centroid2 = get_face_centroid(face2)
    
    distance = centroid1.Distance(centroid2)
    max_distance = 1.01 * thickness # within 1% of thickness
    
    return isclose(distance, thickness, rel_tol=tolerance) and distance <= max_distance

def angle_between_vectors(vec1, vec2):
    """
    Calculates the angle between two vectors.

    Args:
        vec1 (gp_Vec): The first vector.
        vec2 (gp_Vec): The second vector.

    Returns:
        float: Angle in radians between the two vectors.
    """
    dot_product = vec1.Dot(vec2)
    magnitude = vec1.Magnitude() * vec2.Magnitude()
    angle = math.acos(dot_product / magnitude)
    return angle

def export_face_to_dxf(face, output_filename):
    """
    Exports a face to a DXF file.

    Args:
        face (TopoDS_Face): The face to be exported.
        output_filename (str): Path for the output DXF file.
    """
    surf = BRepAdaptor_Surface(face)
    plane = surf.Plane()
    normal = gp_Vec(plane.Axis().Direction())

    z_axis = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))
    z_axis_vec = gp_Vec(z_axis.Direction())
    rotation_angle = angle_between_vectors(normal, z_axis_vec)

    if not normal.IsParallel(z_axis_vec, 1e-6):
        rotation_axis = normal.Crossed(z_axis_vec).Normalized()
        rotation_axis_dir = gp_Dir(rotation_axis)

        trsf = gp_Trsf()
        trsf.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), rotation_axis_dir), rotation_angle)
        face_transform = BRepBuilderAPI_Transform(face, trsf)
        face_transform.Build()
        face_transformed = face_transform.Shape()
    else:
        face_transformed = face

    doc = ezdxf.new()
    msp = doc.modelspace()

    wire_exp = TopExp_Explorer(face_transformed, TopAbs_WIRE)
    while wire_exp.More():
        wire = wire_exp.Current()
        edge_exp = TopExp_Explorer(wire, TopAbs_EDGE)
        while edge_exp.More():
            edge = edge_exp.Current()
            curve = BRepAdaptor_Curve(edge)

            if curve.GetType() == GeomAbs_Line:
                p1 = curve.Value(curve.FirstParameter())
                p2 = curve.Value(curve.LastParameter())
                msp.add_line((p1.X(), p1.Y()), (p2.X(), p2.Y()))
            else:
                prev_point = None
                for i in range(100):
                    u = curve.FirstParameter() + i / 99 * (curve.LastParameter() - curve.FirstParameter())
                    pnt = curve.Value(u)
                    if prev_point is not None:
                        msp.add_line((prev_point.X(), prev_point.Y()), (pnt.X(), pnt.Y()))
                    prev_point = pnt

            edge_exp.Next()
        wire_exp.Next()

    doc.saveas(output_filename)

def is_face_rectangle(face):
    """
    Determines if a given face is a rectangle.

    Args:
        face (TopoDS_Face): The face to check.

    Returns:
        bool: True if the face is a rectangle, False otherwise.
    """
    edge_exp = TopExp_Explorer(face, TopAbs_EDGE)
    edge_count = 0
    while edge_exp.More():
        edge_count += 1
        edge_exp.Next()

    return edge_count == 4

def export_faces_to_dxf(faces, output_folder, thickness, min_area):
    """
    Exports a list of faces to DXF files.

    Args:
        faces (list of TopoDS_Face): Faces to be exported.
        output_folder (str): Directory to store the DXF files.
        thickness (float): Thickness used to filter faces.
        min_area (float): Minimum area used to filter faces.
    """
    unique_faces = []
    
    for face in faces:
        is_duplicate = False
        for unique_face in unique_faces:
            if faces_are_equal(face, unique_face, thickness):
                is_duplicate = True
                break

        if not is_duplicate:
            unique_faces.append(face)

    for i, face in enumerate(unique_faces):
        props = GProp_GProps()
        brepgprop_SurfaceProperties(face, props)
        area = props.Mass()

        if area >= min_area and not is_face_rectangle(face):
            output_filename = os.path.join(output_folder, f"face_{i}.dxf")
            print(f"Exporting face {i + 1} to DXF file: {output_filename}")
            export_face_to_dxf(face, output_filename)
        else:
            print(f"Skipping face {i + 1} due to area below the minimum threshold or because it's a rectangle")
   
def export_image_with_highlighted_faces(shape, faces_to_highlight, output_filename, display, fit_all=True):
    """
    Exports an image with certain faces highlighted.

    Args:
        shape (TopoDS_Shape): The overall shape to display.
        faces_to_highlight (list of TopoDS_Face): Faces to be highlighted.
        output_filename (str): Path for the output image file.
        display (OCC.Display.SimpleGui.Display3d): Display object for rendering.
        fit_all (bool): Whether to fit the view to all objects.
    """
    # Clear the previous display context
    display.Context.RemoveAll(False)

    # Display the shape
    ais_shape = display.DisplayShape(shape, update=True)

    # Highlight faces if needed
    if faces_to_highlight:
        red_color = Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB)  # RGB red
        for face in faces_to_highlight:
            ais_face = AIS_Shape(face)
            display.Context.Display(ais_face, False)
            display.Context.SetColor(ais_face, red_color, False)
            display.Context.SetTransparency(ais_face, 0.0, False)

    # Update the view and save the rendering to a file
    display.View_Iso()
    if fit_all:
        display.FitAll()
    display.View.Dump(output_filename)

if __name__ == "__main__":
    args = parse_arguments()

    step_filename = args.step_file
    thickness_to_find = args.thickness
    # step_filename = "sample1.step"  # Replace with the path to your STEP file
    # thickness_to_find = 6  # Replace with the thickness you want to find
    min_area = 300.0
    output_folder = "output_dxf"

    # Read the STEP file
    shape = read_step_file(step_filename)

    # Initialize the 3D display
    display, start_display, add_menu, add_function_to_menu = init_display()

    # Find the faces with the specified thickness
    faces = find_faces_with_thickness(step_filename, thickness_to_find)

    # Export image with highlighted faces
    export_image_with_highlighted_faces(shape, faces, "output_with_highlight.png", display)

    # Export image without highlighted faces
    export_image_with_highlighted_faces(shape, [], "output_without_highlight.png", display)


    # Export the faces to DXF files
    os.makedirs(output_folder, exist_ok=True)
    export_faces_to_dxf(faces, output_folder, thickness_to_find, min_area)

