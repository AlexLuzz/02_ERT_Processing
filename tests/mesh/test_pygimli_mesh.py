from src.mesh.pygimli_mesh_tools import build_grid_mesh, build_unstructured_mesh
from src.visualization.basic_plotting import plot_array_on_mesh, extract_polygons, plot_electrodes
import matplotlib.pyplot as plt
from src.loaders.loading_tools import load_geometry
from config.paths import ProjectPaths
import gmsh
import pygimli as pg

def test_build_grid_mesh():
    grid = build_grid_mesh(x_min=0, x_max=10, y_min=-10)
    grid_polygons = extract_polygons(grid)
    ax, coll = plot_array_on_mesh(grid_polygons, edgecolor='black', facecolor='none', alpha=0.5)

def test_build_unstructured_mesh():
    electrode_x = [0, 2, 4, 6, 8]
    electrode_y = [0, 0, 0, 0, 0]
    mesh = build_unstructured_mesh(electrode_x, electrode_y)
    mesh_polygons = extract_polygons(mesh)
    ax, coll = plot_array_on_mesh(mesh_polygons, edgecolor='black', facecolor='none', alpha=0.2)

def test_build_MCM_GEO():
    paths = ProjectPaths(user='alexi')            
    bb_geom = load_geometry(paths.MCM_GEO_ELECS_POS,
                            params={"absolute_pos": True, 
                                    "inverse_order": True,
                                    "projection": {"type": "best_fit", "output_axis": "X"}})

    mesh = build_unstructured_mesh(bb_geom)
    mesh_polygons = extract_polygons(mesh)
    ax, coll = plot_array_on_mesh(mesh_polygons, edgecolor='black', alpha=0.2)
    plot_electrodes(bb_geom, ax)
    print(f"Mesh has {mesh.cellCount()} cells and {mesh.nodeCount()} nodes.")

def safe_mesh_save(mesh, target_path):
    """
    Saves a PyGIMLi mesh by bypassing Windows/C++ long path limits.
    """
    import shutil
    import tempfile
    from pathlib import Path
    target = Path(target_path)
    
    # 1. Generate a short temporary file path (e.g., C:/Users/name/AppData/Local/Temp/MCM_MONO2M.bms)
    temp_dir = Path(tempfile.gettempdir())
    short_temp_path = temp_dir / target.name
    
    # 2. Let PyGIMLi save to the short path
    mesh.save(str(short_temp_path.as_posix()))
    
    # 3. Create your deep target directories if they don't exist
    target.parent.mkdir(parents=True, exist_ok=True)
    
    # 4. Let Python move it to the deep OneDrive folder
    shutil.move(str(short_temp_path), str(target))

def test_build_MCM_M2m():
    paths = ProjectPaths(user='alexi')            
    bb_geom = load_geometry(paths.MCM_MONO2M_ELECS_POS,
                            params={"absolute_pos": True, 
                                    "inverse_order": False,
                                    "projection": {"type": "distance", "output_axis": "X"}})

    mesh = build_unstructured_mesh(bb_geom, area=2, quality=34)
    mesh_polygons = extract_polygons(mesh)
    ax, coll = plot_array_on_mesh(mesh_polygons, edgecolor='black', alpha=0.2)

    mesh_path_str = str(paths.OUTPUT_DIR / 'MCM_MONO2M.bms').replace('\\', '/')
    safe_mesh_save(mesh, mesh_path_str)
    
    #plot_electrodes(bb_geom, ax)
    #ax, cb = pg.show(mesh, markers=True, showMesh=True)
    #ax.plot(bb_geom['X'].values, bb_geom['Z'].values, "mx")
    print(f"Mesh has {mesh.cellCount()} cells and {mesh.nodeCount()} nodes.")

if __name__ == "__main__":
    #test_build_grid_mesh()
    #test_build_MCM_GEO()
    test_build_MCM_M2m()
    plt.show()

