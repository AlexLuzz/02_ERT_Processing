from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import safe_mesh_load
from src.processing.inversion.ert_processor import ERTProcessor
from src.visualization.ensemble_survey_report import EnsembleSurveyReport
from src.loaders.ert_loader import ERTLoader
from src.processing.data.data_preparator import DataPreparator

if __name__ == "__main__":
    paths = ProjectPaths(user='AQ96560') 
    geom = load_geometry(paths.MCM_GEO_ELECS_POS, 
                         params={"absolute_pos": True, 
                                 'inverse_order': True,
                                 "projection": {"type": "best_fit", "output_axis": "X"}})


    mesh = safe_mesh_load(paths.OUTPUT_DIR / 'MCM_GEO_9247cells_V2.bms')

    loader = ERTLoader(site_id="MCM_GEO", elec_pos=geom)

    thresholds = {
                "Vmn (mV)": {"min": 0.1},
                "R (Ohm)": {"min": 0.01},
                "err_stk (%)": {"max": 40.0},
                "err_rec (%)": {"max": 40.0},
                
            }
    
    dfs = loader.load_sas4000(source=paths.MCM_SAS4000_GEO / "MCM_GEO_DD_DDrecip.AMP")
                    
    dfs_clean = DataPreparator(memory=True).filter_standard_survey(dfs, thresholds)

    single_df_raw = dfs_clean[dfs_clean['date_survey'] == dfs_clean['date_survey'].iloc[0]].copy()
    
    report_dir = paths.OUTPUT_DIR / "20260831_GEO_tests"
    processor = ERTProcessor(folder_path=report_dir, 
                             mesh=mesh, electrode_positions=geom, simulation_name="param_test")

    params = {
                'lam': [20],
                'robustData': [True],
                'zWeight': [0.7],
                #'limits': [[1, 10000]]
            }
    
    ensemble_results = processor.run_ensemble(
        df=single_df_raw, # Pass clean data
        param_grid=params, 
        inversion_type="classic"
    )
    
    # Generate the unified grid report
    pdf_path = report_dir / "Test_report_once.pdf"
    
    EnsembleSurveyReport.print(
            filepath=pdf_path,
            ensemble_results=ensemble_results,
            geom_df=geom,
            mesh=mesh,
            param_grid=params
        )

    print(f"✅ Ensemble grid report saved to {pdf_path.name}")