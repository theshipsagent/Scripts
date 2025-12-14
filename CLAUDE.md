# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data processing and automation scripts for maritime/shipping operations, primarily focused on:
- Vessel movement and port call data processing (Panjiva trade data)
- Company name normalization and harmonization
- Geocoding addresses
- Invoice generation
- Weather data retrieval

## Running Scripts

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run scripts directly
python script_name.py

# For panjiva pipeline scripts
python panjiva\step1.py
python panjiva\step2.py
```

## Project Structure

```
Scripts/
├── panjiva/           # Shipping/trade data pipeline
│   ├── step1.py       # Load CSVs, merge, standardize IMO/vessel names
│   ├── step2.py       # Further processing with berth dictionary
│   ├── claude_normalize_v3.py  # Fuzzy company name matching
│   └── *_harmonization*.py     # Shipper/consignee normalization
├── Input/             # Raw input data (CSV files)
├── Output/            # Processed output files
├── Dictionary/        # Reference/lookup data
├── geocode_*.py       # Address geocoding (Nominatim, Census API)
├── invoice.py         # PDF invoice generator (ReportLab)
└── .venv/             # Python 3.13 virtual environment
```

## Data Pipeline Pattern

The panjiva scripts follow a consistent pattern:
1. Load CSV files from `Input/` directory
2. Standardize fields (IMO to 7 chars, strip names)
3. Apply exclusion lists for non-vessel records
4. Process and transform data
5. Output to `Output/` directory with timestamps

## Common Conventions

- **Timestamps**: Use `stamp()` helper for console output with `[YYYY-MM-DD HH:MM:SS]` prefix
- **Paths**: Hardcoded at script top using raw strings (`r"/Input"`)
- **Data types**: Load CSVs with `dtype=str` to preserve leading zeros
- **Exclusions**: Vessel name exclusion sets defined at module level
- **Logging**: Scripts in root use Python logging to `C:/Users/wsd3/OneDrive/GRoK/Logs/`

## Key Dependencies

- pandas - Data manipulation
- reportlab - PDF generation (invoices)
- geopandas, shapely - Geospatial operations
- requests - API calls (geocoding, weather)
- tkinter - File dialogs for interactive scripts
- difflib - Fuzzy string matching
