import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Wedge
import matplotlib.patches as mpatches

# Set style for professional charts
plt.style.use('default')
sns.set_palette("husl")

# Create output directory
import os

if not os.path.exists('fertilizer_charts'):
    os.makedirs('fertilizer_charts')

# Set figure parameters for high-quality output
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['figure.figsize'] = [12, 8]

# Data from our analysis
port_data = {
    'Port': ['Lower Mississippi', 'Tampa Bay', 'PNW Ports', 'North Florida',
             'North Carolina', 'California Ports', 'Houston/Galveston', 'Georgia Ports'],
    'Tonnage': [10582708, 2967238, 733913, 456061, 421042, 413956, 404913, 207880],
    'Percentage': [63.0, 17.7, 4.4, 2.7, 2.5, 2.5, 2.4, 1.2]
}

country_data = {
    'Country': ['Peru', 'Saudi Arabia', 'Qatar', 'Russia', 'Algeria',
                'Norway', 'Nigeria', 'Morocco', 'Belgium', 'Egypt'],
    'Tonnage': [5691997, 1731977, 1609390, 1212918, 573550,
                547953, 516872, 497850, 474060, 440936],
    'Percentage': [33.9, 10.3, 9.6, 7.2, 3.4, 3.3, 3.1, 3.0, 2.8, 2.6],
    'Flag': ['🇵🇪', '🇸🇦', '🇶🇦', '🇷🇺', '🇩🇿', '🇳🇴', '🇳🇬', '🇲🇦', '🇧🇪', '🇪🇬']
}

fertilizer_data = {
    'Type': ['Phosrock', 'Urea', 'MAP', 'DAP', 'Ammonium Sulphate',
             'Nitrates', 'Calcium Nitrate', 'Potash', 'Prilled Sulphur', 'GTSP'],
    'Tonnage': [5691997, 4995856, 1407465, 1292669, 639232,
                598400, 481691, 473733, 369674, 359578],
    'Category': ['Phosphorus', 'Nitrogen', 'Phosphorus', 'Phosphorus', 'Nitrogen',
                 'Nitrogen', 'Nitrogen', 'Potassium', 'Sulfur', 'Phosphorus']
}

nutrient_data = {
    'Nutrient': ['Phosphorus', 'Nitrogen', 'Potassium', 'Sulfur', 'Mixed/Complex'],
    'Tonnage': [8879676, 6803940, 663831, 460188, 145477],
    'Percentage': [52.4, 40.1, 3.9, 2.7, 0.9]
}

transport_data = {
    'Mode': ['Barge', 'Rail', 'Truck'],
    'Cost_Per_Tonne_Mile': [0.04, 0.40, 0.64],
    'Relative_Cost': [1, 10, 16]
}

balance_data = {
    'Nutrient': ['Nitrogen', 'Phosphorus', 'Potassium'],
    'Consumption': [11.96, 3.70, 4.40],
    'Production': [8.75, 4.35, 0.90],
    'Self_Sufficiency': [73, 118, 20]
}


# Chart 1: Port Import Analysis
def create_port_chart():
    plt.figure(figsize=(14, 8))

    # Create horizontal bar chart
    ports = port_data['Port']
    tonnages = [x / 1000000 for x in port_data['Tonnage']]  # Convert to millions
    percentages = port_data['Percentage']

    colors = ['#2E5BBA', '#8FA6DB', '#B8C5E0', '#D4DAE8', '#E8EBF1',
              '#F0F2F6', '#F5F6F9', '#FAFBFC']

    bars = plt.barh(ports, tonnages, color=colors)

    # Add percentage labels on bars
    for i, (bar, pct) in enumerate(zip(bars, percentages)):
        width = bar.get_width()
        plt.text(width + 0.1, bar.get_y() + bar.get_height() / 2,
                 f'{pct}%', ha='left', va='center', fontweight='bold', fontsize=10)

    plt.xlabel('Import Volume (Million Tonnes)', fontsize=12, fontweight='bold')
    plt.title('US Fertilizer Ocean Imports by Port (2023-2025)\nTotal: 16.8 Million Tonnes',
              fontsize=14, fontweight='bold', pad=20)

    # Add grid and styling
    plt.grid(axis='x', alpha=0.3, linestyle='--')
    plt.tight_layout()

    # Add annotation
    plt.figtext(0.02, 0.02, 'Source: Ocean import trade data analysis', fontsize=8, style='italic')

    plt.savefig('fertilizer_charts/01_port_imports.png', bbox_inches='tight', dpi=300)
    plt.savefig('fertilizer_charts/01_port_imports.pdf', bbox_inches='tight')
    plt.close()


