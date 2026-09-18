# Project Tree: 02_Geophy_Processing

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
│   ├── ERT_useful
│   │   ├── clean_vec_pycache.py
│   │   ├── prime_survey_building.py
│   │   └── prime_survey_building_V2.py
│   ├── MCM_GEO
│   │   ├── GEO_data_filter.py
│   │   ├── GEO_gmsh.py
│   │   ├── GEO_plot_report.py
│   │   ├── GEO_single_survey_ensemble_inv.py
│   │   └── GEO_single_survey_inv.py
│   ├── MCM_MONOS
│   │   ├── mesh_building
│   │   │   └── MONO_gmsh.py
│   │   ├── MONO1M_single_survey_inv.py
│   │   ├── MONO1M_timelapse_inv.py
│   │   ├── MONO2M_data_filter.py
│   │   ├── MONO2M_single_inv_flat_topo.py
│   │   ├── MONO2M_single_survey_inv.py
│   │   ├── MONO2M_timelapse_inv.py
│   │   ├── MONOS_rawData_TLERT_report.py
│   │   ├── plot_report.py
│   │   └── run_both.py
│   └── Weather
│       ├── find_station.py
│       └── plot_weather.py
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
│   │   ├── raw_data_report.py
│   │   ├── report_base.py
│   │   └── single_filtrated_report.py
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
│   ├── visualization
│   │   └── test_plot_elec_geometry.py
│   └── test.py
├── .env
├── ARCHITECTURE_AUDIT.md
├── JOURNAL.txt
├── main.py
├── PROJECT_ARCHITECTURE.md
├── README.md
└── TODO.txt
```
