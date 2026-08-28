from src.loaders.ert_loader import ERTLoader
from src.processing.data.filtration_tools import get_date_range_mask
from config.paths import ProjectPaths
from src.visualization.raw_data_report import RawDataReport, InversionDataReport
from src.processing.inversion.ert_processor import ERTProcessor
from pygimli.meshtools import readGmsh
from src.loaders.loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import build_unstructured_mesh

import pandas as pd
import numpy as np

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    
    # 1. Load Data
    loader = ERTLoader(site_id="MCM_MONO2M", 
                       elec_pos_path=paths.MCM_MONO2M_ELECS_POS,
                       elec_pos_params={
                           "absolute_pos": True, 
                           "inverse_order": False,
                           "projection": {"type": "distance", "output_axis": "X"}
                       })

    dfs = loader.load_prime(source=paths.RAW_PRIME, pattern="7001*.tab")
    report_dir = paths.OUTPUT_DIR / "MCM_MONO2M" 
    report_dir.mkdir(parents=True, exist_ok=True)

    filtered_dfs = get_date_range_mask(dfs, pd.to_datetime("2026-08-01"), pd.to_datetime("2026-08-03"), return_df=True)

    # 2. Build Mesh
    MONO2M_geom = load_geometry(paths.MCM_MONO2M_ELECS_POS,
                                params={"absolute_pos": True, 
                                        "inverse_order": False,
                                        "projection": {"type": "distance", "output_axis": "X"}})
    
    mesh = build_unstructured_mesh(MONO2M_geom, area=2, quality=33)

    # 3. Run Inversion
    print("\n--- Starting Inversion ---")
    processor = ERTProcessor(report_dir, mesh, loader.elec_pos)
    res = processor.run_inversion(filtered_dfs, inv_params={})
    
    # 4. Format data for the Report
    print("\n--- Formatting Data for Report ---")
    # Zipping the times and models together into the exact dictionary format the report needs
    inv_data_dict = {
        time_str: model_array 
        for time_str, model_array in zip(res['times'], res['models'])
    }
    
    # 5. Generate the PDF
    report_pdf_path = report_dir / "inversion_results_test.pdf"
    print(f"Generating report at: {report_pdf_path}")
    
    InversionDataReport.print(
        mesh=mesh,
        inv_data=inv_data_dict,
        filepath=report_pdf_path
    )
    
    print("\n✅ Pipeline test complete!")