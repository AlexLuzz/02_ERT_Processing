import pandas as pd
import numpy as np
import pygimli as pg
from pygimli.physics import ert

def build_ert_container(df_survey: pd.DataFrame, geom_df: pd.DataFrame, 
                        err_values: float | bool = 5) -> pg.DataContainerERT:
    """
    Converts a standardized Pandas DataFrame for a SINGLE survey into a PyGIMLi DataContainerERT.
    Applies a fixed error float, or pulls 'err_val (%)' directly from the DataFrame if err_values is False.
    """
    n_electrodes = len(geom_df)
    sensor_positions = np.zeros((n_electrodes, 2))
    sensor_positions[:, 0] = geom_df['X'].values
    sensor_positions[:, 1] = geom_df['Z'].values
    
    data = ert.createData(elecs=sensor_positions, schemeName='uk')
    
    data['a'] = df_survey['A'].astype(int).values - 1
    data['b'] = df_survey['B'].astype(int).values - 1
    data['m'] = df_survey['M'].astype(int).values - 1
    data['n'] = df_survey['N'].astype(int).values - 1
    
    data['r'] = df_survey['R (Ohm)'].astype(float).values
    data['k'] = ert.createGeometricFactors(data)

    if 'rhoa (Ohm.m)' in df_survey.columns and not df_survey['rhoa (Ohm.m)'].isna().all():
        data['rhoa'] = df_survey['rhoa (Ohm.m)'].astype(float).values
    else:
        data['rhoa'] = data['k'] * data['r']
        
    # --- Simplified Error Injection ---
    if isinstance(err_values, (float, int)) and not isinstance(err_values, bool):
        # Fixed value (e.g., 5 -> 0.05)
        val = err_values / 100.0 if err_values >= 1.0 else float(err_values)
        data['err'] = np.full(data.size(), val)
        
    elif err_values is False:
        # Pull directly from dataframe (dividing by 100 to get relative error)
        # Checking 'err_val (%)' first, with fallbacks to your other common naming conventions
        if 'err_val (%)' in df_survey.columns:
            err_col = df_survey['err_val (%)']
        elif 'err_rec (%)' in df_survey.columns and not df_survey['err_rec (%)'].isna().all():
            err_col = df_survey['err_rec (%)']
        elif 'err_stk (%)' in df_survey.columns:
            err_col = df_survey['err_stk (%)']
        else:
            raise ValueError("err_values is False, but no error column (err_val (%), err_rec (%), or err_stk (%)) was found.")
            
        data['err'] = err_col.astype(float).values / 100.0
        
    else:
        raise TypeError("err_values must be a float, an int, or False.")
    
    data['valid'] = np.ones(data.size(), dtype=int)
    data.date_survey = df_survey['date_survey'].iloc[0]
    
    return data

def build_ert_containers_timeseries(df: pd.DataFrame, geom_df: pd.DataFrame, error_param: dict = None, date_col='date_survey') -> list:
    """ Wrapper that turns a multi-survey dataframe into a list of PyGIMLi containers. """
    containers = []
    for date_survey, group in df.groupby(date_col):
        group = group.sort_values(['A', 'B', 'M', 'N'])
        data = build_ert_container(group, geom_df, error_param=error_param, date_str=str(date_survey))
        containers.append(data)
    return containers

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

