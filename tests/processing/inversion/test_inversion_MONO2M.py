from src.loaders.ert_loader import ERTLoader
from src.processing.data.filtration_tools import get_date_range_mask
from config.paths import ProjectPaths
from src.visualization.raw_tlert_report import RawTLERTReport
from src.visualization.inversion_data_report import InversionDataReport
from src.processing.inversion.ert_processor import ERTProcessor
from src.loaders.ert_loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import build_unstructured_mesh

import pandas as pd
import numpy as np

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    
    # 1. Load electrode geometry
    MONO2M_elecs = load_geometry(paths.MCM_MONO2M_ELECS_POS,
                                    params={"absolute_pos": True, 
                                            "inverse_order": False,
                                            "projection": {"type": "distance", "output_axis": "X"}})

    loader = ERTLoader(site_id="MCM_MONO2M", 
                       elec_pos=MONO2M_elecs)

    dfs = loader.load_prime(source=paths.RAW_PRIME, pattern="7001*.tab")

    report_dir = paths.OUTPUT_DIR / "MCM_MONO2M" 

    filtered_dfs = get_date_range_mask(dfs, pd.to_datetime("2026-08-01"), pd.to_datetime("2026-08-03"), return_df=True)

    # 2. Build Mesh
    mesh = build_unstructured_mesh(MONO2M_elecs, area=2, quality=33)

    # 3. Run Inversion
    print("\n--- Starting Inversion ---")
    processor = ERTProcessor(report_dir, mesh, MONO2M_elecs)
    res = processor.run_inversion(filtered_dfs, inv_params={})
    