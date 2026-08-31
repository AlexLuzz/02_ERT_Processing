import pygimli.meshtools as mt
import numpy as np
import pygimli as pg
import shutil
import tempfile
from pathlib import Path

def build_grid_mesh(x_min, x_max, y_min, y_max=0, dx=0.25, dy=0.25):
    """Creates a structured quadrilateral grid."""
    x = np.arange(x_min, x_max, dx)
    y = np.arange(y_min, y_max, dy)
    return mt.createGrid(x=x, y=y)

def build_unstructured_mesh(
    df,
    surface_offset=0.5,
    depth=10.0,
    extension=10.0,
    refine_dist=1.0,
    **kwargs,
):
    """
    Create an unstructured triangular mesh from electrode positions with 
    local refinement and a coarsened outer boundary.
    """
    data = df.sort_values("X")
    x = data["X"].to_numpy()
    z = data["Z"].to_numpy()

    surface = [[xi, zi + surface_offset] for xi, zi in zip(x, z)]
    boundary = surface + [
        [x[-1] + extension, z.min()], 
        [x[-1] + extension, z.min() - depth],
        [x[0] - extension, z.min() - depth],
        [x[0] - extension, z.max()]
    ]
    
    plc = mt.createPolygon(
        boundary, 
        isClosed=True, 
        addNodes=3, 
        interpolate="linear", 
        marker=1  # Explicitly mark the inner domain
    )

    # Mark all top surface boundaries with -1 (Neumann condition) for appendTriangleBoundary
    for b in plc.boundaries():
        # Any boundary edge resting in the upper section is treated as surface topography
        if b.center().y() > z.min():
            b.setMarker(-1)

    # Add electrodes and local refinement dummy nodes
    for xi, zi in zip(x, z):
        plc.createNode([xi, zi], marker=99)      # Main electrode
        plc.createNode([xi, zi - refine_dist])   # Force fine cells below
        plc.createNode([xi - refine_dist, zi])   # Force fine cells left
        plc.createNode([xi + refine_dist, zi])   # Force fine cells right


    # Apply distinct mesh areas: [inner_area, outer_area]
    mesh_kwargs = {
        "quality": 33,
        "area": kwargs.pop("area", 2.0), # [Core, Boundary]
        "smooth": [10, 1],
        **kwargs,
    }

    return mt.createMesh(plc, **mesh_kwargs)


def safe_mesh_save(mesh, target_path: Path | str) -> Path:
    """
    Saves a PyGIMLi mesh by bypassing Windows/C++ long path and accent limits.
    """
    target = Path(target_path)
    target_folder = target.parent

    # Generate a short temporary ASCII file path
    temp_dir = Path(tempfile.gettempdir())
    short_temp_path = temp_dir / target.name

    # Let PyGIMLi save to the safe path
    mesh.save(str(short_temp_path))

    # Create the deep target directory if it doesn't exist
    target_folder.mkdir(parents=True, exist_ok=True)

    # Let Python move it to the final destination (handles accents/long paths fine)
    shutil.move(str(short_temp_path), str(target))
    
    return target

def safe_mesh_load(source_path: Path | str):
    """
    Loads a PyGIMLi mesh bypassing Windows/C++ encoding and path limits.
    """
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Cannot find mesh at {source}")

    # Use TemporaryDirectory so it cleans up after loading
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / source.name
        
        # Python copies the file from the accented/deep path
        shutil.copy(source, temp_path)
        
        # PyGIMLi loads it safely from the short ASCII temp path
        mesh = pg.Mesh(str(temp_path))
        
    return mesh