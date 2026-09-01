from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import safe_mesh_load
from src.processing.inversion.ert_processor import ERTProcessor
from src.processing.inversion.pygimli_tools import compute_error_model
from src.loaders.ert_loader import ERTLoader
from src.visualization.ensemble_survey_report import EnsembleSurveyReport

if __name__ == "__main__":
    paths = ProjectPaths(user='AQ96560', project_name='MCM_Ensemble_Test') 
    
    geom = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, params={"absolute_pos": True, "projection": {"type": "distance", "output_axis": "X"}})
    mesh = safe_mesh_load(paths.OUTPUT_DIR / 'MCM_MONO2M.bms')

    loader = ERTLoader(site_id="MCM_MONO2M", elec_pos=geom)
    df = loader.load_prime(source=paths.DATA_DIR / "9011_BGS_2026-09-01_040052.tab")
    
    df_main = df[df['reciprocal'] == False].copy()
    df_rec = df[df['reciprocal'] == True].copy()
    
    computed_err = compute_error_model(r_meas=df_rec['R (Ohm)'], err_rec=df_rec['err_rec'])

    processor = ERTProcessor(output_dir=paths.ACTIVE_PROJECT_DIR, mesh=mesh, electrode_positions=geom)

    # Testing 4 configurations: 2 lambdas x 2 error models (one computed dynamically, one fixed at 5%)
    ensemble_params = {
        'lam': [2, 20],
        'zWeight': [0.1],
        'robustData': [True],
        'error_param': [computed_err, 5] 
    }
    
    ensemble_results = processor.run_ensemble(df=df_main, param_grid=ensemble_params)
    
    # Generate the unified grid report
    pdf_path = paths.ACTIVE_PROJECT_DIR / "Ensemble_Sensitivity_Report.pdf"
    
    EnsembleSurveyReport.print(
        filepath=pdf_path,
        ensemble_results=ensemble_results,
        geom_df=geom,
        mesh=mesh,
        param_grid=ensemble_params
    )