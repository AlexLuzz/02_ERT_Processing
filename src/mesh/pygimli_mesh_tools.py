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

def build_mono2m_mesh_old(
    df, surface_offset=0.3, depth=8.0, extension=10.0,
    refine_dist=0.5, layer_depth=2.0, **kwargs
):
    data = df.sort_values("X")
    x, z = data["X"].to_numpy(), data["Z"].to_numpy()

    surface = (
        [[x[0] - extension, z.max()]]
        + [[xi, zi + surface_offset] for xi, zi in zip(x, z)]
        + [[x[-1] + extension, z.min()]]
    )
    bottom = [
        [x[-1] + extension, z.min() - depth],
        [x[0] - extension, z.min() - depth]
    ]

    plc = mt.createPolygon(surface + bottom, isClosed=True, marker=10)

    layer_boundary = [[xi, zi - layer_depth] for xi, zi in surface]
    plc += mt.createPolygon(
        surface + layer_boundary,
        isClosed=True,
        marker=20
    )

    for b in plc.boundaries():
        if b.center().y() > z.min():
            b.setMarker(-1)

    for xi, zi in zip(x, z):
        plc.createNode([xi, zi], marker=99)
        plc.createNode([xi, zi - refine_dist])
        plc.createNode([xi - refine_dist, zi])
        plc.createNode([xi + refine_dist, zi])

    mesh_kwargs = {
        "quality": 33,
        "area": kwargs.pop("area", 2.0),
        "smooth": [10, 1],
        **kwargs,
    }

    return mt.createMesh(plc, **mesh_kwargs)

def build_mono2m_mesh(
    df, depth=8.0, extension=10.0,
    refine_dist=0.5, layer_depth=2.5, area_top=0.5, area_bottom=5.0,
    save_path=None, **kwargs
):
    data = df.sort_values("X")
    x, z = data["X"].to_numpy(), data["Z"].to_numpy()

    # 1. Define coordinate lists based on topography
    surface_pts = (
        [[x[0] - extension, z.max()]]
        + [[xi, zi] for xi, zi in zip(x, z)]
        + [[x[-1] + extension, z.min()]]
    )
   
    # Layer follows the topography precisely
    layer_pts = [[pt[0], pt[1] - layer_depth] for pt in surface_pts]
   
    bottom_pts = [
        [surface_pts[-1][0], z.min() - depth],
        [surface_pts[0][0], z.min() - depth]
    ]

    world = mt.createPolygon(surface_pts + bottom_pts, isClosed=True, marker=1)
    tailings = mt.createPolygon(layer_pts + bottom_pts, isClosed=False, marker=2)

    # 7. Mesh generation
    mesh_kwargs = {
        "quality": 33,
        "smooth": [10, 1],
        **kwargs,
    }
    
    mesh = mt.createMesh(world + tailings, **mesh_kwargs)
   
    # 8. Save if a path is provided (.vtk or .bms)
    if save_path:
        mesh.save(save_path)
       
    return mesh 

def build_mono2m_mesh_new(
    df,
    depth=8.0,
    extension=10.0,
    refine_dist=0.5,
    layer_depth=2.5,
    area_top=0.5,
    area_bottom=5.0,
    save_path=None,
    **kwargs,
):
    # 1. Extract unique physical electrode positions
    sensors = df[["X", "Z"]].drop_duplicates().sort_values("X")
    x = sensors["X"].to_numpy()
    z = sensors["Z"].to_numpy()

    # 2. Define coordinate layers
    surface_pts = (
        [[x[0] - extension, z[0]]]
        + [[xi, zi] for xi, zi in zip(x, z)]
        + [[x[-1] + extension, z[-1]]]
    )
    interface_pts = [[pt[0], pt[1] - layer_depth] for pt in surface_pts]
    bottom_pts = [
        [surface_pts[-1][0], z.min() - depth],
        [surface_pts[0][0], z.min() - depth],
    ]

    plc = pg.Mesh(2)

    # 3. Create Nodes
    surf_nodes = [plc.createNode(surface_pts[0])]
    for xi, zi in zip(x, z):
        surf_nodes.append(plc.createNode([xi, zi], marker=99))
    surf_nodes.append(plc.createNode(surface_pts[-1]))

    inter_nodes = [plc.createNode(pt) for pt in interface_pts]
    bot_right = plc.createNode(bottom_pts[0])
    bot_left = plc.createNode(bottom_pts[1])

    # 4. Create Edges
    # Surface gets -1
    for i in range(len(surf_nodes) - 1):
        plc.createEdge(surf_nodes[i], surf_nodes[i+1], marker=-1)
        
    # Internal interface gets 0 (transparent)
    for i in range(len(inter_nodes) - 1):
        plc.createEdge(inter_nodes[i], inter_nodes[i+1], marker=0)

    # Outer edges of the core box MUST be 0 (transparent) so current flows into the buffer
    plc.createEdge(surf_nodes[-1], inter_nodes[-1], marker=0)
    plc.createEdge(inter_nodes[-1], bot_right, marker=0)
    plc.createEdge(bot_right, bot_left, marker=0)
    plc.createEdge(bot_left, inter_nodes[0], marker=0)
    plc.createEdge(inter_nodes[0], surf_nodes[0], marker=0)

    # 5. Region Markers
    mid_idx = len(surface_pts) // 2
    x_mid = surface_pts[mid_idx][0]
    
    z_mid_top = (surface_pts[mid_idx][1] + interface_pts[mid_idx][1]) / 2.0
    plc.addRegionMarker([x_mid, z_mid_top], marker=1, area=area_top)
    
    z_mid_bot = (interface_pts[mid_idx][1] + bottom_pts[0][1]) / 2.0
    plc.addRegionMarker([x_mid, z_mid_bot], marker=2, area=area_bottom)

    # 6. Local Refinement
    for xi, zi in zip(x, z):
        plc.createNode([xi, zi - refine_dist])

    # 7. Append the Far-Field Background Buffer
    # This creates Region 1. PyGIMLi will sacrifice this region and leave 10 and 20 alone.
    plc = mt.appendTriangleBoundary(
        plc, 
        marker=0, 
        xbound=extension * 2, 
        ybound=depth * 2, 
        isSubSurface=True 
    )

    # 8. Mesh generation
    mesh_kwargs = {
        "quality": 33,
        "area": kwargs.pop("area", 2.0),
        "smooth": [10, 1],
        **kwargs,
    }
    
    mesh = mt.createMesh(plc, **mesh_kwargs)

    if save_path:
        mesh.save(str(save_path))

    return mesh
    
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

