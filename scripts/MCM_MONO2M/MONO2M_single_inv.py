from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from src.processing.inversion.pygimli_tools import compute_error_model
from src.mesh.pygimli_mesh_tools import safe_mesh_load
from src.processing.inversion.ert_processor import ERTProcessor
from src.loaders.ert_loader import ERTLoader

if __name__ == "__main__":
    # 1. Centralized Path Routing
    paths = ProjectPaths(user='alexi', project_name='MCM_MONO2M_Single') 
    
    # 2. Load Static Assets
    geom = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, params={
        "absolute_pos": True, 
        'inverse_order': False,
        "projection": {"type": "distance", "output_axis": "X"}
    })
    mesh = safe_mesh_load(paths.OUTPUT_DIR / 'MCM_MONO2M.bms')

    # 3. Load & Prep Data
    loader = ERTLoader(site_id="MCM_MONO2M", elec_pos=geom)
    df = loader.load_prime(source=paths.DATA_DIR / "9011_BGS_2026-09-01_040052.tab")

    df_main = df[df['reciprocal'] == False].copy()
    df_rec = df[df['reciprocal'] == True].copy()

    #computed_err = compute_error_model(r_meas=df_rec['R (Ohm)'], err_rec=df_rec['err_rec'], model_type='power')

    processor = ERTProcessor(output_dir=paths.ACTIVE_PROJECT_DIR, mesh=mesh, electrode_positions=geom, df=df_main)

    params = {
        'lam': 20,
        'robustData': True,
        'zWeight': 0.1,
        'error_param': 3  # Pass the dictionary directly; the wrapper handles it
    }
    
    results = processor.run_single(df=df_main, params=params)
    
    # 6. Generate Report in the same active directory
    pdf_path = paths.ACTIVE_PROJECT_DIR / "MONO2M_0901_WA_WArec.pdf"
    EnsembleSurveyReport.print(
        filepath=pdf_path,
        ensemble_results=results,
        geom_df=geom,
        mesh=mesh,
        param_grid=params
    )