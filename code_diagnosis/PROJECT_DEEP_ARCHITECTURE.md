# Project Deep Architecture: 02_ERT_Processing

## Summary of Modules & Structures

### `code_diagnosis\architecture_audit.py`

**Functions:**
- `def analyze_python_file(file_path)` — *Extracts imports, classes, and functions using AST.*
- `def run_external_tool(module_name, args)` — *Runs a Python module tool using the current Python environment.*
- `def build_full_audit(target_dir, output_file, ignore_dirs)`

---

### `code_diagnosis\generate_architecture.py`

**Functions:**
- `def extract_signatures(file_path)` — *Extracts top-level and class-level definitions from a Python file using AST.*
- `def generate_full_architecture(root_dir, output_file, ignore_dirs)`

---

### `code_diagnosis\generate_enhanced_architecture.py`

**Functions:**
- `def analyze_python_file(file_path)` — *Parses a Python file to extract imports, class/method hierarchies, and functions.*
- `def generate_deep_architecture_report(root_dir, output_file, ignore_dirs)`

---

### `code_diagnosis\generate_tree.py`

**Functions:**
- `def save_tree_to_file(root_dir, output_file, ignore_dirs)`

---

### `config\paths.py`

**Classes:**
- `class ProjectPaths` (2 methods) — *Centralized, READ-ONLY path management for raw ERT data.*
  - `def __init__(self, user, project_name)`
  - `def __repr__(self)`

---

### `main.py`

**Dependencies:**
- *Third-party:* `config, src`

---

### `scripts\ERT\run_123.py`

**Dependencies:**
- *Third-party:* `config, src`

---

### `src\__init__.py`

---

### `src\core\__init__.py`

---

### `src\core\base.py`

**Dependencies:**
- *Third-party:* `h5py, numpy, pandas, src`

**Classes:**
- `class ProjectBase` (6 methods) — *Abstract base class providing logging, standardized saving/loading, *
  - `def __init__(self)`
  - `def _setup_logging(self)`
  - `def load(self, file_path)`
  - `def save(self, data, file_path, metadata)`
  - `def save_mesh(self, mesh, file_path)`
  - `def load_mesh(self, file_path)`

---

### `src\loaders\__init__.py`

---

### `src\loaders\ert_loader.py`

**Dependencies:**
- *Third-party:* `numpy, pandas, src`

**Classes:**
- `class ERTLoader` (6 methods) — *Data loader for ERT instruments*
  - `def __init__(self, site_id, elec_pos)`
  - `def _resolve_files(self, source, pattern)`
  - `def finalize_standardization(self)`
  - `def load_prime(self, source, pattern, standardize)`
  - `def load_sas4000(self, source, pattern, standardize)`
  - `def load_ohmpi(self, source, pattern, standardize)`

---

### `src\loaders\ert_loading_tools.py`

**Dependencies:**
- *Third-party:* `numpy, pandas`

**Functions:**
- `def scan_header(filepath, data_start_markers, delimiter, keys_to_keep)` — *Scans a text file to extract specific metadata and find the data starting line.*
- `def split_sas4000_surveys(df, time_gap_hours)` — *Detects multiple surveys within a single dataframe by looking for time *
- `def pygimli_compute_geometric_factors(df, df_elec_pos)` — *Compute geometric factors using PyGIMLi.*
- `def compute_geometric_factors(df, df_elec_pos)` — *Compute geometric factors using 3D Euclidean distances.*
- `def get_reciprocal_mask(df)` — *Identify reciprocal ERT measurements by following acquisition order.*
- `def get_reciprocal_mask_vectorized(df)` — *Fast vectorized version of get_reciprocal_mask().*
- `def process_reciprocals(df)` — *Flips reciprocal dipoles to match forward configurations, isolates true *
- `def load_geometry(filepath, params)` — *Load and process electrode geometry.*

---

### `src\loaders\weather_loading_tools.py`

**Dependencies:**
- *Third-party:* `pandas, requests`

**Functions:**
- `def fetch_weather_data(start_date, end_date, freq, station_id)` — *Fetches daily weather data from Environment Canada and resamples to desired frequency.*

---

### `src\mesh\__init__.py`

---

### `src\mesh\gmesh_tools.py`

**Dependencies:**
- *Third-party:* `gmsh, pandas, pygimli`

**Functions:**
- `def build_gmsh_mesh(df, surface_offset, depth, extension, size_surface, size_depth, params, out_path)` — *Build an unstructured X-Z mesh using Gmsh tailored for PyGIMLi.*

---

### `src\mesh\pygimli_mesh_tools.py`

**Dependencies:**
- *Third-party:* `numpy, pygimli`

