# 02_ERT_Processing

This repository contains a modular Python pipeline for processing, inverting, and visualizing Time-Lapse Electrical Resistivity Tomography (TL-ERT) and hydrogeological sensor data.

## Architecture Overview
The codebase follows a strict separation of concerns to remain scalable and testable:
- **`config/`**: Global path management and environment variables.
- **`src/io/`**: Pure data loaders. Reads raw instrument files (.s4k, .csv, .tab) and returns standardized Pandas DataFrames.
- **`src/data/`**: Data fusion and homogenization.
- **`src/processing/`**: Mathematical transformations (filtering, resampling, k-factors, temperature corrections).
- **`src/mesh/`**: Mesh generation (structured and unstructured).
- **`src/inversion/`**: PyGIMLi wrappers and time-lapse solvers.
- **`src/visualization/`**: Plotting utilities and PDF report generation.

## Installation

```bash # Anaconda Prompt
# Create and activate the clean environment
conda create -n ert_env python=3.10 -y
conda activate ert_env

# Upgrade pip and install the data/utility packages
python -m pip install --upgrade pip
python -m pip install pygimli matplotlib gmsh numpy scipy pandas requests h5py

# TO check if necessary : pyarrow fastparquet pyyaml
# pip install numpy==1.26.4 # in case of conflict for pygimli

# IN CASE OF MATPLOTLIB SECRET CRASH - Separate pygimli venv with the rest
# To remove and environment
conda deactivate
conda remove -n myenv --all
 
# To avoid import errors, make su
my_project/
├── .env                  # Goes in the ROOT
├── .vscode/              # Folder in the root
│   └── settings.json     # MUST be inside .vscode/
├── src/
└── main.py