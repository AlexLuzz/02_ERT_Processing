import pygimli.meshtools as mt
import numpy as np
import pygimli as pg
import shutil
import tempfile
from pathlib import Path
from scipy.spatial import cKDTree

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

def build_mono2m_plc(df, layer_depth=2.5, depth=15.0, extension=10.0, 
                     markers=[2, 2], area_top=0.5, area_bottom=5.0, curved_bottom=True):
    """
    Helper: Builds the core layered polygons and fuses them with explicit area constraints.
    Prevents self-intersections and enforces correct boundary markers.
    """
    data = df.sort_values("X")
    x, z = data["X"].to_numpy(), data["Z"].to_numpy()

    # 1. Topography & Interface
    surface_pts = (
        [[x[0] - extension, z.max()]]
        + [[xi, zi] for xi, zi in zip(x, z)]
        + [[x[-1] + extension, z.min()]]
    )
    layer_pts = [[pt[0], pt[1] - layer_depth] for pt in surface_pts]

    # 2. Bottom Geometry (Anchored safely below the lowest point of the layer)
    z_bottom_ref = min(pt[1] for pt in layer_pts)

    if curved_bottom:
        x_start, x_end = layer_pts[0][0], layer_pts[-1][0]
        x_center = (x_start + x_end) / 2.0
        a = (x_end - x_start) / 2.0
        b = depth
        
        theta = np.linspace(np.pi, 2*np.pi, 30)
        # Drops 'b' meters down from the lowest point of the layer
        bottom_pts = [[x_center + a * np.cos(t), z_bottom_ref + b * np.sin(t)] for t in theta]
    else:
        bottom_pts = [
            [layer_pts[0][0], z_bottom_ref - depth],
            [layer_pts[-1][0], z_bottom_ref - depth]
        ]

    # 3. Create closed polygons
    poly_overburden = mt.createPolygon(
        surface_pts + layer_pts[::-1], 
        isClosed=True, worldMarker=True, area=area_top
    )
    
    poly_tailings = mt.createPolygon(
        layer_pts + bottom_pts[::-1], 
        isClosed=True, marker=markers[1], area=area_bottom
    )

    # 4. Fuse the Geometries
    # Because layer_pts is perfectly shared, PyGIMLi merges the nodes cleanly.
    plc = poly_overburden + poly_tailings

    # 5. Explicitly enforce Boundary Markers
    # 0 = Internal, -1 = Surface/Neumann, 1 = Subsurface/Mixed
    surf_x = [pt[0] for pt in surface_pts]
    surf_y = [pt[1] for pt in surface_pts]
    
    for b in plc.boundaries():
        # Only touch non-internal boundaries
        if b.marker() != 0:
            # Check if the boundary center matches the expected topography elevation
            expected_y = np.interp(b.center().x(), surf_x, surf_y)
            
            if b.center().y() >= expected_y - 1e-3:
                b.setMarker(-1)
            else:
                b.setMarker(1)

    # 6. Add sensor nodes for refinement
    for xi, zi in zip(x, z):
        plc.createNode([xi, zi], marker=99)
        
    return plc


def build_mono2m_meshes(df, layer_depth=2.5, depth=15.0, extension=10.0, 
                        area_top=0.5, area_bottom=5.0, quality=34,
                        add_boundary=True, bound_ext=50.0, bound_depth=50.0, 
                        start_markers=[10, 20], **kwargs):
    """
    Builds both the inversion mesh and the starting model mesh simultaneously 
    to ensure perfect spatial alignment.
    """
    # 1. Build both PLCs
    plc_inv = build_mono2m_plc(
        df, layer_depth, depth, extension, markers=[2, 2], 
        area_top=area_top, area_bottom=area_bottom)
    plc_start_model = build_mono2m_plc(
        df, layer_depth, depth, extension, markers=start_markers, 
        area_top=area_top, area_bottom=area_bottom)
    
    # 2. Generate meshes
    mesh_kwargs = {"quality": quality, "smooth": [10, 1], **kwargs}
    inv_mesh = mt.createMesh(plc_inv, **mesh_kwargs)
    start_model_mesh = mt.createMesh(plc_start_model, **mesh_kwargs)
    
    # 3. Append infinite boundaries if requested
    if add_boundary:
        inv_mesh = mt.appendTriangleBoundary(inv_mesh, marker=1, xbound=bound_ext, ybound=bound_depth)
        start_model_mesh = mt.appendTriangleBoundary(start_model_mesh, marker=1, xbound=bound_ext, ybound=bound_depth)
        
    return inv_mesh, start_model_mesh


def build_starting_model(mesh, para_domain, rhomap, default_res=100.0):
    """
    Maps resistivity values from a fine start mesh to the para_domain using a rhomap.
    Accepts rhomap as a dict {marker: res} or list of lists [[marker, res], ...].
    """
    markers = np.array(mesh.cellMarkers())
    mesh_res = np.full(len(markers), default_res, dtype=float)
    
    # Process rhomap flexibility (Dict or List of Lists)
    if isinstance(rhomap, dict):
        for marker, res in rhomap.items():
            mesh_res[markers == marker] = res
    elif isinstance(rhomap, (list, tuple, np.ndarray)):
        for marker, res in rhomap:
            mesh_res[markers == marker] = res

    # Spatial KDTree mapping
    mesh_centers = np.column_stack([pg.x(mesh.cellCenters()), pg.y(mesh.cellCenters())])
    para_centers = np.column_stack([pg.x(para_domain.cellCenters()), pg.y(para_domain.cellCenters())])

    tree = cKDTree(mesh_centers)
    _, nearest_mesh_idx = tree.query(para_centers)

    return mesh_res[nearest_mesh_idx]