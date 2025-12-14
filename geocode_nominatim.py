import pandas as pd
import requests
import geopandas as gpd
from shapely.geometry import Point
import logging
import os
from datetime import datetime
import time
import re

# Set up logging
log_dir = 'C:/Users/wsd3/OneDrive/GRoK/Logs'
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = f'{log_dir}/geocode_nominatim_{timestamp}.log'
summary_file = f'{log_dir}/geocode_nominatim_summary_{timestamp}.log'
checkpoint_file = f'{log_dir}/geocode_checkpoint_{timestamp}.csv'
failed_addresses_file = f'{log_dir}/failed_addresses_{timestamp}.csv'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_address(address):
    """Validate address format (basic check for non-empty, no invalid characters)."""
    if not isinstance(address, str) or not address.strip():
        return False
    if re.search(r'[\n\r\t;]', address):
        return False
    return True

def geocode_nominatim(address, city, state, zip_code):
    """Geocode an address using Nominatim API."""
    try:
        query = f"{address}, {city}, {state} {zip_code}, USA"
        logger.info(f"Geocoding address: {query}")
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        headers = {'User-Agent': 'GeocodingApp/1.0 (your.email@example.com)'}
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
    logger.info("Starting geocoding process with Nominatim")
    success_count = 0
    error_count = 0
    total_count = 0
    output_base = None

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
            raise ValueError(f"Missing required columns: {missing}")

        # Clean data
        df = df.dropna(subset=required_columns).reset_index(drop=True)
        df.index = df.index.astype(str)  # Ensure index is string
        df = df[df[required_columns].apply(
            lambda x: all(validate_address(x.iloc[j]) for j in range(3)) and pd.notna(x.iloc[3]), axis=1
        )]
        logger.info(f"After cleaning, {len(df)} valid addresses remain")

        # Load checkpoint if exists
        checkpoint_path = 'C:/Users/wsd3/OneDrive/GRoK/Logs/geocode_checkpoint_20250801_113509.csv'
        if os.path.exists(checkpoint_path):
            checkpoint_df = pd.read_csv(checkpoint_path)
            processed_indices = set(checkpoint_df.index)
            df = df[~df.index.isin(processed_indices)]
            logger.info(f"Resumed from checkpoint: {len(processed_indices)} addresses processed")
            success_count = checkpoint_df[['Latitude', 'Longitude']].notnull().all(axis=1).sum()
            error_count = len(checkpoint_df) - success_count
        else:
            checkpoint_df = pd.DataFrame()
            logger.info("No checkpoint found, starting fresh")

        # Geocode addresses
        logger.info("Starting geocoding")
        results = []
        failed_addresses = []
        for idx, row in df.iterrows():
            lat, lon = geocode_nominatim(
                row['Street Address'], row['City'], row['State'], row['Zip']
            )
            row_dict = row.to_dict()
            row_dict['Latitude'] = lat
            row_dict['Longitude'] = lon
            results.append(pd.Series(row_dict, name=idx))
            if lat is None or lon is None:
                failed_addresses.append(row[required_columns])
            else:
                success_count += 1
            error_count = len(df) - success_count

            # Save checkpoint every 100 addresses
            if len(results) % 100 == 0 or idx == df.index[-1]:
                checkpoint_df = pd.concat([checkpoint_df, pd.DataFrame(results)], ignore_index=False)
                checkpoint_df.to_csv(checkpoint_file, index=True)
                logger.info(f"Saved checkpoint: {checkpoint_file}")
                results = []

        # Save failed addresses
        if failed_addresses:
            pd.concat(failed_addresses, axis=1).T.to_csv(failed_addresses_file, index=False)
            logger.info(f"Saved failed addresses: {failed_addresses_file}")

        # Combine results
        result_df = checkpoint_df
        if results:
            result_df = pd.concat([result_df, pd.DataFrame(results)], ignore_index=False)

        if result_df.empty:
            logger.error("No geocoding results obtained")
            raise ValueError("No geocoding results obtained")

        # Filter out rows with no coordinates
        df_valid = result_df.dropna(subset=['Latitude', 'Longitude'])
        logger.info(f"Filtered to {len(df_valid)} valid geocoded records")

        # Create output directory
        output_dir = 'C:/Users/wsd3/OneDrive/GRoK/Projects/RAIL/Output'
        os.makedirs(output_dir, exist_ok=True)
        output_base = f'{output_dir}/geocoded_addresses_{timestamp}'

        # Create GeoDataFrame
        geometry = [Point(lon, lat) for lon, lat in zip(df_valid['Longitude'], df_valid['Latitude'])]
        gdf = gpd.GeoDataFrame(df_valid, geometry=geometry, crs="EPSG:4326")
        logger.info("Created GeoDataFrame")

        # Save outputs
        gdf.to_file(f'{output_base}.shp')
        logger.info(f"Saved shapefile: {output_base}.shp")
        df_valid.to_csv(f'{output_base}.csv', index=False)
        logger.info(f"Saved CSV: {output_base}.csv")
        gdf.to_file(f'{output_base}.json', driver='GeoJSON')
        logger.info(f"Saved GeoJSON: {output_base}.json")

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
            f"  Shapefile: {output_base if output_base else 'Not created'}\n"
            f"  CSV: {output_base + '.csv' if output_base else 'Not created'}\n"
            f"  GeoJSON: {output_base + '.json' if output_base else 'Not created'}\n"
            f"Checkpoint File: {checkpoint_file}\n"
            f"Failed Addresses: {failed_addresses_file}\n"
        )
        with open(summary_file, 'w') as f:
            f.write(summary)
        logger.info(f"Saved summary log: {summary_file}")
        logger.info("Geocoding process completed")

if __name__ == "__main__":
    main()