import pandas as pd
from src.loaders.ert_loader import ERTLoader
from config.paths import ProjectPaths

def run_save_reload_tests(paths: ProjectPaths, loader: ERTLoader):
    print("\n=== TESTING SAVE & RELOAD ===")
    
    # 1. Load some data
    ohmpi_file = paths.RAW_OHMPI / "measurements_20260818T060008.csv"
    df_raw = loader.load_ohmpi("BB", ohmpi_file)
    
    # 2. Save it
    target_dir = paths.DATA_DIR / "TEST_SAVE"
    loader.save_dataset(df_raw, target_dir, "test_dataset", metadata={"test": "data"})
    
    # 3. Reload it directly with Pandas
    try:
        df_reloaded = pd.read_parquet(target_dir / "test_dataset.parquet")
        match = df_raw.shape == df_reloaded.shape
        print(f"✅ Reload successful from Parquet! Shape matches: {match}")
    except Exception as e:
        print(f"❌ Reload failed: {e}")

if __name__ == "__main__":
    run_save_reload_tests(ProjectPaths(user='AQ96560'), ERTLoader())