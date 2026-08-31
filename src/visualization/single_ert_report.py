import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import pandas as pd
import pygimli as pg
import pygimli.physics.ert as ert
from pathlib import Path

from src.visualization.report_base import ReportBase

class SingleSurveyERTReport(ReportBase):
    def __init__(self, filepath: str | Path, df: pd.DataFrame, mgr: ert.ERTManager, params: dict, run_id: str):
        """
        Args:
            filepath: Destination PDF path.
            df: Standardized DataFrame for the single survey.
            mgr: The PyGIMLi ERTManager post-inversion.
            params: Dictionary of parameters used for this run.
            run_id: Unique identifier for the title.
        """
        super().__init__(filepath)
        self.df = df
        self.mgr = mgr
        self.params = params
        self.run_id = run_id
        
        # Extract PyGIMLi data container
        self.data = self.mgr.data

    @classmethod
    def print(cls, *args, **kwargs):
        with cls(*args, **kwargs) as report:
            report.build()

    def build(self):
        self._build_page_1_data()
        self._build_page_2_inversion()
        self._build_page_3_coverage()

    def _build_page_1_data(self):
        """Page 1: Apparent Resistivity, Data Errors, and Layout"""
        with self.page(rows=3, cols=1, landscape=False) as (fig, gs):
            fig.suptitle(f"Run ID: {self.run_id} | Raw Data & Quality", fontsize=14, fontweight='bold', y=0.98)
            
            # 1. Apparent Resistivity Pseudo-section
            ax0 = fig.add_subplot(gs[0, 0])
            ert.show(self.data, vals=self.data("rhoa"), ax=ax0, cMap="Spectral_r", colorBar=True)
            ax0.set_title(r"Apparent Resistivity $\rho_a$ Pseudo-section", fontsize=11, loc='left')
            
            # 2. Error Distribution
            ax1 = fig.add_subplot(gs[1, 0])
            if 'err_rec (%)' in self.df.columns and self.df['err_rec (%)'].notna().any():
                self.df['err_rec (%)'].plot(kind='hist', bins=50, ax=ax1, color='teal', alpha=0.7, label='Reciprocal Error')
            if 'err_stk (%)' in self.df.columns and self.df['err_stk (%)'].notna().any():
                self.df['err_stk (%)'].plot(kind='hist', bins=50, ax=ax1, color='orange', alpha=0.7, label='Stacking Error')
            
            ax1.set_title("Error Distributions", fontsize=11, loc='left')
            ax1.set_xlabel("Error (%)")
            ax1.set_xlim(0, max(self.df['err_stk (%)'].max(), 10)) # Cap display reasonably
            ax1.legend()
            
            # 3. Electrode Topography / Layout
            ax2 = fig.add_subplot(gs[2, 0])
            sensor_x = [self.data.sensorPosition(i)[0] for i in range(self.data.sensorCount())]
            sensor_z = [self.data.sensorPosition(i)[2] for i in range(self.data.sensorCount())]
            
            ax2.plot(sensor_x, sensor_z, 'kv-', markersize=4, label='Electrodes')
            ax2.set_title("Electrode Array Geometry", fontsize=11, loc='left')
            ax2.set_xlabel("Distance (m)")
            ax2.set_ylabel("Elevation (m)")
            ax2.grid(True, linestyle='--', alpha=0.5)

    def _build_page_2_inversion(self):
        """Page 2: Final Model, Misfit, and Parameters"""
        with self.page(rows=3, cols=1, landscape=False, height_ratios=[1.5, 1.5, 1]) as (fig, gs):
            fig.suptitle(f"Run ID: {self.run_id} | Inversion Results", fontsize=14, fontweight='bold', y=0.98)
            
            # 1. Inverted Resistivity Section
            ax0 = fig.add_subplot(gs[0, 0])
            pg.show(self.mgr.paraDomain, self.mgr.model, ax=ax0, cMap="Spectral_r", logScale=True, colorBar=True, label="Resistivity (Ohm.m)")
            ax0.set_title(r"Absolute Resistivity Model ($\rho$)", fontsize=11, loc='left')
            
            # 2. Normalized Data Misfit Pseudo-section
            # Shows how well the forward response matches the measured data relative to error
            ax1 = fig.add_subplot(gs[1, 0])
            misfit = (self.mgr.inv.response - self.data("rhoa")) / self.data("err")
            ert.show(self.data, vals=misfit, ax=ax1, cMap="bwr", cMin=-3, cMax=3, colorBar=True, label="Normalized Misfit")
            ax1.set_title("Data Misfit Pseudo-section (Response vs Data)", fontsize=11, loc='left')
            
            # 3. Parameter and Metric Summary Text Block
            ax2 = fig.add_subplot(gs[2, 0])
            ax2.axis('off')
            
            stats_text = (
                f"FINAL METRICS:\n"
                f"Iterations: {len(self.mgr.inv.chi2History)}\n"
                f"Final Chi-Square (\u03C7\u00B2): {self.mgr.inv.chi2():.3f}\n"
                f"Final Relative RMS: {self.mgr.inv.relrms():.3f}%\n"
            )
            
            param_text = "INVERSION PARAMETERS:\n" + "\n".join([f"{k}: {v}" for k, v in self.params.items()])
            
            ax2.text(0.1, 0.9, stats_text, fontsize=10, family='monospace', va='top')
            ax2.text(0.5, 0.9, param_text, fontsize=10, family='monospace', va='top')

    def _build_page_3_coverage(self):
        """Page 3: Model Resolution / Sensitivity"""
        with self.page(rows=2, cols=1, landscape=False) as (fig, gs):
            fig.suptitle(f"Run ID: {self.run_id} | Model Resolution", fontsize=14, fontweight='bold', y=0.98)
            
            # 1. Coverage (Standard PyGIMLi metric for sensitivity)
            ax0 = fig.add_subplot(gs[0, 0])
            coverage = self.mgr.coverage()
            pg.show(self.mgr.paraDomain, coverage, ax=ax0, cMap="magma", colorBar=True, label="Coverage")
            ax0.set_title("Log-Scaled Coverage (Sensitivity)", fontsize=11, loc='left')
            
            # 2. Standardized Coverage Threshold (Binary Mask of Reliable Data)
            # Typically, areas with coverage < 0 (or a specific small value) are highly unreliable
            ax1 = fig.add_subplot(gs[1, 0])
            reliable_mask = np.where(coverage > 0.01, 1, 0) # Adjust threshold as needed for your array
            pg.show(self.mgr.paraDomain, reliable_mask, ax=ax1, cMap="Blues", colorBar=False)
            ax1.set_title("Reliable Resolution Zone Mask", fontsize=11, loc='left')