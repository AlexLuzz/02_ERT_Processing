from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection, PatchCollection
import pandas as pd
import numpy as np
import requests
from io import StringIO

def format_time_axis(ax):
    """Smart date locator with MM-dd format and 45-degree angle."""
    locator = mdates.AutoDateLocator(minticks=4, maxticks=12)
    formatter = mdates.DateFormatter('%m-%d')
    
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    
    # Rotate and align labels
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment('right')
    
def plot_electrodes(df, colors=None, projection="xz", ax=None):
    if ax is None:
        fig, ax = plt.subplots()

    colors = colors or {}
    x_col, y_col = ("X", "Z") if projection.lower() == "xz" else ("X", "Y")

    # Plot ALL background electrodes in light grey
    ax.scatter(df[x_col], df[y_col], c='lightgrey', s=10, zorder=1)

    # Plot active electrodes in their designated legend colors
    for color, electrodes in colors.items():
        mask = df["elec_number"].isin(electrodes)
        ax.scatter(df.loc[mask, x_col], df.loc[mask, y_col], c=color, s=25, zorder=2)

    # Electrode numbers (every 4th, integers only)
    for _, row in df.iterrows():
        elec_num = int(row["elec_number"])
        if elec_num % 4 == 0:
            ax.annotate(str(elec_num), (row[x_col], row[y_col]), 
                        xytext=(0, 3), textcoords="offset points", 
                        fontsize=6, ha='center', va='bottom')

    # Apply 1m padding and remove self-explanatory axes
    ax.set_xlim(df[x_col].min() - 1, df[x_col].max() + 1)
    ax.set_ylim(df[y_col].min() - 1, df[y_col].max() + 2) # +2 for label clearance
    ax.set_aspect("equal", adjustable="datalim")
    ax.axis('off') 

    return ax

def fetch_weather_data(start_date, end_date, freq='D', station_id=51157):
    """
    Fetches daily weather data from Environment Canada and resamples to desired frequency.
    
    Parameters:
        start_date (str or datetime): Start date.
        end_date (str or datetime): End date.
        freq (str): Pandas frequency string (e.g., 'D' for daily, '6h' for 6 hours).
        station_id (int): Weather station ID. 
                - For Berlier-Bergman, Laval : 51157 (YUL) 
                - For MCM, Val d'Or : 71725 (city), 71941 (airport)
    Returns:
        pd.DataFrame: Single DataFrame containing date, snow, rain, and temp.
    """
    start_date = pd.to_datetime(start_date, errors='coerce')
    end_date = pd.to_datetime(end_date, errors='coerce')

    def get_daily_data(station, year):
        url = (
            "https://climate.weather.gc.ca/climate_data/bulk_data_e.html?"
            f"format=csv&stationID={station}&Year={year}&Month=1&Day=1&timeframe=2"
        )
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return pd.read_csv(StringIO(r.text))

    # Fetch data across the required years
    frames = []
    for y in range(start_date.year, end_date.year + 1):
        print(f"Fetching {y}...")
        frames.append(get_daily_data(station_id, y))
    
    df = pd.concat(frames, ignore_index=True)
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])

    # Improved data filtering logic
    date_mask = (df['Date/Time'] >= start_date) & (df['Date/Time'] <= end_date)
    filtered_df = df.loc[date_mask].copy()

    # Rename columns for standardisation 
    filtered_df = filtered_df.rename(columns={
        'Date/Time': 'date',
        'Total Snow (cm)': 'snow',
        'Total Rain (mm)': 'rain',
        'Mean Temp (°C)': 'temp'
    })

    # Keep only target columns, handle NaNs, and set index for resampling
    final_df = filtered_df[['date', 'snow', 'rain', 'temp']].fillna(0)
    final_df.set_index('date', inplace=True)

    # Resample to the requested frequency (e.g., '6h', 'D')
    if freq:
        final_df = final_df.resample(freq).mean().fillna(0)

    return final_df.reset_index()

