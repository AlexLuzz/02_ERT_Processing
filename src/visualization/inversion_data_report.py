from matplotlib.colors import Normalize, LogNorm
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import extract_polygons, plot_array_on_mesh, plot_electrodes

class InversionDataReport(ReportBase):
    def __init__(self, filepath: str | Path, results_list, mesh, elec_pos: pd.DataFrame, logs: list = None, title: str = "ERT Inversion Report"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        super().__init__(f"{filepath}_{timestamp}.pdf")
        
        self.mesh = mesh
        self.elec_pos = elec_pos
        self.logs = logs or []
        self.title = title
        self.polygons = extract_polygons(self.mesh)
        
        # Parse and format the data exactly once upon initialization
        self._unpack_results(results_list)

    def _unpack_results(self, results):
        """Converts results directly into clean NumPy arrays and standardized lists."""
        # --- THE FIX: Smart Dictionary Handling ---
        if isinstance(results, dict):
            if 'model' in results:
                # It is a single run dictionary (from run_single)
                results = [results]
            else:
                # It is a nested dictionary of multiple runs (older run_ensemble format)
                results = list(results.values())

        # Vectorized NumPy arrays
        self.models = np.array([r['model'] for r in results])
        self.responses = np.array([r['response'] for r in results])
        self.times = np.array([r['time'] for r in results])
        self.chi2 = np.array([r['chi2'] for r in results], dtype=float)
        self.rms = np.array([r['rms'] for r in results], dtype=float)

        # Standard lists for variable-length items
        self.params = [r.get('params', {}) for r in results]
        self.chi2_histories = [r.get('chi2_history', []) for r in results]

        # Optional sensitivity array
        if results and 'coverage' in results[0]:
            self.coverages = np.array([r['coverage'] for r in results])
        else:
            self.coverages = None

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def build(self):
        """Orchestrates the sequence of pages in the report."""
        self._print_cover_page()
        
        if len(self.models) > 0:
            self._print_grid_pages(self.models, title_prefix="Absolute Resistivity", cmap='Spectral_r')
            
        if self.coverages is not None:
            self._print_grid_pages(self.coverages, title_prefix="Sensitivity (Standardized Coverage)", cmap='magma')
            
        if len(self.chi2_histories) > 0:
            self._print_convergence_page()

    def _print_cover_page(self):
        with self.page(rows=2, cols=1, height_ratios=[1, 1.5]) as (fig, gs):
            fig.suptitle(self.title, fontsize=18, fontweight='bold')
            
            # Top: Execution Logs
            ax_logs = fig.add_subplot(gs[0, 0])
            ax_logs.axis('off')
            log_text = "\n".join(self.logs) if self.logs else "No execution logs provided."
            ax_logs.text(0.02, 0.95, log_text, fontsize=9, fontfamily='monospace', va='top', ha='left', wrap=True)
            
            # Bottom: Mesh & Geometry
            ax_mesh = fig.add_subplot(gs[1, 0])
            plot_array_on_mesh(self.polygons, array=np.zeros(self.mesh.cellCount()), ax=ax_mesh, cmap='Greys', alpha=0.3)
            plot_electrodes(self.elec_pos, ax=ax_mesh, show_numbers=True, number_every=4)
            ax_mesh.set_title("Finite Element Mesh & Electrode Array", fontsize=12, fontweight='bold')

    def _print_grid_pages(self, data_array: np.ndarray, title_prefix: str, cmap: str, rows: int = 5, cols: int = 2):
        """Generic plotting loop that iterates directly over the clean 2D NumPy array."""
        # Direct percentile calculation on the 2D NumPy array
        vmin, vmax = np.percentile(data_array, [3, 97])
        norm = LogNorm(vmin=max(vmin, 1e-1), vmax=vmax) if 'Resistivity' in title_prefix else Normalize(vmin=vmin, vmax=vmax)

        plots_per_page = rows * cols
        n_plots = len(data_array)
        
        # Create chunked indices for pagination
        chunks = [range(i, min(i + plots_per_page, n_plots)) for i in range(0, n_plots, plots_per_page)]

        for chunk in chunks:
            with self.page(rows=rows, cols=cols, landscape=True) as (fig, gs):
                fig.suptitle(title_prefix, fontsize=16, fontweight='bold', y=0.98)

                for plot_idx, i in enumerate(chunk):
                    r, c = divmod(plot_idx, cols)
                    ax = fig.add_subplot(gs[r, c])

                    # Plot array
                    ax, collection = plot_array_on_mesh(self.polygons, array=data_array[i], ax=ax, cmap=cmap, norm=norm)
                    plot_electrodes(self.elec_pos, ax=ax)

                    # Simple indexing from standardized attributes
                    time_val = self.times[i]
                    time_str = time_val if isinstance(time_val, str) else time_val.strftime('%Y-%m-%d %H:%M')
                    
                    param_str = " | ".join([f"{k}: {v}" for k, v in self.params[i].items()]) if self.params[i] else ""
                    metrics_str = f"RRMS: {self.rms[i]:.1f}% (\u03C7\u00B2: {self.chi2[i]:.1f})"
                    left_title = f"[{param_str}]\n{metrics_str}" if param_str else metrics_str

                    # Dual-title layout
                    ax.set_title(left_title, fontsize=9, loc='left', pad=4)
                    ax.set_title(time_str, fontsize=9, loc='right', color='dimgrey')

                    # Clean inner axes
                    ax.tick_params(labelsize=8)
                    if c == 0: ax.set_ylabel("Z (m)", fontsize=8)
                    if r == rows - 1 or plot_idx >= len(chunk) - cols: ax.set_xlabel("X (m)", fontsize=8)

                # Append the colorbar for the whole page
                cbar = fig.colorbar(collection, ax=fig.axes, location='right', fraction=0.03, pad=0.02)
                cbar_label = r"Absolute Resistivity ($\Omega\cdot$m)" if 'Resistivity' in title_prefix else title_prefix
                cbar.set_label(cbar_label, fontsize=10)

    def _print_convergence_page(self):
        with self.page(rows=1, cols=1, landscape=True) as (fig, gs):
            fig.suptitle("Inversion Convergence History", fontsize=16, fontweight='bold', y=0.95)
            ax = fig.add_subplot(gs[0, 0])

            # Zip the parallel lists directly for plotting
            for chi2_hist, param, time_val in zip(self.chi2_histories, self.params, self.times):
                if not chi2_hist:
                    continue
                    
                # Setup label
                time_str = time_val if isinstance(time_val, str) else time_val.strftime('%Y-%m-%d')
                label_str = ", ".join([f"{k}:{v}" for k, v in param.items()]) if param else time_str
                
                # Plot directly on the axis
                ax.plot(range(1, len(chi2_hist) + 1), chi2_hist, marker='o', markersize=4, linewidth=1.5, label=label_str)

            ax.set_xlabel("Iteration Number", fontsize=11)
            ax.set_ylabel("\u03C7\u00B2 (Chi-Square Misfit)", fontsize=11)
            ax.set_yscale('log')
            ax.grid(True, which='both', linestyle='--', alpha=0.5)
            ax.legend(title="Run Identifiers", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
            fig.subplots_adjust(right=0.75)