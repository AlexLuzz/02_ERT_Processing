from abc import ABC, abstractmethod
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from contextlib import contextmanager
from pathlib import Path

class ReportBase(ABC):
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        # Safely create any missing directories in the path
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.pdf = None

    def __enter__(self):
        self.pdf = PdfPages(self.filepath)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pdf.close()
        print(f"✓ Report saved: {self.filepath}")

    def create_page(self, rows=1, cols=1, height_ratios=None, width_ratios=None):
        """Creates and returns a figure and gridspec layout."""
        figsize = (8.27, 11.69) # A4 Portrait
        fig = plt.figure(figsize=figsize)

        margins = dict(left=0.1, right=0.88, top=0.94, bottom=0.07)
        gs = fig.add_gridspec(
            nrows=rows,
            ncols=cols,
            height_ratios=height_ratios,
            width_ratios=width_ratios,
            hspace=0.3,
            wspace=0.2,
            **margins
        )
        return fig, gs
    
    def save_current_page(self, fig):
        """Saves the figure to the PDF and clears it from memory."""
        self.pdf.savefig(fig)
        plt.close(fig)

    @abstractmethod
    def build(self):
        """This is where you define the sequence of pages."""
        pass