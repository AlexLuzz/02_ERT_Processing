import matplotlib
matplotlib.use('Agg') # MUST be before any other imports

from src.loaders.ert_loader import ERTLoader
from config.paths import ProjectPaths
from src.visualization.raw_data_report import RawDataReport

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    loader = ERTLoader(site_id="MCM_mono2m", elec_pos_path=paths.MCM_MONO2M_ELECS_POS)

    prime_files = paths.RAW_PRIME #/ "26_BB_2303_2703_6h.AMP"

    dfs = loader.load_prime(site_id="MCM_mono2m", source=prime_files, pattern="7001*.tab")

    # Resolve the final filepath entirely outside of the report class
    output_filepath = paths.VISUALIZATION_DIR / "MCM_mono2m" / "raw_data_results.pdf"

    RawDataReport.print(
        df=dfs,
        df_pos=loader.elec_pos,
        filepath=output_filepath,
        max_groups=40,
    )