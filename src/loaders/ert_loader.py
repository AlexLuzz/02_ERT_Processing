import pandas as pd
from pathlib import Path
from datetime import datetime
import re
from src.loaders.loading_tools import scan_header, split_sas4000_surveys, compute_geometric_factors
from src.core.base import ProjectBase

class ERTLoader(ProjectBase):
    """Data loader for ERT instruments"""

    def __init__(
        self,
        site_id: str,
        elec_pos_path: Path | str | None = None,
        absolute_pos: bool = True,
        inverse_order: bool = False,
    ):
        super().__init__()
        self.site_id = site_id
        self.elec_pos = None

        if elec_pos_path is not None:
            self.elec_pos = self.load_geometry(
                elec_pos_path, absolute_pos=absolute_pos, inverse_order=inverse_order
            )
            self.logger.info(
                f"Initialized ERTLoader for site: '{self.site_id}' with"
                f" {len(self.elec_pos)} electrodes loaded."
            )
        else:
            self.logger.info(
                f"Initialized ERTLoader for site: '{self.site_id}' (No geometry"
                " bound)."
            )
        
    # Standard columns mapped to their expected pandas data types
    ERT_COLS = {
      'A': 'Int64',
      'B': 'Int64',
      'M': 'Int64',
      'N': 'Int64',
      'R (Ohm)': float,
      'Vmn (mV)': float,
      'Iab (mA)': float,
      'Tx (V)': float,
      'R_ab (kOhm)': float,
      'k (m)': float,
      'rhoa (Ohm.m)': float,
      'err_stk (%)': float,
      'err_rec (%)': float,
      'date_survey': 'datetime64[ns]',
      'date_meas': 'datetime64[ns]',
      'site_id': str,
      'hardware_id': str,
      'survey_id': str,
    }
    

    def _resolve_files(self, source: Path | str | list, pattern: str = "*") -> list[Path]:
        if isinstance(source, list):
            return [Path(f) for f in source if Path(f).exists()]
        
        source_path = Path(source)
        if source_path.is_file(): return [source_path]
        if source_path.is_dir(): return list(source_path.glob(pattern))
        if source_path.parent.is_dir(): return list(source_path.parent.glob(source_path.name))
        
        self.logger.error(f"Path does not exist: {source_path}")
        return []

    def _finalize_standardization(
        self, 
        df: pd.DataFrame, 
        site_id: str, 
        hardware_id: str, 
        filepath_stem: str, 
        survey_date, 
        elec_pos: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Centralized method to add identifiers, compute geometric factors & rhoa, 
        hard-cast types, apply whitelist, and log survey statistics.
        """
        # Add Identifiers & Dates
        df['site_id'] = site_id
        df['hardware_id'] = hardware_id
        df['survey_id'] = f"{site_id}_{filepath_stem}"
        df['date_survey'] = survey_date

        # Geometric factor and apparent resistivity computation
        if self.elec_pos is not None:
            df = compute_geometric_factors(df, self.elec_pos)
            df['rhoa (Ohm.m)'] = df['k (m)'] * df['R (Ohm)']
            self.logger.info(f" -> Computed k and rhoa using {len(self.elec_pos)} electrode positions.")
        elif 'k (m)' in df.columns and 'R (Ohm)' in df.columns:
            df['rhoa (Ohm.m)'] = df['k (m)'] * df['R (Ohm)']
            self.logger.info(f" -> Computed rhoa using existing k values.")

        # Ensure standard columns exist and HARD-CAST types
        for col, dtype in self.ERT_COLS.items():
            if col not in df.columns:
                df[col] = pd.NA
                
            if dtype == 'datetime64[ns]':
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif dtype == str:
                df[col] = df[col].astype(str).replace({'nan': pd.NA, '<NA>': pd.NA})
            else:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(dtype)

        # STRICT WHITELIST
        df_final = df[list(self.ERT_COLS.keys())].copy()

        # STATS EXTRACTION & LOGGING
        num_meas = len(df_final)
        
        # Electrode usage and missing sequence detection
        elecs = pd.unique(df_final[['A', 'B', 'M', 'N']].values.ravel())
        elecs = sorted([int(e) for e in elecs if pd.notna(e)])
        
        if elecs:
            min_e, max_e = min(elecs), max(elecs)
            full_expected_set = set(range(min_e, max_e + 1))
            missing_elecs = sorted(list(full_expected_set - set(elecs)))
            missing_str = f" | Missing: {missing_elecs}" if missing_elecs else " | No gaps"
            elec_log = f"{len(elecs)} total (Range: {min_e} to {max_e}{missing_str})"
        else:
            elec_log = "0 detected"

        # Dates and duration
        start_date = df_final['date_survey'].min()
        end_date = df_final['date_survey'].max()
        if not df_final['date_meas'].isna().all():
            duration = df_final['date_meas'].max() - df_final['date_meas'].min()
            duration_str = str(duration).split('.')[0]
        else:
            duration_str = "N/A"

        # Apparent resistivity checks
        rhoa_valid = df_final['rhoa (Ohm.m)'].dropna()
        if not rhoa_valid.empty:
            neg_count = (rhoa_valid < 0).sum()
            rhoa_stats = f"Min: {rhoa_valid.min():.2f}, Max: {rhoa_valid.max():.2f} Ohm.m (Negatives: {neg_count})"
        else:
            rhoa_stats = "Not computed"

        self.logger.info(f"--- Standardized: {site_id}_{filepath_stem} ---")
        self.logger.info(f"  Measurements : {num_meas}")
        self.logger.info(f"  Electrodes   : {elec_log}")
        self.logger.info(f"  Survey Dates : {start_date} to {end_date}")
        self.logger.info(f"  Duration     : {duration_str}")
        self.logger.info(f"  rhoa stats   : {rhoa_stats}")
        self.logger.info(f"------------------------------------------------")

        return df_final

    def load_prime(self, site_id: str, source: Path | str | list, pattern: str = "*.tab") -> pd.DataFrame:
        files = self._resolve_files(source, pattern)
        dfs = []
        
        for filepath in files:
            self.logger.info(f"Loading Prime file: {filepath.name}")
            data_start, metadata = scan_header(filepath, data_start_markers=['pt_line_number:', 'pt_calc_res:'])
            
            start_time_str = metadata.get('set_actual_start_time')
            survey_date = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S") if start_time_str else pd.NA
                    
            df = pd.read_csv(filepath, skiprows=data_start, sep=r'\s+')
            df.columns = df.columns.str.strip()
            
            df = df.rename(columns={
                'pt_c1_no:': 'A', 'pt_c2_no:': 'B', 'pt_p1_no:': 'M', 'pt_p2_no:': 'N',
                'pt_calc_res:': 'R (Ohm)', 'pt_meas_voltage_mean:': 'Vmn (mV)', 'pt_meas_current_mag:': 'Iab (mA)', 
                'pt_meas_applied_voltage:': 'Tx (V)', 'pt_meas_contact_resistance:': 'R_ab (kOhm)', 
                'pt_calc_res_error:': 'err_stk (%)', 'pt_time:': 'date_meas'
            })
            
            df = self._finalize_standardization(df, site_id, 'Prime', filepath.stem, survey_date)
            dfs.append(df)
            
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    def load_sas4000(self, site_id: str, source: Path | str | list, pattern: str = "*.AMP") -> pd.DataFrame:
        files = self._resolve_files(source, pattern)
        dfs = []
        
        for filepath in files:
            self.logger.info(f"Loading SAS4000 file: {filepath.name}")
            data_start, metadata = scan_header(filepath, data_start_markers=['No.', 'A(x)'])
            
            start_time_str = metadata.get('Date & Time')
            survey_date = datetime.strptime(start_time_str, "%d/%m/%Y %H:%M:%S") if start_time_str else pd.NA
                    
            df = pd.read_csv(filepath, skiprows=data_start, sep=r'\s+')
            
            if 'Voltage(V)' in df.columns:
                df['Voltage(V)'] = df['Voltage(V)'] * 1000.0
                self.logger.info(f" -> Converted Voltage(V) to mV for {filepath.name}")
            
            df = df.rename(columns={
                'A(x)': 'A', 'B(x)': 'B', 'M(x)': 'M', 'N(x)': 'N',
                'Res.(ohm)': 'R (Ohm)', 'Voltage(V)': 'Vmn (mV)', 'I(mA)': 'Iab (mA)', 
                'Error(%)': 'err_stk (%)'
            })
            
            df['err_stk (%)'] = pd.to_numeric(df['err_stk (%)'].replace('1.#QNAN0', pd.NA), errors='coerce')
            df = df[~df['A'].astype(str).isin(['32767', '32767.0'])]
            
            # SAS4000 specific time logic (must happen before finalizer casts types)
            df['date_meas'] = survey_date + pd.to_timedelta(pd.to_numeric(df['Time'], errors='coerce'), unit='s')

            # Apply splitting before finalization to update survey_id and date_survey
            df['survey_id'] = f"{site_id}_{filepath.stem}"
            df = split_sas4000_surveys(df, time_gap_hours=0.25)

            df = self._finalize_standardization(df, site_id, 'SAS4000', filepath.stem, survey_date)
            dfs.append(df)
            
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    def load_ohmpi(self, site_id: str, source: Path | str | list, pattern: str = "*.csv") -> pd.DataFrame:
        files = self._resolve_files(source, pattern)
        dfs = []
        
        for filepath in files:
            self.logger.info(f"Loading OhmPi file: {filepath.name}")
            df = pd.read_csv(filepath, sep=',')
            
            date_match = re.search(r'\d{8}T\d{6}', filepath.stem)
            survey_date = datetime.strptime(date_match.group(), "%Y%m%dT%H%M%S") if date_match else pd.NA

            df = df.rename(columns={
                'R [Ohm]': 'R (Ohm)', 'Vmn [mV]': 'Vmn (mV)', 'I [mA]': 'Iab (mA)',
                'Tx [V]': 'Tx (V)', 'R_ab [kOhm]': 'R_ab (kOhm)',
                'time': 'date_meas', 'R_std [%]': 'err_stk (%)', 
            })
            
            df = self._finalize_standardization(df, site_id, 'OhmPi', filepath.stem, survey_date)
            dfs.append(df)
            
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    def load_geometry(self, filepath: Path, absolute_pos: bool = False, inverse_order: bool = False) -> pd.DataFrame:
        """
        Loads electrode geometry files.
        Header expected: elec_number, X, Y, Z
        """
        self.logger.info(f"Loading geometry file: {filepath.name}")
        
        # We use decimal=',' to correctly parse '-0,2' as a float#
        # sep=None with engine='python' allows it to guess if it's separated by commas or semicolons
        df = pd.read_csv(filepath, sep=None, engine='python')
        df.columns = df.columns.str.strip()
        
        # Ensure correct numeric types
        for col in ['X', 'Y', 'Z']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        if inverse_order:
            # Reverses the coordinates but keeps the elec_number in place
            # E.g., Electrode 1 gets the coordinates of the very last electrode
            coords = df[['X', 'Y', 'Z']].iloc[::-1].reset_index(drop=True)
            df[['X', 'Y', 'Z']] = coords
            self.logger.info(" -> Applied inverse order to coordinates.")
            
        if absolute_pos:
            # Shifts the entire array so the first electrode sits perfectly at 0, 0, 0
            df['X'] = df['X'] - df['X'].iloc[0]
            df['Y'] = df['Y'] - df['Y'].iloc[0]
            df['Z'] = df['Z'] - df['Z'].iloc[0]
            self.logger.info(" -> Converted to absolute positions (Electrode 1 = Origin, X=0, Y=0, Z=0).")
            
        return df