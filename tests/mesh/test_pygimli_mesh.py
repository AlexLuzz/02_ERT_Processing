from src.mesh.pygimli_mesh_tools import build_grid_mesh, build_unstructured_mesh
from src.visualization.basic_plotting import plot_array_on_mesh, extract_polygons, plot_electrodes
import matplotlib.pyplot as plt
from src.loaders.loading_tools import load_geometry
from config.paths import ProjectPaths

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

def test_build_MCM_M2m():
    paths = ProjectPaths(user='alexi')            
    bb_geom = load_geometry(paths.MCM_MONO2M_ELECS_POS,
                            params={"absolute_pos": True, 
                                    "inverse_order": False,
                                    "projection": {"type": "distance", "output_axis": "X"}})

    mesh = build_unstructured_mesh(bb_geom, area=2, quality=34)
    mesh_polygons = extract_polygons(mesh)
    ax, coll = plot_array_on_mesh(mesh_polygons, edgecolor='black', alpha=0.2)
    plot_electrodes(bb_geom, ax)
    print(f"Mesh has {mesh.cellCount()} cells and {mesh.nodeCount()} nodes.")

if __name__ == "__main__":
    #test_build_grid_mesh()
    #test_build_MCM_GEO()
    test_build_MCM_M2m()
    plt.show()

