#!/usr/bin/env python3
"""
Enhanced Entity Normalization Script - Windows Explorer Version
"""

import pandas as pd
import os
import re
import logging
from datetime import datetime
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox

class EnhancedEntityNormalizer:
    def __init__(self):
        self.setup_logging()
        self.source_file = None
        self.dest_directory = None
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
        self.start_time = time.time()
        self.setup_enhanced_patterns()

    def setup_logging(self):
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"enhanced_normalization_log_{timestamp}.log")

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

        logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 80)
        self.logger.info("ENHANCED ENTITY NORMALIZATION SCRIPT STARTED")
        self.logger.info("=" * 80)

    def setup_enhanced_patterns(self):
        self.business_suffixes = [
            r'\b(LLC|L\.L\.C\.?)\b', r'\b(INC|INCORPORATED?)\b',
            r'\b(CORP|CORPORATION)\b', r'\b(LTD|LIMITED)\b',
            r'\b(CO|COMPANY)\b', r'\b(LP|L\.P\.?)\b',
            r'\b(LLP|L\.L\.P\.?)\b'
        ]
        self.geographic_terms = [r'\b(USA|US|AMERICA)\b']
        self.company_standardizations = {"POSCO INTERNATIONAL AMERICA": "POSCO"}
        self.suffix_pattern = '|'.join(self.business_suffixes)
        self.geographic_pattern = '|'.join(self.geographic_terms)

    def select_files(self):
        root = tk.Tk()
        root.withdraw()
        try:
            source_file = filedialog.askopenfilename(
                title="Select source CSV file",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if not source_file:
                self.logger.error("No file selected")
                return False
            self.source_file = source_file
            self.dest_directory = os.path.dirname(source_file)
            self.logger.info(f"Selected file: {self.source_file}")
            return True
        finally:
            root.destroy()

    def enhanced_normalize_entity(self, entity_name, entity_type='standard'):
        if pd.isna(entity_name) or str(entity_name).strip() == '':
            return ''
        original_name = str(entity_name).strip().upper()
        name = original_name

        for variation, standard in self.company_standardizations.items():
            if variation in name:
                name = name.replace(variation, standard)

        name = re.sub(f'({self.suffix_pattern})\\b', '', name, flags=re.IGNORECASE).strip()
        temp_name = re.sub(f'({self.geographic_pattern})\\b', '', name, flags=re.IGNORECASE).strip()
        if len(temp_name) > 3:
            name = temp_name

        name = re.sub(r'[,.\-_\|;]+$', '', name).strip()
        return name

    def load_and_validate_file(self):
        try:
            self.df = pd.read_csv(self.source_file, low_memory=False)
            self.stats['total_rows'] = len(self.df)
            self.logger.info(f"Loaded {self.stats['total_rows']} rows")
            return True
        except Exception as e:
            self.logger.error(f"Error loading file: {e}")
            return False

    def normalize_wsd_columns(self):
        for col_name in ['Shipper_WSD', 'Consignee_WSD', 'Notify_WSD']:
            if col_name not in self.df.columns:
                continue
            changes = 0
            for idx, val in self.df[col_name].items():
                new_val = self.enhanced_normalize_entity(val)
                if val != new_val:
                    self.df.at[idx, col_name] = new_val
                    changes += 1
            self.logger.info(f"{col_name}: {changes} changes")
        return True

    def save_results(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = os.path.splitext(os.path.basename(self.source_file))[0]
            output_filename = f"{base_filename}_enhanced_{timestamp}.csv"
            output_file = os.path.join(self.dest_directory, output_filename)
            self.df.to_csv(output_file, index=False)
            self.logger.info(f"Results saved to {output_file}")
            return output_file
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            return None

    def run(self):
        if not self.select_files():
            return
        if not self.load_and_validate_file():
            return
        self.normalize_wsd_columns()
        self.save_results()
        self.logger.info("Normalization completed")

def main():
    normalizer = EnhancedEntityNormalizer()
    normalizer.run()
    print("Done. Check logs/ directory for details.")

if __name__ == "__main__":
    main()
