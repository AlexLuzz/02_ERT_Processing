from pathlib import Path
from datetime import datetime

class ProjectPaths:
    """Centralized, READ-ONLY path management for raw ERT data."""

    def __init__(self, user: str = 'AQ96560', project_name: str | None = None):
        self.user = user
        self.project_name = project_name

        user_home = Path(f"C:/Users/{self.user}")

        onedrive_root = user_home / 'OneDrive - ETS'

        # Hardcoded base directory
        self.base_dir = (onedrive_root 
            / 'Géophysique appliquée - GTO365 - 02 - Alexis Luzy'
            / '02_ERT_Processing'
        )

        # The Main Folders
        self.DATA_DIR = self.base_dir / 'DATA'
        self.OUTPUT_DIR = self.base_dir / 'OUTPUT'
        self.PROJECTS_DIR = self.base_dir / 'PROJECTS'

        # Ensure base structure exists
        for d in [self.DATA_DIR, self.OUTPUT_DIR, self.PROJECTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        # If project_name exists, append it. Otherwise, just use the timestamp.
        if self.project_name:
            folder_name = f"{self.project_name}"
            self.ACTIVE_PROJECT_DIR = self.PROJECTS_DIR / folder_name
            self.ACTIVE_PROJECT_DIR.mkdir(parents=True, exist_ok=True)
        else:
            self.ACTIVE_PROJECT_DIR = self.OUTPUT_DIR
            
        # ---------------------------------------------------------
        # HARDCODED RAW DATA SOURCES (READ-ONLY)
        # ---------------------------------------------------------
        
        # Time-Lapse ERT projects survey databases
        self.TLERT_BB_SAS4000 = onedrive_root / 'Géophysique appliquée - GTO365 - Berlier-Bergman Time-Lapse'
        self.TLERT_BB_OHMPI = onedrive_root / 'Géophysique appliquée - GTO365 - 03 - Ohmpi - IV à Laval'
        self.TLERT_MCM_PRIME = onedrive_root / 'Géophysique appliquée - GTO365 - TL-ERT 2026E onward'

        # TL-ERT MCM MONO2M 7001 (old command file)
        self.TLERT_MONO2M_7001 = onedrive_root / '000-Doctorat' / '13_MCM' / '03_TLERT_MONO2M_7001'
        self.TLERT_MONO2M_7002 = onedrive_root / '000-Doctorat' / '13_MCM' / '03_TLERT_MONO2M_7002'

        # Single survey ERT projects survey folders 
        self.MCM_SAS4000_GEO = onedrive_root / '000-Doctorat' / '13_MCM' / '04_ERT_MCM_2026E'

        # Site specific electrode position files
        self.BB_ELECS_POS = self.DATA_DIR / 'ELECS_POS' / 'BB_ELECS_POS.csv'
        self.MCM_MONO2M_ELECS_POS = self.DATA_DIR / 'ELECS_POS' / 'MCM_MONO2M_ELECS_POS.csv'
        self.MCM_MONO1M_ELECS_POS = self.DATA_DIR / 'ELECS_POS' / 'MCM_MONO1M_ELECS_POS.csv'
        self.MCM_MONO2M_ELECS_POS_TRUE = self.DATA_DIR / 'ELECS_POS' / 'MCM_MONO2M_ELECS_POS_TRUE.csv'
        self.MCM_MONO1M_ELECS_POS_TRUE = self.DATA_DIR / 'ELECS_POS' / 'MCM_MONO1M_ELECS_POS_TRUE.csv'
        self.MCM_GEO_ELECS_POS = self.DATA_DIR / 'ELECS_POS' / 'MCM_GEO_ELECS_POS.csv'
