import pandas as pd
from src.processing.inversion.ert_processor import ERTProcessor 
from config.paths import ProjectPaths
from src.loaders.ert_loader import ERTLoader

def test_single_inversion(df_clean):
    
    # Lightweight parameters for a fast test run
    test_params = {
        'lam': 20,              
        'maxIter': 5,           # Kept low for a quick test
        'robustData': False,
        'robustModel': False,
        'blockyModel': False,
        'creep': False,         # False for classic, True for cascade
        'startModel': 300,
        'zWeight': 0.75
    }
    
    print("Initializing ERTProcessor...")
    processor = ERTProcessor(
        project_name="Inversion_Test",
        inv_params=test_params
    )
    
    print("Launching inversion...")
    # This will call pygimli_tools.build_ert_containers(df) internally 
    # and execute the TimelapseERT manager
    processor.run_inversion(df_clean)
    
    print("Test completed successfully.")

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    loader = ERTLoader(site_id="Berlier-Bergman", elec_pos_path=paths.BB_ELECS_POS)

    sas_files = paths.RAW_SAS4000 / "26_BB_2303_2703_6h.AMP"

    dfs = loader.load_sas4000(site_id="Berlier-Bergman", source=sas_files)

    # Resolve the final filepath entirely outside of the report class
    output_filepath = paths.VISUALIZATION_DIR / "BB_Site" / "raw_data_results.pdf"

    test_single_inversion(dfs)