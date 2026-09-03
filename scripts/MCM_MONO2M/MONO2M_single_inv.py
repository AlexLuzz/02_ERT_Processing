from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from src.processing.inversion.pygimli_tools import compute_error_model
from src.mesh.pygimli_mesh_tools import *
from src.processing.inversion.ert_processor import ERTProcessor
from src.loaders.ert_loader import ERTLoader
from src.visualization.inversion_data_report import InversionDataReport

from src.visualization.basic_plotting import plot_array_on_mesh, extract_polygons
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi', project_name='MCM_MONO2M_Single') 
    
    geom = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, params={
        "absolute_pos": True, 
        'inverse_order': False,
        "projection": {"type": "distance", "output_axis": "X"}
    })

    #mesh = safe_mesh_load(paths.OUTPUT_DIR / 'MCM_MONO2M.bms')
    #mesh = build_unstructured_mesh(geom, area=1, quality=34)

    mesh, start_model_mesh = build_mono2m_meshes(
        geom, 
        area_top=0.3, 
        area_bottom=2.0, 
        quality=34,
        add_boundary=False, 
        extension=5.0,
        depth=10.0,
    )
    
    loader = ERTLoader(site_id="MCM_MONO2M", elec_pos=geom)
    df = loader.load_prime(source=paths.DATA_DIR / "9011_BGS_2026-09-01_040052.tab")

    df_main = df[df['reciprocal'] == False].copy()
    #df_main = df_main[abs(df_main['A'] - df_main['B']) < 10]
    #df_main = df_main.iloc[::5]
    df_rec = df[df['reciprocal'] == True].copy()

    #computed_err = compute_error_model(r_meas=df_rec['R (Ohm)'], err_rec=df_rec['err_rec'], model_type='power')

    processor = ERTProcessor(output_dir=paths.ACTIVE_PROJECT_DIR, mesh=mesh, electrode_positions=geom, df=df_main)

    paraDomain = processor.paraDomain

    start_model = build_starting_model(start_model_mesh, paraDomain, rhomap=[[10, 1000], [20, 10]])

    #start_model[:200] = 1000
    #mesh_polygons = extract_polygons(paraDomain)
    #ax, coll = plot_array_on_mesh(mesh_polygons, start_model, edgecolor='black', alpha=0.2)
    #cbar = plt.colorbar(coll, ax=ax, location='right', fraction=0.03, pad=0.02)
    #plt.show()

    a = True
    if a:
        params = {
            'lam': 20,
            'robustData': False,
            'blockyModel': False,
            'startModel': start_model,
            'zWeight': 0.7,
            'limits': [1, 2000],
            'error_param': 3  # Pass the dictionary directly; the wrapper handles it
        }
        
        results = processor.run_single(params=params)
        
        # 6. Generate Report in the same active directory
        pdf_path = paths.ACTIVE_PROJECT_DIR / "Test_newERTProc_Report.pdf"
        InversionDataReport.print(
            filepath=pdf_path,
            results_list=results,
            elec_pos=geom,
            mesh=paraDomain,
        )