from src.processing.core.base import ProjectBase
from src.processing.inversion import pygimli_tools


class ERTProcessor(ProjectBase):
    def __init__(self, project_name, inv_params: dict):
        super().__init__(project_name=project_name)
        self.inv_params = inv_params
        
    def run_inversion(self, df):
        self.logger.info(f"Starting inversion with params: {self.inv_params}")
        
        # Create containers statelessly
        containers = pygimli_tools.build_ert_containers(df)
        
        # PyGIMLi execution here...
        
        # Save the exact parameters used for this specific run
        self.save_json(self.inv_params, "inversion_parameters.json")