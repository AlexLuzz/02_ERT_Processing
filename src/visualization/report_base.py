from abc import ABC, abstractmethod
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from pathlib import Path
from contextlib import contextmanager

class ReportBase(ABC):
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.pdf = None

    def __enter__(self):
        self.pdf = PdfPages(self.filepath)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pdf:
            self.pdf.close()
            
        if exc_type:
            print(f"\n❌ CRASH DETECTED: {exc_val}")
        else:
            print(f"\n✓ Report saved: {self.filepath}")

    @contextmanager
    def page(self, rows=1, cols=1, height_ratios=None, width_ratios=None, landscape=False):
        """Yields a gridspec page and automatically saves/closes it upon exit."""
        figsize = (11.69, 8.27) if landscape else (8.27, 11.69)
        fig = plt.figure(figsize=figsize)
        
        margins = dict(left=0.06, right=0.98, top=0.95, bottom=0.1)
        gs = fig.add_gridspec(
            nrows=rows, ncols=cols, 
            height_ratios=height_ratios, width_ratios=width_ratios,
            hspace=0.1, wspace=0.05, **margins)
        try:
            yield fig, gs
        finally:
            if self.pdf:
                self.pdf.savefig(fig)
            plt.close(fig)

    @abstractmethod
    def build(self):
        pass