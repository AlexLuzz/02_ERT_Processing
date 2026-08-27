import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union

import gmsh
import pandas as pd
from pygimli.meshtools import readGmsh


def build_gmsh_mesh(
    df: pd.DataFrame,
    surface_offset: float = 0.25,
    depth: float = 5.0,
    extension: float = 5.0,
    size_surface: float = 0.5,
    size_depth: float = 10.0,
    params: Optional[Dict[str, Any]] = None,
    out_path: Optional[Union[str, Path]] = None,
):
    """Build an unstructured X-Z mesh using Gmsh tailored for PyGIMLi.

    This function generates a mesh with a graded density: very fine at the 
    surface near the electrodes, expanding to become coarse at the outer 
    and bottom boundaries. 

    How to control mesh coarseness:
    -------------------------------
    In Gmsh, sizing parameters define the target length of triangle edges. 
    To make the mesh lighter (fewer elements), INCREASE these values.

    Args:
        df: Electrode geometry DataFrame with ``elec_number``, ``X``, ``Z``.
        surface_offset: Height above the highest electrode to build the domain.
        depth: Total depth below the lowest electrode.
        extension: Horizontal extension beyond the first and last electrodes.
        size_surface: Target triangle edge length near the electrodes. 
            - Example: 0.2 creates a very dense, heavy mesh.
            - Example: 0.5 to 1.0 creates a lighter, coarser mesh.
            - Rule of thumb: keep this smaller than your electrode spacing.
        size_depth: Target triangle edge length at the bottom boundary.
            - Example: 3.0 keeps the deep mesh relatively dense.
            - Example: 10.0 or 15.0 allows the mesh to become very coarse at depth.
        params: Optional Gmsh meshing parameters (algorithm, optimize, verbose).
        out_path: Base path to save the .msh and .bms files (no extension needed).

    Returns:
        pg.Mesh: Gmsh mesh imported into PyGIMLi.
    """
    params = params or {}

    # Sort by X to guarantee the first/last elements are the physical edges
    data = df.sort_values("X")
    x, z = data["X"].to_numpy(), data["Z"].to_numpy()
    x_min, x_max, z_min, z_max = x.min(), x.max(), z.min(), z.max()

    gmsh.initialize()
    gmsh.model.add("electrode_mesh")

    try:
        geo = gmsh.model.geo

        # Geometry
        elec_tags = [geo.addPoint(xi, zi, 0, size_surface) for xi, zi in zip(x, z)]
        
        # Tie extensions to the exact Z-level of the outermost electrodes
        p_tl = geo.addPoint(x_min - extension, z[0], 0, size_surface)
        p_tr = geo.addPoint(x_max + extension, z[-1], 0, size_surface)
        
        p_br = geo.addPoint(x_max + extension, z_min - depth, 0, size_depth)
        p_bl = geo.addPoint(x_min - extension, z_min - depth, 0, size_depth)

        surface = geo.addSpline(elec_tags)
        right, bottom, left = geo.addLine(p_tr, p_br), geo.addLine(p_br, p_bl), geo.addLine(p_bl, p_tl)
        top_left, top_right = geo.addLine(p_tl, elec_tags[0]), geo.addLine(elec_tags[-1], p_tr)

        loop = geo.addCurveLoop([top_left, surface, top_right, right, bottom, left])
        domain = geo.addPlaneSurface([loop])
        geo.synchronize()

        # Physical groups: -1 (surface), -2 (subsurface boundaries), 2 (domain), 99 (electrodes)
        gmsh.model.addPhysicalGroup(1, [top_left, surface, top_right], tag=-1)
        gmsh.model.addPhysicalGroup(1, [left, bottom, right], tag=-2)
        gmsh.model.addPhysicalGroup(2, [domain], tag=2)
        gmsh.model.addPhysicalGroup(0, elec_tags, tag=99)

        # Depth-dependent mesh sizing (Linear gradient from surface to depth)
        field = gmsh.model.mesh.field.add("MathEval")
        expr = f"{size_surface} + ({size_depth} - {size_surface}) * ((z - ({z_max + surface_offset})) / (-{depth - surface_offset}))"
        gmsh.model.mesh.field.setString(field, "F", expr)
        gmsh.model.mesh.field.setAsBackgroundMesh(field)

        # Generate mesh
        gmsh.option.setNumber("Mesh.Algorithm", params.get("algorithm", 6))
        gmsh.option.setNumber("Mesh.ElementOrder", params.get("element_order", 1))
        gmsh.option.setNumber("Mesh.Optimize", params.get("optimize", 1))
        gmsh.model.mesh.generate(2)

        # Set format for PyGIMLi compatibility
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)

        # I/O handling
        if out_path:
            p = Path(out_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            
            msh_file = str(p.with_suffix(".msh"))
            
            # Save ONLY the Gmsh format. PyGIMLi can read this directly later.
            gmsh.write(msh_file)
            mesh = readGmsh(msh_file, verbose=params.get("verbose", False))
            
        else:
            with tempfile.TemporaryDirectory() as tmp:
                msh_file = str(Path(tmp) / "mesh.msh")
                gmsh.write(msh_file)
                mesh = readGmsh(msh_file, verbose=params.get("verbose", False))

    finally:
        gmsh.finalize()

    return mesh