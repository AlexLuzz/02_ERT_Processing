import pandas as pd
import numpy as np
import pygimli as pg
from pygimli.physics import ert
from scipy.optimize import curve_fit

def compute_error_model(r_meas: np.ndarray, err_rec: np.ndarray, model_type: str = 'power') -> dict:
    """
    Computes the error model parameters from reciprocal measurements.
    Returns a dictionary of parameters to be passed to the container builder.
    """
    r_abs = np.abs(r_meas)
    err_abs = np.abs(err_rec)

    if model_type == 'power':
        # Absolute Error: \Delta R = a * (R^b)
        def power_law(x, a, b):
            return a * (x ** b)
        
        popt, _ = curve_fit(power_law, r_abs, err_abs, p0=[0.05, 1.0])
        return {'model_type': 'power', 'a': popt[0], 'b': popt[1]}
        
    elif model_type == 'linear':
        # Absolute Error: \Delta R = a * R + b
        def linear_law(x, a, b):
            return a * x + b
            
        popt, _ = curve_fit(linear_law, r_abs, err_abs, p0=[0.05, 0.001])
        return {'model_type': 'linear', 'a': popt[0], 'b': popt[1]}
        
    raise ValueError(f"Unknown model_type: {model_type}")

def calculate_relative_error_array(r_meas: np.ndarray, error_param) -> np.ndarray:
    """
    Evaluates the error_param to generate the relative error array for PyGIMLi.
    Handles None (default), numbers (fixed), or dictionaries (computed models).
    """
    r_abs = np.abs(r_meas)
    r_abs[r_abs < 1e-6] = 1e-6  # Prevent division by zero
    
    # Situation 1: No error specified -> Default to 0.05 (5%)
    if error_param is None:
        return np.full_like(r_abs, 0.05)
        
    # Situation 2: Fixed error specified (e.g., 3, 10, or 0.05)
    if isinstance(error_param, (int, float)):
        # Smart conversion: If user passes 3 (meaning 3%), convert to 0.03
        val = error_param / 100.0 if error_param >= 1.0 else float(error_param)
        return np.full_like(r_abs, val)
        
    # Situation 3: Computed model parameters (Dictionary)
    if isinstance(error_param, dict):
        model = error_param.get('model_type', 'fixed')
        a = error_param.get('a', 0.05)
        
        if model == 'power':
            b = error_param.get('b', 1.0)
            abs_err = a * (r_abs ** b)
        elif model == 'linear':
            b = error_param.get('b', 0.001)
            abs_err = (a * r_abs) + b
        else:
            return np.full_like(r_abs, a)
            
        return abs_err / r_abs
        
    raise TypeError("error_param must be None, a number, or a parameter dictionary.")

def build_ert_container(df_survey: pd.DataFrame, geom_df: pd.DataFrame, 
                        error_param: dict = None, date_str: str = "static") -> pg.DataContainerERT:
    """
    Converts a standardized Pandas DataFrame for a SINGLE survey into a PyGIMLi DataContainerERT.
    Dynamically applies the error model to the data['err'] array.
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

    #if 'rhoa (Ohm.m)' in df_survey.columns and not df_survey['rhoa (Ohm.m)'].isna().all():
    #    data['rhoa'] = df_survey['rhoa (Ohm.m)'].astype(float).values

    data['rhoa'] = data['k'] * data['r']
        
    data['err'] = calculate_relative_error_array(data['r'].array(), error_param)
    
    data['valid'] = np.ones(data.size(), dtype=int)
    data.date_survey = date_str
    
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

def fit_reciprocal_error_model(r_meas: np.ndarray, err_rec: np.ndarray, model_type: str = 'power') -> dict:
    """
    Fits a mathematical relationship between measured resistance and absolute reciprocal error.
    Returns the parameter dictionary ready to be passed into the ERTProcessor.
    """
    r_abs = np.abs(r_meas)
    err_abs = np.abs(err_rec)

    if model_type == 'power':
        # Absolute Error: \Delta R = a * (R^b)
        def power_law(x, a, b):
            return a * (x ** b)
        
        popt, _ = curve_fit(power_law, r_abs, err_abs, p0=[0.05, 1.0])
        return {'model_type': 'power', 'a': popt[0], 'b': popt[1]}
        
    elif model_type == 'linear':
        # Absolute Error: \Delta R = a * R + b
        def linear_law(x, a, b):
            return a * x + b
            
        popt, _ = curve_fit(linear_law, r_abs, err_abs, p0=[0.05, 0.001])
        return {'model_type': 'linear', 'a': popt[0], 'b': popt[1]}
        
    raise ValueError(f"Unknown model_type: {model_type}")