from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import safe_mesh_load
from src.processing.inversion.ert_processor import ERTProcessor
from src.visualization.ensemble_survey_report import EnsembleSurveyReport

if __name__ == "__main__":
    paths = ProjectPaths(user='AQ96560') 
    geom = load_geometry(paths.MCM_GEO_ELECS_POS, 
                         params={"absolute_pos": True, 
                                 'inverse_order': True,
                                 "projection": {"type": "best_fit", "output_axis": "X"}})


    mesh = safe_mesh_load(paths.OUTPUT_DIR / 'MCM_GEO_9247cells_V2.bms')
    
    # Assuming you pass the single_df_clean from the previous step here
    # single_df_clean = pd.read_csv(...) 
    
    report_dir = paths.OUTPUT_DIR / "MCM_GEO" / "20260831_tests"
    processor = ERTProcessor(folder_path=report_dir, 
                             mesh=mesh, electrode_positions=geom, simulation_name="param_test")

    single_df_clean = processor.load(paths.OUTPUT_DIR / "MCM_GEO" / "clean_df.pkl")

    param_grid = {
            'lam': [5, 10, 20],
            'robustData': [True, False],
            'zWeight': [0.1, 0.4, 0.7, 1.0],
            'limits': [[1, 10000], [10, 5000]]
        }

    parameters = {
                'lam': [20],
                'robustData': [True],
                'zWeight': [0.7],
                #'limits': [[1, 10000]]
            }

    params = parameters
    
    ensemble_results = processor.run_ensemble(
        df=single_df_clean, # Pass clean data
        param_grid=params, 
        inversion_type="classic"
    )
    
    # Generate the unified grid report
    pdf_path = processor.folder_path / processor.sim_name / "Test_report.pdf"
    
    EnsembleSurveyReport.print(
        filepath=pdf_path,
        ensemble_results=ensemble_results,
        geom_df=geom,
        mesh=mesh,
        param_grid=params
    )
    print(f"✅ Ensemble grid report saved to {pdf_path.name}")