# Scripts

Data processing and automation scripts for maritime/shipping operations.

## Overview

This repository contains Python scripts for:
- **Vessel movement and port call data processing** (Panjiva trade data)
- **Company name normalization** and harmonization
- **Geocoding** addresses using Nominatim and Census APIs
- **Invoice generation** (PDF)
- **Weather data retrieval** (NOAA)

## Project Structure

```
Scripts/
├── panjiva/           # Shipping/trade data pipeline
│   ├── step1.py       # Load CSVs, merge, standardize IMO/vessel names
│   ├── step2.py       # Further processing with berth dictionary
│   └── claude_normalize_v3.py  # Fuzzy company name matching
├── geocode_*.py       # Address geocoding utilities
├── invoice.py         # PDF invoice generator
├── brantley/          # Document processing scripts
├── scratch/           # Utility and experimental scripts
├── Input/             # Raw input data (not tracked)
├── Output/            # Processed output (not tracked)
└── Dictionary/        # Reference/lookup data (not tracked)
```

## Setup

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install pandas reportlab geopandas shapely requests
```

## Usage

```powershell
# Run panjiva data pipeline
python panjiva\step1.py
python panjiva\step2.py

# Generate invoice
python invoice.py

# Geocode addresses
python geocode_nominatim.py
```

## Data Pipeline

The panjiva scripts follow a consistent pattern:
1. Load CSV files from `Input/` directory
2. Standardize fields (IMO to 7 chars, strip names)
3. Apply exclusion lists for non-vessel records
4. Process and transform data
5. Output to `Output/` directory with timestamps

## License

Private repository.
