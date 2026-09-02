from src.mesh.pygimli_mesh_tools import build_mono2m_mesh_new, build_mono2m_mesh_old, build_unstructured_mesh, build_mono2m_mesh
from src.visualization.basic_plotting import plot_array_on_mesh, extract_polygons, plot_electrodes
import matplotlib.pyplot as plt
from src.loaders.ert_loading_tools import load_geometry
from config.paths import ProjectPaths
import pygimli as pg
import numpy as np

def test_build_MCM_M2m():
    paths = ProjectPaths(user='AQ96560')            
    geom_mono2m = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, params={"absolute_pos": True, 
                                                                  'inverse_order': False,
                                                                  "projection": {"type": "distance", "output_axis": "X"}})

    mesh = build_mono2m_mesh_new(geom_mono2m, area=2, quality=32)
    print(np.unique(mesh.cellMarkers()))
    res_map = {
    1: 500,   # layer
    2: 100,  # background
    }

    start_model = pg.solver.parseMapToCellArray(res_map, mesh)

    mesh_polygons = extract_polygons(mesh)
    ax, coll = plot_array_on_mesh(mesh_polygons, start_model, edgecolor='black', alpha=0.2)
    
    plot_electrodes(geom_mono2m, ax)
    ax, cb = pg.show(mesh, res=res_map, markers=True, showMesh=True)
    ax.plot(geom_mono2m['X'].values, geom_mono2m['Z'].values, "mx")
    print(f"Mesh has {mesh.cellCount()} cells and {mesh.nodeCount()} nodes.")

if __name__ == "__main__":

    test_build_MCM_M2m()
    plt.show()

