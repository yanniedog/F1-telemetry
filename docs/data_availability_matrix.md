# F1 Historical Dataset - Data Availability Matrix

This document provides a comprehensive overview of what data is available for which years in the F1 historical dataset.

## Summary Table

| Data Type | Availability | Source(s) | Notes |
|-----------|--------------|-----------|-------|
| **Races** | 1950-present | Ergast API | Complete coverage |
| **Drivers** | 1950-present | Ergast API | Complete coverage |
| **Constructors** | 1950-present | Ergast API | Complete coverage |
| **Circuits** | 1950-present | Ergast API | Complete coverage |
| **Race Results** | 1950-present | Ergast API | Complete coverage |
| **Lap Times** | 1996-present | Ergast API | Limited before 1996 |
| **Pit Stops** | 2012-present | Ergast API | Duration data from 2012+ |
| **Sector Times** | 2018-present | FastF1, OpenF1 | Modern years only |
| **Tyre Compounds** | 2018-present | FastF1 | Modern years only |
| **Weather Data** | 2018-present | FastF1 | Modern years only |
| **Telemetry** | 2018-present | OpenF1, FastF1 | Speed, throttle, brake, gear, RPM, DRS |
| **GPS Position** | 2018-present | OpenF1, FastF1 | X/Y coordinates |
| **Track Status** | 2018-present | OpenF1 | Green, yellow, SC, VSC, red flags |
| **Safety Car Periods** | 2000-present | StatsF1 | Historical data from StatsF1 |
| **VSC Periods** | 2015-present | StatsF1, OpenF1 | VSC introduced in 2015 |
| **Red Flags** | 2000-present | StatsF1, OpenF1 | Limited historical data |
| **DRS Zones** | 2011-present | F1.com, FastF1 | DRS introduced in 2011 |

## Detailed Breakdown by Category

### Available for All Years (1950-present)

#### Core Reference Data
- **Seasons**: All seasons from 1950 to present
- **Races**: Every race in every season
- **Drivers**: All drivers who participated
- **Constructors**: All teams/constructors
- **Circuits**: All circuits that hosted races
- **Race Results**: Final positions, points, status (DNF, DNS, DSQ)

**Sources:**
- Ergast API (primary)
- Wikipedia (cross-reference)

**Coverage:** 100% complete

### Available from 1980+

#### Detailed Timing Data
- **Lap Times**: Individual lap times for all drivers
  - Note: Some races may have incomplete lap time data
  - Best coverage from 1996 onwards

**Sources:**
- Ergast API

**Coverage:** ~95% of races from 1980+, ~99% from 1996+

### Available from 2012+

#### Pit Stop Details
- **Pit Stop Durations**: Detailed pit stop timing
  - Before 2012: Only pit stop lap numbers available
  - From 2012: Full duration data

**Sources:**
- Ergast API

**Coverage:** 100% from 2012+

### Available from 2018+ Only

#### Modern Telemetry and Advanced Data

**Telemetry Data:**
- Speed trace (Hz-level sampling)
- Throttle position
- Brake application
- Gear selection
- RPM (when available)
- DRS state
- GPS X/Y position
- Car delta times
- Micro-sector times

**Session Data:**
- Sector times (S1, S2, S3) for all laps
- Tyre compound usage per stint
- Weather data (air temp, track temp, humidity, precipitation)
- Track status changes
- Marshal sector flags

**Sources:**
- OpenF1 API (primary for telemetry)
- FastF1 library (primary for timing and weather)
- F1.com (supplementary)

**Coverage:** 
- Telemetry: ~95% of sessions from 2018+
- Weather: ~90% of sessions from 2018+
- Sector times: ~98% of sessions from 2018+

### Available from Specific Years

#### Safety Car Periods
- **2000-present**: Comprehensive data from StatsF1
- **2018-present**: Real-time data from OpenF1 API

**Coverage:** ~80% of races from 2000+, ~95% from 2018+

#### Virtual Safety Car (VSC)
- **2015-present**: VSC introduced in 2015
- **2018-present**: Real-time data from OpenF1 API

**Coverage:** ~90% of races from 2015+, ~98% from 2018+

#### Red Flags
- **2000-present**: Historical data from StatsF1
- **2018-present**: Real-time data from OpenF1 API

**Coverage:** ~70% of races from 2000+, ~95% from 2018+

#### DRS Zones
- **2011-present**: DRS introduced in 2011
- Circuit-specific DRS zone configurations

**Coverage:** 100% from 2011+

### Not Available Publicly

The following data is **not available** from free public sources:

1. **Detailed Telemetry Pre-2018**
   - No public telemetry data exists for races before 2018
   - Only lap times and basic timing available

2. **Comprehensive Incident Data**
   - Limited incident reporting for historical races
   - Modern races (2018+) have better coverage via track status

3. **Some Historical Weather Data**
   - Weather data is sparse before 2018
   - Some race reports may mention weather conditions

4. **Detailed Strategy Data (Pre-2018)**
   - Tyre compound usage not tracked before 2018
   - Pit stop strategies not fully documented

5. **Real-time Timing Data (Historical)**
   - No real-time timing streams for historical races
   - Only final results and some lap times available

## Data Source Reliability

### Most Reliable Sources (Primary)
1. **Ergast API**: Historical data (1950-2024)
   - Note: Deprecated end of 2024, migrating to Jolpica F1 API
   - Reliability: 99%+

2. **OpenF1 API**: Modern telemetry (2018+)
   - Reliability: 95%+

3. **FastF1 Library**: Official F1 timing data (2018+)
   - Reliability: 98%+

### Secondary Sources
4. **FIA PDFs**: Official race classifications
   - Reliability: 100% (when available)
   - Coverage: Varies by year

5. **F1.com**: Official website data
   - Reliability: 90%+
   - Coverage: Modern years better than historical

6. **StatsF1**: Historical statistics
   - Reliability: 85%+
   - Coverage: Good for modern years, sparse for early years

### Cross-Reference Sources
7. **Wikipedia**: Race pages
   - Reliability: 80%+
   - Use: Cross-reference only, not primary source

## Data Quality Notes

### Known Gaps
- **1950-1979**: Limited lap time data
- **1980-1995**: Some races missing lap times
- **Pre-2012**: Pit stop durations not available
- **Pre-2018**: No telemetry, sector times, or detailed weather

### Data Completeness by Era

**1950-1979:**
- Race results: 100%
- Lap times: ~20%
- Pit stops: 0% (not tracked)

**1980-1995:**
- Race results: 100%
- Lap times: ~85%
- Pit stops: ~10% (lap numbers only)

**1996-2011:**
- Race results: 100%
- Lap times: ~99%
- Pit stops: ~90% (lap numbers)
- DRS zones: 0% (not introduced)

**2012-2017:**
- Race results: 100%
- Lap times: 100%
- Pit stops: 100% (with durations)
- DRS zones: 100%
- Telemetry: 0% (not available)

**2018-present:**
- Race results: 100%
- Lap times: 100%
- Pit stops: 100%
- Sector times: ~98%
- Telemetry: ~95%
- Weather: ~90%
- Track status: ~95%

## Recommendations

1. **For Historical Analysis (1950-2017)**: Use Ergast API as primary source
2. **For Modern Analysis (2018+)**: Combine OpenF1 API and FastF1 library
3. **For Incident Data**: Use StatsF1 for historical, OpenF1 for modern
4. **For Cross-Validation**: Always cross-reference critical data points

## Future Data Availability

- **Jolpica F1 API**: Successor to Ergast API (post-2024)
- **OpenF1 API**: Continuously updated with new race data
- **FastF1 Library**: Updated regularly with new sessions

