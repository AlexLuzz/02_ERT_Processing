import pandas as pd
from pathlib import Path
import numpy as np

from config.paths import ProjectPaths
from src.core.base import ProjectBase
from src.visualization.ensemble_survey_report import EnsembleSurveyReport
from src.mesh.pygimli_mesh_tools import safe_mesh_load
from src.loaders.ert_loading_tools import load_geometry

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi')
    base = ProjectBase()
    
    # --- Configuration ---
    target_dir = paths.OUTPUT_DIR / "MCM_GEO" / "Ensemble_Sensitivity" / "param_test_20260831_0240"
    mesh_path = paths.OUTPUT_DIR / 'MCM_GEO_9247cells.bms'
    
    geom = load_geometry(paths.MCM_GEO_ELECS_POS, 
                         params={"absolute_pos": True, 
                                 'inverse_order': True,
                                 "projection": {"type": "best_fit", "output_axis": "X"}})
    mesh = safe_mesh_load(mesh_path)
    
    # --- Load and Fuse Data ---
    h5_files = sorted(list(target_dir.glob("*_results.h5")))
    print(f"Found {len(h5_files)} independent runs. Fusing...")
    
    ensemble_results = {}
    dynamic_param_grid = {}
    
    for i, h5_path in enumerate(h5_files):
        run_key = f"run_{i}"
        
        data, meta = base.load(h5_path)
        params = meta.get("params", {})
        
        for k, v in params.items():
            if k not in dynamic_param_grid:
                dynamic_param_grid[k] = set()
            if isinstance(v, list):
                dynamic_param_grid[k].add(tuple(v))
            else:
                dynamic_param_grid[k].add(v)
        
        csv_path = h5_path.parent / h5_path.name.replace("_results.h5", "_metrics.csv")
        df_metrics = pd.read_csv(csv_path)
        
        # EXTRACT LOWEST CHI2 AND REBUILD ITERATION HISTORY
        iter_hist = []
        if 'chi2_history' in df_metrics.columns and pd.notna(df_metrics['chi2_history'].iloc[0]):
            hist_str = str(df_metrics['chi2_history'].iloc[0])
            chi2_hist = [float(x) for x in hist_str.split(',') if x.strip()]
            lowest_chi2 = min(chi2_hist) if chi2_hist else df_metrics['chi2'].iloc[0]
            iter_hist = [{'chi2_history': chi2_hist}]
        else:
            lowest_chi2 = df_metrics['chi2'].iloc[0]
            
        ensemble_results[run_key] = {
            'models': data['models'],
            'times': data['times'],
            'chi2': [lowest_chi2], 
            'rms': df_metrics['rms'].tolist(),
            'params': params,
            'iteration_history': iter_hist  # Crucial for the plot
        }
        
    final_param_grid = {k: list(v) for k, v in dynamic_param_grid.items()}
    
    # --- AGGREGATED SAVE LOGIC ---
    print("Saving fused master files...")
    h5_flat = {}
    csv_rows = []
    
    for k, v in ensemble_results.items():
        h5_flat[f"{k}_models"] = v['models']
        h5_flat[f"{k}_times"] = v['times']
        
        row = {'run_id': k, 'chi2': v['chi2'][0], 'rms': v['rms'][0]}
        row.update(v['params'])
        if v['iteration_history']:
            row['chi2_history'] = ",".join(map(str, v['iteration_history'][0]['chi2_history']))
        csv_rows.append(row)

    config = {"ensemble": True, "param_grid": final_param_grid}
    master_h5 = target_dir / "MCM_GEO_ensemble_results.h5"
    master_csv = target_dir / "MCM_GEO_ensemble_metrics.csv"
    
    base.save(data=h5_flat, file_path=master_h5, metadata=config)
    base.save(data=pd.DataFrame(csv_rows), file_path=master_csv, metadata=config)
        
    print("Generating paginated report...")
    EnsembleSurveyReport.print(
        filepath=target_dir / "Ensemble_Grid_Report_FIXED.pdf",
        ensemble_results=ensemble_results,
        mesh=mesh,
        param_grid=final_param_grid,
        geom_df=geom
    )
    print(f"Done! Saved to {target_dir.name}")