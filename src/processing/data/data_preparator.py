from src.processing.data.data_tools import *
from src.processing.data.filtration_tools import *
from src.core.base import ProjectBase

class DataPreparator(ProjectBase):
    def __init__(self, project_name, **kwargs):
        super().__init__(project_name=project_name, **kwargs)
        
    def apply_site_filtration(self, df, config):
        # 1. Generate individual masks using data_tools
        volt_mask = get_threshold_mask(df, config['min_v'])
        err_mask = get_threshold_mask(df, config['max_err'])
        hampel_mask = get_hampel_mask(df, config['window'], config['sigma'])
        
        # 2. Fuse masks (True means KEEP the data)
        final_mask = volt_mask & err_mask & ~hampel_mask
        
        # 3. Log the exact impact of the filtration via ProjectBase
        dropped = len(df) - final_mask.sum()
        self.logger.info(f"Filtration removed {dropped} measurements.")
        
        # 4. Isolate data
        clean_data = df[final_mask]
        self.save_data(clean_data, "filtered_data.csv") # Inherited method
        return clean_data