# F1 Historical Dataset - Project Structure

All code and files are located in the working directory: `C:\Users\jkoka\.cursor\worktrees\F1-telemetry\viw`

## Directory Structure

```
viw/
├── main.py                          # Main orchestration script
├── README.md                        # Project overview and quick start
├── requirements.txt                 # Python dependencies
├── PROJECT_STRUCTURE.md            # This file
│
├── config/                          # Configuration files
│   ├── __init__.py
│   ├── config.yaml                 # Main configuration
│   └── data_sources.yaml            # Data source endpoints and settings
│
├── schema/                          # Database schemas
│   ├── schema.sql                  # SQLite schema
│   ├── schema_postgresql.sql       # PostgreSQL schema
│   └── relationships.md            # ER diagram documentation
│
├── data_sources/                    # Data fetching modules
│   ├── __init__.py
│   ├── ergast_fetcher.py           # Ergast API fetcher
│   ├── openf1_fetcher.py           # OpenF1 API fetcher
│   ├── fastf1_fetcher.py           # FastF1 library integration
│   ├── statsf1_scraper.py          # StatsF1 web scraper
│   ├── fia_pdf_parser.py           # FIA PDF parser
│   └── f1com_scraper.py            # F1.com scraper
│
├── etl/                             # ETL pipeline modules
│   ├── __init__.py
│   ├── data_normalizer.py          # Data normalization
│   ├── driver_matcher.py           # Driver cross-linking
│   ├── data_merger.py              # Data merging
│   └── data_validator.py           # Data validation
│
├── utils/                           # Utility modules
│   ├── __init__.py
│   ├── logger.py                   # Logging utility
│   ├── cache_manager.py            # Cache management
│   └── rate_limiter.py             # API rate limiting
│
├── exports/                         # Export functionality
│   ├── __init__.py
│   ├── export_to_csv.py            # CSV exporter
│   └── export_to_parquet.py       # Parquet exporter
│
├── docs/                            # Documentation
│   ├── api_examples.md             # API usage examples
│   ├── best_practices.md           # Best practices guide
│   ├── data_availability_matrix.md # Data availability by year
│   └── setup_guide.md              # Setup and usage guide
│
├── data/                            # Database and data files
│   └── f1_dataset.db               # SQLite database
│
├── cache/                           # Cached API responses
│   ├── cache_metadata.json
│   └── *.pkl                       # Cached data files
│
└── logs/                            # Log files
    └── f1_dataset_YYYYMMDD.log     # Daily log files
```

## Key Files

### Main Script
- **main.py** - Entry point for all operations

### Configuration
- **config/config.yaml** - Main configuration (database, cache, logging, etc.)
- **config/data_sources.yaml** - API endpoints and rate limits

### Database
- **schema/schema.sql** - Complete SQLite database schema
- **data/f1_dataset.db** - SQLite database file

### Core Modules
- **data_sources/** - All data fetching modules
- **etl/** - Data processing and validation
- **utils/** - Shared utilities
- **exports/** - Data export functionality

### Documentation
- **README.md** - Project overview
- **docs/** - Comprehensive documentation

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database:**
   ```bash
   sqlite3 data/f1_dataset.db < schema/schema.sql
   ```

3. **Run the script:**
   ```bash
   python main.py --fetch-openf1 --year 2023
   python main.py --validate
   python main.py --export-csv
   ```

## File Count

- Python modules: ~20 files
- Configuration files: 2 YAML files
- Database schemas: 2 SQL files
- Documentation: 5 Markdown files
- Total source files: ~30 files

All code is self-contained in this directory.