def build_starting_model_debug(mesh, para_domain, default_res=100.0):
    """
    Maps resistivity values with diagnostic prints to track array states.
    """
    print("\n--- STARTING MODEL DIAGNOSTICS ---")
    
    # 1. Check the original markers
    markers = np.array(mesh.cellMarkers())
    print(f"1. Total cells in original mesh: {len(markers)}")
    print(f"2. Unique markers found in original mesh: {np.unique(markers)}")
    print(f"   -> Count of marker 1 (Overburden): {np.sum(markers == 1)}")
    print(f"   -> Count of marker 2 (Tailings): {np.sum(markers == 2)}")
    
    mesh_res = np.select(
        [markers == 1, markers == 2], 
        [1000.0, 20.0], 
        default=default_res
    )
    print(f"3. Unique resistivities after mapping: {np.unique(mesh_res)}")

    # 2. Check spatial alignment
    mesh_centers = np.column_stack([pg.x(mesh.cellCenters()), pg.y(mesh.cellCenters())])
    para_centers = np.column_stack([pg.x(para_domain.cellCenters()), pg.y(para_domain.cellCenters())])
    
    print(f"4. Original mesh X bounds: {mesh_centers[:,0].min():.1f} to {mesh_centers[:,0].max():.1f}")
    print(f"   Original mesh Y bounds: {mesh_centers[:,1].min():.1f} to {mesh_centers[:,1].max():.1f}")
    print(f"5. ParaDomain X bounds:    {para_centers[:,0].min():.1f} to {para_centers[:,0].max():.1f}")
    print(f"   ParaDomain Y bounds:    {para_centers[:,1].min():.1f} to {para_centers[:,1].max():.1f}")

    # 3. Check the spatial query
    tree = cKDTree(mesh_centers)
    distances, nearest_mesh_idx = tree.query(para_centers)
    
    print(f"6. Max distance to nearest fine cell: {distances.max():.2f} meters")
    print(f"   Mean distance to nearest fine cell: {distances.mean():.2f} meters")

    # 4. Final output check
    start_model = mesh_res[nearest_mesh_idx]
    print(f"7. Final start_model unique values: {np.unique(start_model)}")
    print("----------------------------------\n")
    
    return start_model

def build_starting_model(mesh, para_domain, default_res=100.0):
    """
    Maps resistivity values by querying the fine marked mesh from the coarse para_domain.
    Overburden (marker 10) -> 1000.0 Ohm.m
    Tailings (marker 20) -> 20.0 Ohm.m
    """
    from scipy.spatial import cKDTree
    # 1. Extract markers and assign resistivity values to the original fine mesh
    markers = np.array(mesh.cellMarkers())
    mesh_res = np.select(
        [markers == 10, markers == 20], 
        [1000.0, 20.0], 
        default=default_res
    )

    # 2. Extract spatial coordinates
    mesh_centers = np.column_stack([pg.x(mesh.cellCenters()), pg.y(mesh.cellCenters())])
    para_centers = np.column_stack([pg.x(para_domain.cellCenters()), pg.y(para_domain.cellCenters())])

    # 3. THE FIX: Build the tree on the FINE mesh, and query from the COARSE mesh
    tree = cKDTree(mesh_centers)
    _, nearest_mesh_idx = tree.query(para_centers)

    # 4. Every para_domain cell instantly adopts the value of the nearest fine mesh cell
    start_model = mesh_res[nearest_mesh_idx]
    
    return start_model