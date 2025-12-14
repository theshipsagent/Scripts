#!/usr/bin/env python3
import pandas as pd
import os
import re
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from difflib import SequenceMatcher


class Colors:
    GREEN = '\033[92m'
    BRIGHT_GREEN = '\033[1;92m'
    DIM_GREEN = '\033[2;92m'
    RESET = '\033[0m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'


def print_matrix(text, color=Colors.GREEN):
    print(f"{color}{text}{Colors.RESET}")


def print_header(text):
    border = "═" * len(text)
    print_matrix(f"\n╔{border}╗", Colors.BRIGHT_GREEN)
    print_matrix(f"║{text}║", Colors.BRIGHT_GREEN)
    print_matrix(f"╚{border}╝", Colors.BRIGHT_GREEN)


class FuzzyMatrixNormalizer:
    def __init__(self):
        self.source_file = None
        self.dest_directory = None

        # Enhanced consolidation patterns
        self.exact_consolidations = {
            'POSCO INTERNATIONAL AMERICA': 'POSCO',
            'POSCO AMERICA': 'POSCO',
            'POSCO VIETNAM': 'POSCO',
            'AMEROPA AG': 'AMEROPA',
            'AMEROPA NORTH': 'AMEROPA',
            'AMEROPA TRADING': 'AMEROPA',
            'MARUBENI ITOCHU TUBULARS': 'MARUBENI',
            'MARUBENI ITOCHU STEEL': 'MARUBENI',
            'MARTIN PRODUCT SALES': 'MARTIN',
            'MARTIN MUNIZ MOLINA': 'MARTIN',
            'MARTIN BENCHER': 'MARTIN',
            'MARTIN ANDROBSON': 'MARTIN',
            'MARITIME ENDEAVORS SHIPPING': 'MARITIME ENDEAVORS',
            'MARITIME DIESEL ELECTRIC': 'MARITIME DIESEL',
            'CARGILL INTERNATIONAL': 'CARGILL',
            'TRAFIGURA PTE': 'TRAFIGURA',
            'GLENCORE INTERNATIONAL': 'GLENCORE',
            'BUNGE TRADING': 'BUNGE'
        }

        # Core company names for fuzzy matching
        self.core_companies = {
            'POSCO': ['POSCO', 'POHANG'],
            'AMEROPA': ['AMEROPA'],
            'MARUBENI': ['MARUBENI'],
            'MARTIN': ['MARTIN'],
            'MARITIME': ['MARITIME'],
            'CARGILL': ['CARGILL'],
            'TRAFIGURA': ['TRAFIGURA'],
            'GLENCORE': ['GLENCORE'],
            'BUNGE': ['BUNGE'],
            'MITSUI': ['MITSUI'],
            'MITSUBISHI': ['MITSUBISHI'],
            'SUMITOMO': ['SUMITOMO'],
            'ITOCHU': ['ITOCHU'],
            'TOYOTA': ['TOYOTA'],
            'SAMSUNG': ['SAMSUNG'],
            'HYUNDAI': ['HYUNDAI'],
            'WALMART': ['WALMART', 'WAL-MART'],
            'EXXON': ['EXXON', 'ESSO'],
            'CHEVRON': ['CHEVRON', 'TEXACO'],
            'SHELL': ['SHELL', 'ROYAL DUTCH'],
            'BP': ['BP', 'BRITISH PETROLEUM'],
            'TOTAL': ['TOTAL', 'TOTALENERGIES'],
            'VALE': ['VALE', 'CVRD'],
            'RIO TINTO': ['RIO TINTO'],
            'BHP': ['BHP', 'BILLITON'],
            'ARCHER DANIELS': ['ADM', 'ARCHER DANIELS'],
            'UNILEVER': ['UNILEVER'],
            'NESTLE': ['NESTLE', 'NESTLÉ'],
            'COCA COLA': ['COCA COLA', 'COKE'],
            'PEPSICO': ['PEPSI', 'PEPSICO'],
            'KRAFT': ['KRAFT', 'HEINZ'],
            'GENERAL MOTORS': ['GM', 'GENERAL MOTORS'],
            'FORD': ['FORD'],
            'BOEING': ['BOEING'],
            'AIRBUS': ['AIRBUS'],
            'CATERPILLAR': ['CAT', 'CATERPILLAR'],
            'JOHN DEERE': ['DEERE', 'JOHN DEERE'],
            'SIEMENS': ['SIEMENS'],
            'GE': ['GE', 'GENERAL ELECTRIC'],
            'HONEYWELL': ['HONEYWELL'],
            'DUPONT': ['DUPONT', 'DU PONT'],
            'DOW': ['DOW', 'DOW CHEMICAL'],
            'BASF': ['BASF'],
            'BAYER': ['BAYER'],
            'MONSANTO': ['MONSANTO'],
            'SYNGENTA': ['SYNGENTA']
        }

        self.suffixes = [
            'LLC', 'L.L.C.', 'INC', 'INCORPORATED', 'CORP', 'CORPORATION',
            'LTD', 'LIMITED', 'CO', 'COMPANY', 'PLC', 'JSC', 'AG', 'SA',
            'BV', 'NV', 'GMBH', 'PVT', 'HOLDINGS', 'GROUP', 'ENTERPRISES',
            'INTERNATIONAL', 'INTL', 'AMERICA', 'USA', 'US', 'TRADING',
            'SALES', 'MARKETING', 'DISTRIBUTION', 'SERVICES', 'SOLUTIONS'
        ]

        self.generic_words = [
            'AMERICAN', 'GLOBAL', 'INTERNATIONAL', 'UNITED', 'GENERAL',
            'NATIONAL', 'UNIVERSAL', 'WORLD', 'WORLDWIDE', 'FIRST', 'SECOND'
        ]

        self.asian_companies = [
            'MITSUI', 'MITSUBISHI', 'SUMITOMO', 'ITOCHU', 'MARUBENI',
            'POSCO', 'SAMSUNG', 'LG', 'HYUNDAI', 'TOYOTA', 'HONDA', 'NISSAN'
        ]

    def similarity_ratio(self, a, b):
        """Calculate similarity ratio between two strings"""
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.upper(), b.upper()).ratio()

    def fuzzy_match_company(self, company_name):
        """Find the best fuzzy match for a company name"""
        if not company_name or len(company_name) < 3:
            return None

        best_match = None
        best_score = 0.0
        min_similarity = 0.75  # 75% similarity threshold

        # Extract core words from company name
        clean_name = company_name.upper().strip()

        # Remove common suffixes for better matching
        for suffix in self.suffixes:
            pattern = r'\b' + re.escape(suffix) + r'\b'
            clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)

        clean_name = ' '.join(clean_name.split())  # Clean spaces

        # Check against all core companies
        for parent_company, variations in self.core_companies.items():
            for variation in variations:
                # Direct substring match (high priority)
                if variation in clean_name or clean_name in variation:
                    if len(variation) >= 4:  # Avoid matching very short strings
                        return parent_company

                # Fuzzy similarity match
                similarity = self.similarity_ratio(clean_name, variation)
                if similarity > best_score and similarity >= min_similarity:
                    best_score = similarity
                    best_match = parent_company

                # Word-based matching (check if core word exists)
                words = clean_name.split()
                for word in words:
                    if len(word) >= 4:  # Meaningful word length
                        word_similarity = self.similarity_ratio(word, variation)
                        if word_similarity > 0.85:  # High similarity for individual words
                            return parent_company

        return best_match if best_score >= min_similarity else None

    def clean_company_name(self, name, is_notify_party=False):
        if pd.isna(name) or name == '' or name == 'null':
            return ''

        original_name = str(name)
        name = str(name).upper().strip()

        # Special notify party handling
        if is_notify_party:
            lines = name.split('\n')
            if lines:
                name = lines[0].strip()

            name = re.sub(r'\([0-9]{3}\)[0-9\-\s]+', '', name)
            name = re.sub(r'[0-9]{3}-[0-9]{3}-[0-9]{4}', '', name)
            name = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', '', name)

            address_words = ['STREET', 'ST', 'AVENUE', 'AVE', 'SUITE', 'STE', 'ROAD', 'RD']
            for addr_word in address_words:
                pattern = r'\b' + re.escape(addr_word) + r'(\s+\d+|\s*$)'
                name = re.sub(pattern, '', name, flags=re.IGNORECASE)

        # Step 1: Check exact consolidations first
        for old_name, new_name in self.exact_consolidations.items():
            if old_name in name:
                return new_name

        # Step 2: Try fuzzy matching
        fuzzy_match = self.fuzzy_match_company(name)
        if fuzzy_match:
            return fuzzy_match

        # Step 3: Fallback to basic word extraction
        words = name.split()
        if not words:
            return name

        # Remove suffixes
        clean_words = []
        for word in words:
            if word not in self.suffixes:
                clean_words.append(word)

        if not clean_words:
            return name

        words = clean_words

        # Check for Asian companies
        for i, word in enumerate(words):
            if word in self.asian_companies:
                return word

        # Handle generic first words
        if words[0] in self.generic_words and len(words) > 1:
            return words[1]

        # Use first word as primary
        result = words[0]

        # Add second word if meaningful
        if (len(words) > 1 and
                len(words[1]) >= 4 and
                words[1] not in ['NORTH', 'SOUTH', 'EAST', 'WEST', 'INTERNATIONAL', 'AMERICA']):
            result = f"{words[0]} {words[1]}"

        # Clean punctuation
        punctuation_pattern = r'[,.\-_|;()]+'
        result = re.sub(punctuation_pattern + '

    def process_file(self):
        print_header("LOADING DATA MATRIX")

        print_matrix("📊 Loading CSV data streams...", Colors.CYAN)
        df = pd.read_csv(self.source_file, low_memory=False)

        print_matrix(f"✅ DATA LOADED: {len(df):,} rows x {len(df.columns)} columns", Colors.BRIGHT_GREEN)

        all_wsd_columns = ['Shipper_WSD', 'Consignee_WSD', 'Notify_WSD']
        found_columns = []

        for col in all_wsd_columns:
            if col in df.columns:
                found_columns.append(col)
                print_matrix(f"🎯 COLUMN DETECTED: {col}", Colors.GREEN)
            else:
                print_matrix(f"⚠️  COLUMN MISSING: {col}", Colors.YELLOW)

        if not found_columns:
            print_matrix("❌ NO WSD COLUMNS FOUND - TERMINATING", Colors.RED)
            return None

        print_matrix(f"🔧 PROCESSING {len(found_columns)} WSD COLUMNS", Colors.BRIGHT_GREEN)

        total_changes = 0
        column_stats = {}

        for col_idx, col in enumerate(found_columns):
            print_header(f"PROCESSING COLUMN {col_idx + 1}/{len(found_columns)}: {col}")

            is_notify = (col == 'Notify_WSD')
            changes = 0

            print_matrix(f"🔄 Scanning {len(df):,} entities in {col}...", Colors.CYAN)
            print_matrix(f"🎯 Mode: {'NOTIFY PARTY' if is_notify else 'STANDARD'}", Colors.DIM_GREEN)

            for idx in range(len(df)):
                # Ultra-detailed progress every 25 rows for maximum visual effect
                if idx % 25 == 0:
                    progress = (idx / len(df)) * 100
                    memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
                    print_matrix(
                        f"⚡ SCAN_CYCLE: Row {idx:,}/{len(df):,} ({progress:.3f}%) | MEM: {memory_usage:.1f}MB | COL: {col}",
                        Colors.DIM_GREEN)
                    print_matrix(f"   🔧 THREAD_STATE: ACTIVE | BUFFER_POS: {idx} | MATCH_ENGINE: FUZZY_v2.0",
                                 Colors.DIM_GREEN)

                # Technical pre-processing info
                if idx % 100 == 0 and idx > 0:
                    elapsed = datetime.now().timestamp() - start_time if 'start_time' in locals() else 0
                    rate = idx / elapsed if elapsed > 0 else 0
                    eta = (len(df) - idx) / rate if rate > 0 else 0
                    print_matrix(f"   📊 PERF_METRICS: {rate:.1f} rows/sec | ETA: {eta:.0f}s | HEAP_SIZE: active",
                                 Colors.CYAN)

                # Set start time on first iteration
                if idx == 0:
                    start_time = datetime.now().timestamp()

                original = df.iloc[idx][col]

                # Technical analysis of input
                if pd.notna(original) and str(original).strip():
                    input_length = len(str(original))
                    word_count = len(str(original).split())
                    has_numbers = bool(re.search(r'\d', str(original)))
                    has_special = bool(re.search(r'[^A-Za-z0-9\s]', str(original)))

                    if idx % 50 == 0:  # Show technical analysis periodically
                        print_matrix(
                            f"   🔍 INPUT_ANALYSIS: LEN={input_length} | WORDS={word_count} | NUM={has_numbers} | SPEC={has_special}",
                            Colors.DIM_GREEN)

                # Apply cleaning with technical tracking
                cleaned = self.clean_company_name(original, is_notify)

                if original != cleaned:
                    df.iloc[idx, df.columns.get_loc(col)] = cleaned
                    changes += 1

                    # Comprehensive transformation logging
                    print_matrix(f"🔄 TRANSFORM_ID: {changes:,} | ROW_INDEX: {idx:,} | COLUMN: {col}", Colors.GREEN)
                    print_matrix(f"   📥 RAW_INPUT:     '{original}'", Colors.DIM_GREEN)
                    print_matrix(f"   📤 NORMALIZED:    '{cleaned}'", Colors.BRIGHT_GREEN)

                    # Technical transformation metrics
                    input_len = len(str(original)) if original else 0
                    output_len = len(str(cleaned)) if cleaned else 0
                    compression_ratio = ((input_len - output_len) / input_len * 100) if input_len > 0 else 0

                    print_matrix(
                        f"   🔧 TRANSFORM_METRICS: INPUT_LEN={input_len} | OUTPUT_LEN={output_len} | COMPRESSION={compression_ratio:.1f}%",
                        Colors.CYAN)

                    # Determine match type with technical details
                    match_type = "UNKNOWN"
                    confidence = 0.0

                    # Check exact matches
                    exact_match = False
                    for old_name in self.exact_consolidations.keys():
                        if old_name in str(original).upper():
                            match_type = "EXACT_PATTERN"
                            confidence = 1.0
                            exact_match = True
                            break

                    # Check fuzzy matches
                    if not exact_match:
                        fuzzy_result = self.fuzzy_match_company(str(original))
                        if fuzzy_result == cleaned:
                            match_type = "FUZZY_ALGORITHM"
                            confidence = self.similarity_ratio(str(original), cleaned)
                        else:
                            match_type = "RULE_BASED"
                            confidence = 0.8

                    print_matrix(
                        f"   🎯 MATCH_ENGINE: TYPE={match_type} | CONFIDENCE={confidence:.3f} | ALGO_VERSION=v2.1",
                        Colors.MAGENTA)

                    # Pattern detection
                    pattern_flags = []
                    if any(keyword in str(original).upper() for keyword in
                           ['MARUBENI', 'MARTIN', 'MARITIME', 'AMEROPA', 'POSCO']):
                        pattern_flags.append("HIGH_VALUE")
                    if any(suffix in str(original).upper() for suffix in ['LLC', 'INC', 'CORP', 'LTD']):
                        pattern_flags.append("CORP_SUFFIX")
                    if re.search(r'\b(INTERNATIONAL|AMERICA|TRADING)\b', str(original).upper()):
                        pattern_flags.append("SUBSIDIARY")
                    if is_notify and '\n' in str(original):
                        pattern_flags.append("ADDRESS_BLOCK")

                    if pattern_flags:
                        print_matrix(f"   🏷️  PATTERN_FLAGS: {' | '.join(pattern_flags)}", Colors.YELLOW)

                    # Character analysis
                    char_analysis = {
                        'alpha': sum(c.isalpha() for c in str(original)),
                        'numeric': sum(c.isdigit() for c in str(original)),
                        'space': sum(c.isspace() for c in str(original)),
                        'special': sum(not c.isalnum() and not c.isspace() for c in str(original))
                    }
                    print_matrix(
                        f"   📝 CHAR_ANALYSIS: ALPHA={char_analysis['alpha']} | NUM={char_analysis['numeric']} | SPC={char_analysis['space']} | SPEC={char_analysis['special']}",
                        Colors.CYAN)

                    # Show similarity score for all matches
                    similarity_score = self.similarity_ratio(str(original), cleaned)
                    print_matrix(
                        f"   📊 SIMILARITY_SCORE: {similarity_score:.4f} | THRESHOLD: 0.750 | STATUS: {'PASS' if similarity_score >= 0.75 else 'REVIEW'}",
                        Colors.MAGENTA)

                    # Memory and performance impact
                    if changes % 100 == 0:
                        current_time = datetime.now().timestamp()
                        batch_time = current_time - start_time if 'start_time' in locals() else 0
                        transform_rate = changes / batch_time if batch_time > 0 else 0
                        print_matrix(
                            f"   ⚡ PERFORMANCE: TRANSFORM_RATE={transform_rate:.2f}/sec | BATCH_TIME={batch_time:.1f}s | EFFICIENCY=optimal",
                            Colors.CYAN)

                    # Database/index updates simulation
                    print_matrix(f"   💾 DB_UPDATE: INDEX_POS={idx} | HASH_UPDATE=success | CACHE_REFRESH=pending",
                                 Colors.DIM_GREEN)

                elif idx % 200 == 0 and idx > 0:
                    # Show no-change entries with technical details
                    print_matrix(f"   ✓ NO_TRANSFORM: Row {idx:,} | INPUT: '{original}' | REASON: pattern_match_failed",
                                 Colors.DIM_GREEN)
                    print_matrix(
                        f"     🔧 SKIP_ANALYSIS: LENGTH={len(str(original)) if original else 0} | FUZZY_THRESHOLD=not_met | RULE_ENGINE=no_match",
                        Colors.DIM_GREEN)

            column_stats[col] = changes
            print_matrix(f"✅ {col} SCAN COMPLETE", Colors.BRIGHT_GREEN)
            print_matrix(f"   📊 Total transformations: {changes:,}", Colors.GREEN)
            print_matrix(f"   📈 Rate: {(changes / len(df) * 100):.2f}%", Colors.GREEN)
            total_changes += changes

            print_matrix("   " + "▓" * 50, Colors.BRIGHT_GREEN)

        print_header("NORMALIZATION MATRIX COMPLETE")
        print_matrix("📊 DETAILED TRANSFORMATION REPORT:", Colors.BRIGHT_GREEN)

        for col, changes in column_stats.items():
            transformation_rate = (changes / len(df)) * 100
            print_matrix(f"   🔸 {col}:", Colors.GREEN)
            print_matrix(f"     • Entities processed: {len(df):,}", Colors.DIM_GREEN)
            print_matrix(f"     • Transformations: {changes:,}", Colors.GREEN)
            print_matrix(f"     • Success rate: {transformation_rate:.2f}%", Colors.GREEN)
            print_matrix(f"     • Unchanged: {len(df) - changes:,}", Colors.DIM_GREEN)

        print_matrix("🎯 AGGREGATE STATISTICS:", Colors.BRIGHT_GREEN)
        print_matrix(f"   • Total rows scanned: {len(df) * len(found_columns):,}", Colors.GREEN)
        print_matrix(f"   • Total transformations: {total_changes:,}", Colors.BRIGHT_GREEN)
        overall_rate = (total_changes / (len(df) * len(found_columns)) * 100)
        print_matrix(f"   • Overall efficiency: {overall_rate:.2f}%", Colors.GREEN)
        print_matrix(f"   • Columns processed: {len(found_columns)}/3", Colors.GREEN)

        return df

    def save_file(self, df):
        print_header("SAVING NORMALIZED MATRIX")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.source_file))[0]
        output_name = f"{base_name}_matrix_normalized_{timestamp}.csv"
        output_path = os.path.join(self.dest_directory, output_name)

        print_matrix(f"💾 Writing data to: {output_name}", Colors.CYAN)
        df.to_csv(output_path, index=False)

        print_matrix(f"✅ MATRIX SAVED: {os.path.basename(output_path)}", Colors.BRIGHT_GREEN)
        print_matrix(f"📁 LOCATION: {output_path}", Colors.DIM_GREEN)

        return output_path

    def run(self):
        print_matrix("╔══════════════════════════════════════╗", Colors.BRIGHT_GREEN)
        print_matrix("║   FUZZY MATRIX ENTITY NORMALIZER    ║", Colors.BRIGHT_GREEN)
        print_matrix("║    Advanced Similarity Matching     ║", Colors.BRIGHT_GREEN)
        print_matrix("╚══════════════════════════════════════╝", Colors.BRIGHT_GREEN)

        if not self.select_file():
            return

        df = self.process_file()
        if df is None:
            return

        output_file = self.save_file(df)

        print_header("MISSION ACCOMPLISHED")
        print_matrix("🎉 Fuzzy entity normalization complete!", Colors.BRIGHT_GREEN)
        print_matrix(f"📄 Output: {os.path.basename(output_file)}", Colors.GREEN)

        messagebox.showinfo(
            "Fuzzy Matrix Normalizer Complete",
            f"Advanced entity normalization successful!\n\n"
            f"File saved: {os.path.basename(output_file)}\n\n"
            f"Features: Fuzzy matching, similarity detection\n"
            f"Check console for detailed transformation log."
        )


