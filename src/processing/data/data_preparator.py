from src.processing.data.data_tools import *
from src.processing.data.filtration_tools import *
from src.core.base import ProjectBase

from functools import wraps
import pandas as pd

def log_filtration(func):
    """Decorator to automatically log dropped measurements and top affected A-B pairs."""
    @wraps(func)
    def wrapper(self, df: pd.DataFrame, *args, **kwargs):
        start_len = len(df)
        
        # Execute the custom filtration function
        clean_df = func(self, df, *args, **kwargs)
        
        dropped = start_len - len(clean_df)
        
        if dropped > 0:
            dropped_df = df.loc[~df.index.isin(clean_df.index)]
            if 'A' in dropped_df.columns and 'B' in dropped_df.columns:
                top_pairs = dropped_df.groupby(['A', 'B']).size().nlargest(5)
                top_str = " | Top dropped A-B: " + ", ".join([f"{a}-{b} ({c})" for (a, b), c in top_pairs.items()])
            else:
                top_str = ""
        else:
            top_str = ""
            
        self.logger.info(f"Filter [{func.__name__}] completed | Dropped in total: {dropped}/{start_len}{top_str}")
        return clean_df
        
    return wrapper


class DataPreparator(ProjectBase):
    def __init__(self, **kwargs):
        # Force memory=True so filtration logs are ALWAYS captured for the report
        kwargs['memory'] = True
        super().__init__(**kwargs)
        self.clean_dfs = pd.DataFrame()
        
    @log_filtration
    def filter_mono2m_custom(self, df, min_v=0.1, max_err=5.0):
        """Example of a dedicated, site-specific filtration function."""
        mask = (df['Vmn (mV)'] >= min_v) & (df['err_stk (%)'] <= max_err)
        return df[mask].copy()

    @log_filtration
    def filter_standard_survey(self, df, thresholds):
        """Filter survey data using configurable min/max thresholds.
            
            Available cols to filter are :
                'A': 'Int64', 
                'B': 'Int64', 
                'M': 'Int64', 
                'N': 'Int64',
                'R (Ohm)': float, 
                'Vmn (mV)': float, 
                'Iab (mA)': float, 
                'Tx (V)': float,
                'R_ab (kOhm)': float, 
                'k (m)': float, 
                'rhoa (Ohm.m)': float,
                'err_stk (%)': float,
        thresholds : dict
            Example: {
            "Vmn (mV)": {"min": 0.1}, 
            "err_stk (%)": {"max": 5.0}
            }
            Supports "min" and/or "max".
        """
        self.logger.info(f"--- Survey Filtration ({len(df)} measurements) ---")
        final_mask = pd.Series(True, index=df.index)

        for param, cfg in thresholds.items():
            if param not in df.columns or not df[param].notna().any():
                self.logger.warning(f" -> Skipped '{param}' (missing or all NaN).")
                continue

            mask = pd.Series(True, index=df.index)

            if cfg.get("min") is not None:
                mask &= get_threshold_mask(df, param, min_val=cfg["min"])

            if cfg.get("max") is not None:
                mask &= get_threshold_mask(df, param, max_val=cfg["max"])

            self.logger.info(f" -> {param}: {(~mask).sum()} dropped.")
            final_mask &= mask

        self.clean_dfs = df[final_mask].copy()
        self.logger.info(f"--- Done: {len(self.clean_dfs)} remaining ---")
        return self.clean_dfs
        
    def print_logs(self):
        if self.memory_handler is None:
            print("Memory logging is not enabled.")
            return

        for log in self.memory_handler.logs:
            print(log)