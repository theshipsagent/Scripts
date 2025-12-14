#!/usr/bin/env python3
"""
Enhanced Entity Normalization Script - Windows Explorer Version
Implements improved normalization logic based on analysis findings.
Transforms Shipper_WSD, Consignee_WSD, and Notify_WSD columns.
Author: Generated for GRoK Projects
Version: 1.0 - Enhanced Logic
"""

import pandas as pd
import numpy as np
import os
import re
import logging
from datetime import datetime
import sys
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


class EnhancedEntityNormalizer:
    def __init__(self):
        self.setup_logging()

        # File paths (will be set via file dialog)
        self.source_file = None
        self.dest_directory = None

        # Processing stats
        self.stats = {
            'total_rows': 0,
            'shipper_wsd_processed': 0,
            'consignee_wsd_processed': 0,
            'notify_wsd_processed': 0,
            'shipper_wsd_changed': 0,
            'consignee_wsd_changed': 0,
            'notify_wsd_changed': 0,
            'errors': 0
        }

        # Start time
        self.start_time = time.time()

        # Setup enhanced normalization patterns
        self.setup_enhanced_patterns()

    def setup_logging(self):
        """Setup detailed logging configuration"""
        # Create logs directory in current working directory
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"enhanced_normalization_log_{timestamp}.log")

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
        self.logger.info("ENHANCED ENTITY NORMALIZATION SCRIPT STARTED")
        self.logger.info("=" * 80)

    def setup_enhanced_patterns(self):
        """Setup enhanced normalization patterns based on analysis"""

        # Enhanced business suffixes (more comprehensive)
        self.business_suffixes = [
            r'\b(LLC|L\.L\.C\.?)\b',
            r'\b(INC|INCORPORATED?)\b',
            r'\b(CORP|CORPORATION)\b',
            r'\b(LTD|LIMITED)\b',
            r'\b(CO|COMPANY)\b',
            r'\b(LP|L\.P\.?)\b',
            r'\b(LLP|L\.L\.P\.?)\b',
            r'\b(PLLC|P\.L\.L\.C\.?)\b',
            r'\b(SA|S\.A\.?)\b',
            r'\b(SRL|S\.R\.L\.?)\b',
            r'\b(GMBH|G\.M\.B\.H\.?)\b',
            r'\b(PVT|PRIVATE)\b',
            r'\b(PUBLIC)\b',
            r'\b(HOLDINGS?)\b',
            r'\b(ENTERPRISES?)\b'
        ]

        # Address indicators for notify party cleanup
        self.address_indicators = [
            r'\b\d{3,}\s+[A-Z][A-Z\s]+\b',  # Street numbers + names
            r'\b(STREET|ST|AVENUE|AVE|ROAD|RD|BOULEVARD|BLVD|LANE|LN|DRIVE|DR)\b',
            r'\b(COURT|CT|PLACE|PL|SUITE|STE|UNIT|FLOOR|FL|BUILDING|BLDG)\b',
            r'\b(NORTH|SOUTH|EAST|WEST|N|S|E|W)\s+(STREET|ST|AVENUE|AVE)\b',
            r'\b(PO\s+BOX|P\.O\.\s+BOX|POBOX)\b',
            r'\b(APT|APARTMENT)\s*\d+\b',
            r'\b\d{5}(-\d{4})?\b',  # ZIP codes
            r'\b[A-Z]{2}\s+\d{5}\b',  # State + ZIP
            r'\b(SUITE|STE)\s+[A-Z0-9#]+\b'
        ]

        # Geographic terms to remove when standardizing subsidiaries
        self.geographic_terms = [
            r'\b(AMERICA|USA|US|UNITED STATES)\b',
            r'\b(INTERNATIONAL|INTL)\b',
            r'\b(EUROPE|ASIA|PACIFIC)\b',
            r'\b(NORTH|SOUTH|EAST|WEST)\b'
        ]

        # Common company standardizations (based on analysis findings)
        self.company_standardizations = {
            # POSCO variations - all should normalize to POSCO
            'POSCO INTERNATIONAL AMERICA': 'POSCO',
            'POSCOINTERNATIONAL AMERICA': 'POSCO',
            'POSCO AMERICA': 'POSCO',
            'POSCO VIETNAM': 'POSCO',
            'POSCO YAMATO VINA': 'POSCO',

            # Other common variations found in analysis
            'CHART ENERGY CHEMICALS': 'CHART INDUSTRIES',
            'CALUCEM': 'CALUCEM',
            'AMERICAN SUGAR REFINING': 'ASR GROUP',
            'MARINE MECHANICS USA': 'MARINE MECHANICS',
            'NORTON LILLY INTERNATIONAL': 'NORTON LILLY'
        }

        # Contact info patterns to remove
        self.contact_patterns = [
            r'\([0-9]{3}\)[0-9\-\s]+',  # Phone numbers
            r'[0-9]{3}-[0-9]{3}-[0-9]{4}',  # Phone numbers
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',  # Email
            r'/\s*\([0-9]{3}\)',  # Phone with slash
        ]

        # Compile patterns
        self.suffix_pattern = '|'.join(self.business_suffixes)
        self.address_pattern = '|'.join(self.address_indicators)
        self.geographic_pattern = '|'.join(self.geographic_terms)
        self.contact_pattern = '|'.join(self.contact_patterns)

    def select_files(self):
        """Use Windows Explorer to select source file"""
        print("🔍 STEP 1: Opening file selection dialog...")
        self.logger.info("Opening file selection dialog...")

        # Create root window and hide it
        root = tk.Tk()
        root.withdraw()

        try:
            print("📁 Please select your CSV file in the dialog...")

            # Select source file
            source_file = filedialog.askopenfilename(
                title="Select source CSV file to normalize",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ],
                initialdir=os.getcwd()
            )

            if not source_file:
                print("❌ No file selected. Exiting.")
                messagebox.showwarning("Warning", "No file selected. Exiting.")
                return False

            self.source_file = source_file
            self.dest_directory = os.path.dirname(source_file)

            print(f"✅ Selected file: {os.path.basename(self.source_file)}")
            print(f"📂 Output directory: {self.dest_directory}")
            self.logger.info(f"Selected file: {self.source_file}")
            self.logger.info(f"Output directory: {self.dest_directory}")

            return True

        except Exception as e:
            print(f"❌ Error in file selection: {e}")
            self.logger.error(f"Error in file selection: {e}")
            messagebox.showerror("Error", f"File selection failed: {e}")
            return False
        finally:
            root.destroy()

    def extract_company_from_address(self, address_block):
        """Extract company name from address block (for notify parties) - FAIL FAST"""
        if pd.isna(address_block) or address_block == '' or address_block == 'null':
            return ''

        # NO TRY-CATCH - LET ERRORS BUBBLE UP IMMEDIATELY

        # Convert to string
        text = str(address_block).strip()

        # Split by newlines and take first line (usually company name)
        lines = text.split('\n')
        company_line = lines[0].strip()

        # Remove contact information
        company_line = re.sub(self.contact_pattern, '', company_line, flags=re.IGNORECASE)

        # Remove address indicators from the company line
        company_line = re.sub(self.address_pattern, '', company_line, flags=re.IGNORECASE)

        # Clean up extra spaces
        company_line = ' '.join(company_line.split())

        return company_line

    def enhanced_normalize_entity(self, entity_name, entity_type='standard'):
        """
        Enhanced entity normalization with IMMEDIATE ERROR STOPPING
        """
        if pd.isna(entity_name) or entity_name == '' or entity_name == 'null':
            return ''

        # NO TRY-CATCH - LET ERRORS BUBBLE UP IMMEDIATELY
        # Start with string conversion
        name = str(entity_name).strip()
        original_name = name

        # Special handling for notify parties (extract from address first)
        if entity_type == 'notify':
            name = self.extract_company_from_address(name)
            if not name:
                return ''

        # Convert to uppercase for consistency
        name = name.upper()

        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name)

        # Apply company standardizations (POSCO variations, etc.)
        for variation, standard in self.company_standardizations.items():
            if variation in name:
                name = name.replace(variation, standard)
                break

        # Remove business suffixes
        name = re.sub(f'({self.suffix_pattern})\\b', '', name, flags=re.IGNORECASE).strip()

        # Remove geographic terms for subsidiaries (but keep for unique identification)
        # Only remove if the company name is still meaningful after removal
        temp_name = re.sub(f'({self.geographic_pattern})\\b', '', name, flags=re.IGNORECASE).strip()
        if len(temp_name) > 3:  # Only if result is meaningful
            name = temp_name

        # Remove trailing punctuation
        name = re.sub(r'[,.\-_\|;]+

    def load_and_validate_file(self):
        """Load and validate the source file"""
        print("\n📊 STEP 2: Loading and validating file...")
        self.logger.info("Loading and validating source file...")

        try:
            print(f"📥 Loading: {os.path.basename(self.source_file)}")

            # Load source file
            self.df = pd.read_csv(self.source_file, low_memory=False)
            self.stats['total_rows'] = len(self.df)

            print(f"✅ File loaded: {self.stats['total_rows']:,} rows, {len(self.df.columns)} columns")
            self.logger.info(f"File loaded: {self.stats['total_rows']} rows, {len(self.df.columns)} columns")

            # Check for required WSD columns
            wsd_columns = []
            if 'Shipper_WSD' in self.df.columns:
                wsd_columns.append('Shipper_WSD')
            if 'Consignee_WSD' in self.df.columns:
                wsd_columns.append('Consignee_WSD')
            if 'Notify_WSD' in self.df.columns:
                wsd_columns.append('Notify_WSD')

            if not wsd_columns:
                print("❌ ERROR: No WSD columns found!")
                raise ValueError("No WSD columns found. Expected: Shipper_WSD, Consignee_WSD, or Notify_WSD")

            print(f"🎯 Found WSD columns: {', '.join(wsd_columns)}")
            self.logger.info(f"Found WSD columns: {wsd_columns}")
            return True

        except Exception as e:
            print(f"❌ Error loading file: {e}")
            self.logger.error(f"Error loading file: {e}")
            return False

    def normalize_wsd_columns(self):
        """Normalize all WSD columns with FAIL-FAST error handling"""
        print("\n🔧 STEP 3: Starting enhanced normalization...")
        print("⚠️  FAIL-FAST MODE: Will stop immediately on any error!")
        print("This may take a few minutes for large files...")
        self.logger.info("Starting enhanced normalization of WSD columns...")

        # NO TRY-CATCH BLOCK - LET ERRORS STOP THE SCRIPT IMMEDIATELY

        # Process each WSD column if it exists
        wsd_columns = [
            ('Shipper_WSD', 'standard'),
            ('Consignee_WSD', 'standard'),
            ('Notify_WSD', 'notify')  # Special handling for notify parties
        ]

        for col_name, entity_type in wsd_columns:
            if col_name not in self.df.columns:
                print(f"⏭️  Column '{col_name}' not found, skipping...")
                self.logger.info(f"Column '{col_name}' not found, skipping...")
                continue

            print(f"\n🔄 Processing '{col_name}' ({entity_type} logic)...")
            self.logger.info(f"Processing column '{col_name}' with {entity_type} logic...")

            # Process in batches for progress reporting
            batch_size = 1000
            total_rows = len(self.df)
            changes_made = 0
            processed = 0

            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
                progress = (batch_start / total_rows) * 100

                # Print progress every batch
                print(f"   📈 Progress: {batch_start:,}/{total_rows:,} ({progress:.1f}%)")
                self.logger.info(f"  Progress: {batch_start}/{total_rows} ({progress:.1f}%)")

                # Process batch - NO ERROR HANDLING, LET ERRORS BUBBLE UP
                for idx in range(batch_start, batch_end):
                    print(f"   🔍 Processing row {idx + 1}...")  # Show every row for debugging

                    original_value = self.df.iloc[idx][col_name]
                    print(f"   📝 Original value: '{original_value}'")

                    # THIS WILL STOP IMMEDIATELY IF THERE'S AN ERROR
                    normalized_value = self.enhanced_normalize_entity(original_value, entity_type)
                    print(f"   ✅ Normalized to: '{normalized_value}'")

                    # Only update if changed
                    if original_value != normalized_value:
                        self.df.iloc[idx, self.df.columns.get_loc(col_name)] = normalized_value
                        changes_made += 1
                        print(f"   🔄 Change made!")

                    processed += 1

            # Update stats
            if col_name == 'Shipper_WSD':
                self.stats['shipper_wsd_processed'] = processed
                self.stats['shipper_wsd_changed'] = changes_made
            elif col_name == 'Consignee_WSD':
                self.stats['consignee_wsd_processed'] = processed
                self.stats['consignee_wsd_changed'] = changes_made
            elif col_name == 'Notify_WSD':
                self.stats['notify_wsd_processed'] = processed
                self.stats['notify_wsd_changed'] = changes_made

            print(f"   ✅ '{col_name}' completed: {changes_made:,} changes out of {processed:,} records")
            self.logger.info(f"'{col_name}' completed: {changes_made} changes made out of {processed} processed")

        print("\n🎉 All WSD column normalization completed!")
        self.logger.info("All WSD column normalization completed")
        return True

    def save_results(self):
        """Save results with versioning"""
        print("\n💾 STEP 4: Saving results...")
        self.logger.info("Saving results...")

        try:
            # Generate filename with versioning
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = os.path.splitext(os.path.basename(self.source_file))[0]

            # Check for existing versions
            version = 1.1
            output_filename = f"{base_filename}_enhanced_v{version:.1f}_{timestamp}.csv"
            output_file = os.path.join(self.dest_directory, output_filename)

            # Increment version if file exists
            while os.path.exists(output_file):
                version += 0.1
                output_filename = f"{base_filename}_enhanced_v{version:.1f}_{timestamp}.csv"
                output_file = os.path.join(self.dest_directory, output_filename)

            print(f"💾 Saving to: {output_filename}")

            # Save file
            self.df.to_csv(output_file, index=False)

            print(f"✅ Results saved successfully!")
            print(f"📁 Location: {output_file}")
            print(f"📊 File contains {len(self.df):,} rows and {len(self.df.columns)} columns")

            self.logger.info(f"Results saved to: {output_file}")
            self.logger.info(f"Output file contains {len(self.df)} rows and {len(self.df.columns)} columns")

            return output_file

        except Exception as e:
            print(f"❌ Error saving results: {e}")
            self.logger.error(f"Error saving results: {e}")
            return None

    def print_summary(self, output_file):
        """Print processing summary"""
        self.logger.info("=" * 80)
        self.logger.info("ENHANCED NORMALIZATION SUMMARY")
        self.logger.info("=" * 80)

        self.logger.info(f"Total rows processed: {self.stats['total_rows']}")

        if self.stats['shipper_wsd_processed'] > 0:
            self.logger.info(
                f"Shipper_WSD: {self.stats['shipper_wsd_changed']} changes out of {self.stats['shipper_wsd_processed']} records")

        if self.stats['consignee_wsd_processed'] > 0:
            self.logger.info(
                f"Consignee_WSD: {self.stats['consignee_wsd_changed']} changes out of {self.stats['consignee_wsd_processed']} records")

        if self.stats['notify_wsd_processed'] > 0:
            self.logger.info(
                f"Notify_WSD: {self.stats['notify_wsd_changed']} changes out of {self.stats['notify_wsd_processed']} records")

        total_changes = (self.stats['shipper_wsd_changed'] +
                         self.stats['consignee_wsd_changed'] +
                         self.stats['notify_wsd_changed'])

        self.logger.info(f"Total changes made: {total_changes}")
        self.logger.info(f"Processing errors: {self.stats['errors']}")

        if output_file:
            self.logger.info(f"Output file: {output_file}")

        elapsed_time = time.time() - self.start_time
        self.logger.info(f"Total processing time: {elapsed_time:.1f} seconds")

        self.logger.info("=" * 80)
        self.logger.info("ENHANCED NORMALIZATION COMPLETED SUCCESSFULLY")
        self.logger.info("=" * 80)

        # Show sample improvements
        self.show_sample_improvements()

    def show_sample_improvements(self):
        """Show examples of improvements made"""
        self.logger.info("\n📊 ENHANCEMENT EXAMPLES:")
        self.logger.info("• POSCO variations → standardized to 'POSCO'")
        self.logger.info("• Address pollution removed from notify parties")
        self.logger.info("• Business suffixes consistently removed")
        self.logger.info("• Geographic terms standardized")
        self.logger.info("• Contact information cleaned from records")

    def run(self):
        """Main execution method - FAIL FAST VERSION"""
        print("🚀 ENHANCED ENTITY NORMALIZATION STARTING...")
        print("⚠️  FAIL-FAST MODE: Script will stop on first error!")
        print("=" * 60)

        # NO TRY-CATCH BLOCKS - LET ERRORS STOP THE SCRIPT IMMEDIATELY

        # Step 1: Select files
        print("🔍 Step 1: File selection...")
        if not self.select_files():
            print("❌ File selection cancelled")
            return

        # Step 2: Load and validate
        print("📊 Step 2: Loading file...")
        if not self.load_and_validate_file():
            print("❌ FATAL ERROR: Could not load file.")
            raise RuntimeError("File loading failed - check file format and permissions")

        # Step 3: Normalize WSD columns
        print("🔧 Step 3: Starting normalization...")
        self.normalize_wsd_columns()  # Will stop immediately on any error

        # Step 4: Save results
        print("💾 Step 4: Saving results...")
        output_file = self.save_results()
        if not output_file:
            print("❌ FATAL ERROR: Could not save results.")
            raise RuntimeError("File saving failed - check directory permissions")

        # Step 5: Show summary
        self.print_summary(output_file)

        # Success message
        print("\n🎉 SUCCESS! Enhanced normalization completed!")
        print("=" * 60)

        messagebox.showinfo("Success",
                            f"Enhanced normalization completed successfully!\n\n"
                            f"Output saved to:\n{os.path.basename(output_file)}\n\n"
                            f"Check the console and log for detailed results.")


def main():
    """Main function - FAIL FAST VERSION"""
    print("🚨 FAIL-FAST VERSION - WILL STOP ON FIRST ERROR!")
    print("Starting Enhanced Entity Normalization Script...")
    print("Make sure you have a CSV file with WSD columns ready!")
    print("=" * 60)

    # NO TRY-CATCH - LET ALL ERRORS BUBBLE UP AND STOP THE SCRIPT
    normalizer = EnhancedEntityNormalizer()
    normalizer.run()

    print("\nScript finished successfully!")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main(), '', name).strip()

    # Final cleanup
    name = ' '.join(name.split())

    # Log significant transformations for debugging
    if len(original_name) > 10 and original_name.upper() != name and name != '':
        self.logger.debug(f"Enhanced normalization ({entity_type}): '{original_name}' → '{name}'")

    return name


    def load_and_validate_file(self):
        """Load and validate the source file"""
        print("\n📊 STEP 2: Loading and validating file...")
        self.logger.info("Loading and validating source file...")

        try:
            print(f"📥 Loading: {os.path.basename(self.source_file)}")

            # Load source file
            self.df = pd.read_csv(self.source_file, low_memory=False)
            self.stats['total_rows'] = len(self.df)

            print(f"✅ File loaded: {self.stats['total_rows']:,} rows, {len(self.df.columns)} columns")
            self.logger.info(f"File loaded: {self.stats['total_rows']} rows, {len(self.df.columns)} columns")

            # Check for required WSD columns
            wsd_columns = []
            if 'Shipper_WSD' in self.df.columns:
                wsd_columns.append('Shipper_WSD')
            if 'Consignee_WSD' in self.df.columns:
                wsd_columns.append('Consignee_WSD')
            if 'Notify_WSD' in self.df.columns:
                wsd_columns.append('Notify_WSD')

            if not wsd_columns:
                print("❌ ERROR: No WSD columns found!")
                raise ValueError("No WSD columns found. Expected: Shipper_WSD, Consignee_WSD, or Notify_WSD")

            print(f"🎯 Found WSD columns: {', '.join(wsd_columns)}")
            self.logger.info(f"Found WSD columns: {wsd_columns}")
            return True

        except Exception as e:
            print(f"❌ Error loading file: {e}")
            self.logger.error(f"Error loading file: {e}")
            return False


    def normalize_wsd_columns(self):
        """Normalize all WSD columns with enhanced logic"""
        print("\n🔧 STEP 3: Starting enhanced normalization...")
        print("This may take a few minutes for large files...")
        self.logger.info("Starting enhanced normalization of WSD columns...")

        try:
            # Process each WSD column if it exists
            wsd_columns = [
                ('Shipper_WSD', 'standard'),
                ('Consignee_WSD', 'standard'),
                ('Notify_WSD', 'notify')  # Special handling for notify parties
            ]

            for col_name, entity_type in wsd_columns:
                if col_name not in self.df.columns:
                    print(f"⏭️  Column '{col_name}' not found, skipping...")
                    self.logger.info(f"Column '{col_name}' not found, skipping...")
                    continue

                print(f"\n🔄 Processing '{col_name}' ({entity_type} logic)...")
                self.logger.info(f"Processing column '{col_name}' with {entity_type} logic...")

                # Process in batches for progress reporting
                batch_size = 1000
                total_rows = len(self.df)
                changes_made = 0
                processed = 0

                for batch_start in range(0, total_rows, batch_size):
                    batch_end = min(batch_start + batch_size, total_rows)
                    progress = (batch_start / total_rows) * 100

                    # Print progress every batch
                    print(f"   📈 Progress: {batch_start:,}/{total_rows:,} ({progress:.1f}%)")
                    self.logger.info(f"  Progress: {batch_start}/{total_rows} ({progress:.1f}%)")

                    # Process batch
                    for idx in range(batch_start, batch_end):
                        try:
                            original_value = self.df.iloc[idx][col_name]
                            normalized_value = self.enhanced_normalize_entity(original_value, entity_type)

                            # Only update if changed
                            if original_value != normalized_value:
                                self.df.iloc[idx, self.df.columns.get_loc(col_name)] = normalized_value
                                changes_made += 1

                            processed += 1

                        except Exception as e:
                            self.logger.error(f"Error processing row {idx}, column '{col_name}': {e}")
                            self.stats['errors'] += 1

                # Update stats
                if col_name == 'Shipper_WSD':
                    self.stats['shipper_wsd_processed'] = processed
                    self.stats['shipper_wsd_changed'] = changes_made
                elif col_name == 'Consignee_WSD':
                    self.stats['consignee_wsd_processed'] = processed
                    self.stats['consignee_wsd_changed'] = changes_made
                elif col_name == 'Notify_WSD':
                    self.stats['notify_wsd_processed'] = processed
                    self.stats['notify_wsd_changed'] = changes_made

                print(f"   ✅ '{col_name}' completed: {changes_made:,} changes out of {processed:,} records")
                self.logger.info(f"'{col_name}' completed: {changes_made} changes made out of {processed} processed")

            print("\n🎉 All WSD column normalization completed!")
            self.logger.info("All WSD column normalization completed")
            return True

        except Exception as e:
            print(f"❌ Error during normalization: {e}")
            self.logger.error(f"Error during normalization: {e}")
            return False


    def save_results(self):
        """Save results with versioning"""
        print("\n💾 STEP 4: Saving results...")
        self.logger.info("Saving results...")

        try:
            # Generate filename with versioning
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = os.path.splitext(os.path.basename(self.source_file))[0]

            # Check for existing versions
            version = 1.1
            output_filename = f"{base_filename}_enhanced_v{version:.1f}_{timestamp}.csv"
            output_file = os.path.join(self.dest_directory, output_filename)

            # Increment version if file exists
            while os.path.exists(output_file):
                version += 0.1
                output_filename = f"{base_filename}_enhanced_v{version:.1f}_{timestamp}.csv"
                output_file = os.path.join(self.dest_directory, output_filename)

            print(f"💾 Saving to: {output_filename}")

            # Save file
            self.df.to_csv(output_file, index=False)

            print(f"✅ Results saved successfully!")
            print(f"📁 Location: {output_file}")
            print(f"📊 File contains {len(self.df):,} rows and {len(self.df.columns)} columns")

            self.logger.info(f"Results saved to: {output_file}")
            self.logger.info(f"Output file contains {len(self.df)} rows and {len(self.df.columns)} columns")

            return output_file

        except Exception as e:
            print(f"❌ Error saving results: {e}")
            self.logger.error(f"Error saving results: {e}")
            return None


    def print_summary(self, output_file):
        """Print processing summary"""
        self.logger.info("=" * 80)
        self.logger.info("ENHANCED NORMALIZATION SUMMARY")
        self.logger.info("=" * 80)

        self.logger.info(f"Total rows processed: {self.stats['total_rows']}")

        if self.stats['shipper_wsd_processed'] > 0:
            self.logger.info(
                f"Shipper_WSD: {self.stats['shipper_wsd_changed']} changes out of {self.stats['shipper_wsd_processed']} records")

        if self.stats['consignee_wsd_processed'] > 0:
            self.logger.info(
                f"Consignee_WSD: {self.stats['consignee_wsd_changed']} changes out of {self.stats['consignee_wsd_processed']} records")

        if self.stats['notify_wsd_processed'] > 0:
            self.logger.info(
                f"Notify_WSD: {self.stats['notify_wsd_changed']} changes out of {self.stats['notify_wsd_processed']} records")

        total_changes = (self.stats['shipper_wsd_changed'] +
                         self.stats['consignee_wsd_changed'] +
                         self.stats['notify_wsd_changed'])

        self.logger.info(f"Total changes made: {total_changes}")
        self.logger.info(f"Processing errors: {self.stats['errors']}")

        if output_file:
            self.logger.info(f"Output file: {output_file}")

        elapsed_time = time.time() - self.start_time
        self.logger.info(f"Total processing time: {elapsed_time:.1f} seconds")

        self.logger.info("=" * 80)
        self.logger.info("ENHANCED NORMALIZATION COMPLETED SUCCESSFULLY")
        self.logger.info("=" * 80)

        # Show sample improvements
        self.show_sample_improvements()


    def show_sample_improvements(self):
        """Show examples of improvements made"""
        self.logger.info("\n📊 ENHANCEMENT EXAMPLES:")
        self.logger.info("• POSCO variations → standardized to 'POSCO'")
        self.logger.info("• Address pollution removed from notify parties")
        self.logger.info("• Business suffixes consistently removed")
        self.logger.info("• Geographic terms standardized")
        self.logger.info("• Contact information cleaned from records")


    def run(self):
        """Main execution method"""
        print("🚀 ENHANCED ENTITY NORMALIZATION STARTING...")
        print("=" * 60)

        try:
            # Step 1: Select files
            if not self.select_files():
                return

            # Step 2: Load and validate
            if not self.load_and_validate_file():
                print("❌ FAILED: Could not load file.")
                messagebox.showerror("Error", "Failed to load file. Check the log for details.")
                return

            # Step 3: Normalize WSD columns
            if not self.normalize_wsd_columns():
                print("❌ FAILED: Normalization process failed.")
                messagebox.showerror("Error", "Normalization failed. Check the log for details.")
                return

            # Step 4: Save results
            output_file = self.save_results()
            if not output_file:
                print("❌ FAILED: Could not save results.")
                messagebox.showerror("Error", "Failed to save results. Check the log for details.")
                return

            # Step 5: Show summary
            self.print_summary(output_file)

            # Success message
            print("\n🎉 SUCCESS! Enhanced normalization completed!")
            print("=" * 60)

            messagebox.showinfo("Success",
                                f"Enhanced normalization completed successfully!\n\n"
                                f"Output saved to:\n{os.path.basename(output_file)}\n\n"
                                f"Check the console and log for detailed results.")

        except Exception as e:
            print(f"❌ FATAL ERROR: {e}")
            self.logger.error(f"Script failed with error: {e}")
            messagebox.showerror("Error", f"Script failed: {e}")


def main():
    """Main function"""
    print("Starting Enhanced Entity Normalization Script...")
    print("Make sure you have a CSV file with WSD columns ready!")
    print("=" * 60)

    try:
        normalizer = EnhancedEntityNormalizer()
        normalizer.run()
    except KeyboardInterrupt:
        print("\n⏹️  Script interrupted by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")

    print("\nScript finished. Check the output!")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()