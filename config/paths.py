import sys
from pathlib import Path

class ProjectPaths:
    """Centralized, READ-ONLY path management for raw ERT data."""

    def __init__(self, user: str = 'AQ96560', project_name: str | None = None):
        self.user = user
        self.project_name = project_name

        user_home = Path(f"C:/Users/{self.user}")

        # Hardcoded base directory
        self.base_dir = (
            user_home
            / 'OneDrive - ETS'
            / 'Géophysique appliquée - GTO365 - 02 - Alexis Luzy'
            / '02_ERT_Processing'
        )

        # The 4 Main Folders
        self.DATA_DIR = self.base_dir / 'DATA'
        self.OUTPUT_DIR = self.base_dir / 'OUTPUT'
        self.VISUALIZATION_DIR = self.base_dir / 'VISUALIZATION'
        self.PROJECTS_DIR = self.base_dir / 'PROJECTS'

        # Ensure base structure exists
        for folder in [self.DATA_DIR, self.OUTPUT_DIR, self.VISUALIZATION_DIR, self.PROJECTS_DIR]:
            folder.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------
        # HARDCODED RAW DATA SOURCES (READ-ONLY)
        # ---------------------------------------------------------
        onedrive_root = user_home / 'OneDrive - ETS'
        
        self.RAW_SAS4000 = onedrive_root / 'Géophysique appliquée - GTO365 - Berlier-Bergman Time-Lapse'
        self.RAW_OHMPI = onedrive_root / 'Géophysique appliquée - GTO365 - 03 - Ohmpi - IV à Laval'
        self.RAW_PRIME = onedrive_root / 'Géophysique appliquée - GTO365 - TL-ERT 2026E onward'
        self.MCM_SAS4000_GEO = onedrive_root / '000-Doctorat/13_MCM/04_Data_SAS4000_2026E'

        self.BB_ELECS_POS = self.DATA_DIR / 'ELECS_POS' / 'BB_ELECS_POS.csv'
        self.BB_ELECS_POS_TRUE = self.DATA_DIR / 'ELECS_POS' / 'BB_ELECS_POS_TRUE.csv'
        self.MCM_MONO2M_ELECS_POS = self.DATA_DIR / 'ELECS_POS' / 'MCM_MONO2M_ELECS_POS.csv'
        self.MCM_MONO1M_ELECS_POS = self.DATA_DIR / 'ELECS_POS' / 'MCM_MONO1M_ELECS_POS.csv'
        self.MCM_GEO_ELECS_POS = self.DATA_DIR / 'ELECS_POS' / 'MCM_GEO_ELECS_POS.csv'

        # If a project name is provided, route outputs to that specific project folder
        if self.project_name:
            self.PROJECT_ROOT = self.PROJECTS_DIR / self.project_name
            self.PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
        else:
            self.PROJECT_ROOT = None

    def __repr__(self) -> str:
        return f"ProjectPaths(user='{self.user}', project='{self.project_name}')"