from pathlib import Path
from typing import Tuple, List
import pandas as pd
import numpy as np

def scan_header(filepath: Path, data_start_markers: List[str], delimiter: str = ':', keys_to_keep: List[str] = None) -> Tuple[int, dict]:
    """
    Scans a text file to extract specific metadata and find the data starting line.
    
    Parameters:
    - filepath: Path to the file.
    - data_start_markers: List of strings that identify the data table header.
    - delimiter: Character separating keys and values in metadata (default: ':').
    - keys_to_keep: List of specific metadata keys to extract. If None, extracts all.
    """
    metadata = {}
    data_start_idx = 0
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f):
            # Check for the data block start
            if all(marker in line for marker in data_start_markers):
                data_start_idx = i
                break
            
            # Extract metadata
            if delimiter in line and not line.startswith('#'):
                parts = line.split(delimiter, 1)
                key = parts[0].strip()
                val = parts[1].strip()
                
                if key and val:
                    # Filter keys if a list is provided
                    if keys_to_keep is None or key in keys_to_keep:
                        metadata[key] = " ".join(val.split())
                    
    return data_start_idx, metadata

def split_sas4000_surveys(df: pd.DataFrame, time_gap_hours: float = 2.0) -> pd.DataFrame:
    """
    Detects multiple surveys within a single dataframe by looking for time 
    discontinuities. Dynamically updates the 'survey_id' and 'date_survey'.
    """
    if 'date_meas' not in df.columns or df['date_meas'].isna().all():
        return df

    df_work = df.sort_values('date_meas').reset_index(drop=True)
    
    # Identify where the time gap exceeds the threshold
    gaps = df_work['date_meas'].diff() > pd.Timedelta(hours=time_gap_hours)
    survey_blocks = gaps.cumsum()
    
    # Append the sequence block to the survey_id
    df_work['survey_id'] = df_work['survey_id'].astype(str) + "_seq" + survey_blocks.astype(str)
    
    # Set the survey date to the first measurement time of each new block
    df_work['date_survey'] = df_work.groupby('survey_id')['date_meas'].transform('min')
    
    return df_work

def compute_geometric_factors(df: pd.DataFrame, df_elec: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the geometric factor k
    using 3D Euclidean distances between electrode positions.
    
    Parameters:
    - df: Standardized ERT DataFrame containing 'A', 'B', 'M', 'N', and 'R (Ohm)'.
    - df_elec: Electrode position DataFrame with columns 'elec_number', 'X', 'Y', 'Z'.
    """
    df_out = df.copy()
    
    # Map electrode numbers to coordinates
    pos = df_elec.set_index('elec_number')[['X', 'Y', 'Z']]
    
    # Extract coordinate arrays for A, B, M, N
    # Reindexing against elec_number handles arbitrary electrode ordering safely
    coords_A = pos.loc[df_out['A']].values
    coords_B = pos.loc[df_out['B']].values
    coords_M = pos.loc[df_out['M']].values
    coords_N = pos.loc[df_out['N']].values
    
    # Euclidean distances
    r_AM = np.linalg.norm(coords_A - coords_M, axis=1)
    r_BM = np.linalg.norm(coords_B - coords_M, axis=1)
    r_AN = np.linalg.norm(coords_A - coords_N, axis=1)
    r_BN = np.linalg.norm(coords_B - coords_N, axis=1)
    
    # Calculate geometric factor with protection against zero division
    with np.errstate(divide='ignore', invalid='ignore'):
        inv_geom = (1.0 / r_AM) - (1.0 / r_BM) - (1.0 / r_AN) + (1.0 / r_BN)
        k = 2.0 * np.pi / inv_geom
        k[np.isinf(k)] = np.nan
        
    df_out['k (m)'] = k
    
    return df_out