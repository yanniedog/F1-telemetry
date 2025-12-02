# F1 Dataset - Best Practices Guide

This document covers best practices for data quality, alignment, normalization, cross-linking, and performance optimization.

## Table of Contents

1. [Data Quality](#data-quality)
2. [Handling Missing Data](#handling-missing-data)
3. [Aligning Lap Numbers](#aligning-lap-numbers)
4. [Normalizing Timestamps](#normalizing-timestamps)
5. [Cross-Linking Drivers](#cross-linking-drivers)
6. [Performance Optimization](#performance-optimization)
7. [Data Validation](#data-validation)

## Data Quality

### Source Priority

When multiple sources provide conflicting data, use this priority order:

1. **FIA Official Documents** (highest priority)
2. **Ergast API** (historical data)
3. **OpenF1 API** (modern telemetry)
4. **FastF1 Library** (official timing)
5. **F1.com** (official website)
6. **StatsF1** (third-party statistics)
7. **Wikipedia** (cross-reference only)

### Data Validation Rules

1. **Foreign Key Integrity**
   - Always validate foreign keys before inserting
   - Check that referenced records exist
   - Handle orphaned records gracefully

2. **Data Type Validation**
   - Verify timestamps are valid datetime objects
   - Check numeric values are within reasonable ranges
   - Validate string formats (e.g., driver codes, status codes)

3. **Business Logic Validation**
   - Lap times should be between 10 seconds and 10 minutes
   - Positions should be positive integers
   - Race dates should not be in the future
   - Driver numbers should be unique per race

## Handling Missing Data

### Strategies

1. **Explicit NULL Values**
   - Use NULL for truly missing data
   - Don't use placeholder values (e.g., -1, 0, "N/A")
   - Document why data is missing

2. **Data Availability Tracking**
   - Use `data_availability` table to track what's available
   - Mark sessions/races with missing data
   - Document data gaps in metadata

3. **Graceful Degradation**
   - If telemetry is missing, still store lap times
   - If sector times are missing, still store lap times
   - Don't fail entire import if one data type is missing

### Example: Handling Missing Lap Times

```python
def import_lap_times(race_id, lap_data):
    """Import lap times, handling missing data gracefully."""
    for lap_record in lap_data:
        # Validate required fields
        if not lap_record.get('driver_id') or not lap_record.get('lap'):
            logger.warning(f"Skipping invalid lap record: {lap_record}")
            continue
        
        # Handle missing time
        lap_time = lap_record.get('time')
        if not lap_time:
            # Check if this is expected (e.g., DNF lap)
            if lap_record.get('status') == 'DNF':
                # Store with NULL time
                lap_time = None
            else:
                logger.warning(f"Missing lap time for driver {lap_record['driver_id']}, lap {lap_record['lap']}")
                continue
        
        # Insert into database
        insert_lap_time(race_id, lap_record['driver_id'], lap_record['lap'], lap_time)
```

## Aligning Lap Numbers

### Challenges

Different sources may have different lap numbering:
- Some sources start from 0, others from 1
- Formation laps may or may not be counted
- In-lap/out-lap handling varies

### Solution

1. **Normalize to Standard Format**
   - Use 1-based indexing (first racing lap = 1)
   - Exclude formation laps
   - Document any special cases

2. **Cross-Reference Validation**
   - Compare lap counts across sources
   - Flag discrepancies for manual review
   - Use race distance to validate total laps

### Example: Lap Number Alignment

```python
def align_lap_numbers(lap_data, source):
    """Align lap numbers across sources."""
    normalized_laps = []
    
    for lap in lap_data:
        lap_num = lap.get('lap_number') or lap.get('lap')
        
        # Convert to integer
        try:
            lap_num = int(lap_num)
        except (ValueError, TypeError):
            continue
        
        # Normalize: ensure 1-based indexing
        if source == 'ergast' and lap_num == 0:
            # Ergast may use 0-based, convert to 1-based
            lap_num = 1
        
        # Validate range (reasonable lap numbers)
        if 1 <= lap_num <= 200:  # Max reasonable laps
            lap['lap'] = lap_num
            normalized_laps.append(lap)
        else:
            logger.warning(f"Invalid lap number {lap_num} from {source}")
    
    return normalized_laps
```

## Normalizing Timestamps

### Timezone Handling

1. **Always Store in UTC**
   - Convert all timestamps to UTC before storage
   - Preserve original timezone in metadata if needed
   - Use timezone-aware datetime objects

2. **Session Time vs. Absolute Time**
   - Session time: Relative to session start (for telemetry)
   - Absolute time: Full timestamp (for events)
   - Store both when available

### Example: Timestamp Normalization

```python
from datetime import datetime
import pytz

def normalize_timestamp(timestamp, source_timezone=None):
    """Normalize timestamp to UTC."""
    if timestamp is None:
        return None
    
    # Parse if string
    if isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        return None
    
    # Handle timezone
    if dt.tzinfo is None:
        if source_timezone:
            source_tz = pytz.timezone(source_timezone)
            dt = source_tz.localize(dt)
        else:
            dt = pytz.UTC.localize(dt)
    
    # Convert to UTC
    return dt.astimezone(pytz.UTC)
```

## Cross-Linking Drivers

### Matching Strategy

1. **Primary Keys**
   - Driver code (3-letter abbreviation) - most reliable
   - Driver number (if consistent)
   - Full name (with fuzzy matching)

2. **Fuzzy Matching**
   - Use similarity threshold (e.g., 0.85)
   - Handle name variations (accents, nicknames)
   - Consider nationality and date of birth

3. **Manual Review**
   - Flag uncertain matches for review
   - Maintain mapping table for edge cases
   - Document manual overrides

### Example: Driver Matching

```python
from difflib import SequenceMatcher

def match_driver(driver_data, existing_drivers, threshold=0.85):
    """Match driver against existing drivers."""
    driver_name = driver_data.get('name', '')
    driver_code = driver_data.get('code')
    driver_number = driver_data.get('number')
    
    # Try exact code match first
    if driver_code:
        for existing in existing_drivers:
            if existing.get('code') == driver_code:
                return existing['driver_id']
    
    # Try number match
    if driver_number:
        for existing in existing_drivers:
            if existing.get('number') == driver_number:
                # Verify name similarity
                similarity = calculate_similarity(driver_name, existing.get('name', ''))
                if similarity >= threshold:
                    return existing['driver_id']
    
    # Try name matching
    best_match = None
    best_similarity = 0.0
    
    for existing in existing_drivers:
        similarity = calculate_similarity(driver_name, existing.get('name', ''))
        if similarity > best_similarity and similarity >= threshold:
            best_similarity = similarity
            best_match = existing['driver_id']
    
    return best_match

def calculate_similarity(name1, name2):
    """Calculate name similarity score."""
    # Normalize names
    norm1 = name1.lower().strip()
    norm2 = name2.lower().strip()
    
    # Exact match
    if norm1 == norm2:
        return 1.0
    
    # Sequence matcher
    return SequenceMatcher(None, norm1, norm2).ratio()
```

## Performance Optimization

### Database Optimization

1. **Indexes**
   - Index foreign keys
   - Index frequently queried columns (race_id, driver_id, date)
   - Use composite indexes for common query patterns

2. **Batch Operations**
   - Use bulk inserts instead of individual inserts
   - Use transactions for multiple operations
   - Commit in batches (e.g., every 1000 records)

3. **Query Optimization**
   - Use prepared statements
   - Avoid N+1 queries
   - Use appropriate JOIN types

### Example: Batch Insert

```python
import sqlite3

def batch_insert_lap_times(conn, lap_times, batch_size=1000):
    """Insert lap times in batches."""
    cursor = conn.cursor()
    
    # Prepare statement
    insert_sql = """
        INSERT INTO lap_times (race_id, driver_id, lap, time, milliseconds)
        VALUES (?, ?, ?, ?, ?)
    """
    
    # Process in batches
    for i in range(0, len(lap_times), batch_size):
        batch = lap_times[i:i+batch_size]
        cursor.executemany(insert_sql, batch)
        conn.commit()
        
        logger.info(f"Inserted batch {i//batch_size + 1} ({len(batch)} records)")
```

### Caching Strategy

1. **API Response Caching**
   - Cache all API responses locally
   - Use appropriate TTL (time-to-live)
   - Invalidate cache when data is updated

2. **Database Query Caching**
   - Cache frequently accessed data
   - Use materialized views for complex queries
   - Consider Redis for distributed caching

### Example: Caching

```python
from functools import lru_cache
import time

class DataCache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time())
```

## Data Validation

### Validation Checklist

1. **Before Import**
   - Validate data types
   - Check required fields
   - Verify foreign key references
   - Check for duplicates

2. **During Import**
   - Log all errors and warnings
   - Continue processing on non-fatal errors
   - Track import statistics

3. **After Import**
   - Run data quality checks
   - Generate validation reports
   - Fix identified issues

### Example: Validation Report

```python
def generate_validation_report(db_path):
    """Generate comprehensive validation report."""
    validator = DataValidator(db_path)
    report = validator.generate_quality_report()
    
    print("=== Data Quality Report ===")
    print(f"Foreign Key Errors: {report['summary']['foreign_key_errors']}")
    print(f"Anomalies: {report['summary']['anomalies']}")
    print(f"Tables with Data: {report['summary']['tables_with_data']}")
    print(f"Races without Results: {report['summary']['races_without_results']}")
    print(f"Races without Lap Times: {report['summary']['races_without_lap_times']}")
    
    # Detailed errors
    if report['foreign_key_errors']:
        print("\n=== Foreign Key Errors ===")
        for table, errors in report['foreign_key_errors'].items():
            print(f"\n{table}:")
            for error in errors[:10]:  # First 10
                print(f"  - {error}")
    
    # Anomalies
    if report['anomalies']:
        print("\n=== Anomalies ===")
        for anomaly in report['anomalies'][:10]:  # First 10
            print(f"  - {anomaly['type']}: {anomaly['message']}")
```

## Error Handling

### Best Practices

1. **Logging**
   - Log all errors with context
   - Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
   - Include stack traces for exceptions

2. **Retry Logic**
   - Implement exponential backoff
   - Set maximum retry attempts
   - Handle rate limiting gracefully

3. **Graceful Degradation**
   - Continue processing on non-fatal errors
   - Store partial data when possible
   - Flag incomplete records

### Example: Error Handling

```python
import logging
from time import sleep

logger = logging.getLogger(__name__)

def fetch_with_retry(url, max_retries=3, delay=1):
    """Fetch with retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = delay * (2 ** attempt)
                logger.warning(f"Rate limited, waiting {wait_time}s...")
                sleep(wait_time)
            elif attempt < max_retries - 1:
                sleep(delay * (2 ** attempt))
            else:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                sleep(delay * (2 ** attempt))
            else:
                logger.error(f"Unexpected error after {max_retries} attempts: {e}")
                raise
```

## Summary

1. **Always validate data** before and after import
2. **Handle missing data explicitly** with NULL values
3. **Normalize timestamps** to UTC
4. **Align lap numbers** across sources
5. **Cross-link drivers** using multiple matching strategies
6. **Optimize performance** with indexes and batch operations
7. **Cache aggressively** to reduce API calls
8. **Log comprehensively** for debugging
9. **Handle errors gracefully** with retry logic
10. **Document data gaps** in metadata

