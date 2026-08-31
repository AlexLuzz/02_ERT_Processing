import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
from pathlib import Path
import pandas as pd
import numpy as np

from src.visualization.report_base import ReportBase
from src.visualization.basic_plotting import extract_polygons, plot_array_on_mesh

class FiltratedDataReport(ReportBase):
    def __init__(self, filepath: str | Path, df_raw: pd.DataFrame, df_clean: pd.DataFrame, geom_df: pd.DataFrame, mesh=None, preparator=None):
        super().__init__(filepath)
        self.df_raw = df_raw
        self.df_clean = df_clean
        self.geom_df = geom_df
        self.mesh = mesh
        
        # Extract memory logs if the preparator was provided and memory logging is active
        self.logs = []
        if preparator and getattr(preparator, 'memory_handler', None):
            self.logs = preparator.memory_handler.logs
        
        # Isolate the dropped data
        self.df_dropped = df_raw.loc[~df_raw.index.isin(df_clean.index)].copy()

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def _plot_custom_pseudo(self, ax, df, val_col, title, cmap, pmin=3, pmax=97, log_scale=True, is_abs=False):
        if df.empty or val_col not in df.columns or df[val_col].isna().all():
            ax.text(0.5, 0.5, f"No Data for {val_col}", ha='center', va='center', fontsize=10)
            ax.axis('off')
            return None
            
        pos = self.geom_df.set_index('elec_number')['X']
        df_valid = df.dropna(subset=['A', 'B', 'M', 'N', val_col])
        
        x_A, x_B = pos.loc[df_valid['A']].values, pos.loc[df_valid['B']].values
        x_M, x_N = pos.loc[df_valid['M']].values, pos.loc[df_valid['N']].values
        
        # Calculate array center and empirical pseudo-depth
        x_AB, x_MN = (x_A + x_B) / 2, (x_M + x_N) / 2
        x_plot = (x_AB + x_MN) / 2
        z_plot = -np.abs(x_AB - x_MN) / 3 
        
        vals = df_valid[val_col].values
        if is_abs:
            vals = np.abs(vals)
            
        # Dynamically compute bounds
        vmin, vmax = np.percentile(vals, [pmin, pmax]) if len(vals) > 0 else (0.1, 1)
        
        if log_scale:
            vmin = max(vmin, 1e-4) # Prevent log(0)
            norm = LogNorm(vmin=vmin, vmax=max(vmax, vmin + 1e-4))
        else:
            norm = Normalize(vmin=vmin, vmax=vmax)
            
        sc = ax.scatter(x_plot, z_plot, c=vals, cmap=cmap, norm=norm, s=15, marker='s', edgecolors='none')
        ax.set_title(title, fontsize=10, loc='left', pad=3)
        ax.set_xlabel("X (m)", fontsize=8)
        ax.set_ylabel("Pseudo-Depth", fontsize=8)
        ax.tick_params(labelsize=7)
        return sc

    def build(self):
        # --- PAGE 1: Filtration Logs ---
        with self.page(rows=1, cols=1, landscape=False) as (fig, gs):
            fig.suptitle("DataPreparator | Filtration Log Summary", fontsize=14, fontweight='bold', y=0.98)
            ax = fig.add_subplot(gs[0, 0])
            ax.axis('off')
            
            if self.logs:
                # Clean up formatting to just show the message payload
                clean_logs = [log.split(" - ")[-1] if " - " in log else log for log in self.logs]
                log_text = "\n\n".join(clean_logs)
            else:
                log_text = "No in-memory logs found.\nMake sure DataPreparator(memory=True) is initialized."
                
            ax.text(0.05, 0.95, log_text, fontsize=10, family='monospace', va='top', wrap=True)

        # --- PAGE 2: Raw Diagnostics ---
        with self.page(rows=4, cols=1, landscape=False, height_ratios=[1, 1, 1, 1]) as (fig, gs):
            
            # 1. Mesh & Electrodes
            ax0 = fig.add_subplot(gs[0, 0])
            if self.mesh is not None:
                plot_array_on_mesh(extract_polygons(self.mesh), array=None, ax=ax0)
            ax0.plot(self.geom_df['X'], self.geom_df['Z'] if 'Z' in self.geom_df else np.zeros(len(self.geom_df)), 
                     'kv', markersize=4, label='Electrodes')
            ax0.set_title("Mesh & Electrode Geometry", fontsize=10, loc='left')
            
            # 2. Injected Current (LogNorm, 0-100 percentiles to capture the whole range)
            ax1 = fig.add_subplot(gs[1, 0])
            sc1 = self._plot_custom_pseudo(ax1, self.df_raw, 'Iab (mA)', "Injected Current (Iab)", 'viridis', pmin=0, pmax=100, log_scale=True)
            if sc1:
                cbar = fig.colorbar(sc1, ax=ax1, pad=0.01, fraction=0.03)
                cbar.set_ticks([1, 2, 5, 20, 50, 100])
                cbar.set_ticklabels(['1', '2', '5', '20', '50', '100'])
                cbar.set_label("mA", fontsize=8)
            
            # 3. Measured Voltage (LogNorm, Abs values, 5-95 percentiles)
            ax2 = fig.add_subplot(gs[2, 0])
            sc2 = self._plot_custom_pseudo(ax2, self.df_raw, 'Vmn (mV)', "Measured Voltage (|Vmn|)", 'plasma', pmin=5, pmax=95, log_scale=True, is_abs=True)
            if sc2: fig.colorbar(sc2, ax=ax2, pad=0.01, fraction=0.03).set_label("|mV|", fontsize=8)
            
            # 4. Errors (LogNorm, 5-95 percentiles)
            ax3 = fig.add_subplot(gs[3, 0])
            if 'err_rec (%)' in self.df_raw.columns and self.df_raw['err_rec (%)'].notna().any():
                sc3 = self._plot_custom_pseudo(ax3, self.df_raw, 'err_rec (%)', "Reciprocal Error (%)", 'Reds', pmin=5, pmax=95, log_scale=True)
            else:
                sc3 = self._plot_custom_pseudo(ax3, self.df_raw, 'err_stk (%)', "Stacking Error (%)", 'Reds', pmin=5, pmax=95, log_scale=True)
            if sc3: fig.colorbar(sc3, ax=ax3, pad=0.01, fraction=0.03).set_label("%", fontsize=8)

        # --- PAGE 3: Apparent Resistivity Filtration ---
        with self.page(rows=3, cols=1, landscape=False) as (fig, gs):
            fig.suptitle(f"Filtration Map | Dropped {len(self.df_dropped)}/{len(self.df_raw)}", fontsize=12, fontweight='bold', y=0.98)
            
            ax0 = fig.add_subplot(gs[0, 0])
            sc_raw = self._plot_custom_pseudo(ax0, self.df_raw, 'rhoa (Ohm.m)', "RAW Apparent Resistivity", 'Spectral_r', pmin=3, pmax=97, log_scale=True, is_abs=True)
            
            # Extract the actual norm used on the first plot to strictly lock the colorbar for the others
            shared_norm = sc_raw.norm if sc_raw else None
            
            ax1 = fig.add_subplot(gs[1, 0])
            # Pass pmin/pmax but override by providing the shared_norm directly in the scatter plotting sequence
            self._plot_custom_pseudo(ax1, self.df_clean, 'rhoa (Ohm.m)', "CLEAN Apparent Resistivity", 'Spectral_r', pmin=3, pmax=97, log_scale=True, is_abs=True)
            if sc_raw and ax1.collections: ax1.collections[0].set_norm(shared_norm)
            
            ax2 = fig.add_subplot(gs[2, 0])
            if not self.df_dropped.empty:
                self._plot_custom_pseudo(ax2, self.df_dropped, 'rhoa (Ohm.m)', "DROPPED Measurements (Data Holes)", 'Spectral_r', pmin=3, pmax=97, log_scale=True, is_abs=True)
                if sc_raw and ax2.collections: ax2.collections[0].set_norm(shared_norm)
            else:
                ax2.text(0.5, 0.5, "No Data Dropped", ha='center', va='center')
                ax2.axis('off')
                
            if sc_raw:
                cbar = fig.colorbar(sc_raw, ax=[ax0, ax1, ax2], orientation='vertical', fraction=0.03, pad=0.02)
                cbar.set_label(r"Absolute $\rho_a$ ($\Omega\cdot$m)", fontsize=10)