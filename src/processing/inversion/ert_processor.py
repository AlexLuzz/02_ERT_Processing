import itertools
import numpy as np
import pandas as pd
import pygimli.physics.ert as ert
from datetime import datetime
from src.core.base import ProjectBase
from src.processing.inversion.pygimli_tools import build_ert_containers_timeseries

class ERTProcessor(ProjectBase):
    """
    Runner class for ERT inversions with ensemble support, detailed iteration tracking,
    and a CSV registry ledger for easy Excel analysis.
    """
    def __init__(self, folder_path: str, mesh, electrode_positions, simulation_name: str = "inversion_run"):
        super().__init__()
        
        self.mesh = mesh
        self.elec_pos = electrode_positions
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        self.sim_name = f"{simulation_name}_{timestamp}"
        
        # Explicit path management built directly into the processor
        self.folder_path = folder_path
        self.registry_path = self.folder_path / self.sim_name / "inversion_registry.csv"
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._log_init_stats()

    def _log_init_stats(self):
        """Logs physical mesh dimensions and array sizes upon initialization."""
        n_cells = self.mesh.cellCount()
        n_nodes = self.mesh.nodeCount()
        width = self.mesh.xmax() - self.mesh.xmin()
        height = self.mesh.ymax() - self.mesh.ymin()
        
        self.logger.info(f"Initialized ERTProcessor for '{self.sim_name}'")
        self.logger.info(f"Electrodes loaded: {len(self.elec_pos)}")
        self.logger.info(f"Mesh geometry: {width:.2f}m wide x {height:.2f}m high")
        self.logger.info(f"Mesh density: {n_cells} cells, {n_nodes} nodes")

    def set_errors(self, df: pd.DataFrame, error_val) -> pd.DataFrame:
        """
        Flexibly assigns error values to the dataset.
        error_val can be a single float (e.g., 5.0) or an array-like series of values.
        """
        df_work = df.copy()
        
        if isinstance(error_val, (int, float)):
            df_work['err_stk (%)'] = float(error_val)
            self.logger.info(f"Applied fixed global error: {error_val}%")
        elif len(error_val) == len(df_work):
            df_work['err_stk (%)'] = error_val
            self.logger.info("Applied array of custom error values.")
        else:
            raise ValueError("error_val must be a single number or an array matching the dataframe length.")
            
        return df_work

    def run_inversion(self, df: pd.DataFrame, 
                      inv_params: dict, 
                      inversion_type: str = "classic", 
                      save_all_iterations: bool = True,
                      save_to_disk: bool = True) -> dict:
        """Executes inversion and logs full history to a pickle file and summary to CSV."""
        run_start_time = datetime.now()
        run_id = run_start_time.strftime("%Y%m%d_%H%M%S")
        self.logger.info(f"Starting {inversion_type} inversion loop (Run ID: {run_id})...")
        
        # Use the timeseries wrapper to handle the groupby and iteration internally
        containers = build_ert_containers_timeseries(df=df, geom_df=self.elec_pos, date_col='date_survey')

        res = {'times': [], 'models': [], 'responses': [], 'chi2': [], 'rms': [], 'params': inv_params}
        if save_all_iterations:
            res['iteration_history'] = []

        current_start_model = inv_params.get('startModel', None)
        total_iterations = 0

        for i, item in enumerate(containers):
            self.logger.info(f"Inverting step {i+1}/{len(containers)}: {item['time']}")
            
            mgr = ert.ERTManager(item['data'], sr=False, verbose=inv_params.get('verbose', True))
            step_params = inv_params.copy()
            
            if inversion_type == "cascade" and i > 0 and current_start_model is not None:
                step_params['startModel'] = current_start_model
                
            model = mgr.invert(mesh=self.mesh, **step_params)
            current_start_model = model
            
            res['times'].append(pd.to_datetime(item['time'], errors='coerce').strftime('%Y-%m-%d %H:%M:%S'))
            res['models'].append(np.array(model))
            res['responses'].append(np.array(mgr.inv.response))
            res['chi2'].append(mgr.inv.chi2())
            res['rms'].append(mgr.inv.relrms())
            
            if save_all_iterations:
                history = {
                    'chi2_history': list(mgr.inv.chi2History),
                    'model_history': list(mgr.inv.modelHistory),
                }
                res['iteration_history'].append(history)
                total_iterations += len(history['chi2_history'])

        res['models'] = np.vstack(res['models'])
        res['responses'] = np.vstack(res['responses'])

        if save_to_disk:
            mesh_filename = f"{run_id}_paraDomain.bms"
            h5_path = self.folder_path / self.sim_name / f"{run_id}_results.h5"
            csv_path = self.folder_path / self.sim_name / f"{run_id}_metrics.csv"
            
            mesh_path = self.folder_path / self.sim_name / mesh_filename
            self.save_mesh(self.mesh, mesh_path)
    
            self._update_registry(run_id, run_start_time, inversion_type, inv_params, res, total_iterations, h5_path.name)
            
            config = {"run_id": run_id, "inversion_type": inversion_type, "params": inv_params, "mesh_file": mesh_filename}
    
            h5_data = {'times': res['times'], 'models': res['models']}
            self.save(data=h5_data, file_path=h5_path, metadata=config)
            
            csv_dict = {
                'time': res['times'], 'chi2': res['chi2'], 'rms': res['rms'],
                'response': [",".join(map(str, r)) for r in res['responses']]
            }
            if 'iteration_history' in res:
                csv_dict['chi2_history'] = [",".join(map(str, h['chi2_history'])) for h in res['iteration_history']]
                
            self.save(data=pd.DataFrame(csv_dict), file_path=csv_path, metadata=config)
        
        return res

    def _update_registry(self, run_id, start_time, inv_type, params, res, total_iters, filename):
        """Appends a summary row to the tracking CSV for easy Excel viewing."""
        avg_chi2 = np.mean(res['chi2']) if res['chi2'] else 0
        avg_rms = np.mean(res['rms']) if res['rms'] else 0
        duration = datetime.now() - start_time
        
        summary = {
            'run_id': run_id,
            'start_time': start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'duration': str(duration).split('.')[0],
            'inversion_type': inv_type,
            'num_surveys': len(res['times']),
            'total_iterations': total_iters,
            'avg_final_chi2': round(avg_chi2, 3),
            'avg_final_rms': round(avg_rms, 3),
            'saved_file': filename
        }
        
        for k, v in params.items():
            summary[f"param_{k}"] = v
            
        df_new = pd.DataFrame([summary])
        
        if self.registry_path.exists():
            df_existing = pd.read_csv(self.registry_path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
            
        df_combined.to_csv(self.registry_path, index=False)
        self.logger.info(f"Ledger updated: {self.registry_path.name}")

    def run_ensemble(self, df: pd.DataFrame, param_grid: dict, inversion_type: str = "classic", save_all_iterations: bool = True) -> dict:
        """Runs multiple inversions based on a grid of parameters and aggregates the save."""
        keys, values = zip(*param_grid.items())
        permutations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        self.logger.info(f"Starting ensemble analysis with {len(permutations)} combinations.")
        all_results = {}
        
        for i, params in enumerate(permutations):
            self.logger.info(f"--- Ensemble {i+1}/{len(permutations)} | Params: {params} ---")
            df_work = self.set_errors(df, 5)
            
            # SUPPRESS individual saves
            res = self.run_inversion(df_work, inv_params=params, 
                                     inversion_type=inversion_type, 
                                     save_all_iterations=save_all_iterations,
                                     save_to_disk=True)
            all_results[f"run_{i}"] = res
            
        # --- AGGREGATED SAVE LOGIC ---
        self.logger.info("Aggregating ensemble results for master save...")
        
        # 1. Save Mesh (Once)
        mesh_filename = f"{self.sim_name}_ensemble_paraDomain.bms"
        self.save_mesh(self.mesh, self.folder_path / self.sim_name / mesh_filename)

        h5_flat = {}
        csv_rows = []
        
        # 2. Flatten Arrays for HDF5 & Extract Metrics for CSV
        for k, v in all_results.items():
            h5_flat[f"{k}_models"] = v['models']
            h5_flat[f"{k}_times"] = v['times']
            
            row = {'run_id': k, 'chi2': v['chi2'][0], 'rms': v['rms'][0]}
            row.update(v['params'])
            csv_rows.append(row)

        config = {"ensemble": True, "param_grid": param_grid, "mesh_file": mesh_filename}

        # 3. Save Master Files
        h5_path = self.folder_path / self.sim_name / f"{self.sim_name}_ensemble_results.h5"
        csv_path = self.folder_path / self.sim_name / f"{self.sim_name}_ensemble_metrics.csv"
        
        self.save(data=h5_flat, file_path=h5_path, metadata=config)
        self.save(data=pd.DataFrame(csv_rows), file_path=csv_path, metadata=config)
            
        return all_results