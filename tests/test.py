import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

print("1. Creating figure...", flush=True)
fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot([1, 2], [1, 2]) # Draw a simple line

print("2. Opening PDF...", flush=True)
with PdfPages("test_crash.pdf") as pdf:
    print("3. Executing savefig...", flush=True)
    pdf.savefig(fig)
    print("4. Success! The environment is fine.", flush=True)
    
plt.close(fig)