"""
CSV Merger Script - Llyods Dataset Integration
================================================
Merges all CSV files in specified directory with:
- Duplicate detection and separation
- Auto-encoding detection
- Matrix green terminal output
- Comprehensive logging
- Error handling
- Summary reports

Author: Auto-generated
Date: 2025-10-15
"""

import os
import pandas as pd
import glob
from datetime import datetime
import logging
import chardet
from pathlib import Path
import sys
from collections import Counter
import hashlib

# ============================================================================
# MATRIX GREEN STYLING
# ============================================================================

class MatrixStyle:
    """Matrix-style terminal output with green text"""
    
    # ANSI color codes
    GREEN = '\033[92m'
    BRIGHT_GREEN = '\033[1;92m'
    DIM_GREEN = '\033[2;92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def header(text):
        """Print header in bright green"""
        width = 80
        print(f"\n{MatrixStyle.BRIGHT_GREEN}{'=' * width}")
        print(f"{text.center(width)}")
        print(f"{'=' * width}{MatrixStyle.RESET}\n")
    
    @staticmethod
    def section(text):
        """Print section header"""
        print(f"\n{MatrixStyle.GREEN}{'─' * 80}")
        print(f"▶ {text}")
        print(f"{'─' * 80}{MatrixStyle.RESET}")
    
    @staticmethod
    def info(label, value):
        """Print info line"""
        print(f"{MatrixStyle.GREEN}  ├─ {label:<30} {MatrixStyle.BRIGHT_GREEN}{value}{MatrixStyle.RESET}")
    
    @staticmethod
    def success(message):
        """Print success message"""
        print(f"{MatrixStyle.BRIGHT_GREEN}  ✓ {message}{MatrixStyle.RESET}")
    
    @staticmethod
    def warning(message):
        """Print warning message"""
        print(f"{MatrixStyle.YELLOW}  ⚠ {message}{MatrixStyle.RESET}")
    
    @staticmethod
    def error(message):
        """Print error message"""
        print(f"{MatrixStyle.RED}  ✗ {message}{MatrixStyle.RESET}")
    
    @staticmethod
    def progress(current, total, item_name=""):
        """Print progress bar"""
        percentage = (current / total) * 100
        bar_length = 50
        filled = int(bar_length * current / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r{MatrixStyle.GREEN}  [{bar}] {percentage:.1f}% {MatrixStyle.BRIGHT_GREEN}{item_name}{MatrixStyle.RESET}", end='', flush=True)
        
        if current == total:
            print()  # New line when complete

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Configuration settings"""
    
    # Directory paths
    SOURCE_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\Llyods"
    OUTPUT_FILENAME_PREFIX = "llyods_merged"
    DUPLICATES_FOLDER = "duplicates_review"
    LOGS_FOLDER = "merge_logs"
    
    # Processing settings
    NEW_COLUMN_NAME = "Type"
    SOURCE_COLUMN_NAME = "Source_File"
    DATETIME_FORMAT = "%Y%m%d_%H%M"
    ENCODING_CONFIDENCE_THRESHOLD = 0.7
    
    # Logging settings
    LOG_LEVEL = logging.DEBUG


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def setup_logging(log_dir):
    """Setup comprehensive logging"""
    timestamp = datetime.now().strftime(Config.DATETIME_FORMAT)
    log_file = os.path.join(log_dir, f"merge_log_{timestamp}.log")
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler (less verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    
    # Setup logger
    logger = logging.getLogger('CSVMerger')
    logger.setLevel(Config.LOG_LEVEL)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file


def detect_encoding(file_path, sample_size=100000):
    """Detect file encoding using chardet"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(sample_size)
            result = chardet.detect(raw_data)
            
            encoding = result['encoding']
            confidence = result['confidence']
            
            # Fallback to utf-8 if confidence is low
            if confidence < Config.ENCODING_CONFIDENCE_THRESHOLD:
                encoding = 'utf-8'
            
            return encoding, confidence
    except Exception as e:
        return 'utf-8', 0.0


def create_row_hash(row):
    """Create hash of row for duplicate detection"""
    # Convert row to string and create hash
    row_str = '|'.join(str(x) for x in row.values)
    return hashlib.md5(row_str.encode()).hexdigest()


def ensure_directories(base_dir):
    """Create necessary directories"""
    duplicates_dir = os.path.join(base_dir, Config.DUPLICATES_FOLDER)
    logs_dir = os.path.join(base_dir, Config.LOGS_FOLDER)
    
    os.makedirs(duplicates_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    return duplicates_dir, logs_dir


# ============================================================================
# MAIN PROCESSING CLASS
# ============================================================================

class CSVMerger:
    """Main CSV merger class"""
    
    def __init__(self, source_dir):
        self.source_dir = source_dir
        self.logger = None
        self.stats = {
            'files_found': 0,
            'files_processed': 0,
            'files_failed': 0,
            'total_rows_read': 0,
            'duplicate_rows': 0,
            'unique_rows': 0,
            'multi_source_records': 0,
            'encoding_issues': 0,
            'processing_time': 0
        }
        self.file_details = []
        
    def initialize(self):
        """Initialize directories and logging"""
        MatrixStyle.header("CSV MERGER - LLYODS DATASET")
        MatrixStyle.section("INITIALIZATION")
        
        # Create directories
        self.duplicates_dir, self.logs_dir = ensure_directories(self.source_dir)
        
        # Setup logging
        self.logger, self.log_file = setup_logging(self.logs_dir)
        self.logger.info("="*80)
        self.logger.info("CSV Merger Script Started")
        self.logger.info("="*80)
        self.logger.info(f"Source Directory: {self.source_dir}")
        
        MatrixStyle.info("Source Directory", self.source_dir)
        MatrixStyle.info("Duplicates Folder", self.duplicates_dir)
        MatrixStyle.info("Logs Folder", self.logs_dir)
        MatrixStyle.success("Initialization complete")
        
    def find_csv_files(self):
        """Find all CSV files in source directory"""
        MatrixStyle.section("SCANNING FOR CSV FILES")
        
        pattern = os.path.join(self.source_dir, "*.csv")
        csv_files = glob.glob(pattern)
        
        self.stats['files_found'] = len(csv_files)
        
        MatrixStyle.info("CSV Files Found", self.stats['files_found'])
        
        if self.stats['files_found'] == 0:
            MatrixStyle.error("No CSV files found in directory!")
            self.logger.error("No CSV files found")
            return []
        
        # Log file list
        self.logger.info(f"Found {len(csv_files)} CSV files:")
        for i, file in enumerate(csv_files, 1):
            filename = os.path.basename(file)
            MatrixStyle.info(f"  [{i}]", filename)
            self.logger.info(f"  {i}. {filename}")
        
        return csv_files
    
    def read_csv_with_encoding(self, file_path):
        """Read CSV with automatic encoding detection"""
        filename = os.path.basename(file_path)
        
        try:
            # Detect encoding
            encoding, confidence = detect_encoding(file_path)
            self.logger.info(f"Detected encoding for {filename}: {encoding} (confidence: {confidence:.2%})")
            
            # Try reading with detected encoding
            try:
                df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
                return df, encoding, confidence, None
            
            except UnicodeDecodeError:
                # Fallback encodings
                fallback_encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                
                for fallback in fallback_encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=fallback, low_memory=False)
                        self.logger.warning(f"Used fallback encoding {fallback} for {filename}")
                        return df, fallback, 0.5, f"Fallback: {fallback}"
                    except:
                        continue
                
                # If all fail, try with error handling
                df = pd.read_csv(file_path, encoding='utf-8', errors='replace', low_memory=False)
                self.logger.warning(f"Read {filename} with error replacement")
                return df, 'utf-8', 0.0, "Errors replaced"
        
        except Exception as e:
            self.logger.error(f"Failed to read {filename}: {str(e)}")
            return None, None, None, str(e)
    
    def load_all_files(self, csv_files):
        """Load all CSV files into memory"""
        MatrixStyle.section("LOADING CSV FILES")
        
        all_dataframes = []
        
        for i, file_path in enumerate(csv_files, 1):
            filename = os.path.basename(file_path)
            
            MatrixStyle.progress(i-1, len(csv_files), f"Loading: {filename}")
            
            # Read file
            df, encoding, confidence, error = self.read_csv_with_encoding(file_path)
            
            if df is not None:
                # Store file details
                file_info = {
                    'filename': filename,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'encoding': encoding,
                    'confidence': confidence,
                    'error': error,
                    'status': 'SUCCESS' if error is None else 'WARNING'
                }
                
                self.file_details.append(file_info)
                self.stats['files_processed'] += 1
                self.stats['total_rows_read'] += len(df)
                
                # Add source filename column for tracking
                df['_source_file'] = filename
                
                all_dataframes.append(df)
                
                self.logger.info(f"Loaded {filename}: {len(df)} rows, {len(df.columns)} columns")
            else:
                self.stats['files_failed'] += 1
                self.stats['encoding_issues'] += 1
                
                file_info = {
                    'filename': filename,
                    'rows': 0,
                    'columns': 0,
                    'encoding': 'N/A',
                    'confidence': 0,
                    'error': error,
                    'status': 'FAILED'
                }
                self.file_details.append(file_info)
                
                MatrixStyle.error(f"Failed to load: {filename}")
                self.logger.error(f"Failed to load {filename}: {error}")
        
        MatrixStyle.progress(len(csv_files), len(csv_files), "Complete")
        MatrixStyle.success(f"Loaded {self.stats['files_processed']}/{self.stats['files_found']} files successfully")
        
        return all_dataframes
    
    def merge_dataframes(self, dataframes):
        """Merge all dataframes"""
        MatrixStyle.section("MERGING DATAFRAMES")
        
        if not dataframes:
            MatrixStyle.error("No dataframes to merge!")
            return None
        
        try:
            # Concatenate all dataframes
            merged_df = pd.concat(dataframes, ignore_index=True, sort=False)
            
            MatrixStyle.info("Total Rows", f"{len(merged_df):,}")
            MatrixStyle.info("Total Columns", len(merged_df.columns))
            MatrixStyle.success("Merge complete")
            
            self.logger.info(f"Merged dataframes: {len(merged_df)} total rows")
            
            return merged_df
        
        except Exception as e:
            MatrixStyle.error(f"Merge failed: {str(e)}")
            self.logger.error(f"Merge failed: {str(e)}")
            return None
    
    def handle_duplicates(self, df):
        """Detect and handle duplicate rows, tracking source files"""
        MatrixStyle.section("DUPLICATE DETECTION & SOURCE TRACKING")
        
        # Create row hashes for duplicate detection (excluding source file column)
        MatrixStyle.info("Status", "Creating row hashes...")
        df['_row_hash'] = df.drop(columns=['_source_file']).apply(create_row_hash, axis=1)
        
        # Group by hash to find duplicates and combine source files
        MatrixStyle.info("Status", "Grouping duplicates and combining sources...")
        
        # Create a function to combine source files
        def combine_sources(sources):
            """Combine unique source filenames, sorted alphabetically"""
            unique_sources = sorted(set(sources))
            return '; '.join(unique_sources)
        
        # Group by row hash and aggregate
        grouped = df.groupby('_row_hash').agg({
            '_source_file': combine_sources,
            **{col: 'first' for col in df.columns if col not in ['_row_hash', '_source_file']}
        }).reset_index(drop=True)
        
        # Calculate statistics
        original_count = len(df)
        deduplicated_count = len(grouped)
        self.stats['duplicate_rows'] = original_count - deduplicated_count
        self.stats['unique_rows'] = deduplicated_count
        
        # Count records from multiple sources
        multi_source_mask = grouped['_source_file'].str.contains(';')
        multi_source_count = multi_source_mask.sum()
        self.stats['multi_source_records'] = multi_source_count
        
        MatrixStyle.info("Total Rows Before", f"{original_count:,}")
        MatrixStyle.info("Unique Rows After", f"{deduplicated_count:,}")
        MatrixStyle.info("Duplicate Rows Removed", f"{self.stats['duplicate_rows']:,}")
        MatrixStyle.info("Records from Multiple Files", f"{multi_source_count:,}")
        
        self.logger.info(f"Duplicate detection complete:")
        self.logger.info(f"  Original rows: {original_count:,}")
        self.logger.info(f"  Unique rows: {deduplicated_count:,}")
        self.logger.info(f"  Duplicates removed: {self.stats['duplicate_rows']:,}")
        self.logger.info(f"  Records appearing in multiple files: {multi_source_count:,}")
        
        if self.stats['duplicate_rows'] > 0:
            # Save duplicate analysis to review folder
            timestamp = datetime.now().strftime(Config.DATETIME_FORMAT)
            duplicates_file = os.path.join(
                self.duplicates_dir, 
                f"duplicate_analysis_{timestamp}.csv"
            )
            
            # Create analysis showing which records appeared in multiple files
            multi_source_records = grouped[multi_source_mask].copy()
            
            if len(multi_source_records) > 0:
                multi_source_records.to_csv(duplicates_file, index=False, encoding='utf-8-sig')
                
                MatrixStyle.info("Multi-Source Records Saved", os.path.basename(duplicates_file))
                self.logger.info(f"Saved {len(multi_source_records)} multi-source records to {duplicates_file}")
        
        # Rename source file column to final name
        grouped = grouped.rename(columns={'_source_file': Config.SOURCE_COLUMN_NAME})
        
        MatrixStyle.success(f"Deduplication complete - removed {self.stats['duplicate_rows']:,} duplicates")
        MatrixStyle.success(f"Tracked sources for {multi_source_count:,} records from multiple files")
        
        return grouped
    
    def add_type_column(self, df):
        """Add Type column as first column (Source_File already exists)"""
        MatrixStyle.section("ADDING TYPE COLUMN")
        
        # Insert blank Type column at position 0
        df.insert(0, Config.NEW_COLUMN_NAME, '')
        
        # Move Source_File column to position 1 (right after Type)
        source_col = df.pop(Config.SOURCE_COLUMN_NAME)
        df.insert(1, Config.SOURCE_COLUMN_NAME, source_col)
        
        MatrixStyle.info("Type Column", f"Position 0 (blank)")
        MatrixStyle.info("Source_File Column", f"Position 1 (tracks origin)")
        MatrixStyle.success("Columns organized")
        
        self.logger.info(f"Added '{Config.NEW_COLUMN_NAME}' column at position 0")
        self.logger.info(f"Moved '{Config.SOURCE_COLUMN_NAME}' column to position 1")
        
        return df
    
    def save_output(self, df):
        """Save final merged CSV"""
        MatrixStyle.section("SAVING OUTPUT FILE")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime(Config.DATETIME_FORMAT)
        output_filename = f"{Config.OUTPUT_FILENAME_PREFIX}_{timestamp}.csv"
        output_path = os.path.join(self.source_dir, output_filename)
        
        try:
            # Save CSV
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            MatrixStyle.info("Output File", output_filename)
            MatrixStyle.info("Full Path", output_path)
            MatrixStyle.info("File Size", f"{file_size_mb:.2f} MB")
            MatrixStyle.info("Total Rows", f"{len(df):,}")
            MatrixStyle.info("Total Columns", len(df.columns))
            MatrixStyle.success("File saved successfully")
            
            self.logger.info(f"Saved merged file: {output_path}")
            self.logger.info(f"  Rows: {len(df):,}")
            self.logger.info(f"  Columns: {len(df.columns)}")
            self.logger.info(f"  Size: {file_size_mb:.2f} MB")
            
            return output_path
        
        except Exception as e:
            MatrixStyle.error(f"Failed to save: {str(e)}")
            self.logger.error(f"Failed to save output: {str(e)}")
            return None
    
    def generate_summary_report(self, output_path):
        """Generate detailed summary report"""
        MatrixStyle.section("GENERATING SUMMARY REPORT")
        
        timestamp = datetime.now().strftime(Config.DATETIME_FORMAT)
        report_file = os.path.join(self.logs_dir, f"summary_report_{timestamp}.txt")
        
        # Calculate statistics
        success_rate = (self.stats['files_processed'] / self.stats['files_found'] * 100) if self.stats['files_found'] > 0 else 0
        duplicate_rate = (self.stats['duplicate_rows'] / self.stats['total_rows_read'] * 100) if self.stats['total_rows_read'] > 0 else 0
        
        # Build report
        report_lines = []
        report_lines.append("="*80)
        report_lines.append("CSV MERGER - SUMMARY REPORT")
        report_lines.append("="*80)
        report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Source Directory: {self.source_dir}")
        report_lines.append(f"\n")
        
        report_lines.append("-"*80)
        report_lines.append("FILE PROCESSING SUMMARY")
        report_lines.append("-"*80)
        report_lines.append(f"CSV Files Found:          {self.stats['files_found']}")
        report_lines.append(f"Files Processed:          {self.stats['files_processed']}")
        report_lines.append(f"Files Failed:             {self.stats['files_failed']}")
        report_lines.append(f"Success Rate:             {success_rate:.1f}%")
        report_lines.append(f"Encoding Issues:          {self.stats['encoding_issues']}")
        report_lines.append(f"\n")
        
        report_lines.append("-"*80)
        report_lines.append("DATA SUMMARY")
        report_lines.append("-"*80)
        report_lines.append(f"Total Rows Read:          {self.stats['total_rows_read']:,}")
        report_lines.append(f"Duplicate Rows Found:     {self.stats['duplicate_rows']:,}")
        report_lines.append(f"Unique Rows:              {self.stats['unique_rows']:,}")
        report_lines.append(f"Multi-Source Records:     {self.stats['multi_source_records']:,}")
        report_lines.append(f"Duplicate Rate:           {duplicate_rate:.2f}%")
        report_lines.append(f"\n")
        
        report_lines.append("-"*80)
        report_lines.append("FILE DETAILS")
        report_lines.append("-"*80)
        report_lines.append(f"{'Filename':<40} {'Rows':>10} {'Cols':>6} {'Encoding':<12} {'Status':<10}")
        report_lines.append("-"*80)
        
        for file in self.file_details:
            report_lines.append(
                f"{file['filename']:<40} "
                f"{file['rows']:>10,} "
                f"{file['columns']:>6} "
                f"{file['encoding']:<12} "
                f"{file['status']:<10}"
            )
        
        report_lines.append(f"\n")
        report_lines.append("-"*80)
        report_lines.append("OUTPUT")
        report_lines.append("-"*80)
        if output_path:
            report_lines.append(f"Merged File: {os.path.basename(output_path)}")
            report_lines.append(f"Full Path: {output_path}")
        else:
            report_lines.append("ERROR: No output file created")
        
        if self.stats['duplicate_rows'] > 0:
            report_lines.append(f"\nDuplicates Folder: {self.duplicates_dir}")
        
        report_lines.append(f"\nLog File: {self.log_file}")
        report_lines.append(f"\n")
        report_lines.append("="*80)
        report_lines.append("END OF REPORT")
        report_lines.append("="*80)
        
        # Save report
        report_content = '\n'.join(report_lines)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Print summary to console
        MatrixStyle.info("Report Saved To", os.path.basename(report_file))
        
        print(f"\n{MatrixStyle.GREEN}{report_content}{MatrixStyle.RESET}")
        
        self.logger.info("Summary report generated")
        self.logger.info(report_content)
        
        return report_file
    
    def run(self):
        """Main execution method"""
        start_time = datetime.now()
        
        try:
            # Initialize
            self.initialize()
            
            # Find CSV files
            csv_files = self.find_csv_files()
            if not csv_files:
                return False
            
            # Load all files
            dataframes = self.load_all_files(csv_files)
            if not dataframes:
                MatrixStyle.error("No files loaded successfully")
                return False
            
            # Merge dataframes
            merged_df = self.merge_dataframes(dataframes)
            if merged_df is None:
                return False
            
            # Handle duplicates
            clean_df = self.handle_duplicates(merged_df)
            
            # Add Type column
            final_df = self.add_type_column(clean_df)
            
            # Save output
            output_path = self.save_output(final_df)
            
            # Calculate processing time
            end_time = datetime.now()
            self.stats['processing_time'] = (end_time - start_time).total_seconds()
            
            # Generate summary report
            self.generate_summary_report(output_path)
            
            # Final success message
            MatrixStyle.header("PROCESS COMPLETE")
            MatrixStyle.info("Processing Time", f"{self.stats['processing_time']:.2f} seconds")
            MatrixStyle.info("Status", "SUCCESS")
            
            self.logger.info("="*80)
            self.logger.info(f"Process completed successfully in {self.stats['processing_time']:.2f} seconds")
            self.logger.info("="*80)
            
            return True
        
        except Exception as e:
            MatrixStyle.error(f"CRITICAL ERROR: {str(e)}")
            self.logger.critical(f"Critical error: {str(e)}", exc_info=True)
            return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point"""
    try:
        # Create merger instance
        merger = CSVMerger(Config.SOURCE_DIR)
        
        # Run merge process
        success = merger.run()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        MatrixStyle.warning("\nProcess interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        MatrixStyle.error(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