**Functions:**
- `def build_grid_mesh(x_min, x_max, y_min, y_max, dx, dy)` — *Creates a structured quadrilateral grid.*
- `def build_unstructured_mesh(df, surface_offset, depth, extension, refine_dist)` — *Create an unstructured triangular mesh from electrode positions with *
- `def safe_mesh_save(mesh, target_path)` — *Saves a PyGIMLi mesh by bypassing Windows/C++ long path and accent limits.*
- `def safe_mesh_load(source_path)` — *Loads a PyGIMLi mesh bypassing Windows/C++ encoding and path limits.*

---

### `src\processing\__init__.py`

---

### `src\processing\data\__init__.py`

---

### `src\processing\data\data_preparator.py`

**Dependencies:**
- *Third-party:* `pandas, src`

**Classes:**
- `class DataPreparator` (2 methods)
  - `def __init__(self)`
  - `def filter_mono2m_custom(self, df, min_v, max_err)`

**Functions:**
- `def log_filtration(func)` — *Decorator to automatically log dropped measurements and top affected A-B pairs.*

---

### `src\processing\data\data_tools.py`

**Dependencies:**
- *Third-party:* `numpy, pandas`

**Functions:**
- `def resample_timeseries(df, freq_hours, max_gap_hours, timestamp_col, config_cols, meas_cols)` — *Resamples data and interpolates missing values strictly bounded by max_gap_hours.*
- `def interpolate_excluded_period(df, electrodes, start_date, end_date, date_col, cols_to_interp, config_cols)` — *Finds measurements containing specific electrodes during a time window, *
- `def filter_common_measurements(df, config_cols, date_col)` — *Ensures every survey has the exact same length by keeping only the *

---

### `src\processing\data\filtration_tools.py`

**Dependencies:**
- *Third-party:* `numpy, pandas`

**Functions:**
- `def get_date_range_mask(df, start_date, end_date, return_df, date_col)` — *Returns True for rows where the date is within the specified range.*
- `def get_threshold_mask(df, col, min_val, max_val)` — *Returns True for values strictly within the min/max bounds.*
- `def get_excluded_elecs_mask(df, excluded_elecs, config_cols)` — *Returns False if any electrode in the configuration is in the excluded list.*
- `def get_excluded_configs_mask(df, excluded_configs, config_cols)` — *Returns False for exact A, B, M, N configuration matches.*
- `def get_hampel_mask(df, target_col, window_size, n_sigma, config_cols)` — *Vectorized Hampel filter. Returns False for outliers detected within the rolling window.*
- `def get_discontinued_configs_mask(df, min_length, config_cols)` — *Returns False for electrode configurations that have fewer total measurements than min_length.*

---

### `src\processing\inversion\__init__.py`

---

### `src\processing\inversion\ert_processor.py`

**Dependencies:**
- *Third-party:* `numpy, pandas, pygimli, src`

**Classes:**
- `class ERTProcessor` (6 methods) — *Runner class for ERT inversions with ensemble support, detailed iteration tracking,*
  - `def __init__(self, folder_path, mesh, electrode_positions, simulation_name)`
  - `def _log_init_stats(self)`
  - `def set_errors(self, df, error_val)`
  - `def run_inversion(self, df, inv_params, inversion_type, save_all_iterations)`
  - `def _update_registry(self, run_id, start_time, inv_type, params, res, total_iters, filename)`
  - `def run_ensemble(self, df, param_grid, inversion_type, save_all_iterations)`

---

### `src\processing\inversion\pygimli_tools.py`

**Dependencies:**
- *Third-party:* `numpy, pandas, pygimli`

**Functions:**
- `def build_ert_container(df_survey, geom_df, default_error)` — *Converts a standardized Pandas DataFrame for a SINGLE survey into a PyGIMLi DataContainerERT.*
- `def build_ert_containers_timeseries(df, geom_df, date_col)` — *Wrapper that turns a multi-survey dataframe into a list of PyGIMLi containers. *
- `def get_common_configs(df, config_cols, date_col)` — *Identifies electrode configurations that exist across ALL surveys.*

---

### `src\visualization\basic_plotting.py`

**Dependencies:**
- *Third-party:* `matplotlib, numpy, pandas`

**Functions:**
- `def format_time_axis(ax)` — *Smart date locator with MM-dd format and 45-degree angle.*
- `def plot_electrodes(df, ax, elec_numbers)` — *Plot selected electrodes on an existing axis.*
- `def plot_weather_data(weather_df, start_date, end_date, ax)`
- `def extract_polygons(mesh)` — *Directly builds Matplotlib polygons from a PyGIMLi mesh.*
- `def plot_array_on_mesh(polygons, array, ax)` — *Plot an array of values on a collection of polygons.*

---

### `src\visualization\inversion_data_report.py`

**Dependencies:**
- *Third-party:* `matplotlib, numpy, pandas, src`

