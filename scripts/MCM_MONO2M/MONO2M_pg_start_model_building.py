from src.mesh.pygimli_mesh_tools import *
from src.mesh.gmesh_tools import *
from src.visualization.basic_plotting import plot_array_on_mesh, extract_polygons, plot_electrodes
import matplotlib.pyplot as plt
from src.loaders.ert_loading_tools import load_geometry
from config.paths import ProjectPaths
import pygimli as pg
import numpy as np

def test_build_MCM_M2m():
    paths = ProjectPaths(user='alexi')            
    geom_mono2m = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, params={"absolute_pos": True, 
                                                                  'inverse_order': False,
                                                                  "projection": {"type": "distance", "output_axis": "X"}})
    a  = False
    if a:
        mesh, start_model_mesh = build_mono2m_meshes(
            geom_mono2m, 
            area_top=0.3, 
            area_bottom=2.0, 
            quality=34,
            add_boundary=True, 
            extension=10.0,
            depth=15.0,
        )
    mesh = build_gmsh_mono2m(geom_mono2m, size_surface=0.2, size_depth=3.0)

    ax, cb = pg.show(mesh, markers=True, showMesh=True)

    ax.plot(geom_mono2m['X'].values, geom_mono2m['Z'].values, "mx")
    print(f"Mesh has {mesh.cellCount()} cells and {mesh.nodeCount()} nodes.")

if __name__ == "__main__":

    test_build_MCM_M2m()
    plt.show()

