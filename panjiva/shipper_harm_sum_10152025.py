"""
Shipper Harmonization Script - Stage 1: Top 35 Companies
=========================================================
Purpose: Build harmonization dictionary from actual data
Focus: Top 25-35 companies representing ~75% of volume
Filter: Only entities with ≥10,000,000 kg (10,000 MT)

Author: Data Harmonization Pipeline
Date: 2025-10-15
"""

import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher
from collections import defaultdict, Counter
import os
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Configuration settings"""
    
    INPUT_FILE = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\panjiva_summaries\summary_keywords\u_s_imports__all_shipments_grouped_by_shipper_original_format_results_1_to_10_000_of_31_780.csv"
    OUTPUT_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Projects\Panjiva\LLM_analysis\outputs"
    
    # Thresholds
    MIN_KG_THRESHOLD = 10000000  # 10 million kg = 10,000 MT
    TOP_N_COMPANIES = 35  # Focus on top 35
    FUZZY_THRESHOLD = 0.85  # 85% similarity for clustering
    
    # Generic terms that need context
    GENERIC_TERMS = {
        'GLOBAL', 'INTERNATIONAL', 'TRADING', 'WORLDWIDE', 'SUPPLY',
        'MARKETING', 'COMMERCIAL', 'EXPORT', 'IMPORT', 'INDUSTRIES',
        'GROUP', 'HOLDINGS', 'COMPANY', 'CORPORATION', 'LIMITED',
        'SERVICES', 'OPERATIONS', 'RESOURCES', 'MATERIALS', 'PRODUCTS'
    }
    
    # Legal entities to remove
    LEGAL_ENTITIES = [
        r'\bS\.?A\.?(?:\s+DE\s+C\.?V\.?)?',
        r'\bDE\s+C\.?V\.?',
        r'\bLLC\.?',
        r'\bL\.?L\.?C\.?',
        r'\bINC\.?',
        r'\bCORP(?:ORATION)?\.?',
        r'\bLTD\.?',
        r'\bLIMITED',
        r'\bPLC\.?',
        r'\bN\.?V\.?',
        r'\bB\.?V\.?',
        r'\bGMBH',
        r'\bAG\b',
        r'\bPTE\.?\s+LTD\.?',
        r'\bPTY\.?\s+LTD\.?',
        r'\bSDN\.?\s+BHD\.?',
        r'\bCO\.?\s+LTD\.?',
    ]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize_name(name):
    """Normalize company name for matching"""
    if pd.isna(name) or not isinstance(name, str):
        return ""
    
    # Convert to uppercase
    name = name.upper().strip()
    
    # Remove legal entities
    for pattern in Config.LEGAL_ENTITIES:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Remove everything after first comma (likely address)
    if ',' in name:
        name = name.split(',')[0]
    
    # Remove special characters but keep spaces
    name = re.sub(r'[^\w\s]', ' ', name)
    
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    return name.strip()


def extract_address_keywords(address):
    """Extract useful address keywords"""
    if pd.isna(address) or not isinstance(address, str):
        return []
    
    address = address.upper()
    
    # Extract city/location keywords (before first comma usually)
    parts = address.split(',')
    keywords = set()
    
    # Cities/locations
    for part in parts[:2]:  # First two parts usually have city/country
        words = re.findall(r'\b[A-Z]{2,}\b', part)  # All-caps words
        keywords.update(words)
    
    # Countries (often at end)
    countries = ['CANADA', 'MEXICO', 'BRAZIL', 'NETHERLANDS', 'COLOMBIA', 
                 'PANAMA', 'IRAQ', 'BARBADOS', 'BAHAMAS', 'MALAYSIA',
                 'HOUSTON', 'ROTTERDAM', 'BOGATA']
    
    for country in countries:
        if country in address:
            keywords.add(country)
    
    return list(keywords)[:5]  # Limit to 5 most relevant


def similarity_ratio(str1, str2):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, str1, str2).ratio()


def is_acronym(name):
    """Check if name appears to be an acronym"""
    # 2-5 uppercase letters, possibly with numbers
    return bool(re.match(r'^[A-Z]{2,5}[0-9]*$', name))


def extract_keywords(variations, canonical_name):
    """Extract match keywords from variations"""
    keywords = set()
    
    # Add canonical name
    keywords.add(canonical_name)
    
    # Process each variation
    for var in variations:
        normalized = normalize_name(var)        
        # Split into words
        words = normalized.split()
        
        # Check for acronyms
        if is_acronym(normalized):
            keywords.add(normalized)
        
        # Add significant word combinations
        for i, word in enumerate(words):
            # Skip very common/generic standalone words
            if word in Config.GENERIC_TERMS and len(words) > 1:
                # Keep generic terms with context
                if i > 0:
                    keywords.add(f"{words[i-1]} {word}")
                if i < len(words) - 1:
                    keywords.add(f"{word} {words[i+1]}")
            else:
                # Add significant standalone words (3+ chars)
                if len(word) >= 3:
                    keywords.add(word)
        
        # Add multi-word combinations for specific patterns
        for i in range(len(words) - 1):
            combo = f"{words[i]} {words[i+1]}"
            if words[i] not in Config.GENERIC_TERMS or words[i+1] not in Config.GENERIC_TERMS:
                keywords.add(combo)
    
    # Remove generic single words
    keywords = {k for k in keywords if not (len(k.split()) == 1 and k in Config.GENERIC_TERMS)}
    
    return sorted(keywords)


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def main():
    """Main execution"""
    
    print("="*80)
    print("SHIPPER HARMONIZATION - STAGE 1: TOP 35 COMPANIES")
    print("="*80)
    print()
    
    # Create output directory
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    # Read data
    print(f"Reading data from: {Config.INPUT_FILE}")
    df = pd.read_csv(Config.INPUT_FILE)
    print(f"Total records: {len(df):,}")
    print()
    
    # Filter by KG threshold
    print(f"Filtering: KG >= {Config.MIN_KG_THRESHOLD:,}")
    df_filtered = df[df['KG'] >= Config.MIN_KG_THRESHOLD].copy()
    print(f"Records after filter: {len(df_filtered):,}")
    print()
    
    # Calculate total KG coverage
    total_kg_all = df['KG'].sum()
    total_kg_filtered = df_filtered['KG'].sum()
    coverage = (total_kg_filtered / total_kg_all) * 100
    print(f"Total KG (all): {total_kg_all:,.0f}")
    print(f"Total KG (filtered): {total_kg_filtered:,.0f}")
    print(f"Coverage: {coverage:.1f}%")
    print()
    
    # Sort by KG and get top N
    df_top = df_filtered.nlargest(Config.TOP_N_COMPANIES, 'KG').copy()
    top_kg = df_top['KG'].sum()
    top_coverage = (top_kg / total_kg_all) * 100
    
    print(f"Top {Config.TOP_N_COMPANIES} companies:")
    print(f"Total KG: {top_kg:,.0f}")
    print(f"Coverage of ALL data: {top_coverage:.1f}%")
    print(f"Coverage of filtered data: {(top_kg/total_kg_filtered)*100:.1f}%")
    print()
    
    # Add normalized name column
    df_top['Normalized_Name'] = df_top['Shipper (Original Format) Name'].apply(normalize_name)
    
    # Cluster similar names
    print("Clustering similar company names...")
    clusters = []
    processed = set()
    
    for idx, row in df_top.iterrows():
        if idx in processed:
            continue
        
        # Start new cluster
        cluster = {
            'indices': [idx],
            'names': [row['Shipper (Original Format) Name']],
            'normalized': row['Normalized_Name'],
            'addresses': [row['Shipper (Original Format) Address']]
        }
        processed.add(idx)
        
        # Find similar names
        for idx2, row2 in df_top.iterrows():
            if idx2 in processed:
                continue
            
            # Calculate similarity
            sim = similarity_ratio(row['Normalized_Name'], row2['Normalized_Name'])
            
            if sim >= Config.FUZZY_THRESHOLD:
                cluster['indices'].append(idx2)
                cluster['names'].append(row2['Shipper (Original Format) Name'])
                cluster['addresses'].append(row2['Shipper (Original Format) Address'])
                processed.add(idx2)
        
        clusters.append(cluster)
    
    print(f"Found {len(clusters)} unique company groups")
    print()    
    # Build dictionary entries
    print("Building harmonization dictionary...")
    results = []
    
    for cluster in clusters:
        # Get cluster data
        cluster_df = df_top.loc[cluster['indices']]
        
        # Choose canonical name (shortest normalized version)
        normalized_names = [normalize_name(n) for n in cluster['names']]
        canonical = min(normalized_names, key=len)
        
        # Flag if acronym
        is_acronym_flag = is_acronym(canonical)
        
        # Extract keywords
        keywords = extract_keywords(cluster['names'], canonical)
        
        # Extract address keywords
        address_kw = []
        for addr in cluster['addresses']:
            address_kw.extend(extract_address_keywords(addr))
        address_kw = list(set(address_kw))  # Unique
        
        # Calculate totals
        total_kg = cluster_df['KG'].sum()
        total_shipments = cluster_df['Shipments'].sum()
        total_value = cluster_df['VALUE (usd)'].sum()
        variations_count = len(cluster['names'])
        
        # Sample variations (up to 3)
        sample_vars = '; '.join(cluster['names'][:3])
        
        # Confidence
        if variations_count == 1:
            confidence = "SINGLE"
        elif all(similarity_ratio(normalize_name(cluster['names'][0]), normalize_name(n)) >= 0.95 
                 for n in cluster['names'][1:]):
            confidence = "HIGH"
        else:
            confidence = "REVIEW"
        
        # Notes
        notes = []
        if is_acronym_flag:
            notes.append("ACRONYM")
        if any(term in canonical for term in Config.GENERIC_TERMS):
            notes.append("HAS_GENERIC_TERMS")
        
        # Rank
        rank = df_top.loc[cluster['indices'][0]]['KG']
        
        results.append({
            'Canonical_Name': canonical,
            'Match_Keywords': '|'.join(keywords),
            'Address_Keywords': '|'.join(address_kw) if address_kw else '',
            'Total_KG': total_kg,
            'Total_Shipments': total_shipments,
            'Total_Value_USD': total_value,
            'Variations_Count': variations_count,
            'Sample_Variations': sample_vars,
            'Confidence': confidence,
            'Volume_Rank': rank,
            'Notes': '|'.join(notes) if notes else ''
        })
    
    # Create output dataframe
    output_df = pd.DataFrame(results)
    output_df = output_df.sort_values('Total_KG', ascending=False)
    
    # Add rank number
    output_df.insert(0, 'Rank', range(1, len(output_df) + 1))
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(Config.OUTPUT_DIR, f"shipper_dictionary_TOP{Config.TOP_N_COMPANIES}_REVIEW_{timestamp}.csv")
    output_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"✓ Dictionary saved to: {output_file}")
    print()
    
    # Print summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total unique companies: {len(output_df)}")
    print(f"High confidence: {len(output_df[output_df['Confidence'] == 'HIGH'])}")
    print(f"Review needed: {len(output_df[output_df['Confidence'] == 'REVIEW'])}")
    print(f"Single variation: {len(output_df[output_df['Confidence'] == 'SINGLE'])}")
    print(f"Acronyms detected: {len(output_df[output_df['Notes'].str.contains('ACRONYM', na=False)])}")
    print()
    
    # Show top 10
    print("TOP 10 COMPANIES BY VOLUME:")
    print("-"*80)
    for i, row in output_df.head(10).iterrows():
        print(f"{row['Rank']:2d}. {row['Canonical_Name']:<40} {row['Total_KG']:>15,.0f} kg")
    print()
    
    print("="*80)
    print(f"STAGE 1 COMPLETE - Please review: {os.path.basename(output_file)}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())