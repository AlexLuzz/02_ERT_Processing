from config.paths import ProjectPaths
from src.visualization.inversion_data_report import InversionDataReport
from src.processing.inversion.ert_processor import ERTProcessor
from src.loaders.ert_loading_tools import load_geometry
from src.mesh.pygimli_mesh_tools import safe_mesh_load

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi') 
    
    report_dir = paths.OUTPUT_DIR / "MCM_MONO2M" 

    # 4. Extract data via the new HDF5 loader
    print("\n--- Loading HDF5 Data for Report ---")
    
    # Pass an explicit Path object instead of globbing
    target_h5_file = report_dir / 'inversion_run_20260830_1443' / f"20260830_1443_results.h5"

    mesh = safe_mesh_load(report_dir / "inversion_run_20260830_1443" / "20260830_1443_paraDomain.bms")

    MONO2M_elecs = load_geometry(paths.MCM_MONO2M_ELECS_POS,
                                        params={"absolute_pos": True, 
                                                "inverse_order": False,
                                                "projection": {"type": "distance", "output_axis": "X"}})

    processor = ERTProcessor(report_dir, mesh, MONO2M_elecs)
    
    data, metadata = processor.load(target_h5_file)
    
    # 5. Generate the PDF using parallel arrays
    report_pdf_path = report_dir / "inversion_run_20260830_1443" / "inversion_results_test.pdf"
    
    InversionDataReport.print(
        mesh=mesh,
        times=data['times'], 
        models=data['models'],
        elec_pos=MONO2M_elecs,
        filepath=report_pdf_path
    )
    
    print(f"\n✅ Pipeline test complete! Report saved to {report_pdf_path.name}")