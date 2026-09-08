import itertools
import numpy as np
import pandas as pd
import pygimli.physics.ert as ert
from pathlib import Path
from src.core.base import ProjectBase
from src.processing.inversion.pygimli_tools import build_ert_container, build_ert_containers_timeseries
import json


class ERTProcessor(ProjectBase):
    def __init__(self, mesh, electrode_positions, df: pd.DataFrame = None):
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
            
        default_inv = {'lam': 10, 'zWeight': 0.7, 'robustData': False, 'blockyModel': False, 
                       'maxIter': 30, 'startModel': None, 'limits': None}
        default_mgr = {'sr': True, 'verbose': True}
        
        routed = {
            'mgr_kwargs': default_mgr.copy(), 
            'inv_kwargs': default_inv.copy(), 
            'err_values': 5  # Default to 5% if not provided
        }
        
        for k, v in params.items():
            if k in default_inv:
                routed['inv_kwargs'][k] = v
            elif k in default_mgr:
                routed['mgr_kwargs'][k] = v
            elif k == 'err_values':
                routed['err_values'] = v 
                
        return routed

    def _compute_paraDomain(self):
        self.fop = ert.ERTModelling()
        self.fop.setMesh(self.mesh)
        self.paraDomain = self.fop.paraDomain

    def _setup_manager(self, data, mgr_kwargs: dict):
        self.mgr = ert.ERTManager(data, **mgr_kwargs)

    def _execute_inversion(self, inv_kwargs: dict, routed_params: dict) -> dict:
        date_survey = self.mgr.data.date_survey
        self.logger.info(f"Inverting survey from: {date_survey}")
        
        model = self.mgr.invert(mesh=self.mesh, **inv_kwargs)
        
        return {
            'date_survey': date_survey,
            'model': np.array(model),
            'response': np.array(self.mgr.inv.response),
            'chi2_history': list(self.mgr.inv.chi2History),
            'rrms': self.mgr.inv.relrms(),
            'chi2': self.mgr.inv.chi2(),
            'params': routed_params
        }
    
    def run_single(self, params: dict = None) -> dict:
        routed = self._route_parameters(params)
        container = build_ert_container(self.df, self.elec_pos, err_values=routed['err_values'])
        self._setup_manager(container, routed['mgr_kwargs'])
        return self._execute_inversion(routed['inv_kwargs'], routed_params=params)
    
    def run_timelapse(self, params: dict = None) -> list:
        routed = self._route_parameters(params)
        containers = build_ert_containers_timeseries(df=self.df, geom_df=self.elec_pos, err_values=routed['err_values'])
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

    def save_results(self, folder_path: Path | str, results_list: list | dict, params: dict = None):
        """Strictly formatted, flattened save logic yielding arrays and JSON."""
        folder_path = Path(folder_path)
        folder_path.mkdir(parents=True, exist_ok=True)
        if isinstance(results_list, dict): results_list = [results_list]

        # Aggregate core matrices
        models = np.array([r['model'] for r in results_list])
        responses = np.array([r['response'] for r in results_list])
        times = np.array([r['date_survey'] for r in results_list])
        
        # Aggregate parameters & metrics
        rrms = [r['rrms'] for r in results_list]
        chi2 = [r['chi2'] for r in results_list]
        run_params = [r['params'] for r in results_list]
        
        # Pad chi2_history into a strict 2D rectangular matrix for HDF5/CSV support
        chi2_histories = [r['chi2_history'] for r in results_list]
        max_len = max((len(h) for h in chi2_histories), default=0)
        chi2_hist_pad = np.full((len(chi2_histories), max_len), np.nan)
        for i, h in enumerate(chi2_histories):
            chi2_hist_pad[i, :len(h)] = h

        # 1. Save Meshes
        self.save_mesh(self.mesh, folder_path / "forward_mesh.bms")
        self.save_mesh(self.paraDomain, folder_path / "paradomain.bms")

        # 2. Save pure arrays to CSVs
        np.savetxt(folder_path / "models.csv", models, delimiter=",")
        np.savetxt(folder_path / "responses.csv", responses, delimiter=",")
        np.savetxt(folder_path / "chi2_history.csv", chi2_hist_pad, delimiter=",")
        np.savetxt(folder_path / "times.csv", times, fmt="%s", delimiter=",")

        # 3. Format and save everything else to JSON
        start_model = run_params[0].get('startModel') if run_params else None
        if isinstance(start_model, np.ndarray):
            start_model = start_model.tolist()

        config = {
            "global_params": params if params else {},
            "run_params": run_params,
            "rrms": rrms,
            "chi2": chi2,
            "start_model": start_model
        }
        with open(folder_path / "params.json", "w") as f:
            json.dump(config, f, indent=4)

        # 4. Save aggregated HDF5 directly via base
        h5_data = {
            "models": models,
            "responses": responses,
            "times": times.astype("S"),
            "chi2_history": chi2_hist_pad
        }
        self.save(data=h5_data, file_path=folder_path / "results.h5", metadata=config)