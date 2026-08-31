import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
from pathlib import Path
import pandas as pd

from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import extract_polygons, plot_array_on_mesh

class EnsembleSurveyReport(ReportBase):
    def __init__(self, filepath: str | Path, ensemble_results: dict, mesh, param_grid: dict, geom_df: pd.DataFrame):
        super().__init__(filepath)
        self.ensemble_results = ensemble_results
        self.mesh = mesh
        self.param_grid = param_grid
        self.geom_df = geom_df
        self.polygons = extract_polygons(self.mesh)

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def build(self):
        run_keys = list(self.ensemble_results.keys())
        
        # Calculate 3rd and 97th percentiles across ALL ensemble models
        all_models = np.vstack([res['models'][0] for res in self.ensemble_results.values()])
        vmin, vmax = np.percentile(all_models, [3, 97])
        
        discrete_cmap = plt.cm.get_cmap('Spectral_r', 12)
        shared_norm = LogNorm(vmin=max(vmin, 1e-1), vmax=vmax)
        
        # --- Page 1 to N: Comparative Model Grid (Paginated) ---
        plots_per_page = 10
        cols = 2
        rows = 5
        chunks = [run_keys[i:i + plots_per_page] for i in range(0, len(run_keys), plots_per_page)]
        
        for chunk in chunks:
            with self.page(rows=rows, cols=cols, landscape=True) as (fig, gs):
                fig.suptitle("Ensemble Parameter Sensitivity (Absolute Resistivity)", fontsize=16, fontweight='bold', y=0.98)
                
                for i, key in enumerate(chunk):
                    r, c = divmod(i, cols)
                    ax = fig.add_subplot(gs[r, c])
                    
                    run_data = self.ensemble_results[key]
                    model = run_data['models'][0]
                    
                    params = run_data.get('params', {})
                    param_str = " | ".join([f"{k}: {v}" for k, v in params.items() if k in self.param_grid.keys()])
                    metrics_str = f"RMS: {run_data['rms'][0]:.1f}% (\u03C7\u00B2: {run_data['chi2'][0]:.1f})"
                    
                    ax, collection = plot_array_on_mesh(
                        self.polygons, array=model, ax=ax, 
                        cmap=discrete_cmap, norm=shared_norm
                    )
                    
                    ax.plot(self.geom_df['X'], self.geom_df['Z'] if 'Z' in self.geom_df else np.zeros(len(self.geom_df)), 
                            'kv', markersize=3, alpha=0.6)
                    
                    ax.set_title(f"[{param_str}]\n{metrics_str}", fontsize=9, loc='left', pad=4)
                    ax.tick_params(labelsize=8)
                    if c == 0: ax.set_ylabel("Z (m)", fontsize=8)
                    if r == rows - 1 or i >= len(chunk) - cols: ax.set_xlabel("X (m)", fontsize=8)
                    
                cbar = fig.colorbar(collection, ax=fig.axes, orientation='vertical', fraction=0.02, pad=0.04)
                cbar.set_label(r"Resistivity ($\Omega\cdot$m)")

        # --- Final Page: Chi-Square Convergence Tracker ---
        with self.page(rows=1, cols=1, landscape=True) as (fig, gs):
            fig.suptitle("Inversion Convergence History (\u03C7\u00B2 Evolution)", fontsize=16, fontweight='bold', y=0.95)
            ax = fig.add_subplot(gs[0, 0])
            
            for key in run_keys:
                run_data = self.ensemble_results[key]
                params = run_data.get('params', {})
                param_str = ", ".join([f"{k}:{v}" for k, v in params.items() if k in self.param_grid.keys()])
                
                if 'iteration_history' in run_data and len(run_data['iteration_history']) > 0:
                    chi2_history = run_data['iteration_history'][0].get('chi2_history', [])
                    ax.plot(range(1, len(chi2_history) + 1), chi2_history, marker='o', markersize=4, linewidth=1.5, label=param_str)

            ax.set_xlabel("Iteration Number", fontsize=11)
            ax.set_ylabel("\u03C7\u00B2 (Chi-Square Misfit)", fontsize=11)
            ax.set_yscale('log')
            ax.grid(True, which='both', linestyle='--', alpha=0.5)
            
            # Place the legend outside the plot area
            ax.legend(title="Parameter Sets", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
            
            # Explicitly shrink the plot area so the legend isn't cropped by the PDF boundary
            fig.subplots_adjust(right=0.75)