**Classes:**
- `class InversionDataReport` (4 methods)
  - `def __init__(self, mesh, times, models, filepath, elec_pos)`
  - `def print(cls)`
  - `def build(self)`
  - `def print_result_array_pages(self, times, models_array, title_prefix, rows, cols, landscape, cmap, norm, cbar_label)`

---

### `src\visualization\raw_tlert_report.py`

**Dependencies:**
- *Third-party:* `matplotlib, numpy, pandas, src`

**Classes:**
- `class RawTLERTReport` (5 methods)
  - `def __init__(self, df, df_elec, df_weather, filepath, max_groups, plot_every_nth_group)`
  - `def print(cls)`
  - `def build(self)`
  - `def _page_survey_data_metrics(self)`
  - `def _build_timeseries_pages(self, plots_per_page)`

---

### `src\visualization\report_base.py`

**Dependencies:**
- *Third-party:* `matplotlib`

**Classes:**
- `class ReportBase` (5 methods)
  - `def __init__(self, filepath)`
  - `def __enter__(self)`
  - `def __exit__(self, exc_type, exc_val, exc_tb)`
  - `def page(self, rows, cols, height_ratios, width_ratios, landscape)`
  - `def build(self)`

---

### `src\visualization\single_ert_report.py`

**Dependencies:**
- *Third-party:* `matplotlib, numpy, pandas, pygimli, src`

**Classes:**
- `class SingleSurveyERTReport` (6 methods)
  - `def __init__(self, filepath, df, mgr, params, run_id)`
  - `def print(cls)`
  - `def build(self)`
  - `def _build_page_1_data(self)`
  - `def _build_page_2_inversion(self)`
  - `def _build_page_3_coverage(self)`

---

### `tests\loaders\00_test_all.py`

**Dependencies:**
- *Third-party:* `config, src, tests`

---

### `tests\loaders\test_elecs_projection.py`

**Dependencies:**
- *Third-party:* `config, matplotlib, src`

**Functions:**
- `def run_geometry_tests(paths, loader)`

---

### `tests\loaders\test_ert_loader.py`

**Dependencies:**
- *Third-party:* `config, src`

**Functions:**
- `def test_loading(site_id, file_path, load_function)` — *Test loading a single file using a specific loader method.*
- `def run_ert_loader_tests(paths)` — *Run full loader test suite for Berlier-Bergman and MCM sites.*

---

### `tests\loaders\test_header_scanner.py`

**Dependencies:**
- *Third-party:* `config, src`

**Functions:**
- `def run_header_tests(paths)`

---

### `tests\loaders\test_load_elecs_pos.py`

**Dependencies:**
- *Third-party:* `config, matplotlib, src`

**Functions:**
- `def run_geometry_tests(paths, loader)`

---

### `tests\loaders\test_sas4000_parser.py`

**Dependencies:**
- *Third-party:* `config, src`

**Functions:**
- `def run_sas4000_split_tests(paths, loader)`

---

### `tests\loaders\test_std_save_reload.py`

**Dependencies:**
- *Third-party:* `config, pandas, src`

**Functions:**
- `def run_save_reload_tests(paths, loader)`

---

### `tests\mesh\test_gmsh.py`

**Dependencies:**
- *Third-party:* `config, matplotlib, pygimli, src`

**Functions:**
- `def test_build_MCM_GEO_gmsh()`
- `def test_build_MCM_M2m_gmsh()`

---

### `tests\mesh\test_pygimli_mesh.py`

**Dependencies:**
- *Third-party:* `config, matplotlib, src`

**Functions:**
- `def test_build_grid_mesh()`
- `def test_build_unstructured_mesh()`
- `def test_build_MCM_GEO()`
- `def test_build_MCM_M2m()`

---

### `tests\processing\data\test_prepared_data_report_BB.py`

**Dependencies:**
- *Third-party:* `config, src`

---

### `tests\processing\inversion\test_inversion_MONO2M.py`

**Dependencies:**
- *Third-party:* `config, numpy, pandas, src`

---

### `tests\test.py`

**Dependencies:**
- *Third-party:* `matplotlib`

---

### `tests\visualization\test_inversion_report_MONO2M.py`

**Dependencies:**
- *Third-party:* `config, src`

---

### `tests\visualization\test_plot_elec_geometry.py`

**Dependencies:**
- *Third-party:* `config, matplotlib, src`

**Functions:**
- `def test_loading(source, file_path, load_function)` — *Test loading a single file using a specific loader function.*

---

### `tests\visualization\test_raw_data_report_BB.py`

**Dependencies:**
- *Third-party:* `config, src`

---

### `tests\visualization\test_raw_data_report_MONO2M.py`

**Dependencies:**
- *Third-party:* `config, src`

---

