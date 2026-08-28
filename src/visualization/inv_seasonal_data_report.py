import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates

class AdvancedInversionReport(InversionDataReport):
    def __init__(self, mesh, inv_data: dict, ts_positions: list, weather_df, filepath: str | Path):
        super().__init__(mesh, inv_data, filepath)
        self.ts_positions = ts_positions
        self.weather_df = weather_df
        
        # Calculate variations globally for the advanced layout[cite: 20]
        baseline = self.inv_data[self.dates[0]]
        self.var_data = {k: ((v / baseline) - 1) * 100 for k, v in self.inv_data.items()}
        
        # Extract Point Time-Series
        self.ts_df = extract_point_timeseries(self.mesh, self.inv_data, self.ts_positions)
        self.var_ts_df = extract_point_timeseries(self.mesh, self.var_data, self.ts_positions)

    def build(self):
        self.print_advanced_summary_page()

    def print_advanced_summary_page(self):
        """Recreates the complex 5-row, nested gridspec layout[cite: 20]."""
        
        # Open a landscape page context, ignoring the default 1x1 gridspec
        with self.page(landscape=True) as (fig, _):
            
            # 1. Define the macro grid[cite: 20]
            gs_macro = gridspec.GridSpec(
                5, 4, figure=fig,
                width_ratios=[0.8, 0.25, 2.5, 0.7], 
                height_ratios=[1, 1, 0.1, 1, 1],
                wspace=0.1, hspace=0.2
            )
            
            # 2. Define the nested micro grid for the 2D sections[cite: 20]
            n_snaps = len(self.dates)
            gs_section = gridspec.GridSpecFromSubplotSpec(
                2, n_snaps - 1, 
                subplot_spec=gs_macro[3:, :], 
                wspace=0.1, hspace=0.1
            )
            
            # --- ROW 0 & 1: TIME SERIES ---
            ax_ts1 = fig.add_subplot(gs_macro[0, 2])
            ax_ts2 = fig.add_subplot(gs_macro[1, 2], sharex=ax_ts1)
            
            dates_dt = pd.to_datetime(self.dates)
            
            for col in self.ts_df.columns:
                ax_ts1.plot(dates_dt, self.ts_df[col], marker='o', ms=3, lw=1)
                ax_ts2.plot(dates_dt, self.var_ts_df[col], marker='o', ms=3, lw=1)
                
            ax_ts1.set_ylabel("Resistivity", fontsize=8)
            ax_ts2.set_ylabel(r"$\Delta\rho$ (%)", fontsize=8)
            ax_ts2.axhline(0, color='k', lw=0.8, ls='--')[cite: 20]
            
            # Add Weather via TwinX[cite: 20]
            ax_w1 = ax_ts1.twinx()
            ax_w1.bar(self.weather_df['date'], self.weather_df['rain'], color='blue', alpha=0.3)
            
            # --- ROW 2 & 3: MESH SNAPSHOTS ---
            for j, date_key in enumerate(self.dates[1:]): # Skip baseline
                
                # Top snapshot: Absolute
                ax_abs = fig.add_subplot(gs_section[0, j])
                plot_array_on_mesh(self.polygons, self.inv_data[date_key], ax=ax_abs, cmap='Spectral_r')
                ax_abs.set_title(date_key, fontsize=7)
                
                # Bottom snapshot: Variation
                ax_var = fig.add_subplot(gs_section[1, j])
                plot_array_on_mesh(self.polygons, self.var_data[date_key], ax=ax_var, cmap='RdBu_r', norm=Normalize(-50, 50))
                
                if j > 0:
                    ax_abs.tick_params(labelleft=False)
                    ax_var.tick_params(labelleft=False)