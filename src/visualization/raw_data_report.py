import pandas as pd
from pathlib import Path
from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import format_time_axis, plot_electrodes, fetch_snow_data

class RawDataReport(ReportBase):
    def __init__(self, df: pd.DataFrame, df_pos: pd.DataFrame, filepath: str | Path, max_groups=40):
        super().__init__(filepath)
        self.df = df
        
        # 1. Force index to datetime if it isn't already, essential for mdates
        if not pd.api.types.is_datetime64_any_dtype(self.df.index):
            self.df.index = pd.to_datetime(self.df.index)
            
        self.geom_df = df_pos
        self.max_groups = max_groups
        self.start, self.end = self.df.index.min(), self.df.index.max()
        
        # 2. Fetch Weather data automatically
        try:
            self.rain_df, _, self.temp_df = fetch_snow_data(self.start, self.end, include_temp=True)
        except Exception as e:
            print(f"⚠️ Warning: Could not fetch weather data: {e}")
            self.rain_df, self.temp_df = None, None

    def build(self):
        self._page_survey_data_metrics()
        self._build_timeseries_pages()
    
    @classmethod
    def print(cls, df: pd.DataFrame, df_pos: pd.DataFrame, filepath: str | Path, max_groups=40):
        with cls(df=df, df_pos=df_pos, filepath=filepath, max_groups=max_groups) as report:
            report.build()

    def _page_survey_data_metrics(self):
        fig, gs = self.create_page(rows=1, cols=1)
        ax = fig.add_subplot(gs[0, 0])
        ax.axis('off')
        
        log_text = (
            f"DATASET LOGGING & SAFETY CHECK\n"
            f"{'='*60}\n\n"
            f"Dataset Length: {len(self.df)} rows\n"
            f"Start Date:     {self.start}\n"
            f"End Date:       {self.end}\n\n"
            f"Data Preview (First 5 Rows):\n"
            f"{'-'*60}\n"
            f"{self.df.head(5).to_string()}\n"
        )
        
        ax.text(0.05, 0.95, log_text, transform=ax.transAxes, fontsize=8, family='monospace', verticalalignment='top')
        ax.set_title("Report Initialization Log", loc='left')
        self.save_current_page(fig) 

    def _build_timeseries_pages(self, plots_per_page=4):
        """Batches data to plot Geometry (top), 4x Timeseries (middle), and Weather (bottom)."""
        res_col = 'R (Ohm)'
        if res_col not in self.df.columns:
            print(f"⚠️ Missing column: {res_col}")
            return
            
        required = {'A', 'B', 'M', 'N'}
        if not required.issubset(self.df.columns):
            return

        # Create list of groups and slice it by max_groups
        grouped = list(self.df.groupby(['A', 'B'], sort=False))[:self.max_groups]
        
        # Chunk groups into batches of 4
        chunks = [grouped[i:i + plots_per_page] for i in range(0, len(grouped), plots_per_page)]

        for page_idx, chunk in enumerate(chunks):
            # Dynamic grid based on how many plots are in the chunk (usually 4, but last page might have less)
            rows = len(chunk) + 2
            height_ratios = [1.5] + [2]*len(chunk) + [1]
            
            fig, gs = self.create_page(rows=rows, cols=1, height_ratios=height_ratios)
            
            # --- TOP ROW: GEOMETRY ---
            ax_geom = fig.add_subplot(gs[0])
            active_a_b = []
            for (a, b), _ in chunk:
                active_a_b.extend([a, b])
                
            if self.geom_df is not None and not self.geom_df.empty:
                colors = {'tab:red': active_a_b} # Highlight all Txs used on this page
                plot_electrodes(self.geom_df, colors=colors, projection='xz', ax=ax_geom)
                ax_geom.set_title(f'Active Txs on Page {page_idx + 1}', fontsize=10)
            else:
                ax_geom.set_visible(False)

            # --- MIDDLE ROWS: TIME SERIES ---
            axes_data = []
            for i, ((a, b), group) in enumerate(chunk):
                ax = fig.add_subplot(gs[i + 1])
                axes_data.append(ax)
                
                for (m, n), mn_group in group.groupby(['M', 'N'], sort=False):
                    values = pd.to_numeric(mn_group[res_col], errors='coerce')
                    valid = values.notna()
                    if valid.any():
                        ax.plot(mn_group.index[valid], values[valid], marker='.', markersize=3, linewidth=0.8, label=f"M{m}-N{n}")
                
                ax.set_ylabel("R (Ω)", fontsize=8)
                ax.grid(True, linestyle='--', alpha=0.5)
                ax.tick_params(labelbottom=False) # Hide x-labels so they don't overlap
                
                # Legend grouping showing the A-B pair as the title
                handles, labels = ax.get_legend_handles_labels()
                if handles:
                    ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(1.01, 1.05), fontsize=6, title=f"Tx: A{a}-B{b}")

            # --- BOTTOM ROW: WEATHER ---
            # Share X-axis with the last data plot for precise alignment
            ax_weather = fig.add_subplot(gs[-1], sharex=axes_data[-1] if axes_data else None)
            
            if self.rain_df is not None and not self.rain_df.empty:
                ax_weather.bar(self.rain_df['date'], self.rain_df['rain'], color='tab:blue', alpha=0.4, label='Rain')
                ax_weather.set_ylabel('Rain (mm)', fontsize=8, color='tab:blue')
                ax_weather.tick_params(axis='y', labelcolor='tab:blue')
                
            if self.temp_df is not None and not self.temp_df.empty:
                ax_temp = ax_weather.twinx()
                ax_temp.plot(self.temp_df['date'], self.temp_df['temp'], color='tab:red', alpha=0.7, label='Temp')
                ax_temp.set_ylabel('Temp (°C)', fontsize=8, color='tab:red')
                ax_temp.tick_params(axis='y', labelcolor='tab:red')

            ax_weather.grid(True, linestyle='--', alpha=0.3)
            
            # Apply our 45-degree Date Formatter to the very bottom axis
            format_time_axis(ax_weather)
            
            # Tweak spacing so twinx and legends don't clip out of the right side
            fig.subplots_adjust(right=0.82) 
            self.save_current_page(fig)