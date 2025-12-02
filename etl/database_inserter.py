"""
Database inserter for F1 dataset.
Handles insertion of fetched data into the SQLite database.
"""

import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from utils.logger import get_logger

logger = get_logger()


class DatabaseInserter:
    """Handles database insertions for F1 dataset."""
    
    def __init__(self, db_path: str):
        """
        Initialize database inserter.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.logger = logger
        self.batch_size = 1000
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _get_or_create_race(self, cursor: sqlite3.Cursor, year: int, circuit_name: str, session_key: int) -> Optional[int]:
        """Get or create a race for the session."""
        # Ensure year is an integer
        if not isinstance(year, int):
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = 2023  # Default fallback
        
        # First, get or create season
        cursor.execute("SELECT season_id FROM seasons WHERE year = ?", (year,))
        season_row = cursor.fetchone()
        if not season_row:
            cursor.execute("INSERT OR IGNORE INTO seasons (year) VALUES (?)", (year,))
            cursor.execute("SELECT season_id FROM seasons WHERE year = ?", (year,))
            season_row = cursor.fetchone()
            season_id = season_row[0] if season_row else None
        else:
            season_id = season_row[0]
        
        if not season_id:
            return None
        
        # Get or create circuit
        cursor.execute("SELECT circuit_id FROM circuits WHERE name LIKE ?", (f"%{circuit_name}%",))
        circuit_row = cursor.fetchone()
        if not circuit_row:
            cursor.execute("""
                INSERT OR IGNORE INTO circuits (circuit_ref, name, location, country)
                VALUES (?, ?, ?, ?)
            """, (circuit_name.lower().replace(' ', '_'), circuit_name, circuit_name, None))
            cursor.execute("SELECT circuit_id FROM circuits WHERE name LIKE ?", (f"%{circuit_name}%",))
            circuit_row = cursor.fetchone()
            circuit_id = circuit_row[0] if circuit_row else None
        else:
            circuit_id = circuit_row[0]
        
        if not circuit_id:
            return None
        
        # First, try to find existing race for this circuit and season
        cursor.execute("""
            SELECT race_id FROM races 
            WHERE season_id = ? AND circuit_id = ?
            LIMIT 1
        """, (season_id, circuit_id))
        race_row = cursor.fetchone()
        
        if race_row:
            # Use existing race
            return race_row[0]
        
        # No existing race found, create a new one
        # Find the next available round number for this season
        cursor.execute("""
            SELECT MAX(round) FROM races WHERE season_id = ?
        """, (season_id,))
        max_round_row = cursor.fetchone()
        next_round = (max_round_row[0] + 1) if max_round_row and max_round_row[0] is not None else 1
        
        # Ensure round number is within valid range (1-100)
        if next_round > 100:
            # If we've exceeded 100, use a hash-based approach
            next_round = ((session_key % 100) + 1)
            # Check if this round already exists for this season
            cursor.execute("""
                SELECT race_id FROM races WHERE season_id = ? AND round = ?
            """, (season_id, next_round))
            if cursor.fetchone():
                # If collision, find next available
                for r in range(1, 101):
                    cursor.execute("""
                        SELECT race_id FROM races WHERE season_id = ? AND round = ?
                    """, (season_id, r))
                    if not cursor.fetchone():
                        next_round = r
                        break
        
        # Create new race
        try:
            cursor.execute("""
                INSERT INTO races (season_id, round, circuit_id, name, date, race_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (season_id, next_round, circuit_id, f"{circuit_name} {year}", f"{year}-01-01", f"{year}-01-01"))
            race_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # UNIQUE constraint failed, try to get existing race
            cursor.execute("""
                SELECT race_id FROM races 
                WHERE season_id = ? AND round = ?
            """, (season_id, next_round))
            race_row = cursor.fetchone()
            race_id = race_row[0] if race_row else None
        
        return race_id
    
    def insert_sessions(self, sessions: List[Dict]) -> Dict[int, int]:
        """
        Insert sessions into database.
        
        Args:
            sessions: List of session dictionaries from OpenF1
            
        Returns:
            Dictionary mapping session_key to session_id
        """
        if not sessions:
            return {}
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        session_map = {}  # session_key -> session_id
        
        for session in sessions:
            try:
                session_key = session.get('session_key')
                if not session_key:
                    continue
                
                # Get or create race
                year = session.get('year') or 2023
                # Ensure year is an integer
                if not isinstance(year, int):
                    try:
                        year = int(year)
                    except (ValueError, TypeError):
                        year = 2023
                
                circuit_name = session.get('circuit_short_name') or session.get('location') or 'Unknown'
                race_id = self._get_or_create_race(cursor, year, circuit_name, session_key)
                
                if not race_id:
                    continue
                
                # Parse date - ensure session_date_str is always a valid string
                date_start = session.get('date_start')
                session_date_str = f"{year}-01-01"  # Default fallback
                session_time_str = None
                if date_start:
                    try:
                        from datetime import datetime
                        # Handle ISO format with or without timezone
                        date_str = date_start.replace('Z', '+00:00') if 'Z' in date_start else date_start
                        dt = datetime.fromisoformat(date_str)
                        session_date_str = dt.strftime('%Y-%m-%d')
                        session_time_str = dt.strftime('%H:%M:%S')
                    except Exception as e:
                        self.logger.debug(f"Could not parse date {date_start}: {e}")
                        # Keep default session_date_str
                
                # Ensure session_date_str is never None or empty
                if not session_date_str or not isinstance(session_date_str, str):
                    session_date_str = f"{year}-01-01"
                
                session_type = session.get('session_name', 'Race')
                session_name = session.get('session_name', 'Race')
                
                # Insert or update session
                cursor.execute("""
                    INSERT OR IGNORE INTO sessions (
                        race_id, session_type, session_name, date, time, openf1_session_key
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    race_id,
                    session_type,
                    session_name,
                    session_date_str,
                    session_time_str,
                    session_key
                ))
                
                if cursor.rowcount > 0:
                    session_id = cursor.lastrowid
                else:
                    # Get existing session_id
                    cursor.execute("""
                        SELECT session_id FROM sessions WHERE openf1_session_key = ?
                    """, (session_key,))
                    row = cursor.fetchone()
                    session_id = row[0] if row else None
                
                if session_id:
                    session_map[session_key] = session_id
                    
            except sqlite3.Error as e:
                self.logger.warning(f"Error inserting session {session.get('session_key')}: {e}")
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Inserted/updated {len(session_map)} sessions")
        return session_map
    
    def _get_or_create_driver(self, cursor: sqlite3.Cursor, driver_number: int) -> Optional[int]:
        """Get or create a driver by driver number."""
        # Check if driver exists by number
        cursor.execute("SELECT driver_id FROM drivers WHERE number = ?", (driver_number,))
        row = cursor.fetchone()
        if row:
            return row[0]
        
        # Create placeholder driver
        cursor.execute("""
            INSERT INTO drivers (driver_ref, number, forename, surname, full_name)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"driver_{driver_number}",
            driver_number,
            "Driver",
            str(driver_number),
            f"Driver {driver_number}"
        ))
        return cursor.lastrowid
    
    def insert_lap_times(self, laps: List[Dict], session_id: int) -> int:
        """
        Insert lap times into database.
        
        Args:
            laps: List of lap dictionaries
            session_id: Session ID (not session_key)
            
        Returns:
            Number of lap times inserted
        """
        if not laps:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get race_id from session
        cursor.execute("SELECT race_id FROM sessions WHERE session_id = ?", (session_id,))
        session_row = cursor.fetchone()
        if not session_row:
            self.logger.warning(f"Session {session_id} not found, skipping lap times")
            conn.close()
            return 0
        
        race_id = session_row[0]
        
        inserted = 0
        batch = []
        
        for lap in laps:
            try:
                driver_number = lap.get('driver_number')
                if not driver_number:
                    continue
                
                # Get or create driver
                driver_id = self._get_or_create_driver(cursor, driver_number)
                if not driver_id:
                    continue
                
                lap_number = lap.get('lap_number')
                if not lap_number:
                    continue
                
                lap_time = lap.get('lap_time')
                milliseconds = None
                if lap_time:
                    try:
                        # Convert time string to milliseconds
                        parts = lap_time.split(':')
                        if len(parts) == 2:
                            minutes, seconds = parts
                            milliseconds = int(float(minutes) * 60000 + float(seconds) * 1000)
                    except:
                        pass
                
                batch.append((
                    race_id,
                    driver_id,
                    lap_number,
                    lap.get('position'),
                    lap_time,
                    milliseconds
                ))
                
                if len(batch) >= self.batch_size:
                    cursor.executemany("""
                        INSERT OR IGNORE INTO lap_times (
                            race_id, driver_id, lap, position, time, milliseconds
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, batch)
                    inserted += cursor.rowcount
                    batch = []
                    conn.commit()
            except sqlite3.Error as e:
                self.logger.warning(f"Error inserting lap: {e}")
        
        # Insert remaining batch
        if batch:
            cursor.executemany("""
                INSERT OR IGNORE INTO lap_times (
                    race_id, driver_id, lap, position, time, milliseconds
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, batch)
            inserted += cursor.rowcount
            conn.commit()
        
        conn.close()
        
        self.logger.info(f"Inserted {inserted} lap times for session {session_id}")
        return inserted
    
    def insert_position_data(self, positions: List[Dict], session_id: int) -> int:
        """
        Insert position data into database.
        
        Args:
            positions: List of position dictionaries
            session_id: Session ID (not session_key)
            
        Returns:
            Number of position records inserted
        """
        if not positions:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Verify session exists
        cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
        if not cursor.fetchone():
            self.logger.warning(f"Session {session_id} not found, skipping position data")
            conn.close()
            return 0
        
        inserted = 0
        batch = []
        
        for pos in positions:
            try:
                driver_number = pos.get('driver_number')
                if not driver_number:
                    continue
                
                # Get or create driver
                driver_id = self._get_or_create_driver(cursor, driver_number)
                if not driver_id:
                    continue
                
                timestamp = pos.get('date')
                if not timestamp:
                    continue
                
                # Parse timestamp
                try:
                    from datetime import datetime
                    if 'T' in timestamp:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromisoformat(timestamp)
                except:
                    continue
                
                batch.append((
                    session_id,
                    driver_id,
                    dt,
                    None,  # session_time (not in OpenF1 position data)
                    None,  # x
                    None,  # y
                    None   # z
                ))
                
                if len(batch) >= self.batch_size:
                    cursor.executemany("""
                        INSERT OR IGNORE INTO telemetry_position (
                            session_id, driver_id, time, session_time, x, y, z
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    inserted += cursor.rowcount
                    batch = []
                    conn.commit()
            except sqlite3.Error as e:
                self.logger.warning(f"Error inserting position: {e}")
        
        # Insert remaining batch
        if batch:
            cursor.executemany("""
                INSERT OR IGNORE INTO telemetry_position (
                    session_id, driver_id, time, session_time, x, y, z
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, batch)
            inserted += cursor.rowcount
            conn.commit()
        
        conn.close()
        
        self.logger.info(f"Inserted {inserted} position records for session {session_id}")
        return inserted
    
    def insert_openf1_telemetry(self, telemetry: Dict[str, Any], session_id: int) -> Dict[str, int]:
        """
        Insert complete OpenF1 telemetry data.
        
        Args:
            telemetry: Dictionary with all telemetry data
            session_id: Session ID (not session_key)
            
        Returns:
            Dictionary with counts of inserted records
        """
        results = {
            'lap_times': 0,
            'positions': 0
        }
        
        # Insert lap times
        if 'laps' in telemetry and telemetry['laps']:
            results['lap_times'] = self.insert_lap_times(telemetry['laps'], session_id)
        
        # Insert position data
        if 'position' in telemetry and telemetry['position']:
            results['positions'] = self.insert_position_data(telemetry['position'], session_id)
        
        return results

