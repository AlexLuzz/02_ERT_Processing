import pandas as pd
import numpy as np

def resample_timeseries(df, freq_hours=6, max_gap_hours=72, timestamp_col='MeasDate', 
                        config_cols=['A', 'B', 'M', 'N'], 
                        meas_cols=['rhoa', 'Res.(ohm)', 'Error(%)', 'Voltage(mV)', 'I(mA)']):
    """
    Resamples data and interpolates missing values strictly bounded by max_gap_hours.
    """
    df_work = df.copy()
    df_work[timestamp_col] = pd.to_datetime(df_work[timestamp_col], errors='coerce')
    df_work = df_work.dropna(subset=[timestamp_col]).set_index(timestamp_col)
    
    valid_cols = [c for c in meas_cols if c in df_work.columns]
    for c in valid_cols:
        df_work[c] = pd.to_numeric(df_work[c], errors='coerce')
        
    limit = max(1, int(max_gap_hours // freq_hours))

    # Group by configuration, resample by time, and interpolate linearly
    resampled = (
        df_work.groupby(config_cols)[valid_cols]
        .resample(f'{freq_hours}h')
        .mean()
        .interpolate(method='linear', limit=limit, limit_direction='both', limit_area='inside')
        .dropna(how='all', subset=valid_cols)
        .reset_index()
    )
    
    return resampled

def interpolate_excluded_period(df, electrodes, start_date, end_date, date_col='SurveyDate', 
                                cols_to_interp=['rhoa', 'Res.(ohm)'], config_cols=['A', 'B', 'M', 'N']):
    """
    Finds measurements containing specific electrodes during a time window, 
    deletes them, and interpolates the gap using the boundaries of the gap.
    """
    df_work = df.copy()
    df_work[date_col] = pd.to_datetime(df_work[date_col], errors='coerce')
    start_dt, end_dt = pd.to_datetime(start_date), pd.to_datetime(end_date)
    
    if isinstance(electrodes, int):
        electrodes = [electrodes]
        
    # Mask to locate rows fitting both the time window and the target electrodes
    time_mask = (df_work[date_col] >= start_dt) & (df_work[date_col] <= end_dt)
    elec_mask = df_work[config_cols].isin(electrodes).any(axis=1)
    target_mask = time_mask & elec_mask
    
    if not target_mask.any():
        return df_work

    # Set targeted values to NaN, then interpolate over them grouped by config
    for col in cols_to_interp:
        if col in df_work.columns:
            df_work.loc[target_mask, col] = np.nan
            df_work[col] = (
                df_work.groupby(config_cols, group_keys=False)[col]
                .apply(lambda x: x.interpolate(method='time', limit_area='inside'))
            )
            
    # Drop rows that couldn't be interpolated (i.e., at the very start/end of a series)
    df_work = df_work.dropna(subset=cols_to_interp, how='all')
    return df_work