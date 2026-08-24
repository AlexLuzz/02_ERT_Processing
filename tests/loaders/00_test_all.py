from config.paths import ProjectPaths
from src.loaders.ert_loader import ERTLoader

# Import your functionalized tests
from tests.loaders.test_header_scanner import run_header_tests
from tests.loaders.test_ert_loader import test_loading
from tests.loaders.test_sas4000_parser import run_sas4000_split_tests
from tests.loaders.test_load_elecs_pos import run_geometry_tests
from tests.loaders.test_std_save_reload import run_save_reload_tests

if __name__ == "__main__":
    print("🚀 INITIALIZING GLOBAL IO TEST SUITE...")
    
    # Initialize dependencies once
    paths = ProjectPaths(user='AQ96560') 
    loader = ERTLoader()
    
    # Run the sequence
    run_header_tests(paths)
    test_loading(paths, loader)
    run_sas4000_split_tests(paths, loader)
    run_save_reload_tests(paths, loader)
    
    # Usually keep plotting for last so it doesn't block the terminal
    run_geometry_tests(paths, loader) 
    
    print("\n🏁 GLOBAL TEST SUITE COMPLETE.")