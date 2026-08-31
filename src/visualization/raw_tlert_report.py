from matplotlib.colors import LogNorm
import numpy as np
import pandas as pd
from pathlib import Path

from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import extract_polygons, plot_array_on_mesh

class SingleSurveyERTReport(ReportBase):
    def __init__(self, filepath: str | Path, mesh, df: pd.DataFrame, model: np.ndarray, response: np.ndarray, params: dict, metrics: dict, run_id: str):
        """
        Args:
            filepath: Destination PDF path.
            mesh: The PyGIMLi paraDomain mesh.
            df: Standardized DataFrame for the single survey.
            model: 1D inverted resistivity array.
            response: 1D calculated apparent resistivity response array.
            params: Inversion parameter dictionary.
            metrics: Dictionary containing chi2, rms, and iteration counts.
            run_id: Run identifier for titles.
        """
        super().__init__(filepath)
        self.mesh = mesh
        self.polygons = extract_polygons(self.mesh)
        self.df = df
        self.model = model
        self.response = response
        self.params = params
        self.metrics = metrics
        self.run_id = run_id

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def build(self):
        # --- Page 1: Raw Data Distribution & Electrode Geometry ---
        with self.page(rows=3, cols=1, landscape=False) as (fig, gs):
            fig.suptitle(f"Ensemble Test: {self.run_id} | Data Summary", fontsize=13, fontweight='bold', y=0.98)
            
            # 1. Error distributions
            ax0 = fig.add_subplot(gs[0, 0])
            if 'err_stk (%)' in self.df.columns and self.df['err_stk (%)'].notna().any():
                self.df['err_stk (%)'].plot(kind='hist', bins=40, ax=ax0, color='orange', alpha=0.7, label='Stacking Error')
            if 'err_rec (%)' in self.df.columns and self.df['err_rec (%)'].notna().any():
                self.df['err_rec (%)'].plot(kind='hist', bins=40, ax=ax0, color='teal', alpha=0.7, label='Reciprocal Error')
            ax0.set_title("Error Distributions", fontsize=10, loc='left')
            ax0.set_xlabel("Error (%)", fontsize=8)
            ax0.tick_params(labelsize=8)
            ax0.legend(fontsize=8)

            # 2. Apparent Resistivity Distribution
            ax1 = fig.add_subplot(gs[1, 0])
            self.df['rhoa (Ohm.m)'].plot(kind='hist', bins=50, ax=ax1, color='purple', alpha=0.6)
            ax1.set_title(r"Measured Apparent Resistivity ($\rho_a$) Distribution", fontsize=10, loc='left')
            ax1.set_xlabel(r"$\rho_a$ ($\Omega\cdot$m)", fontsize=8)
            ax1.tick_params(labelsize=8)

            # 3. Data Misfit Distribution (Response vs Measured)
            ax2 = fig.add_subplot(gs[2, 0])
            if len(self.response) == len(self.df):
                misfit = ((self.response - self.df['rhoa (Ohm.m)'].to_numpy()) / self.df['rhoa (Ohm.m)'].to_numpy()) * 100
                ax2.hist(misfit, bins=50, color='crimson', alpha=0.7)
                ax2.set_title("Relative Data Misfit Distribution (Response vs Data)", fontsize=10, loc='left')
                ax2.set_xlabel("Relative Difference (%)", fontsize=8)
                ax2.tick_params(labelsize=8)

        # --- Page 2: Inversion Model & Parameters ---
        with self.page(rows=2, cols=1, landscape=False, height_ratios=[2, 1]) as (fig, gs):
            fig.suptitle(f"Ensemble Test: {self.run_id} | Inversion Model", fontsize=13, fontweight='bold', y=0.98)
            
            # 1. Plot Model using custom plot_array_on_mesh
            ax0 = fig.add_subplot(gs[0, 0])
            vmin, vmax = np.percentile(self.model, [3, 97])
            ax0, collection = plot_array_on_mesh(
                self.polygons, 
                array=self.model, 
                ax=ax0, 
                cmap='Spectral_r', 
                norm=LogNorm(vmin=max(vmin, 1e-2), vmax=vmax)
            )
            cbar = fig.colorbar(collection, ax=ax0, pad=0.01, fraction=0.05)
            cbar.set_label(r"Resistivity ($\Omega\cdot$m)", fontsize=8)
            cbar.ax.tick_params(labelsize=7)
            ax0.set_title(r"Inverted Resistivity Model ($\rho$)", fontsize=10, loc='left')
            ax0.set_xlabel("X (m)", fontsize=8)
            ax0.set_ylabel("Z (m)", fontsize=8)
            ax0.tick_params(labelsize=8)

            # 2. Text Summary Block
            ax1 = fig.add_subplot(gs[1, 0])
            ax1.axis('off')
            
            stats_text = (
                f"CONVERGENCE METRICS:\n"
                f"Final Chi-Square (chi2): {self.metrics.get('chi2', 0):.3f}\n"
                f"Final Relative RMS:     {self.metrics.get('rms', 0):.3f}%\n"
                f"Total Iterations:       {self.metrics.get('iterations', 'N/A')}\n"
            )
            
            param_text = "INVERSION PARAMETERS:\n" + "\n".join([f"{k}: {v}" for k, v in self.params.items()])
            
            ax1.text(0.05, 0.9, stats_text, fontsize=9, family='monospace', va='top')
            ax1.text(0.55, 0.9, param_text, fontsize=9, family='monospace', va='top')