# Project Tree: 02_ERT_Processing

```text
├── .vscode
│   └── settings.json
├── code_diagnosis
│   ├── architecture_audit.py
│   ├── generate_architecture.py
│   ├── generate_enhanced_architecture.py
│   └── generate_tree.py
├── config
│   └── paths.py
├── scripts
│   ├── ERT
│   │   └── run_123.py
│   └── TL-ERT
├── src
│   ├── core
│   │   ├── __init__.py
│   │   └── base.py
│   ├── loaders
│   │   ├── __init__.py
│   │   ├── ert_loader.py
│   │   ├── ert_loading_tools.py
│   │   └── weather_loading_tools.py
│   ├── mesh
│   │   ├── __init__.py
│   │   ├── gmesh_tools.py
│   │   └── pygimli_mesh_tools.py
│   ├── processing
│   │   ├── data
│   │   │   ├── __init__.py
│   │   │   ├── data_preparator.py
│   │   │   ├── data_tools.py
│   │   │   └── filtration_tools.py
│   │   ├── inversion
│   │   │   ├── __init__.py
│   │   │   ├── ert_processor.py
│   │   │   └── pygimli_tools.py
│   │   └── __init__.py
│   ├── visualization
│   │   ├── basic_plotting.py
│   │   ├── inversion_data_report.py
│   │   ├── raw_tlert_report.py
│   │   ├── report_base.py
│   │   └── single_ert_report.py
│   └── __init__.py
├── tests
│   ├── loaders
│   │   ├── 00_test_all.py
│   │   ├── test_elecs_projection.py
│   │   ├── test_ert_loader.py
│   │   ├── test_header_scanner.py
│   │   ├── test_load_elecs_pos.py
│   │   ├── test_sas4000_parser.py
│   │   └── test_std_save_reload.py
│   ├── mesh
│   │   ├── test_gmsh.py
│   │   └── test_pygimli_mesh.py
│   ├── processing
│   │   ├── data
│   │   │   └── test_prepared_data_report_BB.py
│   │   └── inversion
│   │       └── test_inversion_MONO2M.py
│   ├── visualization
│   │   ├── test_inversion_report_MONO2M.py
│   │   ├── test_plot_elec_geometry.py
│   │   ├── test_raw_data_report_BB.py
│   │   └── test_raw_data_report_MONO2M.py
│   └── test.py
├── .env
├── ARCHITECTURE_AUDIT.md
├── JOURNAL.txt
├── main.py
├── PROJECT_ARCHITECTURE.md
├── PROJECT_DEEP_ARCHITECTURE.md
├── README.md
└── TODO.txt
```
