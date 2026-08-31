from matplotlib.colors import Normalize, LogNorm
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import extract_polygons, plot_array_on_mesh, plot_electrodes

class InversionDataReport(ReportBase):
    def __init__(self, mesh, times, models, filepath: str | Path, elec_pos: pd.DataFrame):
        """
        Args:
            mesh: The PyGIMLi mesh.
            times: 1D Array/List of datetime objects.
            models: 2D Numpy array (or list of 1D arrays) of inversion results.
        """
        timestamp = datetime.now().strftime("%m%d_%H%M")
        super().__init__(f"{filepath}_{timestamp}")
        self.mesh = mesh
        self.times = times
        self.models = models
        self.elec_pos = elec_pos
        self.polygons = extract_polygons(self.mesh)

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def build(self):
        """Orchestrates the sequence of pages in the report."""

        # Calculate global percentiles (3rd and 97th) for absolute resistivity
        all_models = np.concatenate(self.models) if isinstance(self.models, list) else self.models
        res_vmin, res_vmax = np.percentile(all_models, [3, 97])

        # 1. Print Standard Resistivity (6 per page, Portrait)
        self.print_result_array_pages(
            times=self.times,
            models_array=self.models,
            title_prefix="Resistivity (Ohm.m)",
            cmap='Spectral_r', 
            norm=LogNorm(vmin=res_vmin, vmax=res_vmax),
            cbar_label="ρ (Ohm.m)",
            rows=6, cols=1, landscape=False
        )
        
        # 2. Calculate Variations dynamically using parallel arrays
        # The first time step in the list acts as the baseline
        baseline_array = self.models[0]
        var_models = [((model / baseline_array) - 1) * 100 for model in self.models]

        all_vars = np.concatenate(var_models) if isinstance(var_models, list) else var_models
        var_vmin, var_vmax = np.percentile(all_vars, [3, 97])
            
        # 3. Print Relative Variations (6 per page, Portrait)
        self.print_result_array_pages(
            times=self.times,
            models_array=var_models,
            title_prefix="Relative Var",
            cmap='RdBu_r', 
            norm=Normalize(vmin=var_vmin, vmax=var_vmax),
            cbar_label=r'$\Delta\rho$ (%)',
            rows=6, cols=1, landscape=False
        )

    def print_result_array_pages(self, times, models_array, title_prefix: str, 
                                 rows: int, cols: int, landscape: bool = False,
                                 cmap='Spectral_r', norm=None, cbar_label="Value"):
        
        plots_per_page = rows * cols
        
        # Zipping the parallel arrays dynamically here
        paired_data = list(zip(times, models_array))
        chunks = [paired_data[i:i + plots_per_page] for i in range(0, len(paired_data), plots_per_page)]

        for chunk in chunks:
            with self.page(rows=rows, cols=cols, landscape=landscape) as (fig, gs):
                
                for i, (time_val, array_data) in enumerate(chunk):
                    row_idx, col_idx = divmod(i, cols)
                    ax = fig.add_subplot(gs[row_idx, col_idx])
                    
                    # Ensure time is formatted beautifully for the title
                    time_str = time_val.strftime('%Y-%m-%d %H:%m')
                    
                    ax, collection = plot_array_on_mesh(
                        self.polygons, array=array_data, ax=ax, 
                        cmap=cmap, norm=norm
                    )

                    plot_electrodes(self.elec_pos, ax)
                    
                    # Re-added the Colorbar logic
                    cbar = fig.colorbar(collection, ax=ax, pad=0.01, fraction=0.05)
                    cbar.set_label(cbar_label, fontsize=8)
                    cbar.ax.tick_params(labelsize=7)
                    
                    ax.set_title(f"{title_prefix}: {time_str}", fontsize=9, loc='left', pad=3)
                    ax.tick_params(labelsize=8)
                    
                    # Hide X-labels unless it's the bottom row
                    if row_idx < rows - 1 and (i + cols) < len(chunk):
                        ax.set_xlabel('')
                        ax.tick_params(labelbottom=False)
                    else:
                        ax.set_xlabel('X (m)', fontsize=8)
                        
                    # Hide Y-labels unless it's the first column
                    if col_idx == 0:
                        ax.set_ylabel('Z (m)', fontsize=8)
                    else:
                        ax.set_ylabel('')
                        ax.tick_params(labelleft=False)