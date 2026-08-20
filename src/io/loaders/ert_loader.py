import pandas as pd
from pathlib import Path
from datetime import datetime

class GeophysicsLoader:
    """Unified data loader for ERT instruments, sensors, and geometries."""
    
    # Standard columns expected by downstream processing and PyGIMLi
    ERT_COLS = ['a', 'b', 'm', 'n', 'r', 'v', 'i', 'err', 'datetime']

    def _standardize_ert(self, df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
        """Internal method to unify ERT column names and structure."""
        df = df.rename(columns=col_map)
        
        # Ensure all standard columns exist
        for col in self.ERT_COLS:
            if col not in df.columns:
                df[col] = pd.NA
                
        # Keep standardized columns first, append any extras
        extra_cols = [c for c in df.columns if c not in self.ERT_COLS]
        return df[self.ERT_COLS + extra_cols]

    def load_sas4000(self, filepath: Path) -> pd.DataFrame:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        start_time, data_start = None, 0
        for i, line in enumerate(lines):
            if line.startswith('Date & Time:'):
                time_str = line.split(':', 1)[1].strip()
                start_time = datetime.strptime(time_str, "%d/%m/%Y %H:%M:%S")
            elif 'No.' in line and 'A(x)' in line:
                data_start = i
                break
                
        df = pd.read_csv(filepath, skiprows=data_start, delim_whitespace=True)
        
        col_map = {
            'A(x)': 'a', 'B(x)': 'b', 'M(x)': 'm', 'N(x)': 'n',
            'Res.(ohm)': 'r', 'Voltage(V)': 'v', 'I(mA)': 'i', 'Error(%)': 'err'
        }
        df = self._standardize_ert(df, col_map)
        
        if start_time and 'Time' in df.columns:
            df['datetime'] = start_time + pd.to_timedelta(df['Time'], unit='s')
            
        df['err'] = pd.to_numeric(df['err'].replace('1.#QNAN0', pd.NA), errors='coerce')
        df = df[~df['a'].astype(str).isin(['32767', '32767.0'])]
        
        return df.reset_index(drop=True)

    def load_ohmpi(self, filepath: Path) -> pd.DataFrame:
        df = pd.read_csv(filepath, sep=',')
        col_map = {
            'A': 'a', 'B': 'b', 'M': 'm', 'N': 'n',
            'R [Ohm]': 'r', 'Vmn [mV]': 'v', 'I [mA]': 'i', 'time': 'datetime'
        }
        df = self._standardize_ert(df, col_map)
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        return df

    def load_prime(self, filepath: Path) -> pd.DataFrame:
        df = pd.read_csv(filepath, sep='\t')
        col_map = {
            'A': 'a', 'B': 'b', 'M': 'm', 'N': 'n',
            'R': 'r', 'V': 'v', 'I': 'i', 'Err': 'err'
        }
        return self._standardize_ert(df, col_map)

    def load_sensors(self, filepath: Path) -> pd.DataFrame:
        """Loads environmental sensor data (TDR, LTC)."""
        # Read Excel or CSV based on suffix
        if filepath.suffix in ['.xls', '.xlsx']:
            df = pd.read_excel(filepath)
        else:
            df = pd.read_csv(filepath)
            
        # Example logic: ensure a standard datetime index for sensor alignment
        if 'timestamp' in df.columns:
            df = df.rename(columns={'timestamp': 'datetime'})
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        return df.set_index('datetime')

    def load_electrode_geometry(self, filepath: Path) -> pd.DataFrame:
        """Loads physical X, Y, Z coordinates for electrodes."""
        df = pd.read_csv(filepath)
        # Ensure minimum required coordinates exist
        expected = ['electrode_id', 'x', 'z']
        if not all(col in df.columns for col in expected):
            raise ValueError(f"Geometry file must contain columns: {expected}")
        return df