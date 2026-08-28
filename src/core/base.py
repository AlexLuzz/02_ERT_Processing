import logging
import yaml
import pickle
import pandas as pd
from pathlib import Path
from datetime import datetime

class ProjectBase:
    """
    Abstract base class providing logging, standardized saving/loading, 
    and YAML tracking for the project pipeline.
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
        Loads data directly from an explicitly provided file path.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot find data at {file_path}")
            
        self.logger.info(f"Loading data from {file_path.name}...")
        
        if file_path.suffix == '.parquet':
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
        Saves data and its metadata YAML using a single, explicit file path.
        Infers the export format directly from the file extension.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Save YAML Metadata alongside the file using the stem (filename without extension)
        metadata['_system'] = {
            "module": self.__class__.__name__,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        yaml_path = file_path.parent / f"{file_path.stem}_metadata.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        
        # 2. Save Data based on the provided suffix
        if file_path.suffix == '.parquet' and isinstance(data, pd.DataFrame):
            try:
                data.to_parquet(file_path, index=False)
            except ImportError:
                self.logger.warning("Parquet engine not installed. Falling back to CSV saving.")
                file_path = file_path.with_suffix('.csv')
                data.to_csv(file_path, index=False)
        elif file_path.suffix == '.csv' and isinstance(data, pd.DataFrame):
            data.to_csv(file_path, index=False)
        else:
            # Fallback for non-dataframes or explicit pickle (.pkl) paths
            if file_path.suffix not in ['.csv', '.parquet', '.pkl']:
                file_path = file_path.with_suffix('.pkl')
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
                
        self.logger.info(f"✅ Saved dataset to {file_path.name} (and metadata to .yaml)")
        return file_path