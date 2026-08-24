from pathlib import Path
from src.loaders.loading_tools import scan_header
from config.paths import ProjectPaths

if __name__ == "__main__":
    paths = ProjectPaths(user='alexi')
    
    sas_file = paths.RAW_SAS4000 / "26_BB_2303_2703_6h.AMP"
    prime_file = paths.RAW_PRIME / "7001_BGS_2026-07-31_133052.tab"

    # Test SAS4000 (Uses ':' delimiter)
    data_start, metadata = scan_header(sas_file, data_start_markers=['No.', 'A(x)'], delimiter=':')
    print(f"--- SAS4000 Header Scan ---\nData starts at line: {data_start}")
    for key, value in metadata.items():
        print(f"{key}: {value}")

    # Test Prime 
    data_start, metadata = scan_header(prime_file, data_start_markers=['pt_line_number:', 'pt_calc_res:'], delimiter=':')
    print(f"\n--- Prime Header Scan ---\nData starts at line: {data_start}")
    for key, value in metadata.items():
        print(f"{key}: {value}")