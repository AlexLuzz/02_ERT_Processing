from src.loaders.ert_loading_tools import scan_header
from config.paths import ProjectPaths

def run_header_tests(paths: ProjectPaths):

    def print_header(meta, number_of_keys=5):
        print(f"\n--- Header Scan ---")
        for key, value in list(meta.items())[:number_of_keys]:
            print(f"  {key}: {value}")

    print("\n=== TESTING HEADER SCANNERS ===")
    
    sas_file = paths.RAW_SAS4000 / "26_BB_2303_2703_6h.AMP"
    start, meta = scan_header(sas_file, data_start_markers=['No.', 'A(x)'], delimiter=':')
    print(f"\n--- SAS4000 Header Scan ---\nData starts at line: {start}")
    print_header(meta, number_of_keys=5)

    prime_file = paths.RAW_PRIME / "7001_BGS_2026-07-31_133052.tab"
    start, meta = scan_header(prime_file, data_start_markers=['pt_line_number:', 'pt_calc_res:'], delimiter=':')
    print(f"\n--- Prime Header Scan ---\nData starts at line: {start}")
    print_header(meta, number_of_keys=5)

if __name__ == "__main__":
    run_header_tests(ProjectPaths(user='AQ96560'))