from .report_base import ReportBase
from .basic_plotting import * 
from .standard_page_01 import *
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime
from ..tools.csv_loader import load_csv

class HydrogeoSimulationReport(ReportBase):
    def __init__(self, solver, filename):
        super().__init__(filename)
        self.config = solver.config
        self.domain = solver.domain 
        self.monitoring = solver.monitoring
        self.scenario = solver.source_scenario

    def build(self):
        """Orchestrate the report structure here."""
        self._page_model_setup()
        self._page_timeseries()
        self._page_images()
    
    @classmethod
    def print(cls, solver, filename="results"):
        filename = Path(solver.config.output_dir) / filename
        with cls(solver, filename) as report:
            report.build()

    def _page_model_setup(self):
        fig, gs = self.create_page(rows=4, cols=2)
        ax_config = fig.add_subplot(gs[0,:])
        ax_config.axis("off")
        add_config_text(ax_config, self.config, self.domain)

        ax_domain = fig.add_subplot(gs[1,:])
        plot_domain(ax_domain, self.domain)

        ax_mat_params = fig.add_subplot(gs[2, 0])
        plot_material_report(ax_mat_params, self.domain.materials)

        ax_theta = fig.add_subplot(gs[3, 0])
        ax_kr = fig.add_subplot(gs[3, 1])
        plot_material_curves(ax_theta, ax_kr, self.domain.materials)

    def _page_timeseries(self):
        fig, gs = self.create_page(rows=3, cols=1)
        ax_head = fig.add_subplot(gs[0, :])
        wt_cols = [c for c in self.monitoring.probes_df.columns if 'water_table' in c]
        probe_df = self.monitoring.probes_df
        plot_timeseries(ax_head, probe_df, cols=wt_cols, 
                        source_mgr=self.scenario, y_label="Total Head (m)")
        
        raf_data = load_csv(self.config.paths.RAF_COMSOL_PZ_CG)
        base_date = pd.Timestamp(2024, 2, 22) # Ensure this matches your simulation start!
        raf_data["datetime"] = base_date + pd.to_timedelta(raf_data["Time (d)"], unit="D")
        raf_data = raf_data.set_index("datetime").sort_index()

        # 2. Resample to match simulation frequency (optional but helps with noise)
        dt_freq = f"{self.config.dt}S"
        raf_data = raf_data.resample(dt_freq).mean()

        # 3. Join with Simulation Data for Alignment
        # We combine both into one DataFrame to ensure they share the exact same axis
        combined_df = self.monitoring.probes_df.copy()

        # Extract just the datetime index to use for reindexing the sensor data
        sim_datetimes = combined_df.index.get_level_values('datetime')
        raf_aligned = raf_data.reindex(sim_datetimes).interpolate(method='linear').ffill()

        # Set the index of raf_aligned back to the MultiIndex of the simulation[cite: 2]
        raf_aligned.index = combined_df.index

        # 4. Plotting[cite: 1]
        ax_comp = fig.add_subplot(gs[1, :])

        # Fix: Use + for list concatenation instead of .append()
        external_cols = [f"LTC 10{i+1}" for i in range(3)]
        cols_to_plot = wt_cols + external_cols

        # Plot the aligned sensor data against the simulation results
        plot_timeseries(ax_comp, raf_aligned, cols=cols_to_plot, 
                        source_mgr=self.scenario, y_label="Total Head (m)")
        
        ax_res = fig.add_subplot(gs[2, :])

        # 1. Extract the clean datetime level for plotting
        x_axis = raf_aligned.index.get_level_values('datetime')

        # 2. Iterate using explicit names to ensure correct pairing
        for sim_col, ref_col in zip(wt_cols, external_cols):
            # Direct subtraction aligns perfectly because they share the same MultiIndex
            residual = combined_df[sim_col] - raf_aligned[ref_col]
            
            ax_res.plot(
                x_axis, 
                residual,
                lw=2,
                label=f"Residual: {ref_col}"
            )

        # 3. Formatting
        ax_res.axhline(0, color="black", lw=1.2, ls="--", alpha=0.6)
        ax_res.set_ylabel("Residual (m)")
        ax_res.grid(True, alpha=0.3)
        ax_res.legend(loc="upper left", fontsize='small', ncol=3)


    def _page_images(self):
        fig, gs = self.create_page(rows=1, cols=1)
        ax = fig.add_subplot(gs[:,:])
        cfg = SimpleNamespace(
        contour_levels=15,
        colormap="Blues",
        label="Effective Saturation",
        units="-"
        )
        plot_snapshot_grid(ax, self.monitoring.snapshots_df, 'saturation', cfg)
            


