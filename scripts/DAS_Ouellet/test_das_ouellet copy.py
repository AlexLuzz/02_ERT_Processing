import matplotlib.pyplot as plt
from config.paths import ProjectPaths
from src.loaders.das_loader import DASLoader

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi', project_name='DAS_Initial_Test') 
    
    loader = DASLoader(site_id="MCM_DAS_01")
    
    data = loader.load_nc(source= paths.onedrive_root / "s1.nc")
    
    fig, ax = plt.subplots(figsize=(12, 6))

    data = data['__xarray_dataarray_variable__']

    #data = data.isel(time=slice(0, 2000))
    #data = data.isel(channels=slice(0, 2000))

    data = data.compute()

    data.plot(ax=ax, cmap="RdBu_r", robust=True)
    ax.set_xlabel("Time")
    ax.set_ylabel("Channel")
    
    plt.show()