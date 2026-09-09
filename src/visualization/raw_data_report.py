import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import format_time_axis, plot_electrodes, fetch_snow_data

class RawDataReport(ReportBase):
    def __init__(self, folder_path: str | Path, df: pd.DataFrame, elec_pos: pd.DataFrame, 
                 max_groups: int = 40, filename: str = "_raw_data_report.pdf"):
        
        # 1. Enforce strict, standardized static output filename
        folder_path = Path(folder_path)
        super().__init__(folder_path / filename)
        
        self.df = df.copy()
        self.elec_pos = elec_pos
        self.max_groups = max_groups

        # Ensure datetime formatting and chronological sorting
        self.df['date_meas'] = pd.to_datetime(self.df['date_meas'])
        self.df = self.df.sort_values(by='date_meas')
        self.start, self.end = self.df['date_meas'].min(), self.df['date_meas'].max()

        # Fetch environmental data for the survey period
        self.rain_df, _, self.temp_df = fetch_snow_data(self.start, self.end, include_temp=True)

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def build(self):
        self._print_cover_page()
        self._build_timeseries_pages()

    def _print_cover_page(self):
        with self.page() as (fig, gs):
            ax = fig.add_subplot(gs[0, 0])
            ax.axis('off')
            
            # Formatted log text displaying basic dataset characteristics
            log_text = (
                f"RAW DATASET LOG\n"
                f"{'='*30}\n"
                f"Total Measurements: {len(self.df)} rows\n"
                f"Date Range: {self.start.date()} to {self.end.date()}\n\n"
                f"Preview:\n{self.df.head(10).to_string()}"
            )
            ax.text(0.05, 0.95, log_text, transform=ax.transAxes, fontsize=8, family='monospace', va='top')

    def _build_timeseries_pages(self, plots_per_page=3):
        # Fallback in case columns are named differently
        col = 'rhoa (Ohm.m)' if 'rhoa (Ohm.m)' in self.df.columns else 'rhoa'
        
        grouped = list(self.df.groupby(['A', 'B'], sort=False))[:self.max_groups]
        chunks = [grouped[i:i + plots_per_page] for i in range(0, len(grouped), plots_per_page)]

        # Fetch standard matplotlib cycle colors to map M-N series to geometry
        base_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

        for page_idx, chunk in enumerate(chunks):
            # Rows: 1 for each A-B pair, plus 1 for weather. Cols: 2 (75% / 25%)
            rows = len(chunk) + 1 
            with self.page(rows=rows, cols=2, width_ratios=[3, 1], landscape=True) as (fig, gs):
                
                axes_data = []
                for i, ((a, b), group) in enumerate(chunk):
                    # 75% width for Timeseries, 25% for Geometry
                    ax_ts = fig.add_subplot(gs[i, 0])
                    ax_geom = fig.add_subplot(gs[i, 1])
                    axes_data.append(ax_ts)
                    
                    # Highlight A-B injection in red
                    geom_colors = {'tab:red': [a, b]} 
                    
                    # Loop over M-N receiver pairs
                    for j, ((m, n), mn_group) in enumerate(group.groupby(['M', 'N'], sort=False)):
                        color = base_colors[j % len(base_colors)]
                        
                        # Plot with lines to clearly show the timeseries evolution
                        ax_ts.plot(mn_group['date_meas'], mn_group[col], marker='o', ls='-', 
                                   color=color, markersize=3, lw=1, alpha=0.8, label=f"M{m}-N{n}")
                        
                        # Assign this exact color to the M-N geometry pair
                        geom_colors[color] = [m, n]
                        
                    # Standardized Dual-Title Aesthetic
                    ax_ts.set_title(f"Injection Pair A-B: {a}-{b}", fontsize=9, loc='left', pad=4)
                    
                    ax_ts.set_ylabel(r"Apparent Resistivity ($\Omega\cdot$m)", fontsize=8)
                    ax_ts.grid(True, ls='--', alpha=0.5)
                    ax_ts.tick_params(labelbottom=False, labelsize=8)
                    ax_ts.legend(loc='upper left', fontsize=6, ncol=2)

                    # Plot Geometry alongside using the injected ax parameter
                    if self.elec_pos is not None:
                        plot_electrodes(self.elec_pos, ax=ax_geom, colors=geom_colors)
                        ax_geom.set_title("Configuration Geometry", fontsize=9, loc='right', color='dimgrey')

                # --- WEATHER (Bottom Row, spans 1st column ONLY) ---
                ax_weather = fig.add_subplot(gs[-1, 0], sharex=axes_data[-1] if axes_data else None)
                
                if self.rain_df is not None and not self.rain_df.empty:
                    ax_weather.bar(self.rain_df['date'], self.rain_df['rain'], color='tab:blue', alpha=0.4, label='Rain')
                    ax_weather.set_ylabel('Rain (mm)', fontsize=8, color='tab:blue')
                    
                if self.temp_df is not None and not self.temp_df.empty:
                    ax_temp = ax_weather.twinx()
                    ax_temp.plot(self.temp_df['date'], self.temp_df['temp'], color='tab:red', alpha=0.7)
                    ax_temp.set_ylabel('Temp (°C)', fontsize=8, color='tab:red')
                
                ax_weather.grid(True, ls='--', alpha=0.3)
                ax_weather.tick_params(labelsize=8)
                format_time_axis(ax_weather)