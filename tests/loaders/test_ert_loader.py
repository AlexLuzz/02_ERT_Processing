from pathlib import Path
from src.loaders.ert_loader import ERTLoader
from config.paths import ProjectPaths  # Import your central map!

def test_loading(source: str, file_path: Path, load_function):
    """Test loading a single file using a specific loader function."""
    df = load_function(source, file_path)
    print(f"Shape: {df.shape}")
    print(df.head())

if __name__ == "__main__":
    # 1. Initialize your tools
    loader = ERTLoader()
    
    # Swap to 'alexi' if you are on your home computer
    paths = ProjectPaths(user='alexi') 
        
    # 2. Construct absolute paths by combining the directory from ProjectPaths with the filename
    sas_file = paths.RAW_SAS4000 / "26_BB_2303_2703_6h.AMP"
    ohmpi_file = paths.RAW_OHMPI / "measurements_20260818T060008.csv"
    prime_file = paths.RAW_PRIME / "7001_BGS_2026-07-31_133052.tab"

    # 3. Test them by passing the absolute Path object and the specific loader method
    test_loading("Berlier-Bergman", sas_file, loader.load_sas4000)
    test_loading("Berlier-Bergman", ohmpi_file, loader.load_ohmpi)
    test_loading("MCM", prime_file, loader.load_prime)