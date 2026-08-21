# scripts/quick_inv.py
from config.paths import ProjectPaths
from src.loaders.ert_loader import ERTLoader
from src.processing import spatial_filters, temporal_filters
from src.inversion.pygimli_formatter import build_ert_container

if __name__ == "__main__":
    paths = ProjectPaths(project_name="Laval_IV_Monitoring")
    loader = ERTLoader()
    raw_ohmpi = loader.load_ohmpi(paths.DATA_DIR / "measurements_20260819.csv")

    # 2. Process (Functional, clean, easy to read)
    df_clean = spatial_filters.filter_by_voltage(raw_ohmpi, min_voltage_mv=0.5)
    df_clean = spatial_filters.remove_dead_electrodes(df_clean, bad_electrodes=[18, 34, 41])
    df_clean = temporal_filters.filter_discontinued_quadripoles(df_clean, min_surveys=5)

    # 3. Save to Project with YAML
    loader.save_project_dataset(
        df=df_clean, 
        project_data_dir=paths.OUTPUT_DIR, # Using ProjectPaths OUTPUT_DIR which points to DATA for projects
        location="Laval_IV", 
        hardware="OhmPi"
    )