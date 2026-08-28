import pandas as pd
import numpy as np
import pygimli as pg
from pygimli.physics import ert

def build_ert_container(df_survey: pd.DataFrame, geom_df: pd.DataFrame, default_error: float = 0.05) -> pg.DataContainerERT:
    """
    Converts a standardized Pandas DataFrame for a SINGLE survey into a PyGIMLi DataContainerERT[cite: 7].
    """
    geom_df = geom_df.sort_values('elec_number')
    sensor_positions = geom_df[['X', 'Z']].values
    
    data = ert.createData(elecs=sensor_positions, schemeName='uk')
    
    data['a'] = df_survey['A'].astype(int).values - 1
    data['b'] = df_survey['B'].astype(int).values - 1
    data['m'] = df_survey['M'].astype(int).values - 1
    data['n'] = df_survey['N'].astype(int).values - 1
    
    data['r'] = df_survey['R (Ohm)'].astype(float).values
    
    # K-Value RMSE Validation
    pygimli_k = ert.createGeometricFactors(data)
    if 'k (m)' in df_survey.columns and not df_survey['k (m)'].isna().all():
        df_k = df_survey['k (m)'].astype(float).values
        rmse_k = np.sqrt(np.mean((pygimli_k - df_k)**2))
        print(f"Geometric factor (k) check - RMSE vs PyGIMLi: {rmse_k:.4f}")
        data['k'] = df_k 
    else:
        data['k'] = pygimli_k
        
    if 'rhoa (Ohm.m)' in df_survey.columns and not df_survey['rhoa (Ohm.m)'].isna().all():
        data['rhoa'] = df_survey['rhoa (Ohm.m)'].astype(float).values
    else:
        data['rhoa'] = data['k'] * data['r']
        
    if 'err_stk (%)' in df_survey.columns and not df_survey['err_stk (%)'].isna().all():
        data['err'] = df_survey['err_stk (%)'].astype(float).values / 100.0
    else:
        data['err'] = np.full(data.size(), default_error)
        
    data['valid'] = np.ones(data.size(), dtype=int)
    
    return data

def build_ert_containers_timeseries(df: pd.DataFrame, geom_df: pd.DataFrame, date_col='date_survey') -> list:
    """ Wrapper that turns a multi-survey dataframe into a list of PyGIMLi containers. """
    containers = []
    for survey_date, group in df.groupby(date_col):
        # We sort by A,B,M,N to guarantee PyGIMLi arrays align identically across time steps
        group = group.sort_values(['A', 'B', 'M', 'N'])
        data = build_ert_container(group, geom_df)
        containers.append({'time': survey_date, 'data': data})
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