# Chart 2: Supplier Countries Analysis
def create_country_chart():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Pie chart
    countries = country_data['Country']
    tonnages = country_data['Tonnage']
    colors = plt.cm.Set3(np.linspace(0, 1, len(countries)))

    wedges, texts, autotexts = ax1.pie(tonnages, labels=countries, autopct='%1.1f%%',
                                       colors=colors, startangle=90)
    ax1.set_title('Supplier Country Market Share', fontsize=12, fontweight='bold')

    # Bar chart
    tonnages_millions = [x / 1000000 for x in tonnages]
    bars = ax2.bar(range(len(countries)), tonnages_millions, color=colors)
    ax2.set_xlabel('Countries', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Import Volume (Million Tonnes)', fontsize=10, fontweight='bold')
    ax2.set_title('Import Volume by Country', fontsize=12, fontweight='bold')
    ax2.set_xticks(range(len(countries)))
    ax2.set_xticklabels(countries, rotation=45, ha='right')

    # Add value labels on bars
    for bar, tonnage in zip(bars, tonnages_millions):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 f'{tonnage:.1f}M', ha='center', va='bottom', fontsize=8)

    plt.suptitle('Top 10 Fertilizer Supplier Countries to US (2023-2025)',
                 fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.figtext(0.02, 0.02, 'Source: Ocean import trade data analysis', fontsize=8, style='italic')

    plt.savefig('fertilizer_charts/02_supplier_countries.png', bbox_inches='tight', dpi=300)
    plt.savefig('fertilizer_charts/02_supplier_countries.pdf', bbox_inches='tight')
    plt.close()


# Chart 3: Fertilizer Types by Volume
def create_fertilizer_types_chart():
    plt.figure(figsize=(14, 8))

    types = fertilizer_data['Type']
    tonnages = [x / 1000000 for x in fertilizer_data['Tonnage']]
    categories = fertilizer_data['Category']

    # Color mapping by nutrient category
    color_map = {'Phosphorus': '#8B4513', 'Nitrogen': '#4169E1',
                 'Potassium': '#9ACD32', 'Sulfur': '#FF8C00'}
    colors = [color_map[cat] for cat in categories]

    bars = plt.bar(range(len(types)), tonnages, color=colors)

    plt.xlabel('Fertilizer Type', fontsize=12, fontweight='bold')
    plt.ylabel('Import Volume (Million Tonnes)', fontsize=12, fontweight='bold')
    plt.title('US Fertilizer Imports by Product Type (2023-2025)',
              fontsize=14, fontweight='bold', pad=20)

    plt.xticks(range(len(types)), types, rotation=45, ha='right')

    # Add value labels
    for bar, tonnage in zip(bars, tonnages):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                 f'{tonnage:.1f}M', ha='center', va='bottom', fontsize=9)

    # Create legend
    legend_elements = [mpatches.Patch(color=color_map[cat], label=cat)
                       for cat in color_map.keys()]
    plt.legend(handles=legend_elements, loc='upper right')

    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.figtext(0.02, 0.02, 'Source: Ocean import trade data analysis', fontsize=8, style='italic')

    plt.savefig('fertilizer_charts/03_fertilizer_types.png', bbox_inches='tight', dpi=300)
    plt.savefig('fertilizer_charts/03_fertilizer_types.pdf', bbox_inches='tight')
    plt.close()


