class AdvancedEntityHarmonizer:
    def __init__(self,
                 input_dir=r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\Input",
                 output_dir=r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\Output",
                 processed_dir=r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\Processed"):
        """
        Initialize Advanced Entity Harmonization Process
        """
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Ensure directories exist
        for dir_path in [input_dir, output_dir, processed_dir]:
            os.makedirs(dir_path, exist_ok=True)

        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_dir = processed_dir

        # Predefined entity mapping and keywords
        self.entity_mapping = {
            'ENERGY': {
                'keywords': ['VALERO', 'EXXON', 'CHEVRON', 'SHELL', 'BP'],
                'primary_name': 'ENERGY_CORPORATION'
            },
            'STEEL': {
                'keywords': [
                    'ARCELORMITTAL', 'THYSSENKRUPP', 'VOESTALPINE',
                    'SSAB', 'SEAH STEEL', 'NUCOR'
                ],
                'primary_name': 'STEEL_MANUFACTURER'
            },
            'AUTOMOTIVE': {
                'keywords': [
                    'GENERAL MOTORS', 'FORD', 'NISSAN',
                    'TOYOTA', 'HYUNDAI', 'VOLKSWAGEN'
                ],
                'primary_name': 'AUTOMOTIVE_MANUFACTURER'
            }
        }

    def clean_entity_name(self, name):
        """
        Clean and standardize entity name
        """
        if pd.isna(name):
            return np.nan

        # Convert to uppercase
        name = str(name).upper().strip()

        # Remove common suffixes and noise
        noise_patterns = [
            r'\bINC\.?', r'\bCORP\.?', r'\bCORPORATION',
            r'\bLLC\.?', r'\bLTD\.?', r'\bCO\.?',
            r'\bINTERNATIONAL', r'\bUSA', r'\bNA'
        ]

        for pattern in noise_patterns:
            name = re.sub(pattern, '', name).strip()

        return name

    def harmonize_entity(self, name):
        """
        Harmonize entity name based on predefined mapping
        """
        if pd.isna(name):
            return np.nan

        cleaned_name = self.clean_entity_name(name)

        # Check predefined entity mappings
        for category, mapping in self.entity_mapping.items():
            for keyword in mapping['keywords']:
                if keyword in cleaned_name:
                    return mapping['primary_name']

        # If no match, return cleaned name
        return cleaned_name

        def harmonize_data(self, df):
            """
            Harmonize data with advanced entity processing
            """

        # Create a copy of the DataFrame
        harmonized_df = df.copy()

        # Columns to exclude from final output (machine learning columns)
        exclude_columns = [
            col for col in df.columns
            if any(x in col for x in [
                'Website', 'Ultimate Parent', 'Trade Roles', 'Stock Tickers',
                'State/Region', 'SPCIQ ID', 'SIC Codes', 'Revenue', 'Profile',
                'Postal Code', 'Phone', 'MI Key', 'Market Capitalization',
                'Industry', 'Incorporation Year', 'Global HQ', 'Full Address',
                'Fax', 'Employees', 'Email', 'D-U-N-S', 'Domestic HQ',
                'Country', 'City', 'Address'
            ])
        ]

        # Columns to retain
        retain_columns = [
            col for col in df.columns
            if col not in exclude_columns
        ]

        # Prepare entity columns
        entity_columns = ['Shipper', 'Consignee', 'Notify Party']

        # Process each entity column
        for col in entity_columns:
            # Preserve original column with (Original Format)
            if col in df.columns:
                harmonized_df[f'{col} (Original Format)'] = df[col]

        # Create unified entity column with priority
        def create_unified_entity(row):
            # Priority order for entity identification
            priority_columns = [
                f'Shipper (Original Format)',
                f'Consignee (Original Format)',
                f'Notify Party (Original Format)'
            ]

            for col in priority_columns:
                if pd.notna(row[col]):
                    return row[col]

            return np.nan

        # Add unified entity column
        harmonized_df['Unified_Entity'] = harmonized_df.apply(create_unified_entity, axis=1)

        # Retain only specified columns
        final_columns = [
            col for col in retain_columns +
                           [f'{col} (Original Format)' for col in entity_columns] +
                           ['Unified_Entity']
        ]

        # Final dataframe with selected columns
        harmonized_df = harmonized_df[final_columns]

        return harmonized_df

    def process_harmonization(self):
        """
        Main harmonization workflow
        """
        try:
            # Generate unique timestamp for this run
            run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

            # Find input CSV
            input_file = self.find_input_csv()
            input_filename = os.path.basename(input_file)

            # Create processed and output filenames with unique timestamp
            processed_filename = f'{run_timestamp}_{input_filename}'
            processed_file_path = os.path.join(
                self.processed_dir,
                processed_filename
            )

            # Read input CSV
            df = pd.read_csv(input_file, low_memory=False)

            # Harmonize data
            harmonized_df = self.harmonize_data(df)

            # Save harmonized data with timestamp
            output_filename = f'advanced_harmonized_imports_{run_timestamp}.csv'
            output_path = os.path.join(self.output_dir, output_filename)

            # Save harmonized data
            harmonized_df.to_csv(output_path, index=False)
            self.logger.info(f"Saved harmonized data: {output_path}")

            # Move processed file
            os.rename(input_file, processed_file_path)
            self.logger.info(f"Moved processed file to: {processed_file_path}")

            # Log summary of harmonization
            self.logger.info(f"Total Records: {len(harmonized_df)}")
            self.logger.info("Columns in harmonized DataFrame:")
            self.logger.info(str(list(harmonized_df.columns)))

            # Log top unified entities
            if 'Unified_Entity' in harmonized_df.columns:
                entity_counts = harmonized_df['Unified_Entity'].value_counts().head(10)
                self.logger.info("Top Unified Entities:")
                for entity, count in entity_counts.items():
                    self.logger.info(f"{entity}: {count}")
            else:
                self.logger.warning("No 'Unified_Entity' column found in the harmonized DataFrame")

            return harmonized_df

        except Exception as e:
            self.logger.error(f"Harmonization failed: {e}")
            import traceback
            traceback.print_exc()
            return None

            def process_harmonization(self):
        """
        Main harmonization workflow
        """
        try:
            # Generate unique timestamp for this run
            run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

            # Find input CSV
            input_file = self.find_input_csv()
            input_filename = os.path.basename(input_file)

            # Create processed and output filenames with unique timestamp
            processed_filename = f'{run_timestamp}_{input_filename}'
            processed_file_path = os.path.join(
                self.processed_dir,
                processed_filename
            )

            # Read input CSV
            df = pd.read_csv(input_file, low_memory=False)

            # Harmonize data
            harmonized_df = self.harmonize_data(df)

            # Save harmonized data with timestamp
            output_filename = f'advanced_harmonized_imports_{run_timestamp}.csv'
            output_path = os.path.join(self.output_dir, output_filename)

            # Save harmonized data
            harmonized_df.to_csv(output_path, index=False)
            self.logger.info(f"Saved harmonized data: {output_path}")

            # Move processed file
            os.rename(input_file, processed_file_path)
            self.logger.info(f"Moved processed file to: {processed_file_path}")

            # Log summary of harmonization
            self.logger.info(f"Total Records: {len(harmonized_df)}")
            self.logger.info("Top Unified Entities:")
            if 'Unified Entity' in harmonized_df.columns:
                entity_counts = harmonized_df['Unified Entity'].value_counts().head(10)
                for entity, count in entity_counts.items():
                    self.logger.info(f"{entity}: {count}")
            else:
                self.logger.warning("No 'Unified Entity' column found in the harmonized DataFrame")

            return harmonized_df

        except Exception as e:
            self.logger.error(f"Harmonization failed: {e}")
            import traceback
            traceback.print_exc()
            return Noneimport
            os


import os
import sys
import pandas as pd
import numpy as np
import re
import logging
from datetime import datetime


class AdvancedEntityHarmonizer:
    def __init__(self,
                 input_dir=r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\Input",
                 output_dir=r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\Output",
                 processed_dir=r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\Processed"):
        """
        Initialize Advanced Entity Harmonization Process
        """
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Ensure directories exist
        for dir_path in [input_dir, output_dir, processed_dir]:
            os.makedirs(dir_path, exist_ok=True)

        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_dir = processed_dir

        # Predefined entity mapping and keywords
        self.entity_mapping = {
            'ENERGY': {
                'keywords': ['VALERO', 'EXXON', 'CHEVRON', 'SHELL', 'BP'],
                'primary_name': 'ENERGY_CORPORATION'
            },
            'STEEL': {
                'keywords': [
                    'ARCELORMITTAL', 'THYSSENKRUPP', 'VOESTALPINE',
                    'SSAB', 'SEAH STEEL', 'NUCOR'
                ],
                'primary_name': 'STEEL_MANUFACTURER'
            },
            'AUTOMOTIVE': {
                'keywords': [
                    'GENERAL MOTORS', 'FORD', 'NISSAN',
                    'TOYOTA', 'HYUNDAI', 'VOLKSWAGEN'
                ],
                'primary_name': 'AUTOMOTIVE_MANUFACTURER'
            }
        }

    def find_input_csv(self):
        """
        Find the most recent CSV file in input directory
        """
        csv_files = [
            os.path.join(self.input_dir, f)
            for f in os.listdir(self.input_dir)
            if f.lower().endswith('.csv')
        ]

        if not csv_files:
            raise FileNotFoundError("No CSV files found in input directory")

        return max(csv_files, key=os.path.getctime)

    def clean_entity_name(self, name):
        """
        Clean and standardize entity name
        """
        if pd.isna(name):
            return np.nan

        # Convert to uppercase
        name = str(name).upper().strip()

        # Remove common suffixes and noise
        noise_patterns = [
            r'\bINC\.?', r'\bCORP\.?', r'\bCORPORATION',
            r'\bLLC\.?', r'\bLTD\.?', r'\bCO\.?',
            r'\bINTERNATIONAL', r'\bUSA', r'\bNA'
        ]

        for pattern in noise_patterns:
            name = re.sub(pattern, '', name).strip()

        return name

    def harmonize_entity(self, name):
        """
        Harmonize entity name based on predefined mapping
        """
        if pd.isna(name):
            return np.nan

        cleaned_name = self.clean_entity_name(name)

        # Check predefined entity mappings
        for category, mapping in self.entity_mapping.items():
            for keyword in mapping['keywords']:
                if keyword in cleaned_name:
                    return mapping['primary_name']

        # If no match, return cleaned name
        return cleaned_name

    def harmonize_data(self, df):
        """
        Harmonize data with advanced entity processing
        """
        # Create a copy of the DataFrame
        harmonized_df = df.copy()

        # Columns to exclude from final output (machine learning columns)
        exclude_columns = [
            col for col in df.columns
            if any(x in col for x in [
                'Website', 'Ultimate Parent', 'Trade Roles', 'Stock Tickers',
                'State/Region', 'SPCIQ ID', 'SIC Codes', 'Revenue', 'Profile',
                'Postal Code', 'Phone', 'MI Key', 'Market Capitalization',
                'Industry', 'Incorporation Year', 'Global HQ', 'Full Address',
                'Fax', 'Employees', 'Email', 'D-U-N-S', 'Domestic HQ',
                'Country', 'City', 'Address'
            ])
        ]

        # Columns to retain
        retain_columns = [
            col for col in df.columns
            if col not in exclude_columns
        ]

        # Prepare entity columns
        entity_columns = ['Shipper', 'Consignee', 'Notify Party']

        # Process each entity column
        for col in entity_columns:
            # Preserve original column with (Original Format)
            if col in df.columns:
                harmonized_df[f'{col} (Original Format)'] = df[col]

        # Create unified entity column with priority
        def create_unified_entity(row):
            # Priority order for entity identification
            priority_columns = [
                'Shipper',
                'Consignee',
                'Notify Party'
            ]

            for col in priority_columns:
                if pd.notna(row[f'{col} (Original Format)']):
                    return row[f'{col} (Original Format)']

            return np.nan

        # Add unified entity column
        harmonized_df['Unified Entity'] = harmonized_df.apply(create_unified_entity, axis=1)

        # Retain only specified columns
        final_columns = [
            col for col in retain_columns +
                           [f'{col} (Original Format)' for col in entity_columns] +
                           ['Unified Entity']
        ]

        # Final dataframe with selected columns
        harmonized_df = harmonized_df[final_columns]

        return harmonized_df

    def process_harmonization(self):
        """
        Main harmonization workflow
        """
        try:
            # Generate unique timestamp for this run
            run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

            # Find input CSV
            input_file = self.find_input_csv()
            input_filename = os.path.basename(input_file)

            # Create processed and output filenames with unique timestamp
            processed_filename = f'{run_timestamp}_{input_filename}'
            processed_file_path = os.path.join(
                self.processed_dir,
                processed_filename
            )

            # Read input CSV
            df = pd.read_csv(input_file, low_memory=False)

            # Harmonize data
            harmonized_df = self.harmonize_data(df)

            # Save harmonized data with timestamp
            output_filename = f'advanced_harmonized_imports_{run_timestamp}.csv'
            output_path = os.path.join(self.output_dir, output_filename)

            # Save harmonized data
            harmonized_df.to_csv(output_path, index=False)
            self.logger.info(f"Saved harmonized data: {output_path}")

            # Move processed file
            os.rename(input_file, processed_file_path)
            self.logger.info(f"Moved processed file to: {processed_file_path}")

            # Log summary of harmonization
            self.logger.info(f"Total Records: {len(harmonized_df)}")
            self.logger.info("Top Unified Entities:")
            entity_counts = harmonized_df['Unified_Entity'].value_counts().head(10)
            for entity, count in entity_counts.items():
                self.logger.info(f"{entity}: {count}")

            return harmonized_df

        except Exception as e:
            self.logger.error(f"Harmonization failed: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    # Initialize harmonizer
    harmonizer = AdvancedEntityHarmonizer()

    # Run harmonization
    results = harmonizer.process_harmonization()

    if results is not None:
        print("Advanced Entity Harmonization Complete!")
        print(f"Total Harmonized Records: {len(results)}")
        print(f"Columns: {list(results.columns)}")


if __name__ == '__main__':
    main()