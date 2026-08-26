from pathlib import Path
from config.paths import ProjectPaths
from src.loaders.ert_loader import ERTLoader

def test_loading(site_id: str,file_path: Path, load_function):
    """Test loading a single file using a specific loader method."""
    print(f"\n--- Loading [{site_id}]: {file_path.name} ---")
    df = load_function(file_path)
    print(f"Shape: {df.shape}")
    print(df[['A', 'B', 'M', 'N', 'R (Ohm)', 'k (m)', 'rhoa (Ohm.m)', 'site_id', 'hardware_id']].head())
    return df

def run_ert_loader_tests(paths: ProjectPaths = None):
    """Run full loader test suite for Berlier-Bergman and MCM sites."""
    if paths is None:
        paths = ProjectPaths(user='alexi')

    # 1. Electrode position files
    bb_elec_file = paths.BB_ELECS_POS
    mcm_elec_file = paths.MCM_MONO2M_ELECS_POS

    # 2. Raw measurement files
    sas_file = paths.RAW_SAS4000 / "26_BB_2303_2703_6h.AMP"
    ohmpi_file = paths.RAW_OHMPI / "measurements_20260818T060008.csv"
    prime_file = paths.RAW_PRIME / "7001_BGS_2026-07-31_133052.tab"

    # 3. Instantiate Site-Scoped Loaders with Bound Geometries
    loader_bb = ERTLoader(site_id="Berlier-Bergman", elec_pos_path=bb_elec_file)
    loader_mcm = ERTLoader(site_id="MCM", elec_pos_path=mcm_elec_file)

    # 4. Run Loading Tests
    print("\n================== TESTING BERLIER-BERGMAN ==================")
    df_sas = test_loading("Berlier-Bergman", sas_file, loader_bb.load_sas4000)
    df_ohmpi = test_loading("Berlier-Bergman", ohmpi_file, loader_bb.load_ohmpi)

    print("\n======================= TESTING MCM =======================")
    df_prime = test_loading("MCM", prime_file, loader_mcm.load_prime)

    return {
        "BB_SAS4000": df_sas,
        "BB_OhmPi": df_ohmpi,
        "MCM_Prime": df_prime
    }

if __name__ == "__main__":
    run_ert_loader_tests()