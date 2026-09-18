from pathlib import Path
import shutil

# Folder to clean
ROOT = Path(".")


def cleanup(root):
    # Delete every __pycache__ directory
    for path in root.rglob("__pycache__"):
        if path.is_dir():
            print(f"Deleting: {path}")
            shutil.rmtree(path, ignore_errors=True)

    # Delete every .vec and .vector file
    for pattern in ("*.vec", "*.vector", "negResp.bms", "negResp.vtk"):
        for path in root.rglob(pattern):
            if path.is_file():
                print(f"Deleting: {path}")
                try:
                    path.unlink()
                except OSError as e:
                    print(f"Could not delete {path}: {e}")


if __name__ == "__main__":
    cleanup(ROOT)
    print("Cleanup complete.")