import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

def add_config_text(ax, config, domain):

    data = [
        ("Simulation Name", config.project_name),
        ("Start", config.start_datetime.strftime('%Y-%m-%d %H:%M')),
        ("End", config.end_datetime.strftime('%Y-%m-%d %H:%M')),
        ("Duration", f"{config.t_end_hours:.1f} h"),
        ("Time Step", f"{config.dt:.1f} s"),
        ("Domain", f"{domain.Lx} × {domain.Ly} m"),
        ("Mesh", f"{domain.nx} × {domain.ny}"),
        ("Real time", config.get_sim_duration()),
    ]

    ax.text(0.1, 0.95, "SIMULATION CONFIGURATION",
            transform=ax.transAxes,
            fontsize=12, weight='bold', va='top')

    y = 0.88
    for k, v in data:
        ax.text(0.1, y, f"{k:<18} : {v}",
                transform=ax.transAxes,
                fontsize=11,
                family='monospace',
                va='top')
        y -= 0.06

def plot_domain(ax, domain):
    colors = {"base": "#8B4513", "GI": "#228B22", "MG20": "#C2B943"}
    ax.set_facecolor(colors.get("base", "white"))

    for name, meta in domain.region_metadata.items():
        if name in ["base"]: continue
        
        c = colors.get(name, "gray")
        if meta['type'] in ['layer', 'rectangle']:
            x0, x1 = meta['x_bounds']
            y0, y1 = meta['y_bounds']
            ax.add_patch(mpatches.Rectangle((x0, y0), x1-x0, y1-y0, color=c, label=name))
        elif meta['type'] == 'polygon':
            ax.add_patch(mpatches.Polygon(meta['vertices'], color=c, label=name))

    ax.set_xlim(0, domain.Lx)
    ax.set_ylim(0, domain.Ly)
    ax.set_aspect('equal')
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.grid(True, alpha=0.3)
    
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')

def plot_water_table(ax, t: float, bc_manager, domain):
        if not bc_manager or not domain:
            return
        
        try:
            left_wt, right_wt = bc_manager.get_water_table(t)
            
            if abs(left_wt - right_wt) < 0.01:
                ax.axhline(y=left_wt, color='blue', linestyle='--',
                          linewidth=2, label=f'Water Table ({left_wt:.1f}m)', alpha=0.8)
            else:
                x_vals = np.linspace(0, domain.Lx, 100)
                wt_vals = np.linspace(left_wt, right_wt, 100)
                ax.plot(x_vals, wt_vals, color='blue', linestyle='--',
                       linewidth=2, label=f'Water Table ({left_wt:.1f}m - {right_wt:.1f}m)', 
                       alpha=0.8)
        except Exception:
            pass

def plot_material_curves(materials_dict, axes=None):
    if axes is None:
        _, axes = plt.subplots(1, 2, figsize=(12, 4))

    hp = np.linspace(-10, 0, 500)

    for name, mat in materials_dict.items():
        h = mat.hydraulic

        if hasattr(h, "params"):
            theta = [h._theta(x) for x in hp]
            kr = [h._kr(x) for x in hp]
        else:
            theta = [h._theta(x) for x in hp]
            kr = [h._kr(x) for x in hp]

        axes[0].plot(hp, theta, label=name, lw=2)
        axes[1].plot(hp, kr, label=name, lw=2)

    axes[0].set_title("Water Content")
    axes[1].set_title("Relative Permeability")

    for ax in axes:
        ax.set_xlim(-10, 0)
        ax.grid(True, alpha=0.3)
        ax.legend()

    return axes

def plot_material_report(ax, materials_dict):
    ax.axis("off")
    for i, (name, mat) in enumerate(materials_dict.items()):
        h = mat.hydraulic
        s = mat.soil

        ax.text(
            0.02, 0.9 - i * 0.2,
            f"{name} | Ks={s.Ks:.2e} | φ={s.porosity:.3f}",
            transform=ax.transAxes,
            family="monospace"
        )

def plot_material_curves(ax_theta, ax_kr, materials_dict):
    hp = np.linspace(-10, 0, 500)

    for name, mat in materials_dict.items():
        h = mat.hydraulic
        ax_theta.plot(hp, [h._theta(x) for x in hp], label=name)
        ax_kr.plot(hp, [h._kr(x) for x in hp], label=name)

    for ax in (ax_theta, ax_kr):
        ax.set_xlim(-10, 0)
        ax.grid(True)
        ax.legend()