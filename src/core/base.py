import logging
import json
import pickle
import pandas as pd
import h5py
import numpy as np
from pathlib import Path
from datetime import datetime

from src.mesh.pygimli_mesh_tools import safe_mesh_load, safe_mesh_save

class MemoryHandler(logging.Handler):
    """Logging handler that stores formatted messages in a list."""
    def __init__(self):
        super().__init__()
        self.logs = []

    def emit(self, record):
        self.logs.append(self.format(record))

class ProjectBase:
    """
    Abstract base class providing logging, standardized saving/loading,
    and JSON/HDF5/CSV tracking for the project pipeline.
    """

    def __init__(self, memory=False):
        self.memory = memory
        self.memory_handler = None
        self.logger = self._setup_logging(memory=memory)

    def _setup_logging(self, memory=False) -> logging.Logger:
        logger = logging.getLogger(self.__class__.__name__)
        logger.handlers.clear()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if memory:
            self.memory_handler = MemoryHandler()
            self.memory_handler.setFormatter(formatter)
            logger.addHandler(self.memory_handler)

        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger
    
    def load(self, file_path: Path | str) -> any:
        # ... [Unchanged loading logic] ...
        pass

    def _prepare_h5_value(self, key, val):
        if isinstance(val, pd.Series):
            val = val.to_numpy()
        if isinstance(val, np.ndarray) and np.issubdtype(val.dtype, np.datetime64):
            return val.astype(str)
        if isinstance(val, list) and val and isinstance(val[0], str):
            return np.array([s.encode("utf-8") for s in val])
        return val

    def save(self, data: any, file_path: Path | str, metadata: dict) -> Path:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        metadata["_system"] = {
            "module": self.__class__.__name__,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if file_path.suffix == ".h5" and isinstance(data, dict):
            with h5py.File(file_path, "w") as f:
                f.attrs["metadata"] = json.dumps(metadata)
                for key, val in data.items():
                    val = self._prepare_h5_value(key, val)
                    is_heavy = (isinstance(val, np.ndarray) and val.ndim > 1)
                    f.create_dataset(key, data=val, compression="gzip" if is_heavy else None)
            
            # Auto-dump dual CSV format 
            try:
                csv_path = file_path.with_suffix(".csv")
                # Pandas handles dicts of arrays with unequal lengths cleanly using pd.Series
                df_csv = pd.DataFrame({k: pd.Series(v) for k, v in data.items()})
                df_csv.to_csv(csv_path, index=False)
                self.logger.info(f"✅ Auto-saved parallel CSV to {csv_path.name}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not generate parallel CSV dump: {e}")

        else:
            json_path = file_path.parent / f"{file_path.stem}_metadata.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)

            if file_path.suffix == ".parquet" and isinstance(data, pd.DataFrame):
                data.to_parquet(file_path, index=False)
            elif file_path.suffix == ".csv" and isinstance(data, pd.DataFrame):
                data.to_csv(file_path, index=False)
            else:
                if file_path.suffix not in [".csv", ".parquet", ".pkl"]:
                    file_path = file_path.with_suffix(".pkl")
                with open(file_path, "wb") as f:
                    pickle.dump(data, f)

        self.logger.info(f"✅ Saved dataset to {file_path.name}")
        return file_path

    def save_mesh(self, mesh, file_path: Path | str) -> Path:
        file_path = Path(file_path)
        self.logger.info(f"Saving mesh to {file_path.name}...")
        saved_path = safe_mesh_save(mesh, file_path)
        self.logger.info(f"✅ Mesh securely saved to: {saved_path.name}")
        return saved_path

    def load_mesh(self, file_path: Path | str):
        file_path = Path(file_path)
        self.logger.info(f"Loading mesh from {file_path.name}...")
        mesh = safe_mesh_load(file_path)
        self.logger.info(f"✅ Mesh securely loaded from: {file_path.name}")
        return mesh