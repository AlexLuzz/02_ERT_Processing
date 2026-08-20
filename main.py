# scripts/quick_inv.py
from config.paths import ProjectPaths
from src.data import DataManager
from src.processing import ERTDataFilter
from src.mesh import MeshBuilder
from src.inversion import InversionRunner
from src.visualization import ERTInversionReport

if __name__ == "__main__":
    paths = ProjectPaths(user='AQ96560', project_name="july_2026_test")

    # 1. Load & Process Raw Data
    raw_df = DataManager(paths).load()
    filter_cfg = {'voltage_threshold': 1.0, 'error_threshold': 100.0}
    clean_df = ERTDataFilter(filter_cfg).apply(raw_df)

    # 2. Save Pre-Processed Data (Persistence & Traceability)
    processed_file = paths.OUTPUT_DIR / "preprocessed_data.parquet"
    clean_df.to_parquet(processed_file)

    # 3. Load or Build Mesh
    mesh = MeshBuilder.create_structured_grid(x_range=(-2, 10), z_range=(-3, 0), cell_size=0.1)

    # 4. Invert
    inv_runner = InversionRunner(mesh=mesh, lam=20, z_weight=0.75)
    results = inv_runner.run(clean_df)
    results.save(paths.OUTPUT_DIR / "inversion_results")

    # 5. Generate Report (Decoupled!)
    ERTInversionReport.print(results, filename=paths.OUTPUT_DIR / "report.pdf")