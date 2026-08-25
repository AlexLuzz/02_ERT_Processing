import pandas as pd
import numpy as np
import pygimli as pg
from pygimli.physics import ert

def build_ert_container(df_survey: pd.DataFrame, geom_df: pd.DataFrame, default_error: float = 0.05) -> pg.DataContainerERT:
    """
    Converts a standardized Pandas DataFrame for a SINGLE survey into a PyGIMLi DataContainerERT.
    
    Parameters:
    - df_survey: DataFrame containing ONE time step of data.
    - geom_df: DataFrame containing 'electrode_id', 'x', 'z'.
    - default_error: Error fraction (0.05 = 5%) to apply if 'err_stk (%)' is missing/invalid.
    """
    # 1. Create PyGIMLi electrode positions (sensors)
    # Sort geometry to ensure index matches PyGIMLi's internal 0-based node indexing
    geom_df = geom_df.sort_values('electrode_id')
    sensor_positions = geom_df[['x', 'z']].values
    
    data = ert.createData(elecs=sensor_positions, schemeName='uk')
    
    # 2. Map electrodes (Note: PyGIMLi often expects 0-indexed sensors depending on how you loaded them. 
    # Subtract 1 if your instruments use 1-indexed electrodes)
    data['a'] = df_survey['A'].astype(int).values - 1
    data['b'] = df_survey['B'].astype(int).values - 1
    data['m'] = df_survey['M'].astype(int).values - 1
    data['n'] = df_survey['N'].astype(int).values - 1
    
    # 3. Add measurements
    data['r'] = df_survey['R (Ohm)'].astype(float).values
    
    if 'rhoa (Ohm.m)' in df_survey.columns and not df_survey['rhoa (Ohm.m)'].isna().all():
        data['rhoa'] = df_survey['rhoa (Ohm.m)'].astype(float).values
    else:
        # Let PyGIMLi calculate geometry factors if rhoa isn't provided
        data['k'] = ert.createGeometricFactors(data)
        data['rhoa'] = data['k'] * data['r']
        
    # 4. Handle Errors (PyGIMLi expects fractions, not percentages. e.g. 0.05)
    if 'err_stk (%)' in df_survey.columns and not df_survey['err_stk (%)'].isna().all():
        data['err'] = df_survey['err_stk (%)'].astype(float).values / 100.0
    else:
        data['err'] = np.full(data.size(), default_error)
        
    data['valid'] = np.ones(data.size(), dtype=bool)
    
    return data

def get_common_configs(df, config_cols=['A', 'B', 'M', 'N'], date_col='SurveyDate'):
    """Identifies electrode configurations that exist across ALL surveys."""
    common_configs = None
    for survey_date in df[date_col].unique():
        survey_data = df[df[date_col] == survey_date]
        configs = set(map(tuple, survey_data[config_cols].values))
        if common_configs is None:
            common_configs = configs
        else:
            common_configs = common_configs.intersection(configs)
    return common_configs