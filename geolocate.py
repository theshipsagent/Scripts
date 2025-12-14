import pandas as pd
import requests
import geopandas as gpd
from shapely.geometry import Point
import time
import logging
import os
from datetime import datetime

# Set up logging
log_dir = 'C:/Users/wsd3/OneDrive/GRoK/Logs'
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = f'{log_dir}/geocode_{timestamp}.log'
summary_file = f'{log_dir}/geocode_summary_{timestamp}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def geocode_nominatim(address, city, state, zip_code):
    """Geocode an address using Nominatim API."""
    try:
        query = f"{address}, {city}, {state} {zip_code}, USA"
        logger.info(f"Geocoding address: {query}")
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        headers = {'User-Agent': 'GeocodingApp/1.0 (wsd3@outlook.com)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            lat, lon = float(data[0]['lat']), float(data[0]['lon'])
            logger.info(f"Success: {query} -> ({lat}, {lon})")
            return lat, lon
        else:
            logger.warning(f"No results for {query}")
            return None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error geocoding {query}: {str(e)}")
        return None, None
    finally:
        time.sleep(1)  # Respect Nominatim's rate limit

def main():
    start_time = datetime.now()
    logger.info("Starting geocoding process")
    success_count = 0
    error_count = 0
    total_count = 0

    try:
        # Read CSV file
        input_csv = 'C:/Users/wsd3/OneDrive/GRoK/Projects/RAIL/SCRS/harmonized_output.csv'
        logger.info(f"Reading input CSV: {input_csv}")
        df = pd.read_csv(input_csv)
        total_count = len(df)
        logger.info(f"Loaded {total_count} addresses from CSV")

        # Verify required columns
        required_columns = ['Street Address', 'City', 'State', 'Zip']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            logger.error(f"Missing required columns: {missing}")
            raise ValueError(f"CSV missing required columns: {missing}")

        # Geocode addresses
        logger.info("Starting geocoding")
        coords = df.apply(
            lambda row: geocode_nominatim(
                row['Street Address'], row['City'], row['State'], row['Zip']
            ),
            axis=1
        )
        df['Latitude'], df['Longitude'] = zip(*coords)

        # Count successes and errors
        success_count = df[['Latitude', 'Longitude']].notnull().all(axis=1).sum()
        error_count = total_count - success_count
        logger.info(f"Geocoding complete: {success_count} successes, {error_count} failures")

        # Filter out rows with no coordinates
        df_valid = df.dropna(subset=['Latitude', 'Longitude'])
        logger.info(f"Filtered to {len(df_valid)} valid geocoded records")

        # Create output directory
        output_dir = 'C:/Users/wsd3/OneDrive/GRoK/Projects/RAIL/Output'
        os.makedirs(output_dir, exist_ok=True)

        # Create GeoDataFrame
        geometry = [Point(lon, lat) for lon, lat in zip(df_valid['Longitude'], df_valid['Latitude'])]
        gdf = gpd.GeoDataFrame(df_valid, geometry=geometry, crs="EPSG:4326")
        logger.info("Created GeoDataFrame")

        # Save outputs
        output_base = f'{output_dir}/geocoded_addresses_{timestamp}'
        # Shapefile
        gdf.to_file(f'{output_base}.shp')
        logger.info(f"Saved shapefile: {output_base}.shp")
        # CSV
        df_valid.to_csv(f'{output_base}.csv', index=False)
        logger.info(f"Saved CSV: {output_base}.csv")
        # JSON
        gdf.to_file(f'{output_base}.json', driver='GeoJSON')
        logger.info(f"Saved JSON: {output_base}.json")

    except Exception as e:
        logger.error(f"Fatal error in main process: {str(e)}")
        raise

    finally:
        # Write summary log
        end_time = datetime.now()
        duration = end_time - start_time
        summary = (
            f"Geocoding Summary\n"
            f"Start Time: {start_time}\n"
            f"End Time: {end_time}\n"
            f"Duration: {duration}\n"
            f"Total Addresses: {total_count}\n"
            f"Successful Geocodes: {success_count}\n"
            f"Failed Geocodes: {error_count}\n"
            f"Output Files:\n"
            f"  Shapefile: {output_base}.shp\n"
            f"  CSV: {output_base}.csv\n"
            f"  JSON: {output_base}.json\n"
        )
        with open(summary_file, 'w') as f:
            f.write(summary)
        logger.info(f"Saved summary log: {summary_file}")
        logger.info("Geocoding process completed")

if __name__ == "__main__":
    main()