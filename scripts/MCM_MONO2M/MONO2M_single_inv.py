from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import safe_mesh_load
from src.processing.inversion.ert_processor import ERTProcessor
from src.visualization.ensemble_survey_report import EnsembleSurveyReport
from src.loaders.ert_loader import ERTLoader

if __name__ == "__main__":
    paths = ProjectPaths(user='AQ96560') 
    geom = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, params={"absolute_pos": True, 
                                                              'inverse_order': False,
                                                              "projection": {"type": "distance", "output_axis": "X"}})

    mesh = safe_mesh_load(paths.OUTPUT_DIR / 'MCM_MONO2M.bms')

    loader = ERTLoader(site_id="MCM_MONO2M", elec_pos=geom)
    df = loader.load_prime(source=paths.DATA_DIR / "9011_BGS_2026-09-01_040052.tab")

    df = df[df['reciprocal'] == False].copy()

    report_dir = paths.OUTPUT_DIR / "MCM_MONO2M"
    processor = ERTProcessor(folder_path=report_dir, 
                             mesh=mesh, electrode_positions=geom, simulation_name="param_test")

    params = {
                'lam': [2],
                'robustData': [False],
                'zWeight': [0.1],
                'limits': [[0.1, 10000]]
            }
    
    ensemble_results = processor.run_ensemble(
        df=df, # Pass clean data
        param_grid=params, 
        inversion_type="classic"
    )
    
    # Generate the unified grid report
    pdf_path = report_dir / "MONO2M_0901_WA_WArec.pdf"
    
    EnsembleSurveyReport.print(
            filepath=pdf_path,
            ensemble_results=ensemble_results,
            geom_df=geom,
            mesh=mesh,
            param_grid=params
        )
