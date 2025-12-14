"""
Panjiva Summaries - Cleanup and Analysis Script
================================================
Purpose:
1. Remove duplicate files (with (1), (2), (3) suffixes)
2. Analyze file structure consistency
3. Standardize CSV formatting for workflow development
4. Generate master catalog of available data

Author: Auto-generated
Date: 2025-10-15
"""

import os
import pandas as pd
import glob
import shutil
from datetime import datetime
import hashlib
import json
from pathlib import Path


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    SOURCE_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\panjiva_summaries"
    BACKUP_DIR = "duplicates_backup"
    CLEANED_DIR = "cleaned_files"
    REPORTS_DIR = "analysis_reports"

    # Output files
    CATALOG_FILE = "data_catalog.json"
    SUMMARY_REPORT = "file_analysis_report.txt"
    COLUMN_MAPPING = "column_mapping_reference.csv"

    # Standardization settings
    STANDARD_ENCODING = 'utf-8-sig'
    STANDARD_DELIMITER = ','
    PRESERVE_ORIGINALS = True


# ============================================================================
# STYLING
# ============================================================================

class MatrixStyle:
    GREEN = '\033[92m'
    BRIGHT_GREEN = '\033[1;92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

    @staticmethod
    def header(text):
        width = 80
        print(f"\n{MatrixStyle.BRIGHT_GREEN}{'=' * width}")
        print(f"{text.center(width)}")
        print(f"{'=' * width}{MatrixStyle.RESET}\n")

    @staticmethod
    def section(text):
        print(f"\n{MatrixStyle.GREEN}{'─' * 80}")
        print(f"▶ {text}")
        print(f"{'─' * 80}{MatrixStyle.RESET}")

    @staticmethod
    def info(label, value):
        print(f"{MatrixStyle.GREEN}  ├─ {label:<40} {MatrixStyle.BRIGHT_GREEN}{value}{MatrixStyle.RESET}")

    @staticmethod
    def success(message):
        print(f"{MatrixStyle.BRIGHT_GREEN}  ✓ {message}{MatrixStyle.RESET}")

    @staticmethod
    def warning(message):
        print(f"{MatrixStyle.YELLOW}  ⚠ {message}{MatrixStyle.RESET}")

    @staticmethod
    def error(message):
        print(f"{MatrixStyle.RED}  ✗ {message}{MatrixStyle.RESET}")


# ============================================================================
# FILE UTILITIES
# ============================================================================

def get_file_hash(file_path):
    """Calculate MD5 hash of file content"""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None


def parse_filename(filename):
    """Extract metadata from Panjiva filename"""
    info = {
        'original_name': filename,
        'base_name': filename,
        'is_duplicate': False,
        'duplicate_number': 0,
        'file_type': None,
        'grouping_fields': [],
        'record_range': None,
        'total_records': None,
        'export_date': None
    }

    # Check for duplicate suffix
    if ' (' in filename and ').' in filename:
        info['is_duplicate'] = True
        try:
            num_str = filename.split(' (')[1].split(')')[0]
            info['duplicate_number'] = int(num_str)
            info['base_name'] = filename.split(' (')[0] + filename.split(')')[-1]
        except:
            pass

    # Detect file type
    if filename.lower().endswith('.csv'):
        info['file_type'] = 'csv'
    elif filename.lower().endswith('.xlsx'):
        info['file_type'] = 'xlsx'

    # Extract grouping fields (between "Panjiva-US_Imports-" and "-all-results")
    if 'Panjiva-US_Imports-' in filename and '-all-results' in filename:
        parts = filename.split('Panjiva-US_Imports-')[1].split('-all-results')[0]
        info['grouping_fields'] = parts.split('-')
    elif 'u_s_imports__all_shipments' in filename.lower():
        # Handle alternative naming format
        if 'grouped_by_' in filename.lower():
            group = filename.lower().split('grouped_by_')[1].split('_')[0]
            info['grouping_fields'] = [group]
        else:
            info['grouping_fields'] = ['all_shipments']

    # Extract record counts (e.g., "1_to_100_of_8448")
    if '_to_' in filename and '_of_' in filename:
        try:
            range_part = filename.split('_to_')[1].split('-')[0]
            end_num = range_part.split('_of_')[0].replace('_', '')
            total_num = range_part.split('_of_')[1].replace('_', '')
            info['record_range'] = f"1-{end_num}"
            info['total_records'] = int(total_num)
        except:
            pass

    # Extract date
    import re
    date_pattern = r'(\d{4}-\d{2}-\d{2})'
    date_match = re.search(date_pattern, filename)
    if date_match:
        info['export_date'] = date_match.group(1)

    return info


