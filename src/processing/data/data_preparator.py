from src.processing.data.data_tools import *
from src.processing.data.filtration_tools import *
from src.core.base import ProjectBase

from functools import wraps
import pandas as pd
from src.core.base import ProjectBase

def log_filtration(func):
    """Decorator to automatically log dropped measurements and top affected A-B pairs."""
    @wraps(func)
    def wrapper(self, df: pd.DataFrame, *args, **kwargs):
        start_len = len(df)
        
        # Execute the custom filtration function
        clean_df = func(self, df, *args, **kwargs)
        
        dropped = start_len - len(clean_df)
        
        if dropped > 0:
            # Isolate the exact rows that were dropped
            dropped_df = df.loc[~df.index.isin(clean_df.index)]
            
            # Find the top 5 A-B pairs affected
            if 'A' in dropped_df.columns and 'B' in dropped_df.columns:
                top_pairs = dropped_df.groupby(['A', 'B']).size().nlargest(5)
                top_str = " | Top dropped A-B: " + ", ".join([f"{a}-{b} ({c})" for (a, b), c in top_pairs.items()])
            else:
                top_str = ""
        else:
            top_str = ""
            
        self.logger.info(f"Filter [{func.__name__}] | Params: {kwargs} | Dropped: {dropped}/{start_len}{top_str}")
        return clean_df
        
    return wrapper


class DataPreparator(ProjectBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    @log_filtration
    def filter_mono2m_custom(self, df, min_v=0.1, max_err=5.0):
        """Example of a dedicated, site-specific filtration function."""
        mask = (df['Vmn (mV)'] >= min_v) & (df['err_stk (%)'] <= max_err)
        return df[mask].copy()