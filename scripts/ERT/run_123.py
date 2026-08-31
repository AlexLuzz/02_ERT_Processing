from config.paths import ProjectPaths
from src.loaders.ert_loader import ERTLoader
from src.loaders.ert_loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import safe_mesh_load
from src.processing.inversion.ert_processor import ERTProcessor
from src.visualization.single_ert_report import SingleSurveyERTReport

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    
    # 1. Load Geometry and Single Survey Data
    MCM_GEO_elecs = load_geometry(
        paths.MCM_GEO_ELECS_POS,
        params={
            "absolute_pos": True, 
            "inverse_order": True,
            "projection": {"type": "best_fit", "output_axis": "X"}
        }
    )
    
    loader = ERTLoader(site_id="MCM_GEO", elec_pos=MCM_GEO_elecs)
    dfs = loader.load_sas4000(source=paths.MCM_SAS4000_GEO / "MCM_GEO_SC.AMP")
    
    # Isolate single test survey
    first_date = dfs['date_survey'].iloc[0]
    single_df = dfs[dfs['date_survey'] == first_date].copy()
    
    # 2. Build Mesh and Processor
    mesh = safe_mesh_load(paths.OUTPUT_DIR / 'MCM_GEO_9247cells.bms')
    
    report_dir = paths.OUTPUT_DIR / "MCM_GEO" / "Ensemble_Sensitivity"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    processor = ERTProcessor(
        folder_path=report_dir, 
        mesh=mesh, 
        electrode_positions=MCM_GEO_elecs, 
        simulation_name="param_sensitivity"
    )

    # 3. Define Parameter Grid for Sensitivity Analysis
    param_grid = {
        'lam': [5, 20, 50],
        'robustData': [True, False],
        'maxIter': [30]
    }
    
    print("\n--- Running Ensemble Inversions via ERTProcessor ---")
    ensemble_results = processor.run_ensemble(
        df=single_df, 
        param_grid=param_grid, 
        inversion_type="classic",
        save_all_iterations=True
    )
    
    # 4. Generate Reports for Every Inversion Run in the Ensemble
    print("\n--- Generating Single Survey Reports ---")
    keys, values = zip(*param_grid.items())
    import itertools
    permutations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    for i, params in enumerate(permutations):
        run_key = f"run_{i}"
        run_data = ensemble_results[run_key]
        
        pdf_path = processor.folder_path / processor.sim_name / f"report_{run_key}.pdf"
        
        metrics = {
            'chi2': run_data['chi2'][0],
            'rms': run_data['rms'][0],
            'iterations': len(run_data['iteration_history'][0]['chi2_history']) if 'iteration_history' in run_data else 'N/A'
        }
        
        SingleSurveyERTReport.print(
            filepath=pdf_path,
            mesh=mesh,
            df=single_df,
            model=run_data['models'][0],
            response=run_data['responses'][0],
            params=params,
            metrics=metrics,
            run_id=f"{processor.sim_name}_{run_key}"
        )
        print(f"Generated: {pdf_path.name}")

    print("\n✅ Ensemble run and reporting complete.")