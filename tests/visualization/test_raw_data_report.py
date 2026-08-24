from src.loaders.ert_loader import ERTLoader
from config.paths import ProjectPaths
from src.visualization.raw_data_report import RawDataReport

def test_loading(source: str, file_path, load_function):
    """Test loading a single file using a specific loader function."""
    df = load_function(source, file_path)
    print(f"Shape: {df.shape}")
    print(df.head())

if __name__ == "__main__":
    loader = ERTLoader()
    paths = ProjectPaths(user='AQ96560') 
        
    sas_files = paths.RAW_SAS4000
    bb_geom = loader.load_geometry(paths.BB_ELECS_POS)
    dfs = loader.load_sas4000(site_id="BB", source=sas_files)

    # Resolve the final filepath entirely outside of the report class
    output_filepath = paths.VISUALIZATION_DIR / "BB_Site" / "raw_data_results.pdf"

    RawDataReport.print(
        df=dfs,
        df_pos=bb_geom,
        filepath=output_filepath,
        max_groups=15,
    )