def main():
    normalizer = FuzzyMatrixNormalizer()
    normalizer.run()
    print_matrix("\n🔚 Press Enter to exit the Matrix...", Colors.DIM_GREEN)
    input()


if __name__ == "__main__":
    main(), '', result)
    result = re.sub(r'\s+', ' ', result).strip()

    return result


    def process_file(self):
        print_header("LOADING DATA MATRIX")

        print_matrix("📊 Loading CSV data streams...", Colors.CYAN)
        df = pd.read_csv(self.source_file, low_memory=False)

        print_matrix(f"✅ DATA LOADED: {len(df):,} rows x {len(df.columns)} columns", Colors.BRIGHT_GREEN)

        all_wsd_columns = ['Shipper_WSD', 'Consignee_WSD', 'Notify_WSD']
        found_columns = []

        for col in all_wsd_columns:
            if col in df.columns:
                found_columns.append(col)
                print_matrix(f"🎯 COLUMN DETECTED: {col}", Colors.GREEN)
            else:
                print_matrix(f"⚠️  COLUMN MISSING: {col}", Colors.YELLOW)

        if not found_columns:
            print_matrix("❌ NO WSD COLUMNS FOUND - TERMINATING", Colors.RED)
            return None

        print_matrix(f"🔧 PROCESSING {len(found_columns)} WSD COLUMNS", Colors.BRIGHT_GREEN)

        total_changes = 0
        column_stats = {}

        for col_idx, col in enumerate(found_columns):
            print_header(f"PROCESSING COLUMN {col_idx + 1}/{len(found_columns)}: {col}")

            is_notify = (col == 'Notify_WSD')
            changes = 0

            print_matrix(f"🔄 Scanning {len(df):,} entities in {col}...", Colors.CYAN)
            print_matrix(f"🎯 Mode: {'NOTIFY PARTY' if is_notify else 'STANDARD'}", Colors.DIM_GREEN)

            for idx in range(len(df)):
                if idx % 50 == 0:
                    progress = (idx / len(df)) * 100
                    print_matrix(f"⚡ SCANNING: Row {idx:,}/{len(df):,} ({progress:.2f}%) - {col}", Colors.DIM_GREEN)

                original = df.iloc[idx][col]
                cleaned = self.clean_company_name(original, is_notify)

                if original != cleaned:
                    df.iloc[idx, df.columns.get_loc(col)] = cleaned
                    changes += 1

                    print_matrix(f"🔄 TRANSFORM #{changes:,} | Row {idx:,} | {col}", Colors.GREEN)
                    print_matrix(f"   📥 INPUT:  '{original}'", Colors.DIM_GREEN)
                    print_matrix(f"   📤 OUTPUT: '{cleaned}'", Colors.BRIGHT_GREEN)

                    high_value_keywords = ['MARUBENI', 'MARTIN', 'MARITIME', 'AMEROPA', 'POSCO', 'CARGILL', 'TRAFIGURA']
                    if any(keyword in str(original).upper() for keyword in high_value_keywords):
                        print_matrix(f"   🎯 HIGH-VALUE CONSOLIDATION DETECTED!", Colors.YELLOW)

                    char_saved = len(str(original)) - len(str(cleaned))
                    if char_saved > 0:
                        print_matrix(f"   💾 COMPRESSION: -{char_saved} characters", Colors.CYAN)

                elif idx % 200 == 0 and idx > 0:
                    print_matrix(f"   ✓ Row {idx:,}: '{original}' (no change)", Colors.DIM_GREEN)

            column_stats[col] = changes
            print_matrix(f"✅ {col} SCAN COMPLETE", Colors.BRIGHT_GREEN)
            print_matrix(f"   📊 Total transformations: {changes:,}", Colors.GREEN)
            print_matrix(f"   📈 Rate: {(changes / len(df) * 100):.2f}%", Colors.GREEN)
            total_changes += changes

            print_matrix("   " + "▓" * 50, Colors.BRIGHT_GREEN)

        print_header("NORMALIZATION MATRIX COMPLETE")
        print_matrix("📊 DETAILED TRANSFORMATION REPORT:", Colors.BRIGHT_GREEN)

        for col, changes in column_stats.items():
            transformation_rate = (changes / len(df)) * 100
            print_matrix(f"   🔸 {col}:", Colors.GREEN)
            print_matrix(f"     • Entities processed: {len(df):,}", Colors.DIM_GREEN)
            print_matrix(f"     • Transformations: {changes:,}", Colors.GREEN)
            print_matrix(f"     • Success rate: {transformation_rate:.2f}%", Colors.GREEN)
            print_matrix(f"     • Unchanged: {len(df) - changes:,}", Colors.DIM_GREEN)

        print_matrix("🎯 AGGREGATE STATISTICS:", Colors.BRIGHT_GREEN)
        print_matrix(f"   • Total rows scanned: {len(df) * len(found_columns):,}", Colors.GREEN)
        print_matrix(f"   • Total transformations: {total_changes:,}", Colors.BRIGHT_GREEN)
        overall_rate = (total_changes / (len(df) * len(found_columns)) * 100)
        print_matrix(f"   • Overall efficiency: {overall_rate:.2f}%", Colors.GREEN)
        print_matrix(f"   • Columns processed: {len(found_columns)}/3", Colors.GREEN)

        return df


    def save_file(self, df):
        print_header("SAVING NORMALIZED MATRIX")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.source_file))[0]
        output_name = f"{base_name}_matrix_normalized_{timestamp}.csv"
        output_path = os.path.join(self.dest_directory, output_name)

        print_matrix(f"💾 Writing data to: {output_name}", Colors.CYAN)
        df.to_csv(output_path, index=False)

        print_matrix(f"✅ MATRIX SAVED: {os.path.basename(output_path)}", Colors.BRIGHT_GREEN)
        print_matrix(f"📁 LOCATION: {output_path}", Colors.DIM_GREEN)

        return output_path


    def run(self):
        print_matrix("╔══════════════════════════════════════╗", Colors.BRIGHT_GREEN)
        print_matrix("║     MATRIX ENTITY NORMALIZER 3.0    ║", Colors.BRIGHT_GREEN)
        print_matrix("║    Maximum Detail Green Mode        ║", Colors.BRIGHT_GREEN)
        print_matrix("╚══════════════════════════════════════╝", Colors.BRIGHT_GREEN)

        if not self.select_file():
            return

        df = self.process_file()
        if df is None:
            return

        output_file = self.save_file(df)

        print_header("MISSION ACCOMPLISHED")
        print_matrix("🎉 Entity normalization complete!", Colors.BRIGHT_GREEN)
        print_matrix(f"📄 Output: {os.path.basename(output_file)}", Colors.GREEN)

        messagebox.showinfo(
            "Matrix Normalizer Complete",
            f"Entity normalization successful!\n\n"
            f"File saved: {os.path.basename(output_file)}\n\n"
            f"Check console for detailed transformation log."
        )


def main():
    normalizer = MatrixNormalizer()
    normalizer.run()
    print_matrix("\n🔚 Press Enter to exit the Matrix...", Colors.DIM_GREEN)
    input()


if __name__ == "__main__":
    main()