def plot_weather_data(weather_df, start_date, end_date, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 4))

    # --- Precipitation (Left Axis) ---
    ax.bar(weather_df['date'], weather_df['rain'], width=1.0, color='tab:blue', alpha=0.7, label='Rain (mm)')
    
    if 'snow' in weather_df.columns and weather_df['snow'].sum() > 0:
        ax.bar(weather_df['date'], weather_df['snow'], width=1.0, color='tab:grey', alpha=0.7, label='Snow (cm)')
        ax.set_ylabel('Precipitation (mm/cm)')
    else:
        ax.set_ylabel('Precipitation (mm)')
        
    ax.legend(loc="upper left")
    ax.grid(True, ls='--', alpha=0.5)

    # --- Temperature (Right Axis) ---
    ax_temp = ax.twinx()

    # Convert dates to Matplotlib's numeric date representation
    # (LineCollection cannot directly handle datetime64 + float arrays)
    dates = mdates.date2num(weather_df["date"].to_numpy())
    temps = weather_df["temp"].to_numpy()

    # Build one line segment between each pair of consecutive measurements
    points = np.column_stack([dates, temps])
    segments = np.stack([points[:-1], points[1:]], axis=1)
    
    # Color each segment according to the temperature at its starting point (<0 is blue, >=0 is orange)
    colors = np.where(temps[:-1] < 0, "deepskyblue", "orange")

    lc = LineCollection(segments, colors=colors, linewidths=1.5, zorder=3)
    ax_temp.add_collection(lc)
    ax_temp.autoscale()
    ax_temp.axhline(0, color='grey', linestyle='--', linewidth=0.8, zorder=2)
    ax_temp.set_ylabel("Temperature (°C)")

    # --- Formatting ---
    ax.set_xlim([pd.to_datetime(start_date), pd.to_datetime(end_date)])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30)
    
    # Ensure the top layer (temperature) has a transparent background
    ax_temp.patch.set_visible(False)

    return ax, ax_temp

def extract_polygons(mesh):
    """Directly builds Matplotlib polygons from a PyGIMLi mesh."""
    polygons = []
    # cell.nodes() returns nodes in CCW order, perfect for Matplotlib
    for cell in mesh.cells():
        coords = [[node.x(), node.y()] for node in cell.nodes()]
        polygons.append(Polygon(coords, closed=True))
    return polygons

def plot_array_on_mesh(polygons, array=None, ax=None, **kwargs):
    """Plot an array of values on a collection of polygons.
    Additional keyword arguments are passed to ``PatchCollection``.
    Args:
        polygons: Collection of polygons to plot.
        array: Defaults to ``None``. Values associated with each polygon. 

    Keyword Args:
        top_offset: Padding in meters added above the mesh (default: 1.0).
        cmap: Colormap name, e.g. ``"viridis"`` or ``"Spectral_r"``.
        norm: Matplotlib normalization object.
        alpha: Transparency between 0 and 1.
        edgecolor: Polygon edge color, e.g. ``"black"`` or ``"none"``.
        facecolor: Polygon face color; usually unnecessary with ``values``.
        linewidth: Width of polygon edges.
        linestyle: Style of polygon edges.
    Returns:
        ax: Matplotlib axis object.
        collection: Matplotlib PatchCollection object.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 5))

    # Pop the offset parameter before kwargs gets passed to the collection
    top_offset = kwargs.pop('top_offset', 1.0)

    collection_kwargs = {
        'cmap': 'Spectral_r',
        'alpha': 0.9,
        'edgecolor': 'none',
        **kwargs,
    }

    collection = PatchCollection(polygons, **collection_kwargs)
    if array is not None:
        collection.set_array(np.asarray(array)) 

    ax.add_collection(collection)
    
    # Autoscale to fit the mesh perfectly, then add the extracted offset to the top
    ax.autoscale(axis='both', tight=True)
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(top=ymax + top_offset)
    
    ax.set_aspect('equal')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Z (m)')
    
    return ax, collection

def plot_electrodes(df, ax, **params):
    """Plot electrodes on an existing axis."""
    show_numbers = params.pop("show_numbers", False)
    number_every = params.pop("number_every", 4)

    scatter_kwargs = {"s": 40, "color": "black", "alpha": 1.0,
        **params}

    ax.scatter(df["X"], df["Z"], **scatter_kwargs)

    if show_numbers:
        for i, (_, row) in enumerate(df.iterrows()):
            if i % number_every == 0:
                ax.annotate(
                    str(row["elec_number"]),
                    (row["X"], row["Z"]),
                    xytext=(4, 4),
                    textcoords="offset points")

    return ax