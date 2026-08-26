import pandas as pd
import numpy as np

def get_date_range_mask(df, date_col, start_date=None, end_date=None):
    """Returns True for rows where the date is within the specified range."""
    mask = pd.Series(True, index=df.index)

    if start_date is not None:
        mask &= df[date_col] >= start_date

    if end_date is not None:
        mask &= df[date_col] <= end_date

    return mask

def get_threshold_mask(df, col, min_val=-np.inf, max_val=np.inf):
    """Returns True for values strictly within the min/max bounds."""
    numeric_col = pd.to_numeric(df[col], errors='coerce')
    return (numeric_col > min_val) & (numeric_col <= max_val)

def get_excluded_elecs_mask(df, excluded_elecs, config_cols=['A', 'B', 'M', 'N']):
    """Returns False if any electrode in the configuration is in the excluded list."""
    # Ensure list of integers
    if isinstance(excluded_elecs, (int, str)):
        excluded_elecs = [int(excluded_elecs)]
    
    mask = ~df[config_cols].isin(excluded_elecs).any(axis=1)
    return mask

def get_excluded_configs_mask(df, excluded_configs, config_cols=['A', 'B', 'M', 'N']):
    """Returns False for exact A, B, M, N configuration matches."""
    mask = pd.Series(True, index=df.index)
    for A, B, M, N in excluded_configs:
        config_match = (df['A'] == A) & (df['B'] == B) & (df['M'] == M) & (df['N'] == N)
        mask &= ~config_match
    return mask

def get_hampel_mask(df, target_col, window_size=3, n_sigma=3.0, config_cols=['A', 'B', 'M', 'N']):
    """
    Vectorized Hampel filter. Returns False for outliers detected within the rolling window.
    Groups by configuration to avoid mixing different time-series.
    """
    def _is_outlier(s):
        rolling = s.rolling(window=window_size, center=True)
        median = rolling.median()
        # MAD: Median Absolute Deviation
        mad = rolling.apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True)
        threshold = n_sigma * 1.4826 * mad
        return np.abs(s - median) > threshold

    outliers = df.groupby(config_cols, group_keys=False)[target_col].apply(_is_outlier)
    return ~outliers.fillna(False).astype(bool)

def get_discontinued_configs_mask(df, min_length=100, config_cols=['A', 'B', 'M', 'N']):
    """Returns False for electrode configurations that have fewer total measurements than min_length."""
    config_counts = df.groupby(config_cols).size()
    valid_configs = config_counts[config_counts >= min_length].index
    
    # Create a tuple of configs for each row to check against valid_configs
    current_configs = df[config_cols].apply(tuple, axis=1)
    return current_configs.isin(valid_configs)