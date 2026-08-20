import os
from pathlib import Path

class ProjectPaths:
    """Centralized path management."""
    def __init__(self, user='AQ96560', project_name=None):
        self.USER = user
        self.project_name = project_name
        
        # Flexibly handle WSL vs Windows vs Linux home directories
        base_env = os.getenv('ERT_PROJECT_BASE')
        if base_env:
            self.base_dir = Path(base_env)
        else:
            self.base_dir = Path.home() / 'OneDrive - ETS' / '02 - Alexis Luzy' / '01_Modelization'

        self.DATA_DIR = self.base_dir / 'DATA'
        self.OUTPUT_DIR = self.base_dir / 'PROJECTS' / project_name if project_name else self.base_dir / 'OUTPUT'
        
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)