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

We recommend using `conda` or `mamba` to manage dependencies, as geophysical libraries rely heavily on C++ binaries.

```bash
# Create a new environment and install the libraries
conda create -n ert_env python=3.10
conda activate ert_env
conda install -c conda-forge pandas numpy scipy matplotlib pyyaml 

# In case of a bug (pygimli not avaiable as a conda package for example)
pip install pygimli gmsh pyarrow fastparquet
 
# To avoid import errors, make su
my_project/
├── .env                  # Goes in the ROOT
├── .vscode/              # Folder in the root
│   └── settings.json     # MUST be inside .vscode/
├── src/
└── main.py