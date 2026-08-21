from pathlib import Path
from src.loaders.ert_loader import ERTLoader

def run_tests():
    loader = ERTLoader()
    
    # Define paths (Update these paths to point to your actual local files)
    data_dir = Path("DATA") # Update to match your local setup
    sas_file = data_dir / "26_BB_2303_2703_6h.AMP"
    ohmpi_file = data_dir / "measurements_20260819T180008.csv"
    prime_file = data_dir / "7001_BGS_2026-07-31_133052.tab"

    # Test SAS4000
    if sas_file.exists():
        print(f"\n--- Loading SAS4000: {sas_file.name} ---")
        df_sas = loader.load_sas4000(sas_file)
        print(f"Shape: {df_sas.shape}")
        print(df_sas[['date_survey', 'date_meas', 'A', 'B', 'M', 'N', 'R (Ohm)']].head())
    
    # Test OhmPi
    if ohmpi_file.exists():
        print(f"\n--- Loading OhmPi: {ohmpi_file.name} ---")
        df_ohmpi = loader.load_ohmpi(ohmpi_file)
        print(f"Shape: {df_ohmpi.shape}")
        print(df_ohmpi[['date_survey', 'date_meas', 'A', 'B', 'M', 'N', 'R (Ohm)']].head())

    # Test Prime
    if prime_file.exists():
        print(f"\n--- Loading Prime: {prime_file.name} ---")
        df_prime = loader.load_prime(prime_file)
        print(f"Shape: {df_prime.shape}")
        print(df_prime[['date_survey', 'A', 'B', 'M', 'N', 'R (Ohm)']].head())

if __name__ == "__main__":
    run_tests()