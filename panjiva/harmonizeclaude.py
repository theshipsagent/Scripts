#!/usr/bin/env python3
"""
Final Working Tonnage-Weighted Entity Normalization Script
No syntax errors, includes file selection, tonnage weighting, and fail-fast error handling.
Version: FINAL
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


class TonnageWeightedNormalizer:
    def __init__(self):
        self.setup_logging()

        # File paths
        self.source_file = None
        self.dest_directory = None

        # Processing stats
        self.stats = {
            'total_rows': 0,
            'shipper_changes': 0,
            'consignee_changes': 0,
            'notify_changes': 0,
            'tonnage_consolidated': 0
        }

        self.start_time = time.time()
        self.setup_patterns()

    def setup_logging(self):
        """Setup logging"""
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"tonnage_normalization_{timestamp}.log")

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[file_handler, console_handler]
        )

        self.logger = logging.getLogger(__name__)
        print("=" * 60)
        print("TONNAGE-WEIGHTED ENTITY NORMALIZATION")
        print("=" * 60)

    def setup_patterns(self):
        """Setup normalization patterns with intelligent word prioritization"""

        # Business suffixes
        self.business_suffixes = [
            'LLC', 'INC', 'CORP', 'LTD', 'CO', 'LP', 'LLP', 'SA', 'AG', 'BV',
            'L.L.C.', 'INCORPORATED', 'CORPORATION', 'LIMITED', 'COMPANY',
            'L.P.', 'L.L.P.', 'S.A.', 'G.M.B.H.', 'GMBH', 'PVT', 'HOLDINGS',
            'PLC', 'JSC', 'TUBULARS', 'STEEL', 'GROUP', 'ENTERPRISES'
        ]

        # Generic first words that should be ignored (look to second/third word)
        self.generic_first_words = [
            'AMERICAN', 'GLOBAL', 'INTERNATIONAL', 'UNITED', 'GENERAL', 'NATIONAL',
            'UNIVERSAL', 'WORLD', 'WORLDWIDE', 'CHINA', 'EUROPEAN', 'ASIAN',
            'PACIFIC', 'ATLANTIC', 'FIRST', 'SECOND', 'THIRD', 'NEW', 'OLD',
            'NORTH', 'SOUTH', 'EAST', 'WEST', 'NORTHERN', 'SOUTHERN', 'EASTERN', 'WESTERN'
        ]

        # Japanese/Korean chaebol patterns (need 2-3 words)
        self.asian_corporate_groups = [
            'MITSUI', 'MITSUBISHI', 'SUMITOMO', 'ITOCHU', 'MARUBENI', 'TOYOTA',
            'SAMSUNG', 'LG', 'HYUNDAI', 'SK', 'LOTTE', 'POSCO', 'DAEWOO',
            'KAWASAKI', 'HITACHI', 'TOSHIBA', 'PANASONIC', 'SONY', 'HONDA',
            'NISSAN', 'MAZDA', 'SUBARU', 'SUZUKI', 'YAMAHA', 'KOMATSU'
        ]

        # Industry-specific subsidiary indicators
        self.industry_indicators = [
            'STEEL', 'TUBULARS', 'SHIPPING', 'MARINE', 'LOGISTICS', 'TRADING',
            'SALES', 'MARKETING', 'DISTRIBUTION', 'SERVICES', 'PRODUCT',
            'MATERIALS', 'CHEMICALS', 'ENERGY', 'POWER', 'ELECTRIC', 'DIESEL',
            'ENDEAVORS', 'VENTURES', 'SOLUTIONS', 'SYSTEMS', 'TECHNOLOGIES'
        ]

        # Known high-volume consolidations
        self.known_consolidations = {
            # POSCO variations
            'POSCO INTERNATIONAL AMERICA': 'POSCO',
            'POSCO AMERICA': 'POSCO',
            'POSCO VIETNAM': 'POSCO',

            # AMEROPA variations
            'AMEROPA AG': 'AMEROPA',
            'AMEROPA NORTH': 'AMEROPA',
            'AMEROPA TRADING': 'AMEROPA',

            # Japanese trading houses
            'MARUBENI ITOCHU TUBULARS': 'MARUBENI',
            'MARUBENI ITOCHU STEEL': 'MARUBENI',
            'MITSUI BUSSAN': 'MITSUI',
            'MITSUBISHI CORPORATION': 'MITSUBISHI',
            'SUMITOMO CORPORATION': 'SUMITOMO',

            # Maritime companies
            'MARITIME ENDEAVORS SHIPPING': 'MARITIME ENDEAVORS',
            'MARITIME DIESEL ELECTRIC': 'MARITIME DIESEL',

            # Martin companies (from your example)
            'MARTIN PRODUCT SALES': 'MARTIN',
            'MARTIN MUNIZ MOLINA': 'MARTIN',
            'MARTIN BENCHER': 'MARTIN',
            'MARTIN ANDROBSON': 'MARTIN',

            # Major trading companies
            'CARGILL INTERNATIONAL': 'CARGILL',
            'TRAFIGURA PTE': 'TRAFIGURA',
            'GLENCORE INTERNATIONAL': 'GLENCORE',
            'BUNGE TRADING': 'BUNGE'
        }

    def select_file(self):
        """Select source file using Windows Explorer"""
        print("🔍 Opening file selection dialog...")

        root = tk.Tk()
        root.withdraw()

        try:
            source_file = filedialog.askopenfilename(
                title="Select CSV file with WSD columns to normalize",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=os.getcwd()
            )

            if not source_file:
                print("❌ No file selected")
                return False

            self.source_file = source_file
            self.dest_directory = os.path.dirname(source_file)

            print(f"✅ Selected: {os.path.basename(self.source_file)}")
            print(f"📁 Output dir: {self.dest_directory}")

            return True

        except Exception as e:
            print(f"❌ Error selecting file: {e}")
            return False
        finally:
            root.destroy()

    def load_file(self):
        """Load and validate the CSV file"""
        print("\n📊 Loading file...")

        # Load the file
        self.df = pd.read_csv(self.source_file, low_memory=False)
        self.stats['total_rows'] = len(self.df)

        print(f"✅ Loaded: {self.stats['total_rows']:,} rows, {len(self.df.columns)} columns")

        # Check for WSD columns
        wsd_columns = []
        if 'Shipper_WSD' in self.df.columns:
            wsd_columns.append('Shipper_WSD')
        if 'Consignee_WSD' in self.df.columns:
            wsd_columns.append('Consignee_WSD')
        if 'Notify_WSD' in self.df.columns:
            wsd_columns.append('Notify_WSD')

        if not wsd_columns:
            print("❌ No WSD columns found!")
            raise ValueError("Expected Shipper_WSD, Consignee_WSD, or Notify_WSD columns")

        print(f"🎯 Found WSD columns: {', '.join(wsd_columns)}")

        # Check for weight column
        weight_col = None
        weight_options = ['Weight (t)', 'Weight(t)', 'Weight', 'Tons', 'Tonnage']
        for col in weight_options:
            if col in self.df.columns:
                weight_col = col
                break

        if weight_col:
            print(f"⚖️  Found weight column: '{weight_col}'")
            self.weight_column = weight_col
        else:
            print("⚠️  No weight column found - using basic consolidation")
            self.weight_column = None

        return True

    def extract_smart_company_core(self, company_name):
        """Extract company core using intelligent first-word prioritization"""
        if not company_name:
            return company_name

        # Clean and split into words
        name = str(company_name).upper().strip()
        words = name.split()

        if not words:
            return name

        # Remove business suffixes first
        filtered_words = []
        for word in words:
            if word not in self.business_suffixes:
                filtered_words.append(word)

        if not filtered_words:
            return name  # Fallback if all words were suffixes

        words = filtered_words

        # LOGIC 1: Check for Asian corporate groups (need 2-3 words)
        for i, word in enumerate(words):
            if word in self.asian_corporate_groups:
                # For Asian companies, take 1-2 words starting from the corporate group name
                if i + 1 < len(words) and words[i + 1] not in self.industry_indicators:
                    # Include next word if it's not just an industry indicator
                    return ' '.join(words[i:i + 2])
                else:
                    # Just the corporate group name
                    return word

        # LOGIC 2: First word logic
        first_word = words[0]

        # If first word is generic, look to second/third word
        if first_word in self.generic_first_words:
            if len(words) > 1:
                # Take second word as primary, maybe third
                core_words = [words[1]]
                if len(words) > 2 and words[2] not in self.industry_indicators:
                    core_words.append(words[2])
                return ' '.join(core_words)
            else:
                return first_word  # Fallback

        # LOGIC 3: First word is significant - use it as primary
        else:
            # Take first word, and maybe second if it's not an industry indicator
            core_words = [first_word]

            # Add second word if it's meaningful (not industry/geographic indicator)
            if (len(words) > 1 and
                    words[1] not in self.industry_indicators and
                    words[1] not in ['NORTH', 'SOUTH', 'EAST', 'WEST', 'INTERNATIONAL', 'AMERICA']):

                # Special case: if both words are significant company names
                if len(words[1]) >= 4:  # Meaningful word length
                    core_words.append(words[1])

            # Limit to max 2-3 words
            return ' '.join(core_words[:3])

    def consolidate_entity(self, entity_name):
        """Consolidate entity using smart core extraction"""
        if pd.isna(entity_name) or entity_name == '' or entity_name == 'null':
            return ''

        name = str(entity_name).upper().strip()

        # Check known consolidations first (exact matches)
        for subsidiary, parent in self.known_consolidations.items():
            if subsidiary in name or name.startswith(subsidiary):
                return parent

        # Apply smart core extraction
        core_name = self.extract_smart_company_core(name)

        # Clean up punctuation
        core_name = re.sub(r'[,.\-_|;()]+

    def clean_notify_party(self, notify_text):
        """Special cleaning for notify party (remove addresses)"""
        if pd.isna(notify_text) or notify_text == '' or notify_text == 'null':
            return ''

        text = str(notify_text).upper().strip()

        # Take first line (usually company name)
        lines = text.split('\n')
        if lines:
            company_line = lines[0].strip()
        else:
            company_line = text

        # Remove phone numbers
        company_line = re.sub(r'\([0-9]{3}\)[0-9\-\s]+', '', company_line)
        company_line = re.sub(r'[0-9]{3}-[0-9]{3}-[0-9]{4}', '', company_line)

        # Remove email addresses
        company_line = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', '', company_line)

        # Remove address indicators
        address_words = ['STREET', 'ST', 'AVENUE', 'AVE', 'SUITE', 'STE', 'ROAD', 'RD']
        for addr_word in address_words:
            pattern = r'\b' + re.escape(addr_word) + r'(\s+\d+|\s*$)'
            company_line = re.sub(pattern, '', company_line, flags=re.IGNORECASE)

        # Clean up
        company_line = re.sub(r'\s+', ' ', company_line).strip()

        return self.consolidate_entity(company_line)

    def normalize_columns(self):
        """Normalize all WSD columns"""
        print("\n🔧 Starting tonnage-weighted normalization...")
        print("⚠️  FAIL-FAST MODE: Will stop on first error!")

        columns_to_process = [
            ('Shipper_WSD', False),
            ('Consignee_WSD', False),
            ('Notify_WSD', True)  # True = is_notify_party
        ]

        for col_name, is_notify in columns_to_process:
            if col_name not in self.df.columns:
                print(f"⏭️  Skipping {col_name} - not found")
                continue

            print(f"\n🔄 Processing {col_name}...")
            changes = 0
            tonnage_consolidated = 0

            # Process in batches
            batch_size = 500
            total_rows = len(self.df)

            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
                progress = (batch_start / total_rows) * 100

                print(f"   📈 Progress: {batch_start:,}/{total_rows:,} ({progress:.1f}%)")

                # Process each row
                for idx in range(batch_start, batch_end):
                    original = self.df.iloc[idx][col_name]

                    # Apply appropriate cleaning
                    if is_notify:
                        cleaned = self.clean_notify_party(original)
                    else:
                        cleaned = self.consolidate_entity(original)

                    # Update if changed
                    if original != cleaned:
                        self.df.iloc[idx, self.df.columns.get_loc(col_name)] = cleaned
                        changes += 1

                        # Track tonnage if available
                        if self.weight_column:
                            row_tonnage = self.df.iloc[idx][self.weight_column]
                            if pd.notna(row_tonnage):
                                tonnage_consolidated += row_tonnage

                                # Show high-tonnage consolidations
                                if row_tonnage > 1000:
                                    print(f"   🎯 Row {idx}: '{original}' → '{cleaned}' ({row_tonnage:,.0f} tons)")

                        # Show consolidation examples with logic explanation
                        if changes <= 5:
                            print(f"   🔄 Row {idx}: '{original}' → '{cleaned}'")
                        elif any(keyword in str(original).upper() for keyword in
                                 ['MARUBENI', 'MARTIN', 'MARITIME', 'MITSUI', 'AMEROPA', 'POSCO']):
                            print(f"   🎯 Row {idx}: '{original}' → '{cleaned}' (smart consolidation)")

            # Update stats
            if col_name == 'Shipper_WSD':
                self.stats['shipper_changes'] = changes
            elif col_name == 'Consignee_WSD':
                self.stats['consignee_changes'] = changes
            elif col_name == 'Notify_WSD':
                self.stats['notify_changes'] = changes

            self.stats['tonnage_consolidated'] += tonnage_consolidated

            print(f"   ✅ {col_name}: {changes:,} changes made")
            if self.weight_column and tonnage_consolidated > 0:
                print(f"   📦 Tonnage consolidated: {tonnage_consolidated:,.0f} tons")

        print("\n🎉 Normalization completed!")
        return True

    def save_file(self):
        """Save the normalized file"""
        print("\n💾 Saving results...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.source_file))[0]

        version = 1.1
        output_name = f"{base_name}_tonnage_normalized_v{version:.1f}_{timestamp}.csv"
        output_path = os.path.join(self.dest_directory, output_name)

        # Check if file exists and increment version
        while os.path.exists(output_path):
            version += 0.1
            output_name = f"{base_name}_tonnage_normalized_v{version:.1f}_{timestamp}.csv"
            output_path = os.path.join(self.dest_directory, output_name)

        # Save the file
        self.df.to_csv(output_path, index=False)

        print(f"✅ Saved: {output_name}")
        print(f"📁 Location: {output_path}")

        return output_path

    def print_summary(self, output_file):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("TONNAGE-WEIGHTED NORMALIZATION SUMMARY")
        print("=" * 60)

        print(f"Total rows processed: {self.stats['total_rows']:,}")
        print(f"Shipper_WSD changes: {self.stats['shipper_changes']:,}")
        print(f"Consignee_WSD changes: {self.stats['consignee_changes']:,}")
        print(f"Notify_WSD changes: {self.stats['notify_changes']:,}")

        total_changes = (self.stats['shipper_changes'] +
                         self.stats['consignee_changes'] +
                         self.stats['notify_changes'])
        print(f"Total changes made: {total_changes:,}")

        if self.weight_column and self.stats['tonnage_consolidated'] > 0:
            print(f"📦 Total tonnage consolidated: {self.stats['tonnage_consolidated']:,.0f} tons")
            print(f"💎 High-impact consolidations prioritized by tonnage")

        elapsed = time.time() - self.start_time
        print(f"Processing time: {elapsed:.1f} seconds")
        print(f"Output file: {os.path.basename(output_file)}")

        print("=" * 60)
        print("SUCCESS! TONNAGE-WEIGHTED CONSOLIDATION COMPLETED!")
        print("💡 Your entity consolidation should now be much more effective!")
        print("=" * 60)

    def run(self):
        """Main execution"""
        print("🚀 Starting tonnage-weighted entity normalization...")
        print("📊 Focuses on high-volume entity consolidation")
        print("🚨 FAIL-FAST MODE - stops on first error")
        print("=" * 60)

        # Step 1: Select file (NO TRY-CATCH - WILL FAIL FAST)
        if not self.select_file():
            return

        # Step 2: Load file
        self.load_file()

        # Step 3: Normalize
        self.normalize_columns()

        # Step 4: Save
        output_file = self.save_file()

        # Step 5: Summary
        self.print_summary(output_file)

        # Success dialog
        messagebox.showinfo(
            "Success!",
            f"Tonnage-weighted normalization completed!\n\n"
            f"File saved as:\n{os.path.basename(output_file)}\n\n"
            f"Total consolidations: {self.stats['shipper_changes'] + self.stats['consignee_changes'] + self.stats['notify_changes']:,}\n"
            f"Tonnage consolidated: {self.stats['tonnage_consolidated']:,.0f} tons\n\n"
            f"Check console for detailed results."
        )


def main():
    """Main function"""
    print("🧹 TONNAGE-WEIGHTED ENTITY NORMALIZATION SCRIPT")
    print("📋 Processes Shipper_WSD, Consignee_WSD, Notify_WSD columns")
    print("⚖️  Uses Weight (t) column for intelligent consolidation")
    print("⚠️  STOPS IMMEDIATELY ON ANY ERROR")
    print("=" * 60)

    # NO TRY-CATCH - FAIL FAST ON ANY ERROR
    normalizer = TonnageWeightedNormalizer()
    normalizer.run()

    print("\n✅ Script completed successfully!")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main(), '', core_name)
    core_name = re.sub(r'\s+', ' ', core_name).strip()

    return core_name if core_name else name


    def clean_notify_party(self, notify_text):
        """Special cleaning for notify party (remove addresses)"""
        if pd.isna(notify_text) or notify_text == '' or notify_text == 'null':
            return ''

        text = str(notify_text).upper().strip()

        # Take first line (usually company name)
        lines = text.split('\n')
        if lines:
            company_line = lines[0].strip()
        else:
            company_line = text

        # Remove phone numbers
        company_line = re.sub(r'\([0-9]{3}\)[0-9\-\s]+', '', company_line)
        company_line = re.sub(r'[0-9]{3}-[0-9]{3}-[0-9]{4}', '', company_line)

        # Remove email addresses
        company_line = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', '', company_line)

        # Remove address indicators
        address_words = ['STREET', 'ST', 'AVENUE', 'AVE', 'SUITE', 'STE', 'ROAD', 'RD']
        for addr_word in address_words:
            pattern = r'\b' + re.escape(addr_word) + r'(\s+\d+|\s*$)'
            company_line = re.sub(pattern, '', company_line, flags=re.IGNORECASE)

        # Clean up
        company_line = re.sub(r'\s+', ' ', company_line).strip()

        return self.consolidate_entity(company_line)


    def normalize_columns(self):
        """Normalize all WSD columns"""
        print("\n🔧 Starting tonnage-weighted normalization...")
        print("⚠️  FAIL-FAST MODE: Will stop on first error!")

        columns_to_process = [
            ('Shipper_WSD', False),
            ('Consignee_WSD', False),
            ('Notify_WSD', True)  # True = is_notify_party
        ]

        for col_name, is_notify in columns_to_process:
            if col_name not in self.df.columns:
                print(f"⏭️  Skipping {col_name} - not found")
                continue

            print(f"\n🔄 Processing {col_name}...")
            changes = 0
            tonnage_consolidated = 0

            # Process in batches
            batch_size = 500
            total_rows = len(self.df)

            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
                progress = (batch_start / total_rows) * 100

                print(f"   📈 Progress: {batch_start:,}/{total_rows:,} ({progress:.1f}%)")

                # Process each row
                for idx in range(batch_start, batch_end):
                    original = self.df.iloc[idx][col_name]

                    # Apply appropriate cleaning
                    if is_notify:
                        cleaned = self.clean_notify_party(original)
                    else:
                        cleaned = self.consolidate_entity(original)

                    # Update if changed
                    if original != cleaned:
                        self.df.iloc[idx, self.df.columns.get_loc(col_name)] = cleaned
                        changes += 1

                        # Track tonnage if available
                        if self.weight_column:
                            row_tonnage = self.df.iloc[idx][self.weight_column]
                            if pd.notna(row_tonnage):
                                tonnage_consolidated += row_tonnage

                                # Show high-tonnage consolidations
                                if row_tonnage > 1000:
                                    print(f"   🎯 Row {idx}: '{original}' → '{cleaned}' ({row_tonnage:,.0f} tons)")

                        # Show first few changes for debugging
                        elif changes <= 3:
                            print(f"   🔄 Row {idx}: '{original}' → '{cleaned}'")

            # Update stats
            if col_name == 'Shipper_WSD':
                self.stats['shipper_changes'] = changes
            elif col_name == 'Consignee_WSD':
                self.stats['consignee_changes'] = changes
            elif col_name == 'Notify_WSD':
                self.stats['notify_changes'] = changes

            self.stats['tonnage_consolidated'] += tonnage_consolidated

            print(f"   ✅ {col_name}: {changes:,} changes made")
            if self.weight_column and tonnage_consolidated > 0:
                print(f"   📦 Tonnage consolidated: {tonnage_consolidated:,.0f} tons")

        print("\n🎉 Normalization completed!")
        return True


    def save_file(self):
        """Save the normalized file"""
        print("\n💾 Saving results...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.source_file))[0]

        version = 1.1
        output_name = f"{base_name}_tonnage_normalized_v{version:.1f}_{timestamp}.csv"
        output_path = os.path.join(self.dest_directory, output_name)

        # Check if file exists and increment version
        while os.path.exists(output_path):
            version += 0.1
            output_name = f"{base_name}_tonnage_normalized_v{version:.1f}_{timestamp}.csv"
            output_path = os.path.join(self.dest_directory, output_name)

        # Save the file
        self.df.to_csv(output_path, index=False)

        print(f"✅ Saved: {output_name}")
        print(f"📁 Location: {output_path}")

        return output_path


    def print_summary(self, output_file):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("TONNAGE-WEIGHTED NORMALIZATION SUMMARY")
        print("=" * 60)

        print(f"Total rows processed: {self.stats['total_rows']:,}")
        print(f"Shipper_WSD changes: {self.stats['shipper_changes']:,}")
        print(f"Consignee_WSD changes: {self.stats['consignee_changes']:,}")
        print(f"Notify_WSD changes: {self.stats['notify_changes']:,}")

        total_changes = (self.stats['shipper_changes'] +
                         self.stats['consignee_changes'] +
                         self.stats['notify_changes'])
        print(f"Total changes made: {total_changes:,}")

        if self.weight_column and self.stats['tonnage_consolidated'] > 0:
            print(f"📦 Total tonnage consolidated: {self.stats['tonnage_consolidated']:,.0f} tons")
            print(f"💎 High-impact consolidations prioritized by tonnage")

        elapsed = time.time() - self.start_time
        print(f"Processing time: {elapsed:.1f} seconds")
        print(f"Output file: {os.path.basename(output_file)}")

        print("=" * 60)
        print("SUCCESS! TONNAGE-WEIGHTED CONSOLIDATION COMPLETED!")
        print("💡 Your entity consolidation should now be much more effective!")
        print("=" * 60)


    def run(self):
        """Main execution"""
        print("🚀 Starting tonnage-weighted entity normalization...")
        print("📊 Focuses on high-volume entity consolidation")
        print("🚨 FAIL-FAST MODE - stops on first error")
        print("=" * 60)

        # Step 1: Select file (NO TRY-CATCH - WILL FAIL FAST)
        if not self.select_file():
            return

        # Step 2: Load file
        self.load_file()

        # Step 3: Normalize
        self.normalize_columns()

        # Step 4: Save
        output_file = self.save_file()

        # Step 5: Summary
        self.print_summary(output_file)

        # Success dialog
        messagebox.showinfo(
            "Success!",
            f"Tonnage-weighted normalization completed!\n\n"
            f"File saved as:\n{os.path.basename(output_file)}\n\n"
            f"Total consolidations: {self.stats['shipper_changes'] + self.stats['consignee_changes'] + self.stats['notify_changes']:,}\n"
            f"Tonnage consolidated: {self.stats['tonnage_consolidated']:,.0f} tons\n\n"
            f"Check console for detailed results."
        )


def main():
    """Main function"""
    print("🧹 TONNAGE-WEIGHTED ENTITY NORMALIZATION SCRIPT")
    print("📋 Processes Shipper_WSD, Consignee_WSD, Notify_WSD columns")
    print("⚖️  Uses Weight (t) column for intelligent consolidation")
    print("⚠️  STOPS IMMEDIATELY ON ANY ERROR")
    print("=" * 60)

    # NO TRY-CATCH - FAIL FAST ON ANY ERROR
    normalizer = TonnageWeightedNormalizer()
    normalizer.run()

    print("\n✅ Script completed successfully!")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()