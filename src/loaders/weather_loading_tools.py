import pandas as pd
import requests
from io import StringIO

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
