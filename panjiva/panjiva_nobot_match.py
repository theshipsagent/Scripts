#!/usr/bin/env python3
"""
Vessel Data Matching Script - OPTIMIZED VERSION
Matches vessel records between source and lookup files using efficient indexing.
Author: Generated for GRoK Projects
Version: 2.0 - Performance Optimized
"""

import pandas as pd
import numpy as np
import os
import re
import logging
from datetime import datetime, timedelta
import sys
import time
from pathlib import Path
from collections import defaultdict


class VesselMatcherOptimized:
    def __init__(self):
        # File paths
        self.source_file = r"C:\Users\wsd3\OneDrive\GRoK\Projects\Manifest\River\merged_09172025_formatted_match_step1.csv"
        self.lookup_file = r"/Output/merged_aligned_v2_0825251350.csv"
        self.dest_directory = r"C:\Users\wsd3\OneDrive\GRoK\Projects\Manifest\River"

        # Setup logging
        self.setup_logging()

        # Processing stats
        self.stats = {
            'total_source_rows': 0,
            'total_lookup_rows': 0,
            'matches_found': 0,
            'no_matches': 0,
            'errors': 0,
            'filtered_lookup_rows': 0,
            'imo_matches': 0,
            'vessel_name_matches': 0
        }

        # Timeout settings (30 minutes)
        self.timeout_seconds = 1800
        self.start_time = time.time()

        # Optimization: Create lookup indexes
        self.imo_index = {}
        self.vessel_index = defaultdict(list)

    def setup_logging(self):
        """Setup detailed logging configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.dest_directory, f"vessel_matching_log_{timestamp}.log")

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Setup file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Configure logger
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[file_handler, console_handler]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 80)
        self.logger.info("VESSEL DATA MATCHING SCRIPT STARTED (OPTIMIZED VERSION)")
        self.logger.info("=" * 80)

    def check_timeout(self):
        """Check if script has exceeded timeout limit"""
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout_seconds:
            raise TimeoutError(f"Script exceeded timeout limit of {self.timeout_seconds} seconds")

    def normalize_vessel_name(self, name):
        """Normalize vessel name for comparison (remove punctuation, lowercase)"""
        if pd.isna(name) or name == '':
            return ''
        # Convert to string, lowercase, remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', str(name).lower())
        return ' '.join(normalized.split())

    def parse_date_flexible(self, date_val):
        """Parse date with flexible format handling"""
        if pd.isna(date_val) or date_val == '':
            return None

        try:
            # If it's already a datetime
            if isinstance(date_val, pd.Timestamp):
                return date_val

            # If it's a float (Excel date serial number)
            if isinstance(date_val, (int, float)):
                # Handle Excel serial dates
                if date_val > 25569:  # Excel epoch adjustment
                    return pd.to_datetime(date_val, unit='D', origin='1900-01-01')
                else:
                    return pd.to_datetime(date_val, unit='D', origin='1900-01-01')

            # Try common date formats
            date_formats = [
                '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
                '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S', '%Y%m%d'
            ]

            for fmt in date_formats:
                try:
                    return datetime.strptime(str(date_val), fmt)
                except ValueError:
                    continue

            # Last resort - let pandas try to parse it
            return pd.to_datetime(date_val, errors='coerce')

        except Exception as e:
            self.logger.warning(f"Could not parse date '{date_val}': {e}")
            return None

    def dates_within_range(self, date1, date2, days_tolerance=4):
        """Check if two dates are within specified range"""
        if date1 is None or date2 is None:
            return False

        try:
            # Ensure both are datetime objects
            if not isinstance(date1, pd.Timestamp):
                date1 = pd.to_datetime(date1)
            if not isinstance(date2, pd.Timestamp):
                date2 = pd.to_datetime(date2)

            diff = abs((date1 - date2).days)
            return diff <= days_tolerance

        except Exception as e:
            self.logger.warning(f"Error comparing dates {date1} and {date2}: {e}")
            return False

    def load_and_validate_files(self):
        """Load and validate source and lookup files"""
        self.logger.info("Loading and validating input files...")

        try:
            # Check if files exist
            if not os.path.exists(self.source_file):
                raise FileNotFoundError(f"Source file not found: {self.source_file}")

            if not os.path.exists(self.lookup_file):
                raise FileNotFoundError(f"Lookup file not found: {self.lookup_file}")

            # Load source file
            self.logger.info(f"Loading source file: {self.source_file}")
            self.source_df = pd.read_csv(self.source_file, low_memory=False)
            self.stats['total_source_rows'] = len(self.source_df)
            self.logger.info(
                f"Source file loaded: {self.stats['total_source_rows']} rows, {len(self.source_df.columns)} columns")

            # Load lookup file
            self.logger.info(f"Loading lookup file: {self.lookup_file}")
            self.lookup_df = pd.read_csv(self.lookup_file, low_memory=False)
            self.stats['total_lookup_rows'] = len(self.lookup_df)
            self.logger.info(
                f"Lookup file loaded: {self.stats['total_lookup_rows']} rows, {len(self.lookup_df.columns)} columns")

            # Validate required columns
            required_source_cols = ['Vessel', 'Vessel IMO', 'Arrival Date']
            required_lookup_cols = ['Name', 'IMO', 'ArriveTime', 'PairID', 'Zone', 'Facility', 'Type_y', 'DepartTime']

            missing_source = [col for col in required_source_cols if col not in self.source_df.columns]
            missing_lookup = [col for col in required_lookup_cols if col not in self.lookup_df.columns]

            if missing_source:
                raise ValueError(f"Missing required columns in source file: {missing_source}")
            if missing_lookup:
                raise ValueError(f"Missing required columns in lookup file: {missing_lookup}")

            self.logger.info("File validation completed successfully")

        except Exception as e:
            self.logger.error(f"Error loading files: {e}")
            raise

    def prepare_data(self):
        """Prepare data for matching and create indexes"""
        self.logger.info("Preparing data for matching...")

        try:
            # Filter out unwanted rows from lookup file
            self.logger.info("Filtering lookup file...")
            initial_count = len(self.lookup_df)

            # Filter out rows where Type_y contains 'Pilot Station' or 'Anchorage'
            filter_condition = ~self.lookup_df['Type_y'].astype(str).str.contains(
                'Pilot Station|Anchorage', case=False, na=False
            )
            self.lookup_df = self.lookup_df[filter_condition].copy()

            filtered_count = len(self.lookup_df)
            self.stats['filtered_lookup_rows'] = initial_count - filtered_count
            self.logger.info(f"Filtered out {self.stats['filtered_lookup_rows']} rows from lookup file")
            self.logger.info(f"Remaining lookup rows: {filtered_count}")

            # Add new columns to source dataframe
            self.logger.info("Adding new columns to source file...")
            new_columns = ['PairID', 'Zone', 'Facility', 'Type', 'ArriveTime', 'DepartTime', 'NOBOT_Match']

            for col in new_columns:
                if col not in self.source_df.columns:
                    self.source_df[col] = ''

            # Convert IMO columns to strings for exact matching
            self.logger.info("Converting IMO columns to strings...")
            self.source_df['Vessel IMO'] = self.source_df['Vessel IMO'].astype(str).str.strip()
            self.lookup_df['IMO'] = self.lookup_df['IMO'].astype(str).str.strip()

            # Normalize vessel names for comparison
            self.logger.info("Normalizing vessel names...")
            self.source_df['Vessel_normalized'] = self.source_df['Vessel'].apply(self.normalize_vessel_name)
            self.lookup_df['Name_normalized'] = self.lookup_df['Name'].apply(self.normalize_vessel_name)

            # Parse dates
            self.logger.info("Parsing dates...")
            self.source_df['Arrival_Date_parsed'] = self.source_df['Arrival Date'].apply(self.parse_date_flexible)
            self.lookup_df['Arrive_Time_parsed'] = self.lookup_df['ArriveTime'].apply(self.parse_date_flexible)

            # CREATE OPTIMIZED INDEXES
            self.logger.info("Creating lookup indexes for fast matching...")
            self.create_lookup_indexes()

            self.logger.info("Data preparation completed")

        except Exception as e:
            self.logger.error(f"Error preparing data: {e}")
            raise

    def create_lookup_indexes(self):
        """Create optimized lookup indexes"""
        self.logger.info("Building IMO index...")

        # Build IMO index (IMO -> list of lookup row indices)
        for idx, row in self.lookup_df.iterrows():
            imo = row['IMO']
            if imo and imo not in ['', 'nan', 'None']:
                if imo not in self.imo_index:
                    self.imo_index[imo] = []
                self.imo_index[imo].append(idx)

        self.logger.info(f"IMO index created with {len(self.imo_index)} unique IMOs")

        # Build vessel name index (normalized name -> list of lookup row indices)
        self.logger.info("Building vessel name index...")
        for idx, row in self.lookup_df.iterrows():
            vessel_name = row['Name_normalized']
            if vessel_name and vessel_name != '':
                self.vessel_index[vessel_name].append(idx)

        self.logger.info(f"Vessel name index created with {len(self.vessel_index)} unique names")

    def find_matches_for_row(self, source_row):
        """Find matches for a single source row using indexes"""
        source_vessel = source_row['Vessel_normalized']
        source_imo = source_row['Vessel IMO']
        source_date = source_row['Arrival_Date_parsed']

        candidate_indices = set()

        # First, try IMO match (most reliable)
        if source_imo and source_imo not in ['', 'nan', 'None']:
            if source_imo in self.imo_index:
                candidate_indices.update(self.imo_index[source_imo])

        # If no IMO match or IMO is missing, try vessel name
        if not candidate_indices and source_vessel and source_vessel != '':
            if source_vessel in self.vessel_index:
                candidate_indices.update(self.vessel_index[source_vessel])

        # Check date constraints for all candidates
        best_match = None
        for lookup_idx in candidate_indices:
            lookup_row = self.lookup_df.loc[lookup_idx]
            lookup_date = lookup_row['Arrive_Time_parsed']

            if self.dates_within_range(source_date, lookup_date, 4):
                best_match = lookup_row
                break  # Take first valid match

        return best_match

    def perform_matching(self):
        """Perform the optimized matching process"""
        self.logger.info("Starting optimized matching process...")
        self.logger.info(f"Processing {len(self.source_df)} source records...")

        try:
            # Process in batches for better progress reporting
            batch_size = 1000
            total_rows = len(self.source_df)

            for batch_start in range(0, total_rows, batch_size):
                self.check_timeout()

                batch_end = min(batch_start + batch_size, total_rows)
                progress = (batch_start / total_rows) * 100

                self.logger.info(
                    f"Progress: {batch_start}/{total_rows} ({progress:.1f}%) - Processing batch {batch_start}-{batch_end}")

                # Process batch
                for idx in range(batch_start, batch_end):
                    try:
                        source_row = self.source_df.iloc[idx]

                        # Skip if essential data is missing
                        source_vessel = source_row['Vessel_normalized']
                        source_imo = source_row['Vessel IMO']

                        if not source_vessel and source_imo in ['', 'nan', 'None']:
                            self.source_df.iloc[idx, self.source_df.columns.get_loc('NOBOT_Match')] = 'Not Matched'
                            self.stats['no_matches'] += 1
                            continue

                        # Find match using indexes
                        match = self.find_matches_for_row(source_row)

                        if match is not None:
                            # Copy data from lookup to source
                            self.source_df.iloc[idx, self.source_df.columns.get_loc('PairID')] = match['PairID']
                            self.source_df.iloc[idx, self.source_df.columns.get_loc('Zone')] = match['Zone']
                            self.source_df.iloc[idx, self.source_df.columns.get_loc('Facility')] = match['Facility']
                            self.source_df.iloc[idx, self.source_df.columns.get_loc('Type')] = match['Type_y']
                            self.source_df.iloc[idx, self.source_df.columns.get_loc('ArriveTime')] = match['ArriveTime']
                            self.source_df.iloc[idx, self.source_df.columns.get_loc('DepartTime')] = match['DepartTime']
                            self.source_df.iloc[idx, self.source_df.columns.get_loc('NOBOT_Match')] = 'Matched'

                            self.stats['matches_found'] += 1

                            # Track match type
                            if source_imo and source_imo in self.imo_index:
                                self.stats['imo_matches'] += 1
                            else:
                                self.stats['vessel_name_matches'] += 1
                        else:
                            self.source_df.iloc[idx, self.source_df.columns.get_loc('NOBOT_Match')] = 'Not Matched'
                            self.stats['no_matches'] += 1

                    except Exception as e:
                        self.logger.error(f"Error processing row {idx}: {e}")
                        self.source_df.iloc[idx, self.source_df.columns.get_loc('NOBOT_Match')] = 'Error'
                        self.stats['errors'] += 1

            self.logger.info("Matching process completed")

        except Exception as e:
            self.logger.error(f"Error during matching process: {e}")
            raise

    def save_results(self):
        """Save the results to output file"""
        self.logger.info("Saving results...")

        try:
            # Remove temporary columns
            columns_to_drop = ['Vessel_normalized', 'Arrival_Date_parsed']
            self.source_df = self.source_df.drop(
                columns=[col for col in columns_to_drop if col in self.source_df.columns])

            # Generate output filename with versioning
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Check for existing versions
            version = 1.1
            base_name = f"riverdata_v{version:.1f}_{timestamp}.csv"
            output_file = os.path.join(self.dest_directory, base_name)

            # Increment version if file exists (shouldn't happen with timestamp, but just in case)
            while os.path.exists(output_file):
                version += 0.1
                base_name = f"riverdata_v{version:.1f}_{timestamp}.csv"
                output_file = os.path.join(self.dest_directory, base_name)

            # Ensure destination directory exists
            os.makedirs(self.dest_directory, exist_ok=True)

            # Save file
            self.source_df.to_csv(output_file, index=False)

            self.logger.info(f"Results saved to: {output_file}")
            self.logger.info(
                f"Output file contains {len(self.source_df)} rows and {len(self.source_df.columns)} columns")

            return output_file

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise

    def print_summary(self, output_file):
        """Print processing summary"""
        self.logger.info("=" * 80)
        self.logger.info("PROCESSING SUMMARY")
        self.logger.info("=" * 80)

        self.logger.info(f"Source file rows processed: {self.stats['total_source_rows']}")
        self.logger.info(f"Lookup file rows available: {self.stats['total_lookup_rows']}")
        self.logger.info(f"Lookup rows filtered out: {self.stats['filtered_lookup_rows']}")
        self.logger.info(f"Matches found: {self.stats['matches_found']}")
        self.logger.info(f"  - IMO-based matches: {self.stats['imo_matches']}")
        self.logger.info(f"  - Vessel name matches: {self.stats['vessel_name_matches']}")
        self.logger.info(f"No matches found: {self.stats['no_matches']}")
        self.logger.info(f"Processing errors: {self.stats['errors']}")

        if self.stats['total_source_rows'] > 0:
            match_rate = (self.stats['matches_found'] / self.stats['total_source_rows']) * 100
            self.logger.info(f"Match rate: {match_rate:.1f}%")

        self.logger.info(f"Output file: {output_file}")

        elapsed_time = time.time() - self.start_time
        self.logger.info(f"Total processing time: {elapsed_time:.1f} seconds")

        self.logger.info("=" * 80)
        self.logger.info("SCRIPT COMPLETED SUCCESSFULLY")
        self.logger.info("=" * 80)

    def run(self):
        """Main execution method"""
        try:
            self.load_and_validate_files()
            self.prepare_data()
            self.perform_matching()
            output_file = self.save_results()
            self.print_summary(output_file)

        except TimeoutError as e:
            self.logger.error(f"Script timeout: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Script failed with error: {e}")
            sys.exit(1)


def main():
    """Main function"""
    try:
        matcher = VesselMatcherOptimized()
        matcher.run()
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()