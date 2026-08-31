# Project Architecture: 02_ERT_Processing

## Directory Tree & Signatures

```text
├── code_diagnosis
│   ├── architecture_audit.py
│   │       └── def analyze_python_file(file_path)
│   │           """Extracts imports, classes, and functions using AST."""
│   │       └── def run_external_tool(module_name, args)
│   │           """Runs a Python module tool using the current Python environment."""
│   │       └── def build_full_audit(target_dir, output_file, ignore_dirs)
│   ├── generate_architecture.py
│   │       └── def extract_signatures(file_path)
│   │           """Extracts top-level and class-level definitions from a Python file using AST."""
│   │       └── def generate_full_architecture(root_dir, output_file, ignore_dirs)
│   ├── generate_enhanced_architecture.py
│   │       └── def analyze_python_file(file_path)
│   │           """Parses a Python file to extract imports, class/method hierarchies, and functions."""
│   │       └── def generate_deep_architecture_report(root_dir, output_file, ignore_dirs)
│   └── generate_tree.py
│           └── def save_tree_to_file(root_dir, output_file, ignore_dirs)
├── config
│   └── paths.py
│           └── class ProjectPaths:
│               """Centralized, READ-ONLY path management for raw ERT data."""
│               └── def __init__(self, user, project_name)
│               └── def __repr__(self)
├── scripts
│   ├── ERT
│   │   └── run_123.py
│   └── TL-ERT
├── src
│   ├── core
│   │   ├── __init__.py
│   │   └── base.py
│   │           └── class ProjectBase:
│   │               """Abstract base class providing logging, standardized saving/loading, """
│   │               └── def __init__(self)
│   │               └── def _setup_logging(self)
│   │               └── def load(self, file_path)
│   │               └── def save(self, data, file_path, metadata)
│   │               └── def save_mesh(self, mesh, file_path)
│   │               └── def load_mesh(self, file_path)
│   ├── loaders
│   │   ├── __init__.py
│   │   ├── ert_loader.py
│   │   │       └── class ERTLoader:
│   │   │           """Data loader for ERT instruments"""
│   │   │           └── def __init__(self, site_id, elec_pos)
│   │   │           └── def _resolve_files(self, source, pattern)
│   │   │           └── def finalize_standardization(self)
│   │   │           └── def load_prime(self, source, pattern, standardize)
│   │   │           └── def load_sas4000(self, source, pattern, standardize)
│   │   │           └── def load_ohmpi(self, source, pattern, standardize)
│   │   ├── ert_loading_tools.py
│   │   │       └── def scan_header(filepath, data_start_markers, delimiter, keys_to_keep)
│   │   │           """Scans a text file to extract specific metadata and find the data starting line."""
│   │   │       └── def split_sas4000_surveys(df, time_gap_hours)
│   │   │           """Detects multiple surveys within a single dataframe by looking for time """
│   │   │       └── def pygimli_compute_geometric_factors(df, df_elec_pos)
│   │   │           """Compute geometric factors using PyGIMLi."""
│   │   │       └── def compute_geometric_factors(df, df_elec_pos)
│   │   │           """Compute geometric factors using 3D Euclidean distances."""
│   │   │       └── def get_reciprocal_mask(df)
│   │   │           """Identify reciprocal ERT measurements by following acquisition order."""
│   │   │       └── def get_reciprocal_mask_vectorized(df)
│   │   │           """Fast vectorized version of get_reciprocal_mask()."""
│   │   │       └── def process_reciprocals(df)
│   │   │           """Flips reciprocal dipoles to match forward configurations, isolates true """
│   │   │       └── def load_geometry(filepath, params)
│   │   │           """Load and process electrode geometry."""
│   │   └── weather_loading_tools.py
│   │           └── def fetch_weather_data(start_date, end_date, freq, station_id)
│   │               """Fetches daily weather data from Environment Canada and resamples to desired frequency."""
│   ├── mesh
│   │   ├── __init__.py
│   │   ├── gmesh_tools.py
│   │   │       └── def build_gmsh_mesh(df, surface_offset, depth, extension, size_surface, size_depth, params, out_path)
│   │   │           """Build an unstructured X-Z mesh using Gmsh tailored for PyGIMLi."""
│   │   └── pygimli_mesh_tools.py
│   │           └── def build_grid_mesh(x_min, x_max, y_min, y_max, dx, dy)
│   │               """Creates a structured quadrilateral grid."""
│   │           └── def build_unstructured_mesh(df, surface_offset, depth, extension, refine_dist)
│   │               """Create an unstructured triangular mesh from electrode positions with """
│   │           └── def safe_mesh_save(mesh, target_path)
│   │               """Saves a PyGIMLi mesh by bypassing Windows/C++ long path and accent limits."""
│   │           └── def safe_mesh_load(source_path)
│   │               """Loads a PyGIMLi mesh bypassing Windows/C++ encoding and path limits."""
│   ├── processing
│   │   ├── data
│   │   │   ├── __init__.py
│   │   │   ├── data_preparator.py
│   │   │   │       └── def log_filtration(func)
│   │   │   │           """Decorator to automatically log dropped measurements and top affected A-B pairs."""
│   │   │   │       └── class DataPreparator:
│   │   │   │           └── def __init__(self)
│   │   │   │           └── def filter_mono2m_custom(self, df, min_v, max_err)
│   │   │   ├── data_tools.py
│   │   │   │       └── def resample_timeseries(df, freq_hours, max_gap_hours, timestamp_col, config_cols, meas_cols)
│   │   │   │           """Resamples data and interpolates missing values strictly bounded by max_gap_hours."""
│   │   │   │       └── def interpolate_excluded_period(df, electrodes, start_date, end_date, date_col, cols_to_interp, config_cols)
│   │   │   │           """Finds measurements containing specific electrodes during a time window, """
│   │   │   │       └── def filter_common_measurements(df, config_cols, date_col)
│   │   │   │           """Ensures every survey has the exact same length by keeping only the """
│   │   │   └── filtration_tools.py
│   │   │           └── def get_date_range_mask(df, start_date, end_date, return_df, date_col)
│   │   │               """Returns True for rows where the date is within the specified range."""
│   │   │           └── def get_threshold_mask(df, col, min_val, max_val)
│   │   │               """Returns True for values strictly within the min/max bounds."""
│   │   │           └── def get_excluded_elecs_mask(df, excluded_elecs, config_cols)
│   │   │               """Returns False if any electrode in the configuration is in the excluded list."""
│   │   │           └── def get_excluded_configs_mask(df, excluded_configs, config_cols)
│   │   │               """Returns False for exact A, B, M, N configuration matches."""
│   │   │           └── def get_hampel_mask(df, target_col, window_size, n_sigma, config_cols)
│   │   │               """Vectorized Hampel filter. Returns False for outliers detected within the rolling window."""
│   │   │           └── def get_discontinued_configs_mask(df, min_length, config_cols)
│   │   │               """Returns False for electrode configurations that have fewer total measurements than min_length."""
│   │   ├── inversion
│   │   │   ├── __init__.py
│   │   │   ├── ert_processor.py
│   │   │   │       └── class ERTProcessor:
│   │   │   │           """Runner class for ERT inversions with ensemble support, detailed iteration tracking,"""
│   │   │   │           └── def __init__(self, folder_path, mesh, electrode_positions, simulation_name)
│   │   │   │           └── def _log_init_stats(self)
│   │   │   │           └── def set_errors(self, df, error_val)
│   │   │   │           └── def run_inversion(self, df, inv_params, inversion_type, save_all_iterations)
│   │   │   │           └── def _update_registry(self, run_id, start_time, inv_type, params, res, total_iters, filename)
│   │   │   │           └── def run_ensemble(self, df, param_grid, inversion_type, save_all_iterations)
│   │   │   └── pygimli_tools.py
│   │   │           └── def build_ert_container(df_survey, geom_df, default_error)
│   │   │               """Converts a standardized Pandas DataFrame for a SINGLE survey into a PyGIMLi DataContainerERT[cite: 7]."""
│   │   │           └── def build_ert_containers_timeseries(df, geom_df, date_col)
│   │   │               """Wrapper that turns a multi-survey dataframe into a list of PyGIMLi containers. """
│   │   │           └── def get_common_configs(df, config_cols, date_col)
│   │   │               """Identifies electrode configurations that exist across ALL surveys."""
│   │   └── __init__.py
│   ├── visualization
│   │   ├── basic_plotting.py
│   │   │       └── def format_time_axis(ax)
│   │   │           """Smart date locator with MM-dd format and 45-degree angle."""
│   │   │       └── def plot_electrodes(df, ax, elec_numbers)
│   │   │           """Plot selected electrodes on an existing axis."""
│   │   │       └── def plot_weather_data(weather_df, start_date, end_date, ax)
│   │   │       └── def extract_polygons(mesh)
│   │   │           """Directly builds Matplotlib polygons from a PyGIMLi mesh."""
│   │   │       └── def plot_array_on_mesh(polygons, array, ax)
│   │   │           """Plot an array of values on a collection of polygons."""
│   │   ├── inversion_data_report.py
│   │   │       └── class InversionDataReport:
│   │   │           └── def __init__(self, mesh, times, models, filepath, elec_pos)
│   │   │           └── def print(cls)
│   │   │           └── def build(self)
│   │   │           └── def print_result_array_pages(self, times, models_array, title_prefix, rows, cols, landscape, cmap, norm, cbar_label)
│   │   ├── raw_tlert_report.py
│   │   │       └── class RawTLERTReport:
│   │   │           └── def __init__(self, df, df_elec, df_weather, filepath, max_groups, plot_every_nth_group)
│   │   │           └── def print(cls)
│   │   │           └── def build(self)
│   │   │           └── def _page_survey_data_metrics(self)
│   │   │           └── def _build_timeseries_pages(self, plots_per_page)
│   │   ├── report_base.py
│   │   │       └── class ReportBase:
│   │   │           └── def __init__(self, filepath)
│   │   │           └── def __enter__(self)
│   │   │           └── def __exit__(self, exc_type, exc_val, exc_tb)
│   │   │           └── def page(self, rows, cols, height_ratios, width_ratios, landscape)
│   │   │           └── def build(self)
│   │   └── single_ert_report.py
│   │           └── class SingleSurveyERTReport:
│   │               └── def __init__(self, filepath, df, mgr, params, run_id)
│   │               └── def print(cls)
│   │               └── def build(self)
│   │               └── def _build_page_1_data(self)
│   │               └── def _build_page_2_inversion(self)
│   │               └── def _build_page_3_coverage(self)
│   └── __init__.py
├── tests
│   ├── loaders
│   │   ├── 00_test_all.py
│   │   ├── test_elecs_projection.py
│   │   │       └── def run_geometry_tests(paths, loader)
│   │   ├── test_ert_loader.py
│   │   │       └── def test_loading(site_id, file_path, load_function)
│   │   │           """Test loading a single file using a specific loader method."""
│   │   │       └── def run_ert_loader_tests(paths)
│   │   │           """Run full loader test suite for Berlier-Bergman and MCM sites."""
│   │   ├── test_header_scanner.py
│   │   │       └── def run_header_tests(paths)
│   │   ├── test_load_elecs_pos.py
│   │   │       └── def run_geometry_tests(paths, loader)
│   │   ├── test_sas4000_parser.py
│   │   │       └── def run_sas4000_split_tests(paths, loader)
│   │   └── test_std_save_reload.py
│   │           └── def run_save_reload_tests(paths, loader)
│   ├── mesh
│   │   ├── test_gmsh.py
│   │   │       └── def test_build_MCM_GEO_gmsh()
│   │   │       └── def test_build_MCM_M2m_gmsh()
│   │   └── test_pygimli_mesh.py
│   │           └── def test_build_grid_mesh()
│   │           └── def test_build_unstructured_mesh()
│   │           └── def test_build_MCM_GEO()
│   │           └── def test_build_MCM_M2m()
│   ├── processing
│   │   ├── data
│   │   │   └── test_prepared_data_report_BB.py
│   │   └── inversion
│   │       └── test_inversion_MONO2M.py
│   ├── visualization
│   │   ├── test_inversion_report_MONO2M.py
│   │   ├── test_plot_elec_geometry.py
│   │   │       └── def test_loading(source, file_path, load_function)
│   │   │           """Test loading a single file using a specific loader function."""
│   │   ├── test_raw_data_report_BB.py
│   │   └── test_raw_data_report_MONO2M.py
│   └── test.py
├── .env
├── ARCHITECTURE_AUDIT.md
├── JOURNAL.txt
├── main.py
├── README.md
└── TODO.txt
```
