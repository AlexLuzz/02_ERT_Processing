import logging
import json
import pickle
import pandas as pd
import h5py
import numpy as np
from pathlib import Path
from datetime import datetime

from src.mesh.pygimli_mesh_tools import safe_mesh_load, safe_mesh_save

class ProjectBase:
    """
    Abstract base class providing logging, standardized saving/loading, 
    and JSON/HDF5 tracking for the project pipeline.
    """
    def __init__(self):
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        return logger

    def load(self, file_path: Path | str) -> any:
        """
        Loads data. For HDF5, returns (data_dictionary, metadata_dictionary).
        Automatically decodes strings and standardizes datetimes.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot find data at {file_path}")
            
        self.logger.info(f"Loading data from {file_path.name}...")
        
        if file_path.suffix == '.h5':
            data_dict = {}
            with h5py.File(file_path, 'r') as f:
                metadata = json.loads(f.attrs['metadata'])
                
                for key in f.keys():
                    val = f[key][()]
                    
                    # HDF5 stores strings as binary bytes. If we detect bytes, decode to standard Python strings.
                    if isinstance(val, np.ndarray) and val.dtype.kind == 'S': 
                        val = np.array([s.decode('utf-8') for s in val])
                        
                    # Standardize datetime arrays immediately upon loading to avoid pd.to_datetime clutter elsewhere
                    if key.startswith(("date", "time")): 
                        val = [s.decode('utf-8') if isinstance(s, bytes) else s for s in val]
                        val = pd.to_datetime(val, errors='coerce')
                        
                    data_dict[key] = val
                    
            return data_dict, metadata
        elif file_path.suffix == '.parquet':
            return pd.read_parquet(file_path)
        elif file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        elif file_path.suffix == '.pkl':
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def save(self, data: any, file_path: Path | str, metadata: dict) -> Path:
        """
        Saves data natively to HDF5 or tabular formats based on extension.
        Metadata is stored internally for HDF5, and as a sibling .json file for others.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        metadata['_system'] = {
            "module": self.__class__.__name__,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # HDF5
        if file_path.suffix == '.h5' and isinstance(data, dict):
            with h5py.File(file_path, 'w') as f:
                f.attrs['metadata'] = json.dumps(metadata)
                for key, val in data.items():
                    # HDF5 C-backend crashes on native Python strings. Convert to byte-strings.
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], str):
                        f.create_dataset(key, data=[s.encode('utf-8') for s in val])
                    else:
                        # Only apply gzip compression to multi-dimensional matrices (like model arrays) to save time.
                        is_heavy = isinstance(val, np.ndarray) and val.ndim > 1
                        f.create_dataset(key, data=val, compression='gzip' if is_heavy else None)
        
        # .csv or pickle
        else:
            json_path = file_path.parent / f"{file_path.stem}_metadata.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4)
                
            if file_path.suffix == '.parquet' and isinstance(data, pd.DataFrame):
                data.to_parquet(file_path, index=False)
            elif file_path.suffix == '.csv' and isinstance(data, pd.DataFrame):
                data.to_csv(file_path, index=False)
            else:
                if file_path.suffix not in ['.csv', '.parquet', '.pkl']:
                    file_path = file_path.with_suffix('.pkl')
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
                
        self.logger.info(f"✅ Saved dataset to {file_path.name}")
        return file_path

    def save_mesh(self, mesh, file_path: Path | str) -> Path:
        """
        Helper to securely save a PyGIMLi mesh with project logging.
        """
        file_path = Path(file_path)
        self.logger.info(f"Saving mesh to {file_path.name}...")
        
        saved_path = safe_mesh_save(mesh, file_path)
        
        self.logger.info(f"✅ Mesh securely saved to: {saved_path.name}")
        return saved_path

    def load_mesh(self, file_path: Path | str):
        """
        Helper to securely load a PyGIMLi mesh with project logging.
        """
        file_path = Path(file_path)
        self.logger.info(f"Loading mesh from {file_path.name}...")
        
        mesh = safe_mesh_load(file_path)
        
        self.logger.info(f"✅ Mesh securely loaded from: {file_path.name}")
        return mesh