from matplotlib.colors import Normalize, LogNorm, BoundaryNorm
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pygimli as pg

from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import extract_polygons, plot_array_on_mesh, plot_electrodes
import matplotlib.ticker as ticker

class InversionDataReport(ReportBase):
    def __init__(self, folder_path: str | Path, results_list, mesh, paradomain, elec_pos: pd.DataFrame, logs: list = None, title: str = "ERT Inversion Report"):
        # Standardize the filename internally
        filepath = Path(folder_path) / "data_report.pdf"
        super().__init__(filepath)
        
        self.mesh = mesh
        self.paradomain = paradomain
        self.elec_pos = elec_pos
        self.logs = logs or []
        self.title = title
        self.mesh_polygons = extract_polygons(self.mesh)
        self.paradomain_polygons = extract_polygons(self.paradomain)
        self._unpack_results(results_list)

    def _unpack_results(self, results):
        if isinstance(results, dict):
            if 'model' in results:
                results = [results]
            else:
                results = list(results.values())

        self.models = np.array([r['model'] for r in results])
        self.responses = np.array([r['response'] for r in results])
        self.times = np.array([r['date_survey'] for r in results])
        self.chi2 = np.array([r['chi2'] for r in results], dtype=float)
        self.rms = np.array([r['rms'] for r in results], dtype=float)
        self.params = [r.get('params', {}) for r in results]
        self.chi2_histories = [r.get('chi2_history', []) for r in results]
        self.start_model = results[0].get('start_model') if 'start_model' in results[0] else None

    @classmethod
    def print(cls, folder_path: str | Path, *args, **kwargs):
        # Update the classmethod to mirror the new initialization parameters
        with cls(folder_path, *args, **kwargs) as report:
            report.build()

    def build(self):
        self._print_cover_page()
        if len(self.models) > 0:
            self._print_grid_pages(self.models, cmap_name='Spectral_r', title_prefix="Resistivity (Ohm·m)")
            self._print_focus_layer(self.models, cmap_name='Spectral_r', title_prefix="Resistivity (Ohm·m)", rows=4)
        if len(self.chi2_histories) > 0:
            self._print_convergence_page()

    def _add_unified_colorbar(self, fig, cax, collection, title_prefix, ticks=None):
        """
        Creates a unified, discrete colorbar with integer formatting 
        and exact color-tick alignment.
        """
        cbar = fig.colorbar(
            collection, 
            cax=cax, 
            orientation='vertical', 
            spacing='uniform',   # Forces equal physical spacing between ticks 
            ticks=ticks,
            extend='both'        # Shows the over/under colors clearly at the ends
        )
        
        # Force numeric ticks with no decimals
        cbar.ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x)}"))
        
        cbar.set_label(title_prefix, fontsize=10)
        cbar.ax.tick_params(labelsize=8)
        
        return cbar

    def _print_cover_page(self):
        with self.page(rows=4, cols=1) as (fig, gs):
            fig.suptitle(self.title, fontsize=18, fontweight='bold')
            ax_logs = fig.add_subplot(gs[0, 0])
            ax_logs.axis('off')
            log_text = "\n".join(self.logs) if self.logs else "No execution logs provided."
            ax_logs.text(0.02, 0.95, log_text, fontsize=9, fontfamily='monospace', va='top', ha='left', wrap=True)

            ax_mesh = fig.add_subplot(gs[1, 0])
            plot_array_on_mesh(self.mesh_polygons, ax=ax_mesh, edgecolor='black', alpha=0.3, linewidth=0.1)
            plot_electrodes(self.elec_pos, ax=ax_mesh, show_numbers=True, number_every=4)
            ax_mesh.set_title(f"Starting Model on Paradomain: {self.mesh.cellCount()} cells, {self.mesh.nodeCount()} nodes, {self.mesh.boundaryCount()} boundaries", fontsize=8)

            ax_pd = fig.add_subplot(gs[2, 0])
            plot_array_on_mesh(self.paradomain_polygons, self.start_model, ax=ax_pd, edgecolor='black', alpha=0.3, linewidth=0.1)
            ax_pd.set_title(f"Starting Model on Paradomain: {self.paradomain.cellCount()} cells", fontsize=8)

    def _print_grid_pages(self, data_array: np.ndarray, cmap_name: str, title_prefix: str, rows: int = 5, cols: int = 2):
        vmin, vmax = np.nanpercentile(data_array, [3, 97])
        norm = LogNorm(vmin=max(vmin, 1e-1), vmax=vmax) if 'Resistivity' in title_prefix else Normalize(vmin=vmin, vmax=vmax)

        ticks = [5, 10, 20, 50, 100, 200, 500, 1000]
        cmap = plt.cm.get_cmap(cmap_name, len(ticks) - 1)
        cmap.set_under('gray')
        cmap.set_over('black')
        norm = BoundaryNorm(ticks, cmap.N) # Locks colors between ticks exactly

        plots_per_page = rows * cols
        n_plots = len(data_array)
        chunks = [range(i, min(i + plots_per_page, n_plots)) for i in range(0, n_plots, plots_per_page)]

        for chunk in chunks:
            with self.page(rows=rows, cols=cols + 1, width_ratios=[1, 1, 0.05], landscape=True) as (fig, gs):
                for plot_idx, i in enumerate(chunk):
                    r, c = divmod(plot_idx, cols)
                    ax = fig.add_subplot(gs[r, c])
                    ax, collection = plot_array_on_mesh(self.paradomain_polygons, array=data_array[i], ax=ax, cmap=cmap, norm=norm)
                    plot_electrodes(self.elec_pos, ax=ax)

                    time_val = self.times[i]
                    time_str = time_val if isinstance(time_val, str) else time_val.strftime('%Y-%m-%d %H:%M')
                    param_str = " | ".join([f"{k}: {v}" for k, v in self.params[i].items()]) if self.params[i] else ""
                    metrics_str = f"RRMS: {self.rms[i]:.1f}% (\u03C7\u00B2: {self.chi2[i]:.1f})"
                    left_title = f"[{param_str}]\n{metrics_str}" if param_str else metrics_str

                    ax.set_title(left_title, fontsize=9, loc='left', pad=4)
                    ax.set_title(time_str, fontsize=9, loc='right', color='dimgrey')
                    ax.tick_params(labelsize=8)
                    
                    if c == 0: ax.set_ylabel("Z (m)", fontsize=8)
                    if r == rows - 1 or plot_idx >= len(chunk) - cols: ax.set_xlabel("X (m)", fontsize=8)

                cbar_ax = fig.add_subplot(gs[1:3, -1])
                self._add_unified_colorbar(fig, cbar_ax, collection, title_prefix, ticks)

    def _print_focus_layer(self, data_array: np.ndarray, cmap_name: str, title_prefix: str, rows: int = 4):
        
        ticks = [5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
        cmap = plt.cm.get_cmap(cmap_name, len(ticks) - 1)
        cmap.set_under('gray')
        cmap.set_over('black')
        norm = BoundaryNorm(ticks, cmap.N)

        for start in range(0, len(data_array), rows):
            with self.page(rows=rows, cols=4, width_ratios=[1, 0.35, 0.35, 0.05], landscape=True) as (fig, gs):

                for row in range(min(rows, len(data_array) - start)):
                    i = start + row

                    # Full plot
                    ax = fig.add_subplot(gs[row, 0])
                    ax, collection = plot_array_on_mesh(self.paradomain_polygons, array=data_array[i], ax=ax, cmap=cmap, norm=norm)
                    plot_electrodes(self.elec_pos, ax=ax)

                    time = self.times[i]
                    time = time if isinstance(time, str) else time.strftime("%Y-%m-%d %H:%M")
                    params = " | ".join(f"{k}: {v}" for k, v in self.params[i].items())
                    metrics = f"RRMS: {self.rms[i]:.1f}% (χ²: {self.chi2[i]:.1f})"

                    ax.set_title(
                        f"[{params}]\n{metrics}" if params else metrics,
                        fontsize=9,
                        loc="left",
                        pad=4,
                    )
                    ax.set_title(time, fontsize=9, loc="right", color="dimgrey")
                    ax.set_ylabel("Z (m)", fontsize=8)

                    # Zooms
                    for col, xlim, ylim in [
                        (1, (20, 40), (-10, 1)),
                        (2, (120, 140), (-14, -4)),
                    ]:
                        ax_zoom = fig.add_subplot(gs[row, col])
                        ax_zoom, _ = plot_array_on_mesh(
                            self.paradomain_polygons,
                            array=data_array[i],
                            ax=ax_zoom,
                            cmap=cmap,
                            norm=norm,
                        )
                        ax_zoom.set(xlim=xlim, ylim=ylim)
                        plot_electrodes(self.elec_pos, ax=ax_zoom)

                    if row == rows - 1:
                        ax.set_xlabel("X (m)", fontsize=8)

                cbar_ax = fig.add_subplot(gs[1:3, -1])
                self._add_unified_colorbar(fig, cbar_ax, collection, title_prefix, ticks)

    def _print_convergence_page(self):
        with self.page(rows=1, cols=1, landscape=True) as (fig, gs):
            ax = fig.add_subplot(gs[0, 0])
            for chi2_hist, param, time_val in zip(self.chi2_histories, self.params, self.times):
                if not chi2_hist: continue
                time_str = time_val if isinstance(time_val, str) else time_val.strftime('%Y-%m-%d')
                label_str = ", ".join([f"{k}:{v}" for k, v in param.items()]) if param else time_str
                ax.plot(range(1, len(chi2_hist) + 1), chi2_hist, marker='o', markersize=4, linewidth=1.5, label=label_str)
            ax.set_xlabel("Iteration Number", fontsize=11)
            ax.set_ylabel("\u03C7\u00B2 (Chi-Square Misfit)", fontsize=11)
            ax.set_yscale('log')
            ax.grid(True, which='both', linestyle='--', alpha=0.5)
            ax.legend(title="Run Identifiers", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
            fig.subplots_adjust(right=0.75)