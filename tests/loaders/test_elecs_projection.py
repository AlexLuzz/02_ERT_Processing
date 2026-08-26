import matplotlib.pyplot as plt
from config.paths import ProjectPaths
from src.loaders.ert_loader import ERTLoader


def run_geometry_tests(paths: ProjectPaths, loader: ERTLoader):
    print("\n=== TESTING GEOMETRY PROJECTION ===")

    for geom_file in [paths.MCM_GEO_ELECS_POS, paths.MCM_MONO2M_ELECS_POS]:
        df_raw = loader.load_geometry(geom_file)

        df_projected = loader.load_geometry(
            geom_file,
            params={
                "projection": {
                    "enabled": True,
                    "output_axis": "X (m)",
                }
            },
        )

        fig = plt.figure(figsize=(14, 6))

        ax1 = fig.add_subplot(121, projection="3d")
        ax1.scatter(
            df_raw["X"], df_raw["Y"], df_raw["Z"],
            c="blue", s=50
        )

        for _, row in df_raw.iterrows():
            ax1.text(
                row["X"], row["Y"], row["Z"],
                str(int(row["elec_number"])),
                fontsize=8
            )

        ax1.set_title(f"{geom_file.name} - Raw")
        ax1.set_xlabel("X (m)")
        ax1.set_ylabel("Y (m)")
        ax1.set_zlabel("Z (m)")

        ax2 = fig.add_subplot(122, projection="3d")
        ax2.scatter(
            df_projected["X (m)"],
            df_projected["Y"],
            df_projected["Z"],
            c="red", s=50
        )

        for _, row in df_projected.iterrows():
            ax2.text(
                row["X (m)"], row["Y"], row["Z"],
                str(int(row["elec_number"])),
                fontsize=8
            )

        ax2.set_title(f"{geom_file.name} - Projected")
        ax2.set_xlabel("X (m)")
        ax2.set_ylabel("Y (m)")
        ax2.set_zlabel("Z (m)")

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    run_geometry_tests(
        ProjectPaths(user="alexi"),
        ERTLoader(site_id="example_site"),
    )
