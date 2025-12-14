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

        # Enhanced core companies database with common shipping/trading variations
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

            # Enhanced shipping companies based on your expertise
            'WILHELMSEN': ['WILHELMSEN', 'WILHELMSEN SHIPS SERVICE', 'WILHELMSEN SHIP SERVICE'],
            'MAERSK': ['MAERSK', 'MOLLER', 'A.P. MOLLER'],
            'MSC': ['MSC', 'MEDITERRANEAN SHIPPING'],
            'CMA CGM': ['CMA', 'CGM', 'CMA CGM'],
            'COSCO': ['COSCO', 'CHINA OCEAN SHIPPING'],
            'EVERGREEN': ['EVERGREEN', 'EVERGREEN LINE'],
            'HAPAG LLOYD': ['HAPAG', 'LLOYD', 'HAPAG LLOYD'],
            'ONE': ['ONE', 'OCEAN NETWORK EXPRESS'],
            'YANG MING': ['YANG MING', 'YANGMING'],
            'PIL': ['PIL', 'PACIFIC INTERNATIONAL'],
            'ZIM': ['ZIM', 'ZIM LINES'],
            'HYUNDAI MERCHANT': ['HYUNDAI MERCHANT', 'HMM'],
            'OOCL': ['OOCL', 'ORIENT OVERSEAS'],
            'MOL': ['MOL', 'MITSUI OSK'],
            'NYK': ['NYK', 'NIPPON YUSEN'],
            'K LINE': ['K LINE', 'KAWASAKI KISEN'],
            'APL': ['APL', 'AMERICAN PRESIDENT'],
            'UASC': ['UASC', 'UNITED ARAB SHIPPING'],
            'CSAV': ['CSAV', 'COMPANIA SUD AMERICANA'],
            'HAMBURG SUD': ['HAMBURG', 'HAMBURG SUD'],
            'WANHAI': ['WANHAI', 'WAN HAI'],
            'ARKAS': ['ARKAS', 'ARKAS LINE'],
            'GRIMALDI': ['GRIMALDI', 'GRIMALDI LINES'],
            'STENA': ['STENA', 'STENA LINE'],
            'DFDS': ['DFDS', 'DFDS SEAWAYS'],
            'BRITTANY': ['BRITTANY', 'BRITTANY FERRIES']
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

    def select_file(self):
        print_header("INITIALIZING FUZZY MATRIX NORMALIZER")
        print_matrix("🔍 Opening file selection interface...", Colors.CYAN)

        root = tk.Tk()
        root.withdraw()

        source_file = filedialog.askopenfilename(
            title="Select CSV file to normalize - FUZZY MATRIX MODE",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )

        root.destroy()

        if not source_file:
            print_matrix("❌ FILE SELECTION TERMINATED", Colors.RED)
            return False

        self.source_file = source_file
        self.dest_directory = os.path.dirname(source_file)

        print_matrix(f"✅ TARGET ACQUIRED: {os.path.basename(self.source_file)}", Colors.BRIGHT_GREEN)
        print_matrix(f"📁 OUTPUT DIRECTORY: {self.dest_directory}", Colors.DIM_GREEN)
        return True

    def similarity_ratio(self, a, b):
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.upper(), b.upper()).ratio()

    def advanced_fuzzy_match(self, company_name):
        """Enhanced fuzzy matching for common spelling mistakes"""
        if not company_name or len(company_name) < 3:
            return None

        clean_name = company_name.upper().strip()

        # Remove suffixes for better matching
        for suffix in self.suffixes:
            pattern = r'\b' + re.escape(suffix) + r'\b'
            clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)

        clean_name = ' '.join(clean_name.split())

        best_match = None
        best_score = 0.0
        min_similarity = 0.70  # Lowered threshold for more fuzzy matching

        for parent_company, variations in self.core_companies.items():
            for variation in variations:
                # Direct substring match (highest priority)
                if variation in clean_name or clean_name in variation:
                    if len(variation) >= 4:
                        return parent_company

                # Common spelling mistake patterns you identified:

                # 1. Duplicated letter (e.g., "WILHHEELMSEN" vs "WILHELMSEN")
                for i, char in enumerate(variation):
                    doubled_variation = variation[:i] + char + variation[i:]
                    if doubled_variation in clean_name:
                        return parent_company

                # 2. One letter short (e.g., "WILHELMSE" vs "WILHELMSEN")
                for i in range(len(variation)):
                    shortened_variation = variation[:i] + variation[i + 1:]
                    if len(shortened_variation) >= 4 and shortened_variation in clean_name:
                        return parent_company

                # 3. Space within string (e.g., "WILHEL MSEN" vs "WILHELMSEN")
                spaced_variations = []
                for i in range(1, len(variation)):
                    spaced_var = variation[:i] + ' ' + variation[i:]
                    spaced_variations.append(spaced_var)

                for spaced_var in spaced_variations:
                    if spaced_var in clean_name:
                        return parent_company

                # 4. Plural/singular 'S' differences (e.g., "SHIP" vs "SHIPS")
                if variation.endswith('S') and variation[:-1] in clean_name:
                    return parent_company
                if not variation.endswith('S') and (variation + 'S') in clean_name:
                    return parent_company

                # 5. Standard fuzzy similarity
                similarity = self.similarity_ratio(clean_name, variation)
                if similarity > best_score and similarity >= min_similarity:
                    best_score = similarity
                    best_match = parent_company

                # 6. Word-based matching
                clean_words = clean_name.split()
                for word in clean_words:
                    if len(word) >= 4:
                        word_similarity = self.similarity_ratio(word, variation)
                        if word_similarity > 0.80:  # High similarity for individual words
                            return parent_company

                        # Check word against spelling mistake patterns too
                        # Doubled letter in word
                        for j, char in enumerate(word):
                            if j < len(word) - 1:
                                doubled_word = word[:j] + char + word[j:]
                                if self.similarity_ratio(doubled_word, variation) > 0.85:
                                    return parent_company

        return best_match if best_score >= min_similarity else None

    def fuzzy_match_company(self, company_name):
        """Main fuzzy matching function using advanced techniques"""
        return self.advanced_fuzzy_match(company_name)

    def clean_company_name(self, name, is_notify_party=False):
        if pd.isna(name) or name == '' or name == 'null':
            return ''

        original_name = str(name)
        name = str(name).upper().strip()

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

        for old_name, new_name in self.exact_consolidations.items():
            if old_name in name:
                return new_name

        fuzzy_match = self.fuzzy_match_company(name)
        if fuzzy_match:
            return fuzzy_match

        words = name.split()
        if not words:
            return name

        clean_words = []
        for word in words:
            if word not in self.suffixes:
                clean_words.append(word)

        if not clean_words:
            return name

        words = clean_words

        for i, word in enumerate(words):
            if word in self.asian_companies:
                return word

        if words[0] in self.generic_words and len(words) > 1:
            return words[1]

        result = words[0]

        if (len(words) > 1 and
                len(words[1]) >= 4 and
                words[1] not in ['NORTH', 'SOUTH', 'EAST', 'WEST', 'INTERNATIONAL', 'AMERICA']):
            result = f"{words[0]} {words[1]}"

        # LINE 245 - COMPLETELY FIXED PUNCTUATION CLEANING
        result = re.sub(r'[,.\-_|;()]+$', '', result)
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

            start_time = datetime.now().timestamp()

            for idx in range(len(df)):
                # Fast Matrix visual effects every 10 rows
                if idx % 10 == 0:
                    progress = (idx / len(df)) * 100
                    # Random Matrix-style codes for visual effect
                    matrix_codes = ["0x7F3A", "0xB2E1", "0x9C45", "0xF8A2", "0x3D17", "0xE6B9"]
                    random_code = matrix_codes[idx % len(matrix_codes)]
                    print_matrix(f"⚡ {random_code} | {idx:05d}/{len(df):05d} | {progress:06.2f}% | {col[:3].upper()}",
                                 Colors.DIM_GREEN)

                # Occasional random Matrix glitch effects
                if idx % 137 == 0 and idx > 0:  # Prime number for randomness
                    glitch_chars = ["▓", "▒", "░", "█", "▄", "▀", "◆", "◇", "○", "●"]
                    glitch_line = ''.join([glitch_chars[i % len(glitch_chars)] for i in range(50)])
                    print_matrix(f"   {glitch_line}", Colors.GREEN)

                original = df.iloc[idx][col]
                cleaned = self.clean_company_name(original, is_notify)

                if original != cleaned:
                    df.iloc[idx, df.columns.get_loc(col)] = cleaned
                    changes += 1

                    # Fast transformation display
                    print_matrix(f"🔄 #{changes:04d} | {idx:05d} | '{original}' → '{cleaned}'", Colors.BRIGHT_GREEN)

                    # High-value company detection (minimal overhead)
                    if any(kw in str(original).upper() for kw in
                           ['MARUBENI', 'MARTIN', 'MARITIME', 'AMEROPA', 'POSCO']):
                        print_matrix(f"   🎯 HIGH-VALUE: {cleaned}", Colors.YELLOW)

                # Random Matrix rain effect every 200 rows
                if idx % 200 == 0 and idx > 0:
                    matrix_rain = ['█', '▓', '▒', '░', '▄', '▀', '▌', '▐', '▆', '▇']
                    rain_line = ''.join([matrix_rain[(idx + i) % len(matrix_rain)] for i in range(80)])
                    print_matrix(rain_line, Colors.GREEN)

                # Speed indicators
                if idx % 500 == 0 and idx > 0:
                    speed_indicators = [">>>", "<<<", "^^^", "vvv", "|||", "---"]
                    speed = speed_indicators[idx % len(speed_indicators)]
                    print_matrix(
                        f"   {speed} SPEED: {idx / ((datetime.now().timestamp() - start_time)):.0f} rows/sec {speed}",
                        Colors.CYAN)

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
        output_name = f"{base_name}_fuzzy_normalized_{timestamp}.csv"
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
    print_matrix("\n🔚 Matrix normalization complete - script exiting automatically...", Colors.DIM_GREEN)
    # Removed blocking input() - script will exit cleanly


if __name__ == "__main__":
    main()
