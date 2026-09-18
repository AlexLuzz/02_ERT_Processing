import matplotlib.pyplot as plt
from config.paths import ProjectPaths
from src.loaders.das_loader import DASLoader

if __name__ == "__main__":
    # 1. Centralized Path Routing
    paths = ProjectPaths(user='AQ96560', project_name='DAS_Initial_Test') 
    
    # 2. Initialize Loader
    loader = DASLoader(site_id="MCM_DAS_01")
    
    # 3. Load the NetCDF file lazily 
    ds = loader.load_nc(source= "C:/Users/AQ96560/Downloads/s1.nc")
    
    # 4. Check what variables are actually named in your specific file
    print("Variables in file:", list(ds.data_vars.keys()))
    print("Dimensions in file:", dict(ds.dims))
    
    # 5. Plot the first 2000 time samples and channels 100 to 500
    # Change 'data_var' to whatever string printed in Step 4
    fig, ax = plt.subplots(figsize=(12, 6))
    loader.plot_waterfall(
        data_var='strain', # Replace with your variable name
        time_slice=slice(0, 2000), 
        distance_slice=slice(100, 500), 
        ax=ax
    )
    
    # 6. Save directly to the dynamically generated output folder
    plt.tight_layout()
    plt.savefig(paths.ACTIVE_PROJECT_DIR / "das_first_look.png", dpi=300)
    plt.show()