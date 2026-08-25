import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

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
    start_date = pd.to_datetime(start_date, errors='coerce')
    end_date = pd.to_datetime(end_date, errors='coerce')

    import requests
    from io import StringIO

    def get_daily_data(station_id, year):
        url = (
            "https://climate.weather.gc.ca/climate_data/bulk_data_e.html?"
            f"format=csv&stationID={station_id}&Year={year}&Month=1&Day=1&timeframe=2"
        )
        r = requests.get(url, timeout=20)
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

    df = get_daily_range(
        station_id,
        start_date.year,
        end_date.year,
    )

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