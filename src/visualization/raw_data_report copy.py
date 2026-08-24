import pandas as pd
from pathlib import Path
from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import format_time_axis, plot_electrodes

class RawDataReport(ReportBase):
    def __init__(self, df: pd.DataFrame, df_pos: pd.DataFrame, filepath: str | Path, max_groups=15):
        super().__init__(filepath)
        self.df = df
        self.geom_df = df_pos
        self.max_groups = max_groups
        self.start, self.end = self.df.index.min(), self.df.index.max()

    def build(self):
        self._page_survey_data_metrics()
        self._page_timeseries()
    
    @classmethod
    def print(cls, df: pd.DataFrame, df_pos: pd.DataFrame, filepath: str | Path, max_groups=15):
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
        
        self.save_current_page(fig) # <--- Save and close immediately

    def _page_timeseries(self):
        res_col = 'R (Ohm)' 
        if res_col:
            label = "Resistance (Ohm)"
            self._plot_grouped_pages([res_col], page_title='Electrical time series', y_labels={res_col: label})

    def _plot_grouped_pages(self, columns, page_title, y_labels=None):
        required = {'A', 'B', 'M', 'N'}
        if not required.issubset(self.df.columns):
            return

        grouped = self.df.groupby(['A', 'B'], sort=False)
        total_groups = grouped.ngroups
        groups_to_plot = list(grouped)[:self.max_groups]

        for page_number, ((a, b), group) in enumerate(groups_to_plot, start=1):
            fig, gs = self.create_page(rows=1, cols=2, width_ratios=[4, 1.35])
            ax = fig.add_subplot(gs[0, 0])
            geometry_ax = fig.add_subplot(gs[0, 1])

            for (m, n), mn_group in group.groupby(['M', 'N'], sort=False):
                for column in columns:
                    if column in mn_group.columns:
                        values = pd.to_numeric(mn_group[column], errors='coerce')
                        valid = values.notna()
                        if valid.any():
                            trace_label = f"M{m}-N{n}" if len(columns) == 1 else f"M{m}-N{n} {column}"
                            ax.plot(mn_group.index[valid], values[valid], marker='o', markersize=3, linewidth=0.8, label=trace_label)

            ax.set_title(f"{page_title}: A{a}-B{b}  |  group {page_number}/{total_groups}")
            ax.set_ylabel(', '.join(y_labels.get(c, c) if y_labels else c for c in columns))
            ax.grid(True, linestyle='--', alpha=0.5)
            format_time_axis(ax)
            
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=7)

            if self.geom_df is not None and not self.geom_df.empty:
                colors = {'tab:red': [a, b], 'tab:blue': group['M'].dropna().unique(), 'tab:green': group['N'].dropna().unique()}
                plot_electrodes(self.geom_df, colors=colors, projection='xz', ax=geometry_ax)
                geometry_ax.set_title('Electrodes', fontsize=9)
            else:
                geometry_ax.set_visible(False)
                
            self.save_current_page(fig)  # <--- Save and close immediately