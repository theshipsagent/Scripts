import requests
import json
from datetime import datetime, timedelta

# Simple test to check NOAA API access
BASE_URL = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter'
STATION = '8770777'  # Manchester, TX

# Test with just 7 days of recent data
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

# Test water level data
params = {
    'begin_date': start_date.strftime('%Y%m%d'),
    'end_date': end_date.strftime('%Y%m%d'),
    'station': STATION,
    'product': 'hourly_height',
    'datum': 'MSL',
    'units': 'metric',
    'time_zone': 'gmt',
    'format': 'json'
}

print("Testing NOAA API for Manchester Station...")
print(f"Requesting data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

response = requests.get(BASE_URL, params=params)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if 'data' in data:
        print(f"Success! Retrieved {len(data['data'])} records")
        print("Sample data:")
        for i, record in enumerate(data['data'][:3]):
            print(f"  {record}")
            if i >= 2:
                break
    else:
        print("No data in response")
        print(response.text)
else:
    print(f"Error: {response.status_code}")
    print(response.text)