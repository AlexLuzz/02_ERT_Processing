from src.loaders.ert_loader import ERTLoader
from src.loaders.loading_tools import split_sas4000_surveys
from config.paths import ProjectPaths

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi')
    loader = ERTLoader()
    
    sas_file = paths.RAW_SAS4000 / "26_BB_2303_2703_6h.AMP"

    print(f"\n--- 1. Loading Raw SAS4000 Data: {sas_file.name} ---")
    df_raw = loader.load_sas4000(site_id="BB", source=sas_file)
    print(f"Loaded {len(df_raw)} measurements.")
    
    print("\n--- 2. Splitting Surveys by Time Gap (>2 hours) ---")
    df_split = split_sas4000_surveys(df_raw, time_gap_hours=2.0)
    
    unique_surveys = df_split['survey_id'].unique()
    print(f"Detected {len(unique_surveys)} distinct surveys:")
    for s_id in unique_surveys:
        count = len(df_split[df_split['survey_id'] == s_id])
        print(f"  - {s_id} - {df_split[df_split['survey_id'] == s_id]['date_survey'].iloc[0]} - ({count} measurements)")