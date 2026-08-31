from src.loaders.ert_loader import ERTLoader
from config.paths import ProjectPaths
from src.visualization.raw_tlert_report import RawTLERTReport

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    loader = ERTLoader(site_id="Berlier-Bergman", 
                       elec_pos_path=paths.BB_ELECS_POS)

    dfs = loader.load_sas4000(source= paths.RAW_SAS4000 #/ "26_BB_2303_2703_6h.AMP"
                              )

    output_filepath = paths.VISUALIZATION_DIR / "BB_Site" / "raw_data_results_filter.pdf"

    RawTLERTReport.print(
        df=dfs,
        df_pos=loader.elec_pos,
        filepath=output_filepath,
        max_groups=15,
    )