import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Callable, List, Tuple, Dict
import matplotlib.dates as mdates
from matplotlib.tri import Triangulation

def format_time_axis(ax, ):
    loc = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
    
def plot_electrodes(df, colors=None, projection="xz", ax=None):
    if ax is None:
        fig, ax = plt.subplots()

    colors = colors or {}

    if projection.lower() == "xz":
        x_col, y_col = "X", "Z"
    elif projection.lower() == "xy":
        x_col, y_col = "X", "Y"
    else:
        raise ValueError("projection must be 'xz' or 'xy'")

    electrode_colors = ["black"] * len(df)

    for color, electrodes in colors.items():
        mask = df["elec_number"].isin(electrodes)
        for pos, is_match in enumerate(mask):
            if is_match:
                electrode_colors[pos] = color

    ax.scatter(
        df[x_col],
        df[y_col],
        c=electrode_colors,
        s=40,
        zorder=2
    )

    # Electrode numbers
    for _, row in df.iterrows():
        ax.annotate(
            str(row["elec_number"]),
            (row[x_col], row[y_col]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)

    return ax

def fetch_snow_data(start_date, end_date, include_temp=False):
    """
    Fetches daily snow depth data from Meteostat.

    Parameters:
        start_date (str or datetime): Start date.
        end_date (str or datetime): End date.
        include_temp (bool): Whether to include temperature data.
    Returns:
        pd.DataFrame: DataFrame containing dates and snow depth.
    """
    # Convert start_date and end_date to datetime objects
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    import requests
    from io import StringIO

    def get_daily_data(station_id, year):
        url = (
            "https://climate.weather.gc.ca/climate_data/bulk_data_e.html?"
            f"format=csv&stationID={station_id}&Year={year}&Month=1&Day=1&timeframe=2"
        )
        r = requests.get(url)
        r.raise_for_status()   # Error if station/year invalid

        df = pd.read_csv(StringIO(r.text))
        return df

    def get_daily_range(station_id, start_year, end_year):
        frames = []
        for y in range(start_year, end_year + 1):
            print(f"Fetching {y}...")
            frames.append(get_daily_data(station_id, y))
        return pd.concat(frames, ignore_index=True)

    # Montréal Trudeau – Climate Daily Station
    station_id = 51157   # NOT the METAR station (71183)

    df = get_daily_range(station_id, 2024, 2026)

    # Convert Date/Time column to datetime for proper filtering
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])

    # Fill missing values and filter by date range in one step
    date_mask = (df['Date/Time'] >= start_date) & (df['Date/Time'] <= end_date)
    filtered_df = df[date_mask]

    # Extract snow and rain data from filtered dataframe
    snow_data = filtered_df['Total Snow (cm)'].fillna(0)
    rain_data = filtered_df['Total Rain (mm)'].fillna(0)
    temp_data = filtered_df['Mean Temp (°C)'].fillna(0) if include_temp else None

    # Create final DataFrames
    snow_df = pd.DataFrame({'date': filtered_df['Date/Time'], 'snow': snow_data})
    rain_df = pd.DataFrame({'date': filtered_df['Date/Time'], 'rain': rain_data})
    temp_df = pd.DataFrame({'date': filtered_df['Date/Time'], 'temp': temp_data}) if include_temp else None

    if include_temp:
        return rain_df, snow_df, temp_df
    else:
        return rain_df, snow_df