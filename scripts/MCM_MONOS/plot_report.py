from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import *
from scripts.MCM_MONOS.mesh_building.MONO_gmsh import build_gmsh_layered
from src.mesh.gmesh_tools import *
from src.processing.inversion.ert_processor import ERTProcessor
from src.loaders.ert_loader import ERTLoader
from src.visualization.inversion_data_report import InversionDataReport

def run_MONO1M():
    paths = ProjectPaths(user='AQ96560', project_name='MCM_MONO1M_Single') 
        
    geom = load_geometry(paths.MCM_MONO1M_ELECS_POS_TRUE, params={
        "absolute_pos": True, 
        'inverse_order': False,
        "projection": {"type": "distance", "output_axis": "X"}
    })

    mesh = build_gmsh_layered(geom, size_surface=0.3, size_interface=1.0, size_depth=12.0,
                                interface_depth=5.0, extension=10.0, depth=30.0)

    processor = ERTProcessor(mesh=mesh, electrode_positions=geom)
    paraDomain = processor.paraDomain

    results = {
    "model": [],
    "response": [],
    "params": {},
    }
    data = processor.load(file_path=paths.PROJECTS_DIR / "MCM_MONO1M_Single" / "20260906_0317" / "results.h5")

    for key, value in data[0].items():
        if key.endswith("_model"):
            results["model"].append(value)
        elif key.endswith("_response"):
            results["response"].append(value)

    results["params"] = data[1]

    InversionDataReport.print(
        folder_path=paths.PROJECTS_DIR / "MCM_MONO1M_Single" ,
        results_list=results,
        elec_pos=geom,
        mesh=mesh,
        paradomain=paraDomain,
        logs=processor.memory_handler.logs
    )

if __name__ == "__main__":
    run_MONO1M()