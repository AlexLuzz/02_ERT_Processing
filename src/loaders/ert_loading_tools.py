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

def split_sas4000_surveys(df: pd.DataFrame, time_gap_hours: float = 0.25) -> pd.DataFrame:
    """
    Detects multiple surveys within a single dataframe by looking for time 
    discontinuities. Dynamically updates 'date_survey' only.
    """
    if 'date_meas' not in df.columns:
        raise KeyError("Cannot split SAS4000 surveys: 'date_meas' column is missing.")

    df_work = df.sort_values('date_meas').reset_index(drop=True)
    
    # Identify where the time gap exceeds the threshold
    gaps = df_work['date_meas'].diff() > pd.Timedelta(hours=time_gap_hours)
    survey_blocks = gaps.cumsum()
    
    # Set the survey date to the first measurement time of each new block
    df_work['date_survey'] = df_work.groupby(survey_blocks)['date_meas'].transform('min')
    
    return df_work

def pygimli_compute_geometric_factors(df: pd.DataFrame, df_elec_pos: pd.DataFrame) -> pd.DataFrame:
    """Compute geometric factors using PyGIMLi."""
    import pygimli.physics.ert as ert

    df_out = df.copy()
    sensor_positions = df_elec_pos[["X", "Z"]].to_numpy()
    data = ert.createData(elecs=sensor_positions, schemeName="uk")

    for col in ["A", "B", "M", "N"]:
        data[col.lower()] = df_out[col].astype(int).to_numpy() - 1

    df_out["k (m)"] = ert.createGeometricFactors(data)
    return df_out

def compute_geometric_factors(df: pd.DataFrame, df_elec_pos: pd.DataFrame) -> pd.DataFrame:
    """Compute geometric factors using 3D Euclidean distances."""
    df_out = df.copy()
    pos = df_elec_pos.set_index("elec_number")[["X", "Y", "Z"]]

    coords = {e: pos.loc[df_out[e]].to_numpy() for e in ["A", "B", "M", "N"]}
    r_AM = np.linalg.norm(coords["A"] - coords["M"], axis=1)
    r_BM = np.linalg.norm(coords["B"] - coords["M"], axis=1)
    r_AN = np.linalg.norm(coords["A"] - coords["N"], axis=1)
    r_BN = np.linalg.norm(coords["B"] - coords["N"], axis=1)

    with np.errstate(divide="ignore", invalid="ignore"):
        df_out["k (m)"] = 2 * np.pi / (1/r_AM - 1/r_BM - 1/r_AN + 1/r_BN)

    df_out["k (m)"] = df_out["k (m)"].replace([np.inf, -np.inf], np.nan)
    return df_out

def get_reciprocal_mask(df: pd.DataFrame) -> pd.Series:
    """
    Identify reciprocal ERT measurements by following acquisition order.

    The dataframe must be in acquisition order.

    For each measurement:
    - The first occurrence of a configuration is considered forward.
    - A measurement is reciprocal if its AB and MN electrode pairs
        correspond to a configuration that was already measured, but
        with AB and MN exchanged.
    - Exact repeats are NOT marked as reciprocal.

    Electrode order within each pair is ignored:
        (A, B) == (B, A)
        (M, N) == (N, M)

    Example:
        1 2 3 4  -> forward
        1 2 3 4  -> forward (repeat)
        3 4 1 2  -> reciprocal
    """
    if df.empty:
        raise ValueError("DataFrame is empty in get_reciprocal_mask")

    reciprocal_mask = pd.Series(False, index=df.index)

    # Store configurations that have already been measured.
    # Each configuration is represented as:
    #     ((A, B), (M, N))
    seen = set()

    for idx, row in df.iterrows():
        # Put the two electrodes of each dipole in a consistent order.
        ab = tuple(sorted((row["A"], row["B"])))
        mn = tuple(sorted((row["M"], row["N"])))

        # Configuration as measured: AB -> MN
        current = (ab, mn)

        # Reciprocal configuration: MN -> AB
        reciprocal = (mn, ab)

        # If the reciprocal configuration was measured previously,
        # this measurement is a reciprocal.
        if reciprocal in seen:
            reciprocal_mask.loc[idx] = True

        # Always add the current measurement to the list of
        # configurations that have been measured.
        seen.add(current)

    return reciprocal_mask

def get_reciprocal_mask_vectorized(df: pd.DataFrame) -> pd.Series:
    """
    Fast vectorized version of get_reciprocal_mask().

    Identifies reciprocal ERT measurements based on acquisition order.
    The dataframe must be in acquisition order.

    Exact repeats are NOT marked as reciprocal.
    """
    if df.empty:
        raise ValueError("DataFrame is empty in get_reciprocal_mask_vectorized")

    # Put the electrodes within each dipole in a consistent order.
    ab = np.sort(df[["A", "B"]].to_numpy(), axis=1)
    mn = np.sort(df[["M", "N"]].to_numpy(), axis=1)

    # Configuration as measured: AB -> MN
    forward_keys = pd.MultiIndex.from_arrays([
        ab[:, 0],
        ab[:, 1],
        mn[:, 0],
        mn[:, 1],
    ])

    # Reciprocal configuration: MN -> AB
    reciprocal_keys = pd.MultiIndex.from_arrays([
        mn[:, 0],
        mn[:, 1],
        ab[:, 0],
        ab[:, 1],
    ])

    # Find the first row where each configuration was measured.
    first_seen = (
        pd.Series(np.arange(len(df)), index=forward_keys)
        .groupby(level=[0, 1, 2, 3], sort=False)
        .min()
    )

    # For each measurement, find the first occurrence of its reciprocal.
    reciprocal_first_seen = first_seen.reindex(reciprocal_keys)

    # It is reciprocal only if that configuration occurred earlier.
    mask = reciprocal_first_seen.to_numpy() < np.arange(len(df))

    return pd.Series(mask, index=df.index)

