from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import safe_mesh_load
from src.processing.inversion.ert_processor import ERTProcessor
from src.loaders.ert_loader import ERTLoader

if __name__ == "__main__":
    paths = ProjectPaths(user='AQ96560', project_name='MCM_TimeLapse_August') 
    
    geom = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, params={"absolute_pos": True, "projection": {"type": "distance", "output_axis": "X"}})
    mesh = safe_mesh_load(paths.OUTPUT_DIR / 'MCM_MONO2M.bms')

    # Load a dataset spanning multiple survey dates
    loader = ERTLoader(site_id="MCM_MONO2M", elec_pos=geom)
    df_tl = loader.load_prime(source=paths.DATA_DIR / "MULTI_DATE_SURVEYS.tab")
    df_tl = df_tl[df_tl['reciprocal'] == False].copy()

    processor = ERTProcessor(output_dir=paths.ACTIVE_PROJECT_DIR, mesh=mesh, electrode_positions=geom)

    # Time-lapse parameters using a fixed 3% error rate to guarantee stability across steps
    tl_params = {
        'lam': 15,
        'zWeight': 0.2,
        'robustData': True,
        'error_param': 3  # The wrapper automatically converts this fixed int to an array of 0.03
    }
    
    # Run the cascade loop
    # We specify date_col strictly so PyGIMLi knows what time label to attach
    tl_results = processor.run_timelapse(df=df_tl, params=tl_params, date_col='date_survey')