from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from src.processing.inversion.pygimli_tools import compute_error_model
from src.mesh.pygimli_mesh_tools import build_mono2m_mesh_new, build_unstructured_mesh, safe_mesh_load, build_mono2m_mesh, build_starting_model, build_starting_model_debug
from src.processing.inversion.ert_processor import ERTProcessor
from src.loaders.ert_loader import ERTLoader
from src.visualization.inversion_data_report import InversionDataReport

from src.visualization.basic_plotting import plot_array_on_mesh, extract_polygons
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # 1. Centralized Path Routing
    paths = ProjectPaths(user='AQ96560', project_name='MCM_MONO2M_Single') 
    
    # 2. Load Static Assets
    geom = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, params={
        "absolute_pos": True, 
        'inverse_order': False,
        "projection": {"type": "distance", "output_axis": "X"}
    })

    #mesh = safe_mesh_load(paths.OUTPUT_DIR / 'MCM_MONO2M.bms')
    #mesh = build_unstructured_mesh(geom, area=1, quality=34)

    mesh = build_mono2m_mesh_new(geom, area=2, quality=32)

    #start_model = pg.solver.parseMapToCellArray(res_map, mesh)
    
    # 3. Load & Prep Data
    loader = ERTLoader(site_id="MCM_MONO2M", elec_pos=geom)
    df = loader.load_prime(source=paths.DATA_DIR / "9011_BGS_2026-09-01_040052.tab")

    df_main = df[df['reciprocal'] == False].copy()
    #df_main = df_main.iloc[::5]
    df_rec = df[df['reciprocal'] == True].copy()

    #computed_err = compute_error_model(r_meas=df_rec['R (Ohm)'], err_rec=df_rec['err_rec'], model_type='power')

    processor = ERTProcessor(output_dir=paths.ACTIVE_PROJECT_DIR, mesh=mesh, electrode_positions=geom, df=df_main)

    paraDomain = processor.paraDomain

    #start_model = build_starting_model_debug(mesh, paraDomain)

    #start_model[:200] = 1000
    mesh_polygons = extract_polygons(paraDomain)
    ax, coll = plot_array_on_mesh(mesh_polygons, edgecolor='black', alpha=0.2)

    plt.show()

    a = True
    if a:
        params = {
            #'lam': 20,
            #'robustData': True,
            #'startModel': start_model,
            'zWeight': 0.1,
            'error_param': 5  # Pass the dictionary directly; the wrapper handles it
        }
        
        results = processor.run_single(params=params)
        
        # 6. Generate Report in the same active directory
        pdf_path = paths.ACTIVE_PROJECT_DIR / "Test_newERTProc_Report.pdf"
        InversionDataReport.print(
            filepath=pdf_path,
            results_list=results,
            elec_pos=geom,
            mesh=mesh,
        )