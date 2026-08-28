import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from pathlib import Path
import numpy as np

from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import extract_polygons, plot_array_on_mesh

class InversionDataReport(ReportBase):
    def __init__(self, mesh, inv_data: dict, filepath: str | Path):
        """
        Args:
            mesh: The PyGIMLi mesh.
            inv_data: Dictionary mapping {date_string: numpy_array}.
        """
        super().__init__(filepath)
        self.mesh = mesh
        self.inv_data = inv_data
        self.polygons = extract_polygons(self.mesh)
        self.dates = list(self.inv_data.keys())

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def build(self):
        """Orchestrates the sequence of pages in the report."""
        
        # 1. Print Standard Resistivity (6 per page, Portrait)
        self.print_result_array_pages(
            data_dict=self.inv_data,
            title_prefix="Abs Resistivity",
            cmap='Spectral_r', vmin=0, vmax=200, cbar_label="R (Ohm.m)",
            rows=6, cols=1, landscape=False
        )
        
        # 2. Calculate Variations dynamically
        baseline_array = self.inv_data[self.dates[0]]
        var_data = {}
        for date, array in self.inv_data.items():
            var_data[date] = ((array / baseline_array) - 1) * 100
            
        # 3. Print Relative Variations (6 per page, Portrait)
        self.print_result_array_pages(
            data_dict=var_data,
            title_prefix="Relative Var",
            cmap='RdBu_r', vmin=-50, vmax=50, cbar_label=r'$\Delta\rho$ (%)',
            rows=6, cols=1, landscape=False
        )

    def print_result_array_pages(self, data_dict: dict, title_prefix: str, 
                                 rows: int, cols: int, landscape: bool = False,
                                 width_ratios=None, height_ratios=None,
                                 cmap='Spectral_r', vmin=None, vmax=None, cbar_label="Value"):
        """
        A highly versatile function to print any dictionary of arrays into a grid layout.
        Automatically batches data across multiple PDF pages.
        """
        plots_per_page = rows * cols
        keys = list(data_dict.keys())
        chunks = [keys[i:i + plots_per_page] for i in range(0, len(keys), plots_per_page)]

        for chunk in chunks:
            with self.page(rows=rows, cols=cols, landscape=landscape, 
                           width_ratios=width_ratios, height_ratios=height_ratios) as (fig, gs):
                
                for i, key in enumerate(chunk):
                    row_idx, col_idx = divmod(i, cols)
                    ax = fig.add_subplot(gs[row_idx, col_idx])
                    
                    array_data = data_dict[key]
                    
                    ax, collection = plot_array_on_mesh(
                        self.polygons, array=array_data, ax=ax, 
                        cmap=cmap, norm=Normalize(vmin=vmin, vmax=vmax)
                    )
                    
                    # Attach a tight colorbar
                    cbar = fig.colorbar(collection, ax=ax, pad=0.01, fraction=0.05)
                    cbar.set_label(cbar_label, fontsize=8)
                    cbar.ax.tick_params(labelsize=7)
                    
                    ax.set_title(f"{title_prefix}: {key}", fontsize=9, loc='left', pad=3)
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