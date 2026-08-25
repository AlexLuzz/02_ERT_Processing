import matplotlib
matplotlib.use('Agg') # MUST be before any other imports

from src.loaders.ert_loader import ERTLoader
from config.paths import ProjectPaths
from src.visualization.raw_data_report import RawDataReport

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    loader = ERTLoader(site_id="Berlier-Bergman", elec_pos_path=paths.BB_ELECS_POS)

    sas_files = paths.RAW_SAS4000 #/ "26_BB_2303_2703_6h.AMP"

    dfs = loader.load_sas4000(site_id="Berlier-Bergman", source=sas_files)

    # Resolve the final filepath entirely outside of the report class
    output_filepath = paths.VISUALIZATION_DIR / "BB_Site" / "raw_data_results.pdf"

    RawDataReport.print(
        df=dfs,
        df_pos=loader.elec_pos,
        filepath=output_filepath,
        max_groups=15,
    )