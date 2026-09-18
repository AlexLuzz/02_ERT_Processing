from pathlib import Path
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np

from src.core.base import ProjectBase

class DASLoader(ProjectBase):
    """Data loader for Distributed Acoustic Sensing (DAS) NetCDF files."""

    def __init__(self, site_id: str):
        super().__init__()
        self.site_id = site_id
        self.dataset = None
        
        self.logger.info(f"Initialized DASLoader for site: '{self.site_id}'.")

    def _resolve_files(self, source: Path | str | list, pattern: str = "*.nc") -> list[Path]:
        """Resolves file paths, identical to the ERTLoader logic."""
        if isinstance(source, list):
            return [Path(f) for f in source if Path(f).exists()]
        
        source_path = Path(source)
        if source_path.is_file(): return [source_path]
        if source_path.is_dir(): return list(source_path.glob(pattern))
        if source_path.parent.is_dir(): return list(source_path.parent.glob(source_path.name))
        
        raise FileNotFoundError(f"Path does not exist: {source_path}")

    def load_nc(self, source: Path | str | list, pattern: str = "*.nc", use_dask: bool = True) -> xr.Dataset:
        """
        Loads NetCDF files lazily. 
        Setting use_dask=True allows terabytes of data to be parsed instantly without filling RAM.
        """
        files = self._resolve_files(source, pattern)
        if not files:
            raise FileNotFoundError(f"No files matching '{pattern}' found in {source}")

        self.logger.info(f"Loading {len(files)} DAS NetCDF file(s)...")

        # Scalability Key: 'chunks="auto"' tells Dask to manage RAM dynamically
        chunks = "auto" if use_dask else None
        
        if len(files) == 1:
            self.dataset = xr.open_dataset(files[0], chunks=chunks)
        else:
            # open_mfdataset seamlessly stitches hundreds of .nc files together along the time dimension
            self.dataset = xr.open_mfdataset(files, chunks=chunks, combine="by_coords")

        self.logger.info(f"DAS Data Loaded. Dimensions: {dict(self.dataset.dims)}")
        return self.dataset

    def inspect_metadata(self, print_summary: bool = True) -> dict:
        """
        Scans the loaded NetCDF file and extracts dimensions, coordinates, 
        and variable structures without loading the heavy arrays into RAM.
        """
        if self.dataset is None:
            raise ValueError("Dataset not loaded. Call load_nc() first.")

        ds = self.dataset
        
        metadata = {
            "dimensions": dict(ds.dims),
            "coordinates": list(ds.coords.keys()),
            "variables": {},
            "global_attributes": dict(ds.attrs)
        }

        if print_summary:
            self.logger.info("--- DAS NetCDF Structure Summary ---")
            self.logger.info(f"Dimensions: {metadata['dimensions']}")
            self.logger.info(f"Coordinates: {metadata['coordinates']}")

        for var_name, var_data in ds.data_vars.items():
            var_info = {
                "shape": var_data.shape,
                "dimensions": var_data.dims,
                "dtype": str(var_data.dtype),
                "attributes": dict(var_data.attrs)
            }
            metadata["variables"][var_name] = var_info
            
            if print_summary:
                self.logger.info(f"Var: '{var_name}' | Shape: {var_info['shape']} | Type: {var_info['dtype']}")
                
                # Fetch a tiny 5-element snippet of the actual data to see what the numbers look like
                try:
                    # Slices the first index of all dimensions except the last one, grabbing 5 values
                    slice_dict = {dim: 0 for dim in var_data.dims[:-1]}
                    slice_dict[var_data.dims[-1]] = slice(0, 5)
                    data_snippet = var_data.isel(**slice_dict).values
                    self.logger.info(f"     Preview -> {data_snippet}")
                except Exception:
                    self.logger.info(f"     Preview -> [Cannot extract snippet safely]")

        return metadata

    def plot_waterfall(self, data_var: str, ax=None, time_slice=None, distance_slice=None, cmap="RdBu_r", robust=True):
        """
        Extracts a 2D slice of the data and plots a standard waterfall (Time vs Distance).
        
        Args:
            data_var: The name of the variable in the .nc file (e.g., 'strain', 'strain_rate', 'data').
            time_slice: A standard python slice to restrict time (e.g., slice(0, 1000)).
            distance_slice: A standard python slice to restrict channels/distance (e.g., slice(200, 500)).
            robust: If True, automatically drops massive outlier spikes so the colormap is readable.
        """
        if self.dataset is None:
            raise ValueError("No data loaded. Call load_nc() first.")
        if data_var not in self.dataset.data_vars:
            raise KeyError(f"Variable '{data_var}' not found. Available: {list(self.dataset.data_vars.keys())}")

        # Note: You may need to change 'time' and 'distance' to match the exact dimension names in your .nc file
        ds_plot = self.dataset[data_var]
        
        if time_slice:
            # .isel() slices by index. If you want to slice by physical time/meters, use .sel()
            ds_plot = ds_plot.isel(time=time_slice) 
        if distance_slice:
            ds_plot = ds_plot.isel(distance=distance_slice) 

        self.logger.info("Computing requested slice into RAM for plotting...")
        
        # .compute() forces Dask to actually load the requested slice into memory
        plot_array = ds_plot.compute()

        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 6))
            
        # xarray integrates directly with matplotlib
        plot_array.plot(ax=ax, cmap=cmap, robust=robust)
        ax.set_title(f"DAS Waterfall Plot | {self.site_id}", fontsize=12, fontweight='bold')
        
        return ax