import pygimli.meshtools as mt
import numpy as np

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
        [x[-1] + extension, z.min() - depth],
        [x[0] - extension, z.min() - depth]
    ]
    
    plc = mt.createPolygon(
        boundary, 
        isClosed=True, 
        addNodes=3, 
        interpolate="spline", 
        marker=1  # Explicitly mark the inner domain
    )

    # Mark all top surface boundaries with -1 (Neumann condition) for appendTriangleBoundary
    y_cutoff = z.min() - depth * 0.5
    for b in plc.boundaries():
        # Any boundary edge resting in the upper section is treated as surface topography
        if b.center().y() > y_cutoff:
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