import pandas as pd
import numpy as np

def filter_by_voltage(df: pd.DataFrame, min_voltage_mv: float = 1.0) -> pd.DataFrame:
    """Removes measurements below the voltage threshold."""
    return df[df['V (mV)'] >= min_voltage_mv].copy()

def filter_by_error(df: pd.DataFrame, max_error_pct: float = 20.0) -> pd.DataFrame:
    """Removes measurements where the stacking/instrument error is too high."""
    # Coerce errors to numeric, fill NaNs temporarily for safe filtering, or drop them
    temp_df = df.copy()
    temp_df['err_stk (%)'] = pd.to_numeric(temp_df['err_stk (%)'], errors='coerce')
    return temp_df[temp_df['err_stk (%)'] <= max_error_pct].copy()

def remove_dead_electrodes(df: pd.DataFrame, bad_electrodes: list) -> pd.DataFrame:
    """Drops any measurement using a known bad electrode."""
    mask = df[['A', 'B', 'M', 'N']].isin(bad_electrodes).any(axis=1)
    return df[~mask].copy()

def compute_apparent_resistivity(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates rho_a if k and R are present."""
    if 'k (m)' in df.columns and 'R (Ohm)' in df.columns:
        df = df.copy()
        df['rhoa (Ohm.m)'] = df['k (m)'] * df['R (Ohm)']
    return df

def filter_discontinued_quadripoles(df: pd.DataFrame, min_surveys: int = 10) -> pd.DataFrame:
    """
    Removes A-B-M-N configurations that don't appear in at least `min_surveys` time steps.
    Prevents PyGIMLi from struggling with sparse, ghost measurements.
    """
    df_work = df.copy()
    
    # Create a unique ID for each quadripole
    df_work['quad_id'] = df_work[['A', 'B', 'M', 'N']].astype(str).agg('_'.join, axis=1)
    
    # Count how many unique surveys each quadripole appears in
    counts = df_work.groupby('quad_id')['date_survey'].nunique()
    valid_quads = counts[counts >= min_surveys].index
    
    filtered_df = df_work[df_work['quad_id'].isin(valid_quads)].drop(columns=['quad_id'])
    return filtered_df