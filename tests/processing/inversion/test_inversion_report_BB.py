from src.loaders.ert_loader import ERTLoader
from src.processing.data.filtration_tools import get_date_range_mask
from config.paths import ProjectPaths
from src.visualization.raw_data_report import RawDataReport
from src.processing.inversion.ert_processor import ERTProcessor
from pygimli.meshtools import readGmsh

import pandas as pd
if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    loader = ERTLoader(site_id="MCM_MONO2M", 
                        elec_pos_path=paths.MCM_MONO2M_ELECS_POS,
                        elec_pos_params={
            "absolute_pos": True, 
            "inverse_order": False,
            "projection": {"type": "distance", "output_axis": "X"}
        }
                       )

    dfs = loader.load_prime(source=paths.RAW_PRIME,
                            pattern="7001*.tab")
    report_file = paths.OUTPUT_DIR / "MCM_MONO2M" 
    #RawDataReport.print(df=dfs, df_pos=loader.elec_pos, filepath=report_file, plot_every_nth_group=5)

    filtered_dfs = get_date_range_mask(dfs, pd.to_datetime("2026-08-01"), pd.to_datetime("2026-08-3"), return_df=True)

    mesh = readGmsh(paths.OUTPUT_DIR / "MCM_M2m_mesh.msh")

    res = ERTProcessor(report_file, mesh, loader.elec_pos).run_inversion(filtered_dfs, inv_params={})

    print(res)