import itertools
import numpy as np
import pandas as pd
import pygimli.physics.ert as ert
from datetime import datetime
from src.core.base import ProjectBase
from src.processing.inversion.pygimli_tools import build_ert_container

class ERTProcessor(ProjectBase):
    """
    Runner class for ERT inversions with ensemble support, detailed iteration tracking,
    and a CSV registry ledger for easy Excel analysis.
    """
    def __init__(self, folder_path: str, mesh, electrode_positions, simulation_name: str = "inversion_run"):
        super().__init__()
        
        self.mesh = mesh
        self.elec_pos = electrode_positions
        
        # Create a unique simulation name using the requested date/hour:min format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        self.sim_name = f"{simulation_name}_{timestamp}"
        
        # Setup the CSV registry file path
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

    def filter_and_format(self, df: pd.DataFrame, min_length: int = 100, error_val: float = 5.0) -> pd.DataFrame:
        """Validates survey lengths using date_survey and overrides error values."""
        df_work = df.copy()
        initial_surveys = df_work['date_survey'].nunique()
        
        counts = df_work.groupby('date_survey').size()
        valid_dates = counts[counts >= min_length].index
        df_work = df_work[df_work['date_survey'].isin(valid_dates)]
        
        if error_val is not None:
            df_work['err_stk (%)'] = error_val
            
        self.logger.info(f"Survey check: Kept {len(valid_dates)}/{initial_surveys} surveys (>= {min_length} meas).")
        return df_work

    def run_inversion(self, df: pd.DataFrame, inv_params: dict, inversion_type: str = "classic", save_all_iterations: bool = True) -> dict:
        """Executes inversion and logs full history to a pickle file and summary to CSV."""
        run_start_time = datetime.now()
        run_id = run_start_time.strftime("%Y%m%d_%H%M%S")
        self.logger.info(f"Starting {inversion_type} inversion loop (Run ID: {run_id})...")
        
        containers = build_ert_container(df_survey=df, geom_df=self.elec_pos)

        # Simplified results dictionary
        res = {'times': [], 'models': [], 'responses': [], 'chi2': [], 'rms': []}
        if save_all_iterations:
            res['iteration_history'] = []

        current_start_model = inv_params.get('startModel', None)
        total_iterations = 0

        for i, item in enumerate(containers):
            self.logger.info(f"Inverting step {i+1}/{len(containers)}: {item['time']}")
            
            mgr = ert.ERTManager(item['data'], sr=False, verbose=inv_params.get('verbose', False))
            step_params = inv_params.copy()
            
            if inversion_type == "cascade" and i > 0 and current_start_model is not None:
                step_params['startModel'] = current_start_model
                
            model = mgr.invert(mesh=self.mesh, **step_params)
            current_start_model = model
            
            # Store final states
            res['times'].append(str(item['time']))
            res['models'].append(np.array(model))
            res['responses'].append(np.array(mgr.inv.response))
            res['chi2'].append(mgr.inv.chi2)
            res['rms'].append(mgr.inv.relrms)
            
            # Store full iteration history (model, chi2, and rms per step)
            if save_all_iterations:
                history = {
                    'chi2_history': list(mgr.inv.chi2History),
                    'rms_history': list(mgr.inv.relrmsHistory),
                    'model_history': [np.array(m) for m in mgr.inv.models] if hasattr(mgr.inv, 'models') else []
                }
                res['iteration_history'].append(history)
                total_iterations += len(history['chi2_history'])

        # Stack into 2D matrices
        res['models'] = np.vstack(res['models'])
        res['responses'] = np.vstack(res['responses'])

        # 1. Save deep data via ProjectBase
        config = {"run_id": run_id, "inversion_type": inversion_type, "params": inv_params}
        file_path = self.save(self.sim_name, data=res, config=config, data_format='pkl')
        
        # 2. Save high-level summary to the CSV ledger
        self._update_registry(run_id, run_start_time, inversion_type, inv_params, res, total_iterations, file_path.name)
        
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
        
        # Flatten inversion parameters into the summary row
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
        """
        Runs multiple inversions based on a grid of parameters.
        
        The itertools.product function creates a Cartesian product (every possible combination) 
        of the parameter lists. 
        Example: {'lam': [10, 20], 'zWeight': [0.5, 0.7]} becomes 4 separate inversion runs:
        1. lam=10, zWeight=0.5
        2. lam=10, zWeight=0.7
        3. lam=20, zWeight=0.5
        4. lam=20, zWeight=0.7
        """
        keys, values = zip(*param_grid.items())
        permutations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        self.logger.info(f"Starting ensemble analysis with {len(permutations)} combinations.")
        all_results = {}
        
        for i, params in enumerate(permutations):
            self.logger.info(f"--- Ensemble {i+1}/{len(permutations)} | Params: {params} ---")
            res = self.run_inversion(df, inv_params=params, inversion_type=inversion_type, save_all_iterations=save_all_iterations)
            all_results[f"run_{i}"] = res
            
        return all_results