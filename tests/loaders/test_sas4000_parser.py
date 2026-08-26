from src.loaders.ert_loader import ERTLoader
from src.loaders.loading_tools import split_sas4000_surveys
from config.paths import ProjectPaths

def run_sas4000_split_tests(paths: ProjectPaths, loader: ERTLoader):
    print("\n=== TESTING SAS4000 SPLITTING ===")
    sas_file = paths.RAW_SAS4000 / "26_BB_2303_2703_6h.AMP"

    df_raw = loader.load_sas4000(source=sas_file)
    df_split = split_sas4000_surveys(df_raw, time_gap_hours=2.0)
    
    surveys = df_split['survey_id'].unique()
    print(f"Detected {len(surveys)} distinct surveys in single file:")
    for s_id in surveys:
        count = len(df_split[df_split['survey_id'] == s_id])
        date = df_split[df_split['survey_id'] == s_id]['date_survey'].iloc[0]
        print(f"  - {s_id} | Start: {date} | ({count} meas)")

if __name__ == "__main__":
    run_sas4000_split_tests(ProjectPaths(user='AQ96560'), ERTLoader(site_id="Berlier-Bergman", elec_pos_path=ProjectPaths(user='AQ96560').BB_ELECS_POS))