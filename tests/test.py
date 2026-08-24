from src.loaders.ert_loader import ERTLoader
import numpy as np

a = np.array([1, 2, 3])
b = np.array([1, 4, 3])

assert np.array_equal(a, b)