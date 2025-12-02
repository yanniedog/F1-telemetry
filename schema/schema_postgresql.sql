-- F1 Historical Dataset - PostgreSQL Schema
-- Similar to SQLite but with PostgreSQL-specific features
-- Covers all data from 1950 to present

-- Enable UUID extension if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core reference tables
CREATE TABLE IF NOT EXISTS seasons (
    season_id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL UNIQUE,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS circuits (
    circuit_id SERIAL PRIMARY KEY,
    circuit_ref TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    location TEXT,
    country TEXT,
    latitude REAL,
    longitude REAL,
    altitude INTEGER,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS constructors (
    constructor_id SERIAL PRIMARY KEY,
    constructor_ref TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    nationality TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drivers (
    driver_id SERIAL PRIMARY KEY,
    driver_ref TEXT UNIQUE NOT NULL,
    number INTEGER,
    code TEXT,
    forename TEXT NOT NULL,
    surname TEXT NOT NULL,
    date_of_birth DATE,
    nationality TEXT,
    url TEXT,
    -- Cross-source IDs for matching
    ergast_id INTEGER,
    openf1_id INTEGER,
    fastf1_id TEXT,
    -- Unified name for matching
    full_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Race and session tables
CREATE TABLE IF NOT EXISTS races (
    race_id SERIAL PRIMARY KEY,
    season_id INTEGER NOT NULL,
    round INTEGER NOT NULL,
    circuit_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    date DATE NOT NULL,
    time TIME,
    url TEXT,
    fp1_date DATE,
    fp1_time TIME,
    fp2_date DATE,
    fp2_time TIME,
    fp3_date DATE,
    fp3_time TIME,
    quali_date DATE,
    quali_time TIME,
    sprint_date DATE,
    sprint_time TIME,
    race_date DATE NOT NULL,
    race_time TIME,
    -- Timezone information
    timezone TEXT,
    local_timezone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (season_id) REFERENCES seasons(season_id),
    FOREIGN KEY (circuit_id) REFERENCES circuits(circuit_id),
    UNIQUE(season_id, round)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    session_type TEXT NOT NULL CHECK(session_type IN ('FP1', 'FP2', 'FP3', 'Q', 'Sprint', 'Race', 'Sprint Qualifying', 'Sprint Shootout')),
    session_name TEXT,
    date DATE NOT NULL,
    time TIME,
    -- Session keys for API lookups
    ergast_session_key TEXT,
    openf1_session_key INTEGER,
    fastf1_session_key TEXT,
    -- Data availability flags
    has_telemetry BOOLEAN DEFAULT FALSE,
    has_sector_times BOOLEAN DEFAULT FALSE,
    has_weather BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    UNIQUE(race_id, session_type)
);

-- Results and timing tables
CREATE TABLE IF NOT EXISTS race_results (
    result_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    constructor_id INTEGER NOT NULL,
    number INTEGER,
    grid INTEGER,
    position INTEGER,
    position_text TEXT,
    position_order INTEGER,
    points REAL,
    laps INTEGER,
    time TEXT,
    milliseconds INTEGER,
    fastest_lap INTEGER,
    rank INTEGER,
    fastest_lap_time TEXT,
    fastest_lap_speed REAL,
    status_id INTEGER,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id)
);

CREATE TABLE IF NOT EXISTS lap_times (
    lap_time_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    lap INTEGER NOT NULL,
    position INTEGER,
    time TEXT,
    milliseconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    UNIQUE(race_id, driver_id, lap)
);

CREATE TABLE IF NOT EXISTS sector_times (
    sector_time_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    session_id INTEGER,
    driver_id INTEGER NOT NULL,
    lap INTEGER NOT NULL,
    sector INTEGER NOT NULL CHECK(sector IN (1, 2, 3)),
    time TEXT,
    milliseconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    UNIQUE(race_id, driver_id, lap, sector)
);

CREATE TABLE IF NOT EXISTS pit_stops (
    pit_stop_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    stop INTEGER NOT NULL,
    lap INTEGER NOT NULL,
    time TEXT,
    duration TEXT,
    duration_milliseconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    UNIQUE(race_id, driver_id, stop)
);

CREATE TABLE IF NOT EXISTS tyre_stints (
    stint_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    stint_number INTEGER NOT NULL,
    compound TEXT CHECK(compound IN ('SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET', 'C1', 'C2', 'C3', 'C4', 'C5')),
    laps INTEGER,
    start_lap INTEGER,
    end_lap INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    UNIQUE(race_id, driver_id, stint_number)
);

-- Weather data
CREATE TABLE IF NOT EXISTS weather (
    weather_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    race_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    air_temp REAL,
    track_temp REAL,
    humidity REAL,
    pressure REAL,
    wind_speed REAL,
    wind_direction INTEGER,
    rainfall INTEGER CHECK(rainfall IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

-- Telemetry tables
CREATE TABLE IF NOT EXISTS telemetry (
    telemetry_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    lap INTEGER,
    time TIMESTAMP NOT NULL,
    session_time REAL,
    speed REAL,
    throttle REAL,
    brake INTEGER CHECK(brake IN (0, 1)),
    gear INTEGER,
    rpm INTEGER,
    drs INTEGER CHECK(drs IN (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)),
    n_gear INTEGER,
    brake_pressure REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
);

CREATE TABLE IF NOT EXISTS telemetry_position (
    position_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    time TIMESTAMP NOT NULL,
    session_time REAL,
    x REAL,
    y REAL,
    z REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
);

CREATE TABLE IF NOT EXISTS telemetry_delta (
    delta_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    time TIMESTAMP NOT NULL,
    session_time REAL,
    delta_to_session_best REAL,
    delta_to_leader REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
);

-- Track status and incidents
CREATE TABLE IF NOT EXISTS track_status (
    status_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    time TIMESTAMP NOT NULL,
    session_time REAL,
    status TEXT NOT NULL CHECK(status IN ('Green', 'Yellow', 'SC', 'VSC', 'Red', 'AllClear')),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS safety_car_periods (
    sc_period_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    period_number INTEGER NOT NULL,
    start_lap INTEGER,
    end_lap INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    trigger TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    UNIQUE(race_id, period_number)
);

CREATE TABLE IF NOT EXISTS virtual_safety_car_periods (
    vsc_period_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    period_number INTEGER NOT NULL,
    start_lap INTEGER,
    end_lap INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    trigger TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    UNIQUE(race_id, period_number)
);

CREATE TABLE IF NOT EXISTS red_flags (
    red_flag_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    race_id INTEGER NOT NULL,
    flag_number INTEGER NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    UNIQUE(session_id, flag_number)
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    session_id INTEGER,
    lap INTEGER,
    time TIMESTAMP,
    driver_id INTEGER,
    description TEXT,
    incident_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
);

-- Circuit metadata
CREATE TABLE IF NOT EXISTS circuit_configurations (
    config_id SERIAL PRIMARY KEY,
    circuit_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    configuration_name TEXT,
    lap_length REAL,
    number_of_corners INTEGER,
    direction TEXT CHECK(direction IN ('Clockwise', 'Anti-clockwise')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (circuit_id) REFERENCES circuits(circuit_id),
    UNIQUE(circuit_id, year)
);

CREATE TABLE IF NOT EXISTS drs_zones (
    drs_zone_id SERIAL PRIMARY KEY,
    circuit_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    zone_number INTEGER NOT NULL,
    detection_point REAL,
    activation_point REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (circuit_id) REFERENCES circuits(circuit_id),
    UNIQUE(circuit_id, year, zone_number)
);

-- Data availability tracking
CREATE TABLE IF NOT EXISTS data_availability (
    availability_id SERIAL PRIMARY KEY,
    race_id INTEGER NOT NULL,
    session_id INTEGER,
    data_type TEXT NOT NULL,
    available BOOLEAN NOT NULL,
    source TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (race_id) REFERENCES races(race_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_races_season ON races(season_id);
CREATE INDEX IF NOT EXISTS idx_races_circuit ON races(circuit_id);
CREATE INDEX IF NOT EXISTS idx_races_date ON races(date);
CREATE INDEX IF NOT EXISTS idx_sessions_race ON sessions(race_id);
CREATE INDEX IF NOT EXISTS idx_sessions_openf1_key ON sessions(openf1_session_key);
CREATE INDEX IF NOT EXISTS idx_race_results_race ON race_results(race_id);
CREATE INDEX IF NOT EXISTS idx_race_results_driver ON race_results(driver_id);
CREATE INDEX IF NOT EXISTS idx_race_results_position ON race_results(race_id, position);
CREATE INDEX IF NOT EXISTS idx_lap_times_race_driver ON lap_times(race_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_lap_times_lap ON lap_times(race_id, lap);
CREATE INDEX IF NOT EXISTS idx_sector_times_race_driver_lap ON sector_times(race_id, driver_id, lap);
CREATE INDEX IF NOT EXISTS idx_pit_stops_race_driver ON pit_stops(race_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_session_driver ON telemetry(session_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(session_id, time);
CREATE INDEX IF NOT EXISTS idx_telemetry_position_session_driver ON telemetry_position(session_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_delta_session_driver ON telemetry_delta(session_id, driver_id);
CREATE INDEX IF NOT EXISTS idx_track_status_session ON track_status(session_id);
CREATE INDEX IF NOT EXISTS idx_track_status_time ON track_status(session_id, time);
CREATE INDEX IF NOT EXISTS idx_weather_session ON weather(session_id);
CREATE INDEX IF NOT EXISTS idx_weather_time ON weather(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_drivers_ref ON drivers(driver_ref);
CREATE INDEX IF NOT EXISTS idx_drivers_code ON drivers(code);
CREATE INDEX IF NOT EXISTS idx_circuits_ref ON circuits(circuit_ref);
CREATE INDEX IF NOT EXISTS idx_constructors_ref ON constructors(constructor_ref);

-- Views for common queries
CREATE OR REPLACE VIEW v_race_summary AS
SELECT 
    r.race_id,
    s.year,
    r.round,
    c.name AS circuit_name,
    c.country,
    r.name AS race_name,
    r.date,
    COUNT(DISTINCT rr.driver_id) AS num_drivers,
    COUNT(DISTINCT rr.constructor_id) AS num_constructors
FROM races r
JOIN seasons s ON r.season_id = s.season_id
JOIN circuits c ON r.circuit_id = c.circuit_id
LEFT JOIN race_results rr ON r.race_id = rr.race_id
GROUP BY r.race_id, s.year, r.round, c.name, c.country, r.name, r.date;

CREATE OR REPLACE VIEW v_driver_stats AS
SELECT 
    d.driver_id,
    d.full_name,
    d.nationality,
    COUNT(DISTINCT rr.race_id) AS races_entered,
    COUNT(DISTINCT CASE WHEN rr.position = 1 THEN rr.race_id END) AS wins,
    SUM(rr.points) AS total_points,
    AVG(rr.position) AS avg_position
FROM drivers d
LEFT JOIN race_results rr ON d.driver_id = rr.driver_id
GROUP BY d.driver_id, d.full_name, d.nationality;

