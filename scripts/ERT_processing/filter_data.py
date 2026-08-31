from config.paths import ProjectPaths
from src.loaders.ert_loader import ERTLoader
from src.loaders.ert_loading_tools import load_geometry
from src.processing.data.data_preparator import DataPreparator
from src.visualization.single_filtrated_report import FiltratedDataReport
import pandas as pd

if __name__ == "__main__":
    paths = ProjectPaths(user='AQ96560') 
    
    # 1. Load Data
    geom = load_geometry(paths.MCM_GEO_ELECS_POS, params={"absolute_pos": True, 
                                                          'inverse_order': True,
                                                          "projection": {"type": "best_fit", "output_axis": "X"}})
    loader = ERTLoader(site_id="MCM_GEO", elec_pos=geom)
    dfs = loader.load_sas4000(source=paths.MCM_SAS4000_GEO / "MCM_GEO_DD_DDrecip.AMP")

    dfs.to_csv(paths.OUTPUT_DIR / 'raw_df.csv')
    
    single_df_raw = dfs[dfs['date_survey'] == dfs['date_survey'].iloc[0]].copy()
    
    # 2. Filter Data
    preparator = DataPreparator(memory=True)
    thresholds = {
        "Vmn (mV)": {"min": 0.1},
        "R (Ohm)": {"min": 0.01},
        "err_stk (%)": {"max": 40.0},
        "err_rec (%)": {"max": 40.0},
    }

    single_df_clean = preparator.filter_standard_survey(single_df_raw, thresholds)
    preparator.save(single_df_clean, paths.OUTPUT_DIR / "MCM_GEO" / "clean_DD_df", {})

    # 3. Report
    report_path = paths.OUTPUT_DIR / "MCM_GEO" / "Filtration_Report_DD_DDrecipAAAA.pdf"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    FiltratedDataReport.print(
        filepath=report_path,
        df_raw=single_df_raw,
        df_clean=single_df_clean,
        geom_df=geom,
        preparator=preparator
    )
    print(f"✅ Filtration report saved to {report_path.name}")