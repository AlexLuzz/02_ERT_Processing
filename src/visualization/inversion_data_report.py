import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from pathlib import Path

from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import extract_polygons, plot_array_on_mesh

class InversionDataReport(ReportBase):
    def __init__(self, mesh, variation_data: dict, filepath: str | Path, vmin=-50, vmax=50):
        """
        Args:
            mesh: The PyGIMLi mesh object.
            variation_data: Dictionary mapping {date: numpy_array_of_percentage_variation}.
            filepath: Destination PDF path.
            vmin/vmax: Bounds for the diverging colormap (default +/- 50%).
        """
        super().__init__(filepath)
        self.mesh = mesh
        self.variation_data = variation_data
        self.vmin = vmin
        self.vmax = vmax
        
        # Pre-extract polygons from the mesh to speed up plotting[cite: 19]
        self.polygons = extract_polygons(self.mesh)

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def build(self):
        # Enforce exactly 6 rows, 1 column per page in Portrait mode
        plots_per_page = 6 
        
        dates = list(self.variation_data.keys())
        chunks = [dates[i:i + plots_per_page] for i in range(0, len(dates), plots_per_page)]

        for chunk in chunks:
            with self.page(rows=plots_per_page, cols=1, landscape=False) as (fig, gs):
                for i, date_key in enumerate(chunk):
                    ax = fig.add_subplot(gs[i, 0])
                    array_data = self.variation_data[date_key]
                    
                    # Plot using a diverging colormap centered on 0%[cite: 19]
                    ax, collection = plot_array_on_mesh(
                        self.polygons, 
                        array=array_data, 
                        ax=ax, 
                        cmap='RdBu_r', 
                        norm=Normalize(vmin=self.vmin, vmax=self.vmax)
                    )
                    
                    # Attach a tight colorbar to each subplot
                    cbar = fig.colorbar(collection, ax=ax, pad=0.01, fraction=0.05)
                    cbar.set_label(r'$\Delta\rho$ (%)', fontsize=8)
                    cbar.ax.tick_params(labelsize=7)
                    
                    # Formatting
                    ax.set_title(f"Time-Lapse Variation: {date_key}", fontsize=9, loc='left', pad=3)
                    ax.tick_params(labelsize=8)
                    ax.set_xlabel('X (m)', fontsize=8)
                    ax.set_ylabel('Z (m)', fontsize=8)
                    
                    # Only show x-axis labels on the bottom-most plot of the page to save space
                    if i < len(chunk) - 1:
                        ax.set_xlabel('')
                        ax.tick_params(labelbottom=False)