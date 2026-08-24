import matplotlib.pyplot as plt
from config.paths import ProjectPaths
from src.loaders.ert_loader import ERTLoader

def run_geometry_tests(paths: ProjectPaths, loader: ERTLoader):
    print("\n=== TESTING GEOMETRY LOADING ===")
    geom_file = paths.BB_ELECS_POS
        
    df_std = loader.load_geometry(geom_file)
    df_abs = loader.load_geometry(geom_file, absolute_pos=True)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df_std['X'], df_std['Z'], c='blue', label='Standard Geometry', s=100, alpha=0.6)
    ax.scatter(df_abs['X'], df_abs['Z'], c='red', label='Absolute Position (Shifted)', s=80, marker='x')
    
    for _, row in df_std.iterrows():
        ax.annotate(str(int(row['elec_number'])), (row['X'], row['Z']), xytext=(8, -5), textcoords='offset points', fontsize=9)
                    
    ax.set_title(f'Electrode Array: {geom_file.name}')
    ax.set_xlabel('X (m)'); ax.set_ylabel('Z (m)')
    ax.invert_yaxis()
    ax.legend(); ax.grid(True, linestyle='--')
    plt.show()

if __name__ == "__main__":
    run_geometry_tests(ProjectPaths(user='AQ96560'), ERTLoader())