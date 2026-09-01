from src.mesh.pygimli_mesh_tools import build_unstructured_mesh, safe_mesh_save
from src.visualization.basic_plotting import plot_array_on_mesh, extract_polygons, plot_electrodes
import matplotlib.pyplot as plt
from src.loaders.ert_loading_tools import load_geometry
from config.paths import ProjectPaths
import pygimli as pg

def test_build_MCM_M2m():
    paths = ProjectPaths(user='AQ96560')            
    geom_mono2m = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, params={"absolute_pos": True, 
                                                                  'inverse_order': False,
                                                                  "projection": {"type": "distance", "output_axis": "X"}})

    mesh = build_unstructured_mesh(geom_mono2m, area=1, quality=34)
    mesh_polygons = extract_polygons(mesh)
    ax, coll = plot_array_on_mesh(mesh_polygons, edgecolor='black', alpha=0.2)

    mesh_path_str = str(paths.OUTPUT_DIR / 'MCM_MONO2M.bms').replace('\\', '/')
    safe_mesh_save(mesh, mesh_path_str)
    
    plot_electrodes(geom_mono2m, ax)
    ax, cb = pg.show(mesh, markers=True, showMesh=True)
    ax.plot(geom_mono2m['X'].values, geom_mono2m['Z'].values, "mx")
    print(f"Mesh has {mesh.cellCount()} cells and {mesh.nodeCount()} nodes.")

if __name__ == "__main__":
    #test_build_grid_mesh()
    #test_build_MCM_GEO()
    test_build_MCM_M2m()
    plt.show()