def ensure_directories(base_dir):
    """Create necessary directories"""
    backup_dir = os.path.join(base_dir, Config.BACKUP_DIR)
    cleaned_dir = os.path.join(base_dir, Config.CLEANED_DIR)
    reports_dir = os.path.join(base_dir, Config.REPORTS_DIR)

    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(cleaned_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    return backup_dir, cleaned_dir, reports_dir


# ============================================================================
# MAIN ANALYZER CLASS
# ============================================================================

class PanjivaAnalyzer:

    def __init__(self, source_dir):
        self.source_dir = source_dir
        self.backup_dir = None
        self.cleaned_dir = None
        self.reports_dir = None

        self.all_files = []
        self.duplicates = []
        self.originals = []
        self.file_metadata = {}
        self.data_catalog = {}

        self.stats = {
            'total_files': 0,
            'duplicate_files': 0,
            'original_files': 0,
            'files_removed': 0,
            'csv_files': 0,
            'xlsx_files': 0,
            'total_size_before': 0,
            'total_size_after': 0
        }

    def initialize(self):
        """Initialize directories and scan files"""
        MatrixStyle.header("PANJIVA SUMMARIES - CLEANUP & ANALYSIS")
        MatrixStyle.section("INITIALIZATION")

        self.backup_dir, self.cleaned_dir, self.reports_dir = ensure_directories(self.source_dir)

        MatrixStyle.info("Source Directory", self.source_dir)
        MatrixStyle.info("Backup Directory", self.backup_dir)
        MatrixStyle.info("Cleaned Directory", self.cleaned_dir)
        MatrixStyle.info("Reports Directory", self.reports_dir)
        MatrixStyle.success("Initialization complete")

    def scan_files(self):
        """Scan and categorize all files"""
        MatrixStyle.section("SCANNING FILES")

        # Get all files
        csv_files = glob.glob(os.path.join(self.source_dir, "*.csv"))
        xlsx_files = glob.glob(os.path.join(self.source_dir, "*.xlsx"))
        self.all_files = csv_files + xlsx_files

        self.stats['total_files'] = len(self.all_files)
        self.stats['csv_files'] = len(csv_files)
        self.stats['xlsx_files'] = len(xlsx_files)

        MatrixStyle.info("Total Files Found", self.stats['total_files'])
        MatrixStyle.info("CSV Files", self.stats['csv_files'])
        MatrixStyle.info("Excel Files", self.stats['xlsx_files'])

        # Calculate total size
        for file_path in self.all_files:
            try:
                self.stats['total_size_before'] += os.path.getsize(file_path)
            except:
                pass

        size_mb = self.stats['total_size_before'] / (1024 * 1024)
        MatrixStyle.info("Total Size", f"{size_mb:.2f} MB")

        # Parse filenames
        for file_path in self.all_files:
            filename = os.path.basename(file_path)
            info = parse_filename(filename)
            info['full_path'] = file_path
            info['file_size'] = os.path.getsize(file_path)
            info['file_hash'] = get_file_hash(file_path)

            self.file_metadata[filename] = info

            if info['is_duplicate']:
                self.duplicates.append(file_path)
                self.stats['duplicate_files'] += 1
            else:
                self.originals.append(file_path)
                self.stats['original_files'] += 1

        MatrixStyle.info("Original Files", self.stats['original_files'])
        MatrixStyle.info("Duplicate Files (with suffixes)", self.stats['duplicate_files'])
        MatrixStyle.success("File scan complete")

    def identify_true_duplicates(self):
        """Identify files that are actual content duplicates"""
        MatrixStyle.section("IDENTIFYING TRUE DUPLICATES")

        # Group files by base name
        base_groups = {}
        for file_path in self.all_files:
            filename = os.path.basename(file_path)
            info = self.file_metadata[filename]
            base_name = info['base_name']

            if base_name not in base_groups:
                base_groups[base_name] = []
            base_groups[base_name].append(file_path)

        # Check hash matches within groups
        true_duplicates = []

        for base_name, files in base_groups.items():
            if len(files) > 1:
                # Get hashes
                hashes = {}
                for file_path in files:
                    filename = os.path.basename(file_path)
                    file_hash = self.file_metadata[filename]['file_hash']
                    if file_hash:
                        if file_hash not in hashes:
                            hashes[file_hash] = []
                        hashes[file_hash].append(file_path)

                # If all have same hash, they're true duplicates
                if len(hashes) == 1:
                    # Keep original, mark others as duplicates
                    files_sorted = sorted(files,
                                          key=lambda x: self.file_metadata[os.path.basename(x)]['duplicate_number'])
                    keep_file = files_sorted[0]
                    remove_files = files_sorted[1:]

                    for dup in remove_files:
                        true_duplicates.append(dup)

                    MatrixStyle.info(f"Duplicate Set",
                                     f"{os.path.basename(keep_file)} → {len(remove_files)} duplicates")

        self.duplicates = true_duplicates
        self.stats['files_removed'] = len(true_duplicates)

        MatrixStyle.success(f"Identified {len(true_duplicates)} true duplicates to remove")

    def backup_and_remove_duplicates(self):
        """Backup duplicates and remove them"""
        MatrixStyle.section("REMOVING DUPLICATES")

        if not self.duplicates:
            MatrixStyle.info("Status", "No duplicates to remove")
            return

        for file_path in self.duplicates:
            filename = os.path.basename(file_path)
            backup_path = os.path.join(self.backup_dir, filename)

            try:
                # Backup
                shutil.copy2(file_path, backup_path)

                # Remove original
                os.remove(file_path)

                MatrixStyle.info("Removed", filename)
            except Exception as e:
                MatrixStyle.error(f"Failed to remove {filename}: {e}")

        MatrixStyle.success(f"Removed {len(self.duplicates)} duplicate files")
        MatrixStyle.info("Backups saved to", self.backup_dir)

    def analyze_file_structures(self):
        """Analyze remaining files for structure consistency"""
        MatrixStyle.section("ANALYZING FILE STRUCTURES")

        # Get remaining files
        remaining_files = [f for f in self.all_files if f not in self.duplicates]

        structure_analysis = {}

        for file_path in remaining_files:
            filename = os.path.basename(file_path)
            info = self.file_metadata[filename]

            try:
                # Read file
                if info['file_type'] == 'csv':
                    df = pd.read_csv(file_path, nrows=5)
                elif info['file_type'] == 'xlsx':
                    df = pd.read_excel(file_path, nrows=5)
                else:
                    continue

                # Analyze structure
                structure = {
                    'filename': filename,
                    'grouping': '-'.join(info['grouping_fields']),
                    'columns': list(df.columns),
                    'num_columns': len(df.columns),
                    'column_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
                    'sample_row': df.iloc[0].to_dict() if len(df) > 0 else {},
                    'has_nulls': df.isnull().any().to_dict(),
                    'total_records': info['total_records']
                }

                structure_analysis[filename] = structure

                MatrixStyle.info(f"Analyzed", f"{filename} → {structure['num_columns']} columns")

            except Exception as e:
                MatrixStyle.warning(f"Could not analyze {filename}: {e}")

        self.data_catalog = structure_analysis
        MatrixStyle.success(f"Analyzed {len(structure_analysis)} files")

    def generate_column_mapping_reference(self):
        """Create reference document showing all columns across files"""
        MatrixStyle.section("GENERATING COLUMN MAPPING REFERENCE")

        all_columns = set()
        column_occurrences = {}

        for filename, structure in self.data_catalog.items():
            for col in structure['columns']:
                all_columns.add(col)
                if col not in column_occurrences:
                    column_occurrences[col] = []
                column_occurrences[col].append(filename)

        # Create mapping dataframe
        mapping_data = []
        for col in sorted(all_columns):
            mapping_data.append({
                'Column Name': col,
                'Appears In Files': len(column_occurrences[col]),
                'Sample Files': ', '.join(column_occurrences[col][:3]),
                'Match Group ID': f"MG-{hash(col) % 1000:03d}",
                'Semantic Group': self._infer_semantic_group(col)
            })

        mapping_df = pd.DataFrame(mapping_data)

        output_path = os.path.join(self.reports_dir, Config.COLUMN_MAPPING)
        mapping_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        MatrixStyle.info("Unique Columns Found", len(all_columns))
        MatrixStyle.info("Mapping File Saved", Config.COLUMN_MAPPING)
        MatrixStyle.success("Column mapping reference generated")

    def _infer_semantic_group(self, column_name):
        """Infer semantic group from column name"""
        col_lower = column_name.lower()

        if 'consignee' in col_lower or 'buyer' in col_lower:
            return 'ENTITY_BUYER'
        elif 'shipper' in col_lower or 'seller' in col_lower:
            return 'ENTITY_SHIPPER'
        elif 'vessel' in col_lower or 'ship' in col_lower:
            return 'VESSEL'
        elif 'port' in col_lower:
            return 'PORT'
        elif 'carrier' in col_lower or 'scac' in col_lower:
            return 'CARRIER'
        elif 'date' in col_lower or 'arrival' in col_lower:
            return 'DATE'
        elif 'weight' in col_lower or 'quantity' in col_lower:
            return 'MEASUREMENT'
        elif 'value' in col_lower or 'usd' in col_lower:
            return 'VALUE'
        elif 'hs' in col_lower or 'code' in col_lower:
            return 'CLASSIFICATION'
        elif 'industry' in col_lower or 'gics' in col_lower:
            return 'INDUSTRY'
        else:
            return 'OTHER'

    def generate_data_catalog(self):
        """Generate master data catalog JSON"""
        MatrixStyle.section("GENERATING DATA CATALOG")

        catalog = {
            'generated_date': datetime.now().isoformat(),
            'source_directory': self.source_dir,
            'statistics': self.stats,
            'files': self.data_catalog,
            'grouping_patterns': self._analyze_grouping_patterns()
        }

        output_path = os.path.join(self.reports_dir, Config.CATALOG_FILE)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

        MatrixStyle.info("Catalog File Saved", Config.CATALOG_FILE)
        MatrixStyle.success("Data catalog generated")

    def _analyze_grouping_patterns(self):
        """Analyze what grouping dimensions are available"""
        patterns = {}

        for filename, structure in self.data_catalog.items():
            grouping = structure['grouping']
            if grouping not in patterns:
                patterns[grouping] = {
                    'files': [],
                    'total_records': 0,
                    'common_columns': []
                }

            patterns[grouping]['files'].append(filename)
            patterns[grouping]['total_records'] += structure.get('total_records', 0) or 0

        return patterns

    def generate_summary_report(self):
        """Generate comprehensive text report"""
        MatrixStyle.section("GENERATING SUMMARY REPORT")

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PANJIVA SUMMARIES - ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Source Directory: {self.source_dir}\n")

        report_lines.append("-" * 80)
        report_lines.append("FILE CLEANUP SUMMARY")
        report_lines.append("-" * 80)
        report_lines.append(f"Total Files (before):     {self.stats['total_files']}")
        report_lines.append(f"Original Files:           {self.stats['original_files']}")
        report_lines.append(f"Duplicate Files Removed:  {self.stats['files_removed']}")
        report_lines.append(f"Files Remaining:          {self.stats['original_files']}")
        report_lines.append(f"\nSize Before:              {self.stats['total_size_before'] / (1024 * 1024):.2f} MB")
        report_lines.append(
            f"Estimated Size After:     {(self.stats['total_size_before'] - sum(self.file_metadata[os.path.basename(f)]['file_size'] for f in self.duplicates)) / (1024 * 1024):.2f} MB")
        report_lines.append("")

        report_lines.append("-" * 80)
        report_lines.append("FILE TYPES")
        report_lines.append("-" * 80)
        report_lines.append(f"CSV Files:                {self.stats['csv_files']}")
        report_lines.append(f"Excel Files:              {self.stats['xlsx_files']}")
        report_lines.append("")

        report_lines.append("-" * 80)
        report_lines.append("AVAILABLE DATA GROUPINGS")
        report_lines.append("-" * 80)

        groupings = self._analyze_grouping_patterns()
        for grouping, info in sorted(groupings.items()):
            report_lines.append(f"\n{grouping}:")
            report_lines.append(f"  Files: {len(info['files'])}")
            report_lines.append(f"  Total Records: {info['total_records']:,}")
            for f in info['files']:
                report_lines.append(f"    - {f}")

        report_lines.append("\n" + "-" * 80)
        report_lines.append("RECOMMENDATIONS FOR WORKFLOW DEVELOPMENT")
        report_lines.append("-" * 80)
        report_lines.append("""
1. PRIMARY DATASET:
   - Use: Panjiva-US_Imports-all-results_1_to_4629_of_4629-2025-10-10-02-33.csv
   - Contains: All shipment records (4,629 rows)
   - This is your baseline dataset (DS-001)

2. DIMENSIONAL DATASETS (for enrichment):
   - Vessel summaries: 4,424 unique vessels
   - Port analysis: Origin/Destination combinations
   - Entity relationships: Consignee-Shipper pairs
   - Industry classification: GICS codes
   - Product codes: HS Code hierarchies

3. WORKFLOW INTEGRATION:
   - Map all summary files to Match Groups (see column_mapping_reference.csv)
   - Use vessel/entity/port summaries for validation/enrichment
   - Build dimension tables from grouping files
   - Create fact table from all-shipments file

4. NEXT STEPS:
   - Review column_mapping_reference.csv for semantic groups
   - Check data_catalog.json for detailed structure
   - Apply normalization scripts from your framework
   - Build ETL pipeline using Match Group IDs
        """)

        report_lines.append("\n" + "=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)

        report_content = '\n'.join(report_lines)

        output_path = os.path.join(self.reports_dir, Config.SUMMARY_REPORT)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"\n{MatrixStyle.GREEN}{report_content}{MatrixStyle.RESET}")

        MatrixStyle.info("Summary Report Saved", Config.SUMMARY_REPORT)
        MatrixStyle.success("Summary report generated")

    def run(self):
        """Main execution"""
        start_time = datetime.now()

        try:
            self.initialize()
            self.scan_files()
            self.identify_true_duplicates()
            self.backup_and_remove_duplicates()
            self.analyze_file_structures()
            self.generate_column_mapping_reference()
            self.generate_data_catalog()
            self.generate_summary_report()

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            MatrixStyle.header("PROCESS COMPLETE")
            MatrixStyle.info("Processing Time", f"{processing_time:.2f} seconds")
            MatrixStyle.info("Status", "SUCCESS ✓")
            MatrixStyle.info("Reports Location", self.reports_dir)

            return True

        except Exception as e:
            MatrixStyle.error(f"CRITICAL ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    try:
        analyzer = PanjivaAnalyzer(Config.SOURCE_DIR)
        success = analyzer.run()
        return 0 if success else 1

    except KeyboardInterrupt:
        MatrixStyle.warning("\nProcess interrupted by user")
        return 1

    except Exception as e:
        MatrixStyle.error(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())