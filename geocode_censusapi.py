import pandas as pd
import requests
import geopandas as gpd
from shapely.geometry import Point
import logging
import os
from datetime import datetime
import io
import re

# Set up logging
log_dir = 'C:/Users/wsd3/OneDrive/GRoK/Logs'
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = f'{log_dir}/geocode_census_{timestamp}.log'
summary_file = f'{log_dir}/geocode_census_summary_{timestamp}.log'
checkpoint_file = f'{log_dir}/geocode_checkpoint_{timestamp}.csv'

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
    # Remove invalid characters (e.g., newlines, excessive punctuation)
    if re.search(r'[\n\r\t;]', address):
        return False
    return True

def parse_coordinates(coord_str):
    """Parse malformed coordinate strings (e.g., '-98.256449064768,26.133887275242')."""
    try:
        if isinstance(coord_str, str) and ',' in coord_str:
            lon, lat = map(float, coord_str.split(','))
            return lat, lon
        return float(coord_str), float(coord_str)
    except (ValueError, TypeError):
        return None, None

def geocode_census_batch(df, address_col, city_col, state_col, zip_col, batch_size=1000):
    """Geocode addresses using US Census Bureau Geocoder in batches."""
    url = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
    results = []
    total_count = len(df)
    success_count = 0
    error_count = 0
    checkpoint_index = 0

    # Load checkpoint if exists
    if os.path.exists(checkpoint_file):
        checkpoint_df = pd.read_csv(checkpoint_file)
        checkpoint_index = checkpoint_df.index.max() + 1
        results.append(checkpoint_df)
        logger.info(f"Resumed from checkpoint: {checkpoint_index} addresses processed")
        success_count = checkpoint_df[['Latitude', 'Longitude']].notnull().all(axis=1).sum()
        error_count = len(checkpoint_df) - success_count

    for i in range(checkpoint_index, total_count, batch_size):
        batch = df.iloc[i:i + batch_size].copy()
        logger.info(f"Processing batch {i//batch_size + 1} ({i} to {min(i + batch_size, total_count)})")

        # Validate batch data
        batch = batch[batch[address_col].apply(validate_address) &
                      batch[city_col].apply(validate_address) &
                      batch[state_col].apply(validate_address) &
                      batch[zip_col].notna()]
        if batch.empty:
            logger.warning(f"Batch {i//batch_size + 1} is empty after validation")
            error_count += min(batch_size, total_count - i)
            continue

        # Prepare CSV for batch upload
        batch_csv = io.StringIO()
        batch.to_csv(batch_csv, columns=[address_col, city_col, state_col, zip_col],
                    header=["address", "city", "state", "zip"], index=True)
        batch_csv.seek(0)

        try:
            files = {'addressFile': ('batch.csv', batch_csv, 'text/csv')}
            params = {'benchmark': 'Public_AR_Current', 'vintage': 'Current'}
            response = requests.post(url, files=files, params=params, timeout=30)
            response.raise_for_status()

            # Parse response
            batch_results = pd.read_csv(io.StringIO(response.text),
                                      names=['id', 'address', 'status', 'quality', 'matched_address', 'lon', 'lat',
                                             'tiger_line_id', 'side', 'state_fips', 'county_fips', 'tract', 'block'],
                                      dtype={'id': str, 'address': str, 'status': str, 'quality': str,
                                             'matched_address': str, 'tiger_line_id': str, 'side': str,
                                             'state_fips': str, 'county_fips': str, 'tract': str, 'block': str},
                                      low_memory=False)

            # Handle malformed coordinates
            batch_results['lat'] = batch_results['lat'].apply(lambda x: parse_coordinates(x)[0] if pd.notna(x) else None)
            batch_results['lon'] = batch_results['lon'].apply(lambda x: parse_coordinates(x)[1] if pd.notna(x) else None)

            # Merge with original batch
            batch_results = batch_results.set_index('id').join(batch)
            batch_results['Latitude'] = batch_results['lat']
            batch_results['Longitude'] = batch_results['lon']
            results.append(batch_results)

            # Save checkpoint
            pd.concat(results, ignore_index=False).to_csv(checkpoint_file, index=True)
            logger.info(f"Saved checkpoint: {checkpoint_file}")

            batch_success = batch_results['status'].eq('Match').sum()
            batch_errors = len(batch) - batch_success
            success_count += batch_success
            error_count += batch_errors
            logger.info(f"Batch {i//batch_size + 1}: {batch_success} successes, {batch_errors} failures")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error in batch {i//batch_size + 1}: {str(e)}")
            error_count += len(batch)

        batch_csv.close()

    # Combine results
    result_df = pd.concat(results, ignore_index=False) if results else pd.DataFrame()
    return result_df, success_count, error_count

def main():
    start_time = datetime.now()
    logger.info("Starting geocoding process with US Census Geocoder")
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
        df = df[df[required_columns].apply(lambda x: all(validate_address(v) for v in x[:3]) and pd.notna(x[3]), axis=1)]
        logger.info(f"After cleaning, {len(df)} valid addresses remain")

        # Geocode addresses
        logger.info("Starting geocoding")
        result_df, success_count, error_count = geocode_census_batch(
            df, 'Street Address', 'City', 'State', 'Zip', batch_size=1000
        )

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
        )
        with open(summary_file, 'w') as f:
            f.write(summary)
        logger.info(f"Saved summary log: {summary_file}")
        logger.info("Geocoding process completed")

if __name__ == "__main__":
    main()