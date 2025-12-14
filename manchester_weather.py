# Import necessary libraries
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import json

# Define API base URL and station
BASE_URL = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter'
STATION = '8770777'
DATUM = 'MSL'
UNITS = 'metric'
TIME_ZONE = 'gmt'
FORMAT = 'json'

# Define time period: last 3 years (adjust end_date to current if needed)
start_date = datetime(2022, 8, 7)
end_date = datetime(2025, 8, 7)
delta_year = timedelta(days=365)  # Approximately 1 year


# Function to fetch data in chunks (1 year per request for hourly data)
def fetch_noaa_data(product, interval=None, is_water_level=False):
    data_frames = []
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + delta_year - timedelta(days=1), end_date)
        params = {
            'begin_date': current_start.strftime('%Y%m%d'),
            'end_date': current_end.strftime('%Y%m%d'),
            'station': STATION,
            'product': product,
            'units': UNITS,
            'time_zone': TIME_ZONE,
            'format': FORMAT,
            'application': 'DataAnalysis'  # Optional identifier
        }
        if is_water_level:
            params['datum'] = DATUM
        if interval:
            params['interval'] = interval

        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            try:
                data = response.json()
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                    data_frames.append(df)
                else:
                    print(f"No data for {product} from {current_start} to {current_end}")
            except json.JSONDecodeError:
                print(f"JSON decode error for {product} from {current_start} to {current_end}")
        else:
            print(f"API request failed for {product}: {response.status_code}")

        current_start = current_end + timedelta(days=1)

    if data_frames:
        return pd.concat(data_frames, ignore_index=True)
    return pd.DataFrame()


# Fetch water level data (hourly verified)
water_df = fetch_noaa_data('hourly_height', is_water_level=True)
if not water_df.empty:
    water_df['t'] = pd.to_datetime(water_df['t'])
    water_df['v'] = pd.to_numeric(water_df['v'], errors='coerce')  # Water level in meters

# Fetch wind data (hourly)
wind_df = fetch_noaa_data('wind', interval='h')
if not wind_df.empty:
    wind_df['t'] = pd.to_datetime(wind_df['t'])
    wind_df['s'] = pd.to_numeric(wind_df['s'], errors='coerce')  # Speed in m/s
    wind_df['dr'] = pd.to_numeric(wind_df['dr'], errors='coerce')  # Direction in degrees
    wind_df['d'] = wind_df['dr'] * (np.pi / 180)  # Convert to radians for plotting

# Error handling: Check if data was retrieved
if water_df.empty or wind_df.empty:
    raise ValueError("Data retrieval failed. Check API availability or parameters.")

# Visualization: Water Level Time Series
plt.figure(figsize=(12, 6))
plt.plot(water_df['t'], water_df['v'], label='Water Level (m, MSL)')
plt.title('Water Levels at Manchester Station (8770777) - Last 3 Years')
plt.xlabel('Date')
plt.ylabel('Water Level (meters)')
plt.legend()
plt.grid(True)
plt.show()

# Visualization: Wind Speed and Direction (Polar Plot)
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, polar=True)
ax.set_theta_direction(-1)  # Clockwise
ax.set_theta_zero_location('N')  # North at top
ax.scatter(wind_df['d'], wind_df['s'], c=wind_df['s'], cmap='viridis', alpha=0.5)
ax.set_title('Wind Speed and Direction at Manchester Station - Last 3 Years')
plt.show()