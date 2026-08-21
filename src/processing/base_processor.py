import logging
import yaml
import pickle
import pandas as pd
from pathlib import Path
from datetime import datetime

class BaseProcessor:
    """
    Abstract base class providing logging, standardized saving, and YAML 
    configuration tracking for all pipeline steps.
    """
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Sets up a standardized logger for the inheriting class."""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        return logger

    def save_step(self, step_name: str, data: any, config: dict, data_format: str = 'csv'):
        """
        Creates a dedicated folder for the processing step, saves the data, 
        and dumps the configuration to a YAML file for complete traceability.
        """
        # 1. Create a dedicated folder for this step (e.g., OUTPUT/01_filtered)
        step_dir = self.output_dir / step_name
        step_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{step_name}_{timestamp}"
        
        # 2. Save the configuration/metadata as YAML
        yaml_path = step_dir / f"{base_filename}_config.yaml"
        # Add basic tracking metadata to the config
        config['_metadata'] = {
            "processor": self.__class__.__name__,
            "timestamp": timestamp,
        }
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        # 3. Save the data based on the requested format
        if data_format == 'csv' and isinstance(data, pd.DataFrame):
            data_path = step_dir / f"{base_filename}.csv"
            data.to_csv(data_path, index=False)
        elif data_format == 'parquet' and isinstance(data, pd.DataFrame):
            # Parquet is much faster and smaller than CSV for big ERT datasets
            data_path = step_dir / f"{base_filename}.parquet"
            data.to_parquet(data_path, index=False)
        else:
            # Fallback for PyGIMLi objects, dictionaries, or models
            data_path = step_dir / f"{base_filename}.pkl"
            with open(data_path, 'wb') as f:
                pickle.dump(data, f)
                
        self.logger.info(f"✅ Saved outputs and YAML config to {step_dir.name}/")
        return data_path, yaml_path