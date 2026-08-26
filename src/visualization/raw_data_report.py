import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path

from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import format_time_axis, plot_electrodes, fetch_weather_data, plot_weather_data

class RawDataReport(ReportBase):
    def __init__(self, df: pd.DataFrame, df_pos: pd.DataFrame, filepath: str | Path, max_groups=40):
        super().__init__(filepath)
        self.df = df.copy()
        self.geom_df = df_pos
        self.max_groups = max_groups

        self.df['date_meas'] = pd.to_datetime(self.df['date_meas'])
        self.df = self.df.sort_values(by='date_meas')
        self.start, self.end = self.df['date_meas'].min(), self.df['date_meas'].max()

        self.weather_df = fetch_weather_data(self.start, self.end)

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def build(self):
        self._page_survey_data_metrics()
        self._build_timeseries_pages()

    def _page_survey_data_metrics(self):
        with self.page() as (fig, gs):
            ax = fig.add_subplot(gs[0, 0])
            ax.axis('off')
            log_text = f"DATASET LOG\n{'='*30}\nLength: {len(self.df)} rows\nPreview:\n{self.df.head(5).to_string()}"
            ax.text(0.05, 0.95, log_text, transform=ax.transAxes, fontsize=8, family='monospace', va='top')

    def _build_timeseries_pages(self, plots_per_page=3):
        col = 'rhoa (Ohm.m)'
        grouped = list(self.df.groupby(['A', 'B'], sort=False))[:self.max_groups]
        chunks = [grouped[i:i + plots_per_page] for i in range(0, len(grouped), plots_per_page)]

        # Fetch standard matplotlib cycle colors to map M-N series to geometry
        base_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

        for page_idx, chunk in enumerate(chunks):
            # Rows: 1 for each A-B pair, plus 1 for weather. Cols: 2 (75% / 25%)
            rows = len(chunk) + 1 
            # 75% width for Timeseries, 25% for Geometry
            with self.page(rows=rows, cols=2, width_ratios=[3, 1], landscape=True) as (fig, gs):
                shared_ax = None

                for i, ((a, b), group) in enumerate(chunk):
                    
                    # First time-series axis defines the shared x-axis.
                    ax_ts = (
                    fig.add_subplot(gs[i, 0]) if shared_ax is None 
                    else fig.add_subplot(gs[i, 0], sharex=shared_ax))

                    if shared_ax is None:
                        shared_ax = ax_ts

                    ax_geom = fig.add_subplot(gs[i, 1])
                    
                    # Highlight A-B injection in red
                    geom_colors = {'tab:red': [a, b]} 
                    
                    # Loop over M-N receiver pairs
                    for j, ((m, n), mn_group) in enumerate(group.groupby(['M', 'N'], sort=False)):
                        color = base_colors[j % len(base_colors)]
                        
                        ax_ts.scatter(mn_group['date_meas'], mn_group[col], color=color, s=8, label=f"M{m}-N{n}")
                        
                        # Assign this exact color to the M-N geometry pair
                        geom_colors[color] = [m, n]
                        
                    ax_ts.set_ylabel("Apparent Resistivity (Ω·m)", fontsize=8)
                    ax_ts.grid(True, ls='--', alpha=0.5)
                    ax_ts.tick_params(labelbottom=False)
                    ax_ts.legend(loc='upper left', fontsize=6, title=f"A-B : {a}-{b}")

                    # Plot Geometry alongside
                    plot_electrodes(self.geom_df, colors=geom_colors, ax=ax_geom)

                # --- WEATHER (Bottom Row, spans 1st column ONLY) ---
                ax_weather = fig.add_subplot(gs[-1, 0], sharex=shared_ax)
                plot_weather_data(self.weather_df, self.start, self.end, ax=ax_weather)
                