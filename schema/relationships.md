# F1 Dataset Database Relationships

## Entity Relationship Overview

This document describes the relationships between tables in the F1 historical dataset schema.

## Core Reference Tables

### Seasons
- **Primary Key:** `season_id`
- **Relationships:**
  - One-to-many with `races` (one season has many races)

### Circuits
- **Primary Key:** `circuit_id`
- **Relationships:**
  - One-to-many with `races` (one circuit hosts many races)
  - One-to-many with `circuit_configurations` (circuit changes over years)
  - One-to-many with `drs_zones` (DRS zones per circuit per year)

### Constructors
- **Primary Key:** `constructor_id`
- **Relationships:**
  - One-to-many with `race_results` (one constructor has many race results)

### Drivers
- **Primary Key:** `driver_id`
- **Relationships:**
  - One-to-many with `race_results`
  - One-to-many with `lap_times`
  - One-to-many with `sector_times`
  - One-to-many with `pit_stops`
  - One-to-many with `tyre_stints`
  - One-to-many with `telemetry`
  - One-to-many with `telemetry_position`
  - One-to-many with `telemetry_delta`
  - One-to-many with `incidents`

## Race and Session Hierarchy

### Races
- **Primary Key:** `race_id`
- **Foreign Keys:**
  - `season_id` → `seasons(season_id)`
  - `circuit_id` → `circuits(circuit_id)`
- **Relationships:**
  - Many-to-one with `seasons`
  - Many-to-one with `circuits`
  - One-to-many with `sessions`
  - One-to-many with `race_results`
  - One-to-many with `lap_times`
  - One-to-many with `sector_times`
  - One-to-many with `pit_stops`
  - One-to-many with `tyre_stints`
  - One-to-many with `safety_car_periods`
  - One-to-many with `virtual_safety_car_periods`
  - One-to-many with `red_flags`
  - One-to-many with `incidents`
  - One-to-many with `data_availability`

### Sessions
- **Primary Key:** `session_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
- **Relationships:**
  - Many-to-one with `races`
  - One-to-many with `sector_times`
  - One-to-many with `weather`
  - One-to-many with `telemetry`
  - One-to-many with `telemetry_position`
  - One-to-many with `telemetry_delta`
  - One-to-many with `track_status`
  - One-to-many with `red_flags`
  - One-to-many with `incidents`
  - One-to-many with `data_availability`

## Results and Timing Data

### Race Results
- **Primary Key:** `result_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
  - `driver_id` → `drivers(driver_id)`
  - `constructor_id` → `constructors(constructor_id)`
- **Relationships:**
  - Many-to-one with `races`
  - Many-to-one with `drivers`
  - Many-to-one with `constructors`

### Lap Times
- **Primary Key:** `lap_time_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
  - `driver_id` → `drivers(driver_id)`
- **Unique Constraint:** `(race_id, driver_id, lap)`

### Sector Times
- **Primary Key:** `sector_time_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
  - `session_id` → `sessions(session_id)`
  - `driver_id` → `drivers(driver_id)`
- **Unique Constraint:** `(race_id, driver_id, lap, sector)`

### Pit Stops
- **Primary Key:** `pit_stop_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
  - `driver_id` → `drivers(driver_id)`
- **Unique Constraint:** `(race_id, driver_id, stop)`

### Tyre Stints
- **Primary Key:** `stint_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
  - `driver_id` → `drivers(driver_id)`
- **Unique Constraint:** `(race_id, driver_id, stint_number)`

## Telemetry Data

### Telemetry
- **Primary Key:** `telemetry_id`
- **Foreign Keys:**
  - `session_id` → `sessions(session_id)`
  - `driver_id` → `drivers(driver_id)`
- **Indexes:** `(session_id, driver_id)`, `(session_id, time)`

### Telemetry Position
- **Primary Key:** `position_id`
- **Foreign Keys:**
  - `session_id` → `sessions(session_id)`
  - `driver_id` → `drivers(driver_id)`

### Telemetry Delta
- **Primary Key:** `delta_id`
- **Foreign Keys:**
  - `session_id` → `sessions(session_id)`
  - `driver_id` → `drivers(driver_id)`

## Weather and Track Status

### Weather
- **Primary Key:** `weather_id`
- **Foreign Keys:**
  - `session_id` → `sessions(session_id)`
  - `race_id` → `races(race_id)`

### Track Status
- **Primary Key:** `status_id`
- **Foreign Keys:**
  - `session_id` → `sessions(session_id)`

## Incidents and Safety Periods

### Safety Car Periods
- **Primary Key:** `sc_period_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
- **Unique Constraint:** `(race_id, period_number)`

### Virtual Safety Car Periods
- **Primary Key:** `vsc_period_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
- **Unique Constraint:** `(race_id, period_number)`

### Red Flags
- **Primary Key:** `red_flag_id`
- **Foreign Keys:**
  - `session_id` → `sessions(session_id)`
  - `race_id` → `races(race_id)`
- **Unique Constraint:** `(session_id, flag_number)`

### Incidents
- **Primary Key:** `incident_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
  - `session_id` → `sessions(session_id)` (optional)
  - `driver_id` → `drivers(driver_id)` (optional)

## Circuit Metadata

### Circuit Configurations
- **Primary Key:** `config_id`
- **Foreign Keys:**
  - `circuit_id` → `circuits(circuit_id)`
- **Unique Constraint:** `(circuit_id, year)`

### DRS Zones
- **Primary Key:** `drs_zone_id`
- **Foreign Keys:**
  - `circuit_id` → `circuits(circuit_id)`
- **Unique Constraint:** `(circuit_id, year, zone_number)`

## Data Availability

### Data Availability
- **Primary Key:** `availability_id`
- **Foreign Keys:**
  - `race_id` → `races(race_id)`
  - `session_id` → `sessions(session_id)` (optional)
- Tracks what data types are available for each race/session

## Key Relationships Summary

1. **Season → Races → Sessions** (hierarchical)
2. **Circuit → Races** (one circuit, many races)
3. **Driver → Results/Times/Telemetry** (one driver, many data points)
4. **Constructor → Results** (one constructor, many results)
5. **Session → Telemetry/Weather/Track Status** (one session, many telemetry points)
6. **Race → Incidents/Safety Car** (one race, many incidents/periods)

