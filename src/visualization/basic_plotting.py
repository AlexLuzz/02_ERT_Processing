import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Callable, List, Tuple, Dict
import matplotlib.dates as mdates
from matplotlib.tri import Triangulation

def plot_timeseries(ax, df, cols=None, source_mgr=None, y_label=None, labels=None):
    # 1. Handle Time Axis (use datetime if available, otherwise hours)
    if isinstance(df.index, pd.MultiIndex):
        x_axis = df.index.get_level_values('datetime')
        is_date = True
    else:
        x_axis = df.index / 3600.0  # Convert seconds to hours
        is_date = False

    # 2. Plot selected columns
    target_cols = cols if cols else df.columns
    for i, col in enumerate(target_cols):
        if col in df.columns:
            ax.plot(x_axis, df[col], lw=2, label=labels[i] if labels else col)

    # 3. Overlay Rain
    if source_mgr is not None:
        ax_rain = ax.twinx()
        _plot_rain_bars(ax_rain, source_mgr, is_date)
        ax_rain.set_ylabel("Rain (mm/hr)")

    # Formatting
    if is_date:
        _format_time_axis(ax)
    else:
        ax.set_xlabel("Time (hours)")

    ax.set_ylabel(y_label if y_label else "Value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")

def _plot_rain_bars(ax, source_mgr, use_datetime):
    df_rain = source_mgr.data
    rain_val = df_rain['rain']if 'rain' in df_rain.columns else df_rain.iloc[:, 0]
    
    if use_datetime:
        x = [source_mgr.config.start_datetime + pd.Timedelta(seconds=s) for s in df_rain.index]
        width = source_mgr.config.dt / 86400.0 # width in days
    else:
        x = df_rain.index / 3600.0
        width = source_mgr.config.dt / 3600.0

    ax.bar(x, rain_val, width=width, align='edge', alpha=0.2, color='blue', label='Rain')

def _format_time_axis(ax, ):
    loc = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))

def plot_snapshot(ax, data, cfg, mesh=None, vmin=None, vmax=None,
                  scale="linear"):

    if hasattr(data, "function_space"):
        mesh = data.function_space().mesh()
        values = data.dat.data
    else:
        values = data
        if mesh is None:
            raise ValueError("mesh required for numpy data")

    coords = mesh.coordinates.dat.data
    triang = Triangulation(coords[:, 0], coords[:, 1])

    norm = None
    if scale == "log":
        from matplotlib.colors import LogNorm
        norm = LogNorm(vmin=vmin, vmax=vmax)

    cf = ax.tricontourf(
        triang,
        values,
        levels=cfg.contour_levels,
        cmap=cfg.colormap,
        vmin=vmin,
        vmax=vmax,
        norm=norm,
        extend='both'
    )

    ax.set_aspect("equal")
    ax.set(xlabel="x (m)", ylabel="y (m)")

    return cf

def plot_snapshot_grid(ax, df_snapshots, field_name, cfg, rows=6, cols=1):
    fig = ax.figure
    ax.remove()
    gs = fig.add_gridspec(rows, cols, hspace=0.2, wspace=0.1)
    
    # We use only the first N snapshots that fit in the grid
    times = df_snapshots.index[:rows*cols]
    axes = []
    
    # Determine global Vmin/Vmax for consistent scaling
    all_vals = []
    for t in times:
        func = df_snapshots.at[t, field_name]
        all_vals.append(func.dat.data_ro)
    vmin = np.min(all_vals)
    vmax = np.max(all_vals)

    cf = None
    for i, t in enumerate(times):
        r, c = divmod(i, cols)
        ax_sub = fig.add_subplot(gs[r, c])
        func = df_snapshots.at[t, field_name]
        
        cf = plot_snapshot(ax_sub, func, cfg, vmin=vmin, vmax=vmax)
        
        # Title with hour formatting
        ax_sub.set_title(f"t = {t/3600:.1f}h", fontsize=9)
        
        # Clean labels for inner grid
        if r != rows - 1: ax_sub.set_xlabel(""); ax_sub.set_xticklabels([])
        if c != 0: ax_sub.set_ylabel(""); ax_sub.set_yticklabels([])
        axes.append(ax_sub)

    fig.colorbar(cf, ax=axes, label=f"{cfg.label} ({cfg.units})", fraction=0.02, pad=0.04)
    
def add_probe_markers(ax, probe_positions: List[Tuple], colors: List[str] = None):
    if colors is None:
        base_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        colors = [base_colors[i % len(base_colors)] for i in range(len(probe_positions))]
    
    for i, (x, y) in enumerate(probe_positions):
        ax.plot(x, y, '*', color=colors[i % len(colors)],
                markersize=12, markeredgecolor='black', markeredgewidth=0.8)