def process_reciprocals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flips reciprocal dipoles to match forward configurations, isolates true 
    chronological forward/reciprocal pairs, calculates errors, and interpolates.
    """
    df_out = df.copy()
    
    if 'reciprocal' not in df_out.columns:
        raise KeyError("Cannot process reciprocals: 'reciprocal' column is missing.")
        
    # 1. Flip reciprocal electrodes to turn them into forward configurations 
    recip_mask = df_out['reciprocal'] == True
    df_out.loc[recip_mask, ['A', 'B', 'M', 'N']] = df_out.loc[recip_mask, ['M', 'N', 'A', 'B']].values
    
    # 2. Sort internal dipoles (so A-B matches B-A) to create a universal ID for grouping
    ab = np.sort(df_out[["A", "B"]].to_numpy(), axis=1)
    mn = np.sort(df_out[["M", "N"]].to_numpy(), axis=1)
    df_out['pair_id'] = [f"{a}-{b}_{m}-{n}" for (a, b), (m, n) in zip(ab, mn)]
    
    def calc_rolling_err(grp):
        # Sort chronologically to find adjacent measurements
        grp = grp.sort_values('date_meas')
        
        is_recip = grp['reciprocal']
        R = grp['R (Ohm)']
        
        # Shift to compare the current measurement to the previous one
        shifted_recip = is_recip.shift(1)
        shifted_R = R.shift(1)
        
        # Identify boundaries where measurement flips (Forward -> Recip OR Recip -> Forward)
        valid_pair = (is_recip != shifted_recip) & shifted_recip.notna()
        
        errs = pd.Series(np.nan, index=grp.index)
        
        # Apply the specific formula: abs(Current - Previous) / (Current + Previous)
        errs[valid_pair] = np.abs((R[valid_pair] - shifted_R[valid_pair]) / 
                                  (R[valid_pair] + shifted_R[valid_pair])) * 100
        
        grp['err_rec (%)'] = errs
        
        # Interpolate across the time series for surveys that didn't shoot this reciprocal
        if grp['err_rec (%)'].notna().any():
            grp['err_rec (%)'] = grp['err_rec (%)'].interpolate(method='linear').bfill().ffill()
            
        return grp

    # Apply the logic per unique A-B-M-N configuration
    df_out = df_out.groupby('pair_id', group_keys=False).apply(calc_rolling_err)
    df_out = df_out.drop(columns=['pair_id'])
    
    return df_out

def load_geometry(filepath: Path, params: dict | None = None) -> pd.DataFrame:
    """Load and process electrode geometry.
    Additional params can be passed in a dictionary.
    Args:
        filepath: Path to the geometry file.
        params: Optional geometry processing options, example:

            params = {
                "absolute_pos": True,
                "inverse_order": False,
                "projection": {
                    "type": bestèfit or distance,
                    "output_axis": "X (m)",
                },
            }

            - ``absolute_pos`` (bool, default=False): Set Electrode 1 to ``[0, 0, 0]``.
            - ``inverse_order`` (bool, default=False): Reverse electrode order.
            - ``projection`` (dict, optional): Best-fit line projection:
                - ``type`` (str, default="best_fit"): Projection method.
                  Options are ``"best_fit"`` and ``"distance"``.
                - ``output_axis`` (str, default="X (m)"): Output column for the projected coordinate.
    Returns:
        pd.DataFrame: Electrode geometry.
    """
    params = params or {}
    absolute_pos = params.get("absolute_pos", False)
    inverse_order = params.get("inverse_order", False)
    projection = params.get("projection", {})

    df = pd.read_csv(filepath, sep=None, engine="python")
    df.columns = df.columns.str.strip()

    for col in ["X", "Y", "Z"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if inverse_order:
        df = df.iloc[::-1].reset_index(drop=True)

    if absolute_pos:
        df[["X", "Y", "Z"]] -= df[["X", "Y", "Z"]].iloc[0]

    projection_type = projection.get("type")

    if projection_type:
        axis = projection.get("output_axis", "X (m)")

        if projection_type == "distance":
            dx = df["X"].diff()
            dz = df["Y"].diff()
            spacing = np.sqrt(dx**2 + dz**2)
            df[axis] = spacing.fillna(0).cumsum()

        elif projection_type == "best_fit":
            xz = df[["X", "Y"]].to_numpy()
            center = xz.mean(axis=0)
            _, _, vh = np.linalg.svd(xz - center)
            direction = vh[0]
            df[axis] = (xz - center) @ direction

        else:
            raise ValueError(
                f"Unknown projection type: {projection_type!r}. "
                "Expected 'best_fit' or 'distance'."
            )

    return df