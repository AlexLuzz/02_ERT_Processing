from config.paths import ProjectPaths
from src.loaders.das_loader import DASLoader

if __name__ == "__main__":
    paths = ProjectPaths(user='AQ96560', project_name='DAS_Initial_Test') 
    
    loader = DASLoader(site_id="MCM_DAS_01")
    
    # 1. Load the file lazily
    loader.load_nc(source= "C:/Users/AQ96560/Downloads/s1.nc")
    
    # 2. Extract and print the internal structure
    meta = loader.inspect_metadata(print_summary=True)
    
    # 3. Use the exact variable name printed in the console for your plot
    # loader.plot_waterfall(data_var='<EXACT_VAR_NAME_FROM_CONSOLE>')