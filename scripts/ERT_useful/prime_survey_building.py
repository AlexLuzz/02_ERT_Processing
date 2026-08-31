from config.paths import ProjectPaths
from src.loaders.ert_loading_tools import load_geometry
from pygimli.physics import ert
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 

def plot_pseudo_doi(dataContainer, array_type="schlumberger"):
    """
    Plots the pseudo-section points for ERT data.
    
    Parameters:
    - dataContainer: pyGIMLi / ERT data object
    - array_type: 'schlumberger' (or 'slm') or 'dipole-dipole' (or 'dd')
    """
    sensors = np.asarray(dataContainer.sensors())
    a, b, m, n = (np.asarray(dataContainer[k]) for k in ("a", "b", "m", "n"))

    x_a, x_b = sensors[a, 0], sensors[b, 0]
    x_m, x_n = sensors[m, 0], sensors[n, 0]

    # Centers of the current (AB) and potential (MN) pairs
    x_ab = (x_a + x_b) / 2
    x_mn = (x_m + x_n) / 2

    # X plotting position is always the midpoint of the entire array setup
    pseudo_x = (x_ab + x_mn) / 2

    # Y plotting position (pseudo-depth) depends on the array
    if array_type.lower() in ["schlumberger", "slm"]:
        # Based on the maximum current electrode spread
        pseudo_y = -np.abs(x_a - x_b) / 3
        
    elif array_type.lower() in ["dipole-dipole", "dd"]:
        # Based on the separation between the two dipoles
        # (Intersection of 45-degree lines from dipole centers)
        pseudo_y = -np.abs(x_ab - x_mn) / 2
        
    else:
        raise ValueError("array_type must be 'schlumberger' or 'dipole-dipole'")

    fig, ax = plt.subplots()
    ax.scatter(
        pseudo_x,
        pseudo_y,
        s=50, alpha=0.15,
        marker="s",
        color="black",
        edgecolors="none",
    )
    
    title_str = f"Survey pseudo-depth ({array_type.title()})"
    ax.set(xlabel="X (m)", ylabel="Pseudo-Depth (m)", title=title_str)
    fig.tight_layout()

    return fig, ax

if __name__ == "__main__":
    paths = ProjectPaths(user='AQ96560') 
    geom_df = load_geometry(paths.MCM_MONO2M_ELECS_POS_TRUE, 
                         params={"absolute_pos": True, 
                                 'inverse_order': False,
                                 "projection": {"type": "distance", "output_axis": "X"}})

    geom_df = geom_df.sort_values('elec_number')
    sensor_positions = geom_df[['X', 'Z']].values
    
    data = ert.createData(elecs=sensor_positions, schemeName='wa', inverse=False)

    paths_result = paths.OUTPUT_DIR / "test_wa.csv"

    n = len(data["a"])

    survey_df = pd.DataFrame({
    "type": ["test"] * n,
    "number": np.arange(1, n + 1),
    "a": data["a"] + 1,
    "b": data["b"] + 1,
    "m": data["m"] + 1,
    "n": data["n"] + 1,
    "zero1": [0] * n,
    "zero2": [0] * n,
    "zero3": [0] * n,
    "zero4": [0] * n,
    "zero5": [0] * n,
    "zero6": [0] * n,
    })

    survey_df.to_csv(
        paths_result,
        sep=";",
        header=False,
        index=False,
    )

    plot_pseudo_doi(data, 'slm')
    plt.show()