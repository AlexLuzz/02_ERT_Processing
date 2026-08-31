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
    def filter_standard_survey(self, df, min_v=0.1, max_err_stk=5.0, max_err_rec=10.0):
        """Standardized cascade filter utilizing core threshold masks."""
        self.logger.info(f"--- Breakdown: Standard Survey Filtration ({len(df)} total meas) ---")
        
        # Voltage mask
        v_mask = get_threshold_mask(df, 'Vmn (mV)', min_val=min_v)
        self.logger.info(f" -> Voltage filter (Vmn > {min_v}mV): {(~v_mask).sum()} measurements dropped.")
        
        # Stacking Error mask
        stk_mask = get_threshold_mask(df, 'err_stk (%)', max_val=max_err_stk)
        self.logger.info(f" -> Stacking error filter (err_stk <= {max_err_stk}%): {(~stk_mask).sum()} measurements dropped.")
        
        # Combine
        final_mask = v_mask & stk_mask
        
        # Optional Reciprocal Error mask
        if 'err_rec (%)' in df.columns and df['err_rec (%)'].notna().any():
            rec_mask = get_threshold_mask(df, 'err_rec (%)', max_val=max_err_rec) | df['err_rec (%)'].isna()
            self.logger.info(f" -> Reciprocal error filter (err_rec <= {max_err_rec}%): {(~rec_mask).sum()} measurements dropped.")
            final_mask = final_mask & rec_mask
        else:
            self.logger.info(" -> Reciprocal error filter skipped (column missing or entirely NaN).")

        self.clean_dfs = df[final_mask].copy()
        return self.clean_dfs
    
    def print_logs(self):
        if self.memory_handler is None:
            print("Memory logging is not enabled.")
            return

        for log in self.memory_handler.logs:
            print(log)