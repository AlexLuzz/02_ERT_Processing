from pathlib import Path
from typing import Tuple, List
import pandas as pd

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