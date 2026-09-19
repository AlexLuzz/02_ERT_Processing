from config.paths import ProjectPaths
from src.loaders.das_loader import DASLoader

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi', project_name='DAS_Initial_Test') 
    
    loader = DASLoader(site_id="MCM_DAS_01")
    
    # 1. Load the file lazily
    data = loader.load_nc(source= paths.DAS_OUELLET_2024 / "s4.nc")
    
    # 2. Extract and print the internal structure
    meta = loader.inspect_metadata(print_summary=True)
    
    print(data)