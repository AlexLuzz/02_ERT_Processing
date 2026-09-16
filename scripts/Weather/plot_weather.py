from src.visualization.basic_plotting import plot_weather_data
from src.loaders.weather_loading_tools import fetch_weather_data
import pandas as pd
import matplotlib.pyplot as plt

start = pd.to_datetime("2026-08-01", errors='coerce')
end = pd.to_datetime("2026-09-15", errors='coerce')

# Station ids : 
# Berlier-Bergman : 51157
# MCM : 49390 / 30172
weather_df = fetch_weather_data(start, end, station_id=30172)

fig, ax = plt.subplots()

plot_weather_data(weather_df, start, end, ax)

plt.show()