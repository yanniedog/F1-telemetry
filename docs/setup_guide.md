# F1 Historical Dataset - Setup Guide

Complete installation and usage instructions for the F1 historical dataset.

## Table of Contents

1. [Installation](#installation)
2. [Database Initialization](#database-initialization)
3. [Configuration](#configuration)
4. [Usage Examples](#usage-examples)
5. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- SQLite 3 (included with Python)
- Internet connection (for data fetching)

### Step 1: Clone or Download

```bash
# If using git
git clone <repository-url>
cd f1-dataset

# Or download and extract the project files
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `requests` - HTTP library for API calls
- `pandas` - Data manipulation
- `sqlalchemy` - Database ORM
- `fastf1` - FastF1 library for modern F1 data
- `beautifulsoup4` - Web scraping
- `pdfplumber` - PDF parsing
- `pyarrow` - Parquet export
- And other dependencies

### Step 3: Verify Installation

```bash
python -c "import fastf1; print('FastF1 installed successfully')"
python -c "import requests; print('Requests installed successfully')"
```

## Database Initialization

### Step 1: Create Database Directory

```bash
mkdir -p data
```

### Step 2: Initialize Database Schema

```bash
# Using SQLite
sqlite3 data/f1_dataset.db < schema/schema.sql

# Or using Python
python -c "
import sqlite3
with open('schema/schema.sql', 'r') as f:
    conn = sqlite3.connect('data/f1_dataset.db')
    conn.executescript(f.read())
    conn.close()
print('Database initialized successfully')
"
```

### Step 3: Verify Database

```bash
sqlite3 data/f1_dataset.db "SELECT name FROM sqlite_master WHERE type='table';"
```

You should see all the table names listed.

## Configuration

### Step 1: Review Configuration Files

Edit `config/config.yaml` to customize:
- Database path
- Cache settings
- Logging configuration
- Data fetching options

Edit `config/data_sources.yaml` to configure:
- API endpoints
- Rate limits
- Source priorities

### Step 2: Create Cache Directories

```bash
mkdir -p cache
mkdir -p cache/fastf1
mkdir -p cache/fia_pdfs
mkdir -p logs
```

## Usage Examples

### Example 1: Fetch Historical Data from Ergast

```python
from data_sources.ergast_fetcher import ErgastFetcher

# Initialize fetcher
fetcher = ErgastFetcher()

# Fetch all seasons
seasons = fetcher.fetch_seasons()
print(f"Found {len(seasons)} seasons")

# Fetch races for a specific year
races = fetcher.fetch_races(year=2023)
print(f"Found {len(races)} races in 2023")

# Fetch race results
results = fetcher.fetch_results(year=2023, round_num=1)
print(f"Found {len(results)} results")
```

### Example 2: Fetch Modern Telemetry from OpenF1

```python
from data_sources.openf1_fetcher import OpenF1Fetcher

# Initialize fetcher
fetcher = OpenF1Fetcher()

# Find sessions for a year
sessions = fetcher.fetch_sessions(year=2023, session_name='Race')
print(f"Found {len(sessions)} race sessions")

# Fetch telemetry for a session
if sessions:
    session_key = sessions[0]['session_key']
    telemetry = fetcher.fetch_session_telemetry(session_key)
    print(f"Fetched telemetry: {len(telemetry['car_data'])} data points")
```

### Example 3: Use FastF1 Library

```python
from data_sources.fastf1_fetcher import FastF1Fetcher

# Initialize fetcher
fetcher = FastF1Fetcher()

# Fetch session data
session_data = fetcher.fetch_session_data(2023, 'Monza', 'R')
print(f"Laps: {len(session_data['laps'])}")
print(f"Sector times: {len(session_data['sector_times'])}")
print(f"Weather records: {len(session_data['weather'])}")
```

### Example 4: Run Full Data Import

```python
from main import F1DatasetBuilder

# Initialize builder
builder = F1DatasetBuilder()

# Fetch all historical data
builder.fetch_all_data(start_year=2020, end_year=2023)

# Or fetch specific sources
builder.fetch_ergast_data(start_year=2020, end_year=2023)
builder.fetch_openf1_data(year=2023)
builder.fetch_fastf1_data(year=2023)
```

### Example 5: Export Data

```python
from exports.export_to_csv import CSVExporter
from exports.export_to_parquet import ParquetExporter

# Export to CSV
csv_exporter = CSVExporter()
csv_exporter.export()

# Export to Parquet
parquet_exporter = ParquetExporter()
parquet_exporter.export()
```

### Example 6: Validate Data

```python
from etl.data_validator import DataValidator

# Initialize validator
validator = DataValidator()

# Generate quality report
report = validator.generate_quality_report()

# Print summary
print(f"Foreign key errors: {report['summary']['foreign_key_errors']}")
print(f"Anomalies: {report['summary']['anomalies']}")
```

## Command Line Usage

### Basic Usage

```bash
# Run main script
python main.py --fetch-all --start-year 2020 --end-year 2023

# Fetch specific source
python main.py --fetch-ergast --start-year 2020 --end-year 2023
python main.py --fetch-openf1 --year 2023
python main.py --fetch-fastf1 --year 2023

# Export data
python main.py --export-csv
python main.py --export-parquet

# Validate data
python main.py --validate
```

### Advanced Options

```bash
# Incremental update (only new data)
python main.py --fetch-all --incremental

# Specific sources only
python main.py --fetch-ergast --fetch-openf1

# Export with custom options
python main.py --export-csv --output-dir exports/my_exports
python main.py --export-parquet --partition-by season --compression gzip
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:** `ModuleNotFoundError: No module named 'fastf1'`

**Solution:**
```bash
pip install -r requirements.txt
```

#### 2. Database Locked

**Problem:** `sqlite3.OperationalError: database is locked`

**Solution:**
- Close any other connections to the database
- Wait for ongoing operations to complete
- Check for hung processes

#### 3. API Rate Limiting

**Problem:** `429 Too Many Requests`

**Solution:**
- Reduce request frequency
- Enable caching (already enabled by default)
- Increase delays between requests in config

#### 4. FastF1 Cache Issues

**Problem:** FastF1 fails to load sessions

**Solution:**
```bash
# Clear FastF1 cache
rm -rf cache/fastf1/*

# Or specify custom cache directory
export FASTF1_CACHE_DIR=./cache/fastf1
```

#### 5. Missing Data

**Problem:** Some races missing lap times or telemetry

**Solution:**
- Check data availability matrix (see `docs/data_availability_matrix.md`)
- Some data is not available for all years
- Verify source availability for specific year/race

#### 6. Driver Matching Issues

**Problem:** Drivers not matching across sources

**Solution:**
- Review driver matching logs
- Adjust similarity threshold in config
- Manually review and update driver mappings

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or in config:

```yaml
logging:
  log_level: "DEBUG"
```

### Getting Help

1. Check logs in `logs/` directory
2. Review error messages for specific issues
3. Consult documentation:
   - `docs/data_availability_matrix.md` - What data is available
   - `docs/api_examples.md` - API usage examples
   - `docs/best_practices.md` - Best practices guide

## Performance Tips

1. **Use Caching**
   - Cache is enabled by default
   - Reduces API calls significantly
   - Speeds up repeated operations

2. **Batch Operations**
   - Fetch data in batches
   - Use transactions for database operations
   - Commit in intervals

3. **Parallel Processing**
   - Use multiple workers for independent operations
   - Be mindful of rate limits
   - Don't exceed API limits

4. **Incremental Updates**
   - Use `--incremental` flag for updates
   - Only fetch new data
   - Much faster than full rebuild

## Next Steps

1. **Start Small**: Test with a single year first
2. **Verify Data**: Run validation after import
3. **Explore Data**: Use exported CSV/Parquet files
4. **Customize**: Adjust configuration for your needs
5. **Contribute**: Report issues and improvements

## Support

For issues, questions, or contributions:
- Check existing documentation
- Review error logs
- Consult API documentation for specific sources

