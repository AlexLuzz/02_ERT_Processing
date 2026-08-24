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

    def load(self, step_name: str, file_name: str) -> pd.DataFrame:
        """
        Loads pre-processed data from a specific project step folder.
        Example: load("01_raw_data_filtered", "fused_ert_20260821_120000.parquet")
        """
        file_path = self.project_root / step_name / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot find step data at {file_path}")
            
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

    def save(self, step_name: str, data: any, config: dict, data_format: str = 'parquet'):
        """
        Saves the data and dumps the configuration to a YAML file.
        """
        step_dir = self.project_root / step_name
        step_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{step_name}_{timestamp}"
        
        # Save YAML Config
        config['_metadata'] = {
            "processor": self.__class__.__name__,
            "timestamp": timestamp,
        }
        yaml_path = step_dir / f"{base_filename}_config.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        # Save Data
        if data_format == 'parquet' and isinstance(data, pd.DataFrame):
            data_path = step_dir / f"{base_filename}.parquet"
            data.to_parquet(data_path, index=False)
        elif data_format == 'csv' and isinstance(data, pd.DataFrame):
            data_path = step_dir / f"{base_filename}.csv"
            data.to_csv(data_path, index=False)
        else:
            data_path = step_dir / f"{base_filename}.pkl"
            with open(data_path, 'wb') as f:
                pickle.dump(data, f)
                
        self.logger.info(f"✅ Saved outputs to {step_dir.relative_to(self.project_root.parent)}")
        return data_path

    def save_dataset(self, df: pd.DataFrame, target_dir: Path, filename_prefix: str, metadata: dict):
        """
        Saves a DataFrame to Parquet/CSV and dumps the configuration to a YAML file.
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Save Data (Try Parquet, fallback to CSV)
        try:
            data_path = target_dir / f"{filename_prefix}.parquet"
            df.to_parquet(data_path, index=False)
        except ImportError:
            self.logger.warning("pyarrow not installed. Falling back to CSV saving.")
            data_path = target_dir / f"{filename_prefix}.csv"
            df.to_csv(data_path, index=False)
        
        # Save YAML Config
        metadata['_system'] = {
            "module": self.__class__.__name__,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        yaml_path = target_dir / f"{filename_prefix}_metadata.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
                
        self.logger.info(f"Saved dataset and metadata to {target_dir.name}/")
        return data_path