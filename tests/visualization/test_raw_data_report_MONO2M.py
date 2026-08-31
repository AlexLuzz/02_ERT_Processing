from src.loaders.ert_loader import ERTLoader
from config.paths import ProjectPaths
from src.visualization.raw_tlert_report import RawTLERTReport
from src.loaders.ert_loading_tools import load_geometry
from src.loaders.weather_loading_tools import fetch_weather_data

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    
    MONO2M_elecs = load_geometry(paths.MCM_MONO2M_ELECS_POS,
                                        params={"absolute_pos": True, 
                                                "inverse_order": False,
                                                "projection": {"type": "distance", "output_axis": "X"}})
    
    loader = ERTLoader(site_id="MCM_MONO2M", 
                        elec_pos=MONO2M_elecs)

    dfs = loader.load_prime(source=paths.RAW_PRIME, pattern="7001*.tab")

    weather_MCM =  fetch_weather_data(dfs['date_survey'].min(), dfs['date_survey'].max(), station_id=51157)

    report_dir = paths.OUTPUT_DIR / "MCM_MONO2M.pdf" 
    
    RawTLERTReport.print(
        df=dfs,
        df_elec=MONO2M_elecs,
        df_weather=weather_MCM,
        filepath=report_dir,
        #plot_every_nth_group=5,
    )