# Chart 4: USDA Nutrient Categories
def create_nutrient_categories_chart():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    nutrients = nutrient_data['Nutrient']
    tonnages = nutrient_data['Tonnage']
    percentages = nutrient_data['Percentage']

    colors = ['#8B4513', '#4169E1', '#9ACD32', '#FF8C00', '#8A2BE2']

    # Pie chart
    wedges, texts, autotexts = ax1.pie(tonnages, labels=nutrients, autopct='%1.1f%%',
                                       colors=colors, startangle=90)
    ax1.set_title('USDA Nutrient Category Distribution', fontsize=12, fontweight='bold')

    # Horizontal bar chart with details
    tonnages_millions = [x / 1000000 for x in tonnages]
    bars = ax2.barh(nutrients, tonnages_millions, color=colors)

    for i, (bar, pct, tonnage) in enumerate(zip(bars, percentages, tonnages_millions)):
        ax2.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                 f'{pct}% ({tonnage:.1f}M tonnes)', ha='left', va='center', fontsize=10)

    ax2.set_xlabel('Import Volume (Million Tonnes)', fontsize=10, fontweight='bold')
    ax2.set_title('Volume by Nutrient Category', fontsize=12, fontweight='bold')

    plt.suptitle('US Fertilizer Imports by USDA Nutrient Categories (2023-2025)',
                 fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.figtext(0.02, 0.02, 'Source: USDA nutrient classification analysis', fontsize=8, style='italic')

    plt.savefig('fertilizer_charts/04_nutrient_categories.png', bbox_inches='tight', dpi=300)
    plt.savefig('fertilizer_charts/04_nutrient_categories.pdf', bbox_inches='tight')
    plt.close()


# Chart 5: Transportation Cost Comparison
def create_transport_chart():
    plt.figure(figsize=(12, 8))

    modes = transport_data['Mode']
    costs = transport_data['Cost_Per_Tonne_Mile']
    relative_costs = transport_data['Relative_Cost']

    colors = ['#4169E1', '#9ACD32', '#FF8C00']

    # Create subplot for cost comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Absolute cost chart
    bars1 = ax1.bar(modes, costs, color=colors)
    ax1.set_ylabel('Cost per Tonne-Mile ($)', fontsize=12, fontweight='bold')
    ax1.set_title('Absolute Transportation Costs', fontsize=12, fontweight='bold')

    for bar, cost in zip(bars1, costs):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                 f'${cost:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Relative cost chart
    bars2 = ax2.bar(modes, relative_costs, color=colors)
    ax2.set_ylabel('Relative Cost (Barge = 1x)', fontsize=12, fontweight='bold')
    ax2.set_title('Relative Cost Comparison', fontsize=12, fontweight='bold')

    for bar, rel_cost in zip(bars2, relative_costs):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                 f'{rel_cost}x', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.suptitle('US Fertilizer Transportation Cost Analysis\nBarge Transport Advantage',
                 fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.figtext(0.02, 0.02, 'Source: USDA transportation cost analysis', fontsize=8, style='italic')

    plt.savefig('fertilizer_charts/05_transportation_costs.png', bbox_inches='tight', dpi=300)
    plt.savefig('fertilizer_charts/05_transportation_costs.pdf', bbox_inches='tight')
    plt.close()


# Chart 6: Production vs Consumption Balance
def create_balance_chart():
    plt.figure(figsize=(14, 8))

    nutrients = balance_data['Nutrient']
    consumption = balance_data['Consumption']
    production = balance_data['Production']
    self_sufficiency = balance_data['Self_Sufficiency']

    x = np.arange(len(nutrients))
    width = 0.35

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Production vs Consumption
    bars1 = ax1.bar(x - width / 2, consumption, width, label='Consumption', color='#FF6B6B', alpha=0.8)
    bars2 = ax1.bar(x + width / 2, production, width, label='Production', color='#4ECDC4', alpha=0.8)

    ax1.set_xlabel('Nutrient', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Million Tonnes', fontsize=12, fontweight='bold')
    ax1.set_title('US Fertilizer Production vs Consumption', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(nutrients)
    ax1.legend()

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                     f'{height:.1f}M', ha='center', va='bottom', fontsize=9)

    # Self-sufficiency percentages
    colors_sf = ['#FFE66D' if x < 50 else '#95E1D3' if x < 100 else '#A8E6CF'
                 for x in self_sufficiency]

    bars3 = ax2.bar(nutrients, self_sufficiency, color=colors_sf)
    ax2.set_xlabel('Nutrient', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Self-Sufficiency (%)', fontsize=12, fontweight='bold')
    ax2.set_title('US Fertilizer Self-Sufficiency Rates', fontsize=12, fontweight='bold')
    ax2.axhline(y=100, color='red', linestyle='--', alpha=0.7, label='100% Self-Sufficient')
    ax2.legend()

    for bar, pct in zip(bars3, self_sufficiency):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                 f'{pct}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.suptitle('US Fertilizer Market Balance Analysis (2023-2025)',
                 fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.figtext(0.02, 0.02, 'Source: USDA production and consumption statistics', fontsize=8, style='italic')

    plt.savefig('fertilizer_charts/06_production_balance.png', bbox_inches='tight', dpi=300)
    plt.savefig('fertilizer_charts/06_production_balance.pdf', bbox_inches='tight')
    plt.close()


# Chart 7: Russian Network Sanctions Evasion
def create_russian_network_chart():
    plt.figure(figsize=(12, 8))

    companies = ['EuroChem', 'PhosAgro', 'Uralkali/UralChem']
    operational_capacity = [95, 90, 75]

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    bars = plt.barh(companies, operational_capacity, color=colors)

    plt.xlabel('Operational Capacity Maintained (%)', fontsize=12, fontweight='bold')
    plt.title('Russian Fertilizer Network Sanctions Evasion Effectiveness\nPost-March 2022 Sanctions',
              fontsize=14, fontweight='bold', pad=20)

    # Add percentage labels
    for bar, pct in zip(bars, operational_capacity):
        plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                 f'{pct}%', ha='left', va='center', fontsize=12, fontweight='bold')

    # Add average line
    avg_capacity = np.mean(operational_capacity)
    plt.axvline(x=avg_capacity, color='red', linestyle='--', alpha=0.7)
    plt.text(avg_capacity + 2, 1.5, f'Average: {avg_capacity:.0f}%',
             fontsize=10, color='red', fontweight='bold')

    plt.xlim(0, 100)
    plt.grid(axis='x', alpha=0.3, linestyle='--')
    plt.tight_layout()

    plt.figtext(0.02, 0.02, 'Source: Corporate filings and sanctions database analysis',
                fontsize=8, style='italic')

    plt.savefig('fertilizer_charts/07_russian_sanctions_evasion.png', bbox_inches='tight', dpi=300)
    plt.savefig('fertilizer_charts/07_russian_sanctions_evasion.pdf', bbox_inches='tight')
    plt.close()


# Chart 8: Lock System Fertilizer Flow
def create_lock_system_chart():
    plt.figure(figsize=(14, 8))

    locks = ['Lock & Dam 27\n(St. Louis)', 'Arkansas L&D 1', 'Ohio River System\n(Combined)',
             'Upper Mississippi\nLocks']
    tonnages = [2.4, 0.8, 1.2, 0.6]  # Million tonnes

    colors = ['#2E5BBA', '#8FA6DB', '#B8C5E0', '#D4DAE8']

    bars = plt.bar(locks, tonnages, color=colors)

    plt.ylabel('Annual Fertilizer Tonnage (Million Tonnes)', fontsize=12, fontweight='bold')
    plt.title('USACE Lock System Fertilizer Traffic\nUpbound Movement (85% of total traffic)',
              fontsize=14, fontweight='bold', pad=20)

    # Add value labels
    for bar, tonnage in zip(bars, tonnages):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03,
                 f'{tonnage}M tonnes', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.xticks(rotation=0, ha='center')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    # Add note about seasonal patterns
    plt.figtext(0.5, 0.15,
                'Peak Season: October-April (70% of annual tonnage)\nDistribution: 85% Upbound, 15% Downbound',
                ha='center', fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))

    plt.figtext(0.02, 0.02, 'Source: USACE Lock Performance Monitoring System (LPMS)',
                fontsize=8, style='italic')

    plt.savefig('fertilizer_charts/08_lock_system_flow.png', bbox_inches='tight', dpi=300)
    plt.savefig('fertilizer_charts/08_lock_system_flow.pdf', bbox_inches='tight')
    plt.close()


# Main execution function
def generate_all_charts():
    """Generate all fertilizer market visualization charts"""

    print("Generating US Fertilizer Market Visualizations...")
    print("=" * 50)

    # Generate all charts
    charts = [
        ("Port Import Analysis", create_port_chart),
        ("Supplier Countries Analysis", create_country_chart),
        ("Fertilizer Types by Volume", create_fertilizer_types_chart),
        ("USDA Nutrient Categories", create_nutrient_categories_chart),
        ("Transportation Cost Comparison", create_transport_chart),
        ("Production vs Consumption Balance", create_balance_chart),
        ("Russian Network Sanctions Evasion", create_russian_network_chart),
        ("Lock System Fertilizer Flow", create_lock_system_chart)
    ]

    for i, (name, func) in enumerate(charts, 1):
        print(f"Creating Chart {i}: {name}")
        func()
        print(f"✓ Saved: fertilizer_charts/{i:02d}_*.png and *.pdf")

    print("\n" + "=" * 50)
    print("All charts generated successfully!")
    print(f"Charts saved in 'fertilizer_charts/' directory")
    print("Both PNG (high-res) and PDF formats created")
    print("\nFiles created:")

    for i, (name, _) in enumerate(charts, 1):
        filename = name.lower().replace(" ", "_").replace("/", "_")
        print(f"  {i:02d}_{filename}.png")
        print(f"  {i:02d}_{filename}.pdf")


# Run the chart generation
if __name__ == "__main__":
    generate_all_charts()