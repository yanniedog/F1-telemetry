# F1 Historical Dataset

A comprehensive, historically complete Formula 1 racing dataset (1950-present) built from free, legally accessible public data sources.

## Overview

This project provides a complete blueprint for building the most comprehensive Formula 1 historical dataset possible using only free, public data sources. It includes:

- **Full historical coverage** (1950 → present): Every race, driver, team, circuit, and result
- **Telemetry coverage** (2018+): Speed, throttle, brake, gear, RPM, DRS, GPS position
- **Track-level metadata**: Circuit layouts, DRS zones, lap lengths
- **Strategy and incident data**: Safety car periods, VSC, red flags, pit stops
- **Complete ETL pipeline**: Data fetching, normalization, merging, validation, and export

## Features

- ✅ **Complete Database Schema**: SQLite/PostgreSQL schema with all tables and relationships
- ✅ **Multiple Data Sources**: Ergast API, OpenF1 API, FastF1, StatsF1, FIA PDFs, F1.com
- ✅ **Data Normalization**: Timestamps, lap numbers, status codes, names
- ✅ **Driver Matching**: Cross-link drivers across sources with fuzzy matching
- ✅ **Data Validation**: Comprehensive quality checks and anomaly detection
- ✅ **Export Options**: CSV and Parquet formats with partitioning
- ✅ **Caching**: Local caching to reduce API calls and enable offline processing
- ✅ **Rate Limiting**: Respectful API usage with automatic rate limiting
- ✅ **Comprehensive Documentation**: Setup guides, API examples, best practices

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
sqlite3 data/f1_dataset.db < schema/schema.sql
```

### Basic Usage

```python
from main import F1DatasetBuilder

# Initialize builder
builder = F1DatasetBuilder()

# Fetch historical data
builder.fetch_ergast_data(start_year=2020, end_year=2023)

# Fetch modern telemetry
builder.fetch_openf1_data(year=2023)

# Validate data
builder.validate_data()

# Export to CSV
builder.export_csv()
```

### Command Line

```bash
# Fetch all data
python main.py --fetch-all --start-year 2020 --end-year 2023

# Export data
python main.py --export-csv
python main.py --export-parquet

# Validate
python main.py --validate
```

## Project Structure

```
f1-dataset/
├── schema/                 # Database schemas (SQLite & PostgreSQL)
├── data_sources/           # Data fetchers for each source
├── etl/                    # ETL pipeline (normalizer, matcher, merger, validator)
├── utils/                  # Utilities (logger, cache, rate limiter)
├── exports/                # Export functionality (CSV, Parquet)
├── docs/                   # Documentation
├── config/                 # Configuration files
├── main.py                 # Main orchestration script
└── requirements.txt        # Python dependencies
```

## Data Sources

| Source | Coverage | Data Types |
|--------|----------|------------|
| **Ergast API** | 1950-2024 | Races, drivers, constructors, circuits, results, lap times, pit stops |
| **OpenF1 API** | 2018+ | Telemetry, GPS position, track status, weather |
| **FastF1** | 2018+ | Sector times, tyre compounds, weather, micro-sectors |
| **StatsF1** | 2000+ | Safety car periods, VSC, red flags, incidents |
| **FIA PDFs** | Varies | Official race classifications |
| **F1.com** | Varies | Session summaries, circuit metadata |

## Data Availability

- **Available for all years (1950-present)**: Races, drivers, constructors, circuits, race results
- **Available from 1980+**: Detailed lap times, pit stops
- **Available from 2012+**: Pit stop durations
- **Available from 2018+**: Telemetry, sector times, tyre compounds, weather, track status

See [Data Availability Matrix](docs/data_availability_matrix.md) for complete details.

## Documentation

- [Setup Guide](docs/setup_guide.md) - Installation and usage instructions
- [API Examples](docs/api_examples.md) - Working code examples for all data sources
- [Best Practices](docs/best_practices.md) - Data quality, normalization, performance
- [Data Availability Matrix](docs/data_availability_matrix.md) - What data exists for which years

## Configuration

Edit `config/config.yaml` to customize:
- Database settings
- Cache configuration
- Logging options
- Data fetching preferences

Edit `config/data_sources.yaml` to configure:
- API endpoints
- Rate limits
- Source priorities

## Requirements

- Python 3.9+
- SQLite 3 (included with Python)
- See `requirements.txt` for Python packages

## License

This project uses only free, publicly available data sources. All data is obtained legally and in compliance with source terms of service.

## Contributing

Contributions welcome! Please:
1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Respect API rate limits

## Acknowledgments

- **Ergast API** - Historical F1 data (deprecated end of 2024, migrating to Jolpica F1 API)
- **OpenF1** - Free telemetry API
- **FastF1** - Python library for F1 timing data
- **StatsF1** - Historical statistics
- **FIA** - Official race documents
- **F1.com** - Official Formula 1 website

## Support

For issues, questions, or contributions:
- Check documentation in `docs/` directory
- Review error logs in `logs/` directory
- Consult API documentation for specific sources

## Status

✅ All core components implemented
✅ Database schema complete
✅ Data fetchers for all major sources
✅ ETL pipeline functional
✅ Export functionality ready
✅ Comprehensive documentation

Ready for data collection and analysis!

