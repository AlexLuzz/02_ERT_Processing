from pathlib import Path
from src.io.loaders import ERTLoader

def test_loaders():
    loader = ERTLoader()
    
    # Define your test files here
    sas4000_file = Path(r"C:\path\to\26_BB_2303_2703_6h.AMP")
    ohmpi_file = Path(r"C:\path\to\measurements_20260819T180008.csv")
    prime_file = Path(r"C:\path\to\7001_BGS_2026-07-31_133052.tab")

    print("=== Testing SAS4000 Loader ===")
    if sas4000_file.exists():
        df_sas = loader.load_sas4000(sas4000_file)
        print(f"Shape: {df_sas.shape}")
        print(df_sas[['datetime', 'a', 'b', 'm', 'n', 'r', 'err']].head())
    else:
        print("File not found, skipping.")

    print("\n=== Testing OhmPi Loader ===")
    if ohmpi_file.exists():
        df_ohm = loader.load_ohmpi(ohmpi_file)
        print(f"Shape: {df_ohm.shape}")
        print(df_ohm[['datetime', 'a', 'b', 'm', 'n', 'r']].head())
    else:
        print("File not found, skipping.")

if __name__ == "__main__":
    test_loaders()