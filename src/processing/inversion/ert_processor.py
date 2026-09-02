import itertools
import numpy as np
import pandas as pd
import pygimli.physics.ert as ert
from pathlib import Path

from src.core.base import ProjectBase
from src.processing.inversion.pygimli_tools import build_ert_container, build_ert_containers_timeseries

class ERTProcessor(ProjectBase):
    def __init__(self, output_dir: Path, mesh, electrode_positions, df: pd.DataFrame):
        super().__init__(memory=True)
        self.mesh = mesh
        self.elec_pos = electrode_positions
        self.df = df
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._log_init_stats()
        self._compute_paraDomain()

    def _log_init_stats(self):
        self.logger.info(f"Processor Initialized. Mesh: {self.mesh.cellCount()} cells.")

    def _route_parameters(self, params: dict) -> dict:
        """Separates inversion parameters, manager kwargs, and the error parameter."""
        if params is None:
            params = {}
            
        # 1. Define the default dictionaries
        default_inv = {'lam': 10, 'zWeight': 0.7, 'robustData': False, 'blockyModel': False, 'maxIter': 30, 'startModel': None, 'limits': None}
        default_mgr = {'sr': True, 'verbose': True}
        
        # 2. Pre-fill the routed dictionary with copies of the defaults
        routed = {
            'mgr_kwargs': default_mgr.copy(), 
            'inv_kwargs': default_inv.copy(), 
            'error_param': None
        }
        
        # 3. Overwrite the defaults with any user-provided values
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

        # Create forward operator and jacobian
        #model = np.ones(self.mesh.cellCount())
        #self.fop.createJacobian(model)
        #self.jacobian = self.fop.jacobian()

    def _setup_manager(self, data, mgr_kwargs: dict):
        """Unlocks the manager for pre-computation adjustments."""
        self.mgr = ert.ERTManager(data, **mgr_kwargs)

    def _execute_inversion(self, inv_kwargs: dict, routed_params: dict) -> dict:
        """Core mathematical execution block."""
        # Extract the date directly from the container
        survey_date = getattr(self.mgr.data, 'date_survey', 'static')
        
        self.logger.info(f"Inverting step for date: {survey_date}")
        model = self.mgr.invert(mesh=self.mesh, **inv_kwargs)
        
        return {
            'time': survey_date,
            'model': np.array(model),
            'response': np.array(self.mgr.inv.response),
            'chi2': self.mgr.inv.chi2(),
            'rms': self.mgr.inv.relrms(),
            'chi2_history': list(self.mgr.inv.chi2History),
            'params': routed_params
        }
    
    def run_single(self, params: dict = None) -> dict:
        routed = self._route_parameters(params)
        
        container = build_ert_container(self.df, self.elec_pos, error_param=routed['error_param'])
        self._setup_manager(container, routed['mgr_kwargs'])
        
        res = self._execute_inversion(routed['inv_kwargs'], routed_params=params)
        
        self._save_results([res], params)
            
        return res
    
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
            
            # Cascade approach: automatically update the startModel for the next time step 
            #routed['inv_kwargs']['startModel'] = res['model']
            
        self._save_results(all_res, params)
        return all_res
    
    def run_ensemble(self, param_grid: dict) -> list:
        keys, values = zip(*param_grid.items())
        permutations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        self.logger.info(f"Starting ensemble analysis: {len(permutations)} permutations.")
        all_res = []
        
        for params in permutations:
            # Suppress internal save and let the aggregator handle it
            res = self.run_single(params, save=False) 
            all_res.append(res)
            
        self._save_results(all_res, param_grid)
        return all_res

    def _save_results(self, results_list: list, params: dict, model_ext: str = ".h5", metrics_ext: str = ".csv"):
        """Unified flat saving logic, entirely agnostic to specific file formats."""
        structured_models = {}
        metrics_rows = []
        
        for i, r in enumerate(results_list):
            # Guarantee unique dictionary keys even if 'time' is identical across ensemble runs
            step_key = f"step_{i:03d}_{r['time']}"
            
            structured_models[f"{step_key}_model"] = r['model']
            structured_models[f"{step_key}_response"] = r['response']
            
            row = {'step': i, 'time': r['time'], 'chi2': r['chi2'], 'rms': r['rms']}
            if r['params']:
                row.update(r['params'])
            metrics_rows.append(row)
            
        config = {"params": params}
        
        # Generic filenames using dynamically passed extensions
        self.save(
            data=structured_models, 
            file_path=self.output_dir / f"results{model_ext}", 
            metadata=config
        )
        
        self.save(
            data=pd.DataFrame(metrics_rows), 
            file_path=self.output_dir / f"metrics{metrics_ext}", 
            metadata=config
        )