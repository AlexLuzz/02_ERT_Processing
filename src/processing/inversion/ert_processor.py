import itertools
import numpy as np
import pandas as pd
import pygimli.physics.ert as ert
from pathlib import Path
from src.core.base import ProjectBase
from src.processing.inversion.pygimli_tools import build_ert_container, build_ert_containers_timeseries

class ERTProcessor(ProjectBase):
    def __init__(self, mesh, electrode_positions, df: pd.DataFrame):
        super().__init__(memory=True)
        self.mesh = mesh
        self.elec_pos = electrode_positions
        self.df = df
        self._log_init_stats()
        self._compute_paraDomain()

    def _log_init_stats(self):
        self.logger.info(f"Processor Initialized. Mesh: {self.mesh.cellCount()} cells.")

    def _route_parameters(self, params: dict) -> dict:
        if params is None:
            params = {}
            
        default_inv = {'lam': 10, 'zWeight': 0.7, 'robustData': False, 'blockyModel': False, 'maxIter': 30, 'startModel': None, 'limits': None}
        default_mgr = {'sr': True, 'verbose': True}
        
        routed = {
            'mgr_kwargs': default_mgr.copy(), 
            'inv_kwargs': default_inv.copy(), 
            'error_param': None
        }
        
        for k, v in params.items():
            if k in default_inv:
                routed['inv_kwargs'][k] = v
            elif k in default_mgr:
                routed['mgr_kwargs'][k] = v
            elif k == 'error_param':
                routed['error_param'] = v 
                
        return routed

    def _compute_paraDomain(self):
        data = build_ert_container(self.df, self.elec_pos)
        self.fop = ert.ERTModelling()
        self.fop.setData(data)
        self.fop.setMesh(self.mesh)
        self.paraDomain = self.fop.paraDomain

    def _setup_manager(self, data, mgr_kwargs: dict):
        self.mgr = ert.ERTManager(data, **mgr_kwargs)

    def _execute_inversion(self, inv_kwargs: dict, routed_params: dict) -> dict:
        """Core mathematical execution block."""
        date_survey = self.mgr.data.date_survey
        self.logger.info(f"Inverting survey from: {date_survey}")
        
        # 1. Extract Data Statistics
        n_meas = self.mgr.data.size()
        rhoa = np.array(self.mgr.data('rhoa'))
        rhoa_min, rhoa_max = np.min(rhoa), np.max(rhoa) if len(rhoa) > 0 else (0, 0)
        
        # 2. Extract Starting Model 
        # If not manually provided, we force PyGIMLi to generate it so we can save it
        start_model = inv_kwargs.get('startModel', None)
        
        # 3. Execution
        model = self.mgr.invert(mesh=self.mesh, **inv_kwargs)
        
        return {
            'date_survey': date_survey,
            'model': np.array(model),
            'start_model': np.array(start_model) if start_model is not None else None,
            'response': np.array(self.mgr.inv.response),
            'coverage': np.array(self.mgr.standardizedCoverage()), # Jacobian is computed here
            'chi2': self.mgr.inv.chi2(), # This returns the final iteration's chi2
            'rms': self.mgr.inv.relrms(),
            'chi2_history': list(self.mgr.inv.chi2History),
            'params': routed_params,
            'n_meas': n_meas,
            'rhoa_min': rhoa_min,
            'rhoa_max': rhoa_max
        }
    
    def run_single(self, params: dict = None) -> dict:
        routed = self._route_parameters(params)
        
        container = build_ert_container(self.df, self.elec_pos, error_param=routed['error_param'])
        self._setup_manager(container, routed['mgr_kwargs'])
        
        return self._execute_inversion(routed['inv_kwargs'], routed_params=params)
    
    def run_timelapse(self, params: dict = None, date_col: str = 'date_survey') -> list:
        routed = self._route_parameters(params)
        
        containers = build_ert_containers_timeseries(
            df=self.df, 
            geom_df=self.elec_pos, 
            error_param=routed['error_param'], 
            date_col=date_col
        )
        
        all_res = []
        for container in containers:
            self._setup_manager(container, routed['mgr_kwargs'])
            res = self._execute_inversion(routed['inv_kwargs'], routed_params=params)
            all_res.append(res)
            
        return all_res
    
    def run_ensemble(self, param_grid: dict) -> list:
        keys, values = zip(*param_grid.items())
        permutations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        self.logger.info(f"Starting ensemble analysis: {len(permutations)} permutations.")
        all_res = []
        
        for params in permutations:
            res = self.run_single(params) 
            all_res.append(res)
            
        return all_res

    def save_results(self, folder_path: Path | str, results_list: list | dict, params: dict = None, model_ext: str = ".h5", metrics_ext: str = ".csv"):
        """Explicit saving logic called from the runner script using standardized filenames."""
        folder_path = Path(folder_path)
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Allow passing a single dictionary directly for convenience
        if isinstance(results_list, dict):
            results_list = [results_list]

        structured_models = {}
        metrics_rows = []
        safe_params = params.copy() if params else {}

        if 'startModel' in safe_params and hasattr(safe_params['startModel'], '__len__'):
            u, c = np.unique(safe_params['startModel'], return_counts=True)
            safe_params['startModel'] = "_".join([f"{count}cells_{val:g}" for count, val in zip(c, u)])

        for i, r in enumerate(results_list):
            step_key = f"step_{i:03d}_{r['date_survey']}"
            
            structured_models[f"{step_key}_model"] = r['model']
            structured_models[f"{step_key}_response"] = r['response']
            
            row = {'step': i, 'date_survey': r['date_survey'], 'chi2': r['chi2'], 'rms': r['rms']}
            if r['params']:
                row.update(safe_params)
            metrics_rows.append(row)
            
        config = {"params": safe_params}
        
        self.save(
            data=structured_models, 
            file_path=folder_path / f"results{model_ext}", 
            metadata=config
        )
        
        self.save(
            data=pd.DataFrame(metrics_rows), 
            file_path=folder_path / f"metrics{metrics_ext}", 
            metadata=config
        )