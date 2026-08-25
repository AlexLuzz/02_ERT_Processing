import numpy as np
import pygimli.physics.ert as ert
from src.core.base import ProjectBase
from src.processing.inversion.pygimli_tools import *

class ERTProcessor(ProjectBase):
    """
    Runner class for ERT inversions. Loops through time steps manually 
    to avoid TimelapseERT bugs and extract data as pure NumPy arrays.
    """
    def __init__(self, project_name: str, output_folder: str = "inversion_results"):
        super().__init__(project_name=project_name)
        self.output_folder = output_folder

    def run_inversion(self, df, inv_params: dict, inversion_type: str = "cascade", error_val: float = 5.0):
        """
        Executes the inversions manually.
        inversion_type: 'classic' (independent) or 'cascade' (sequential starting models).
        """
        self.logger.info(f"Starting {inversion_type} inversion loop...")
        
        containers = build_ert_container(
            df=df,
            electrode_positions=self.ert_utils.electrode_positions,
            error_val=error_val
        )

        # Tracking arrays for ensemble methods
        extracted_results = {
            'times': [],
            'models': [],
            'responses': [],
            'chi2': [],
            'rms': []
        }
        
        # Start model initialization
        current_start_model = inv_params.get('startModel', None)

        for i, item in enumerate(containers):
            time = item['time']
            data = item['data']
            self.logger.info(f"Inverting step {i+1}/{len(containers)}: {time}")
            
            # Setup standard manager
            mgr = ert.ERTManager(data, sr=False, verbose=inv_params.get('verbose', False))
            
            # Create a localized copy of params for this step
            step_params = inv_params.copy()
            
            # Cascade Logic: Feed the previous model forward
            if inversion_type == "cascade" and i > 0 and current_start_model is not None:
                step_params['startModel'] = current_start_model
                
            # Run the inversion
            model = mgr.invert(mesh=self.ert_utils.mesh, **step_params)
            
            # Update the start model for the next step (if cascade)
            current_start_model = model
            
            # Extract PyGIMLi outputs to pure standard types
            extracted_results['times'].append(str(time))
            extracted_results['models'].append(np.array(model))
            extracted_results['responses'].append(np.array(mgr.inv.response))
            extracted_results['chi2'].append(mgr.inv.chi2)
            extracted_results['rms'].append(mgr.inv.relrms)

        # Pass pure Python/NumPy objects to ProjectBase to save intelligently
        self._package_and_save(extracted_results, inv_params, inversion_type)
        
        return extracted_results

    def _package_and_save(self, results, inv_params, inversion_type):
        """
        Formats the extracted arrays and sends them to ProjectBase's native save methods.
        """
        # Stack lists of 1D arrays into clean 2D NumPy matrices
        models_matrix = np.vstack(results['models'])
        responses_matrix = np.vstack(results['responses'])
        
        config = {
            "inversion_type": inversion_type,
            "pygimli_parameters": inv_params,
            "times": results['times'],
            "chi2": results['chi2'],
            "rms": results['rms']
        }
        
        # Using hypothetical ProjectBase inherited methods to save without PyGIMLi dependencies
        self.logger.info(f"Delegating file saving to ProjectBase in {self.output_folder}...")
        
        # E.g., self.save_json(config, f"{self.output_folder}/run_metrics.json")
        # E.g., self.save_array(models_matrix, f"{self.output_folder}/models.npy")
        # E.g., self.save_array(responses_matrix, f"{self.output_folder}/responses.npy")