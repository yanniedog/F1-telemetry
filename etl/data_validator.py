"""
Data validator for F1 dataset.
Validates data completeness, checks foreign keys, detects anomalies, and generates quality reports.
"""

from typing import Dict, List, Optional, Any, Set
from collections import defaultdict
import sqlite3

from utils.logger import get_logger

logger = get_logger()


class DataValidator:
    """Validates F1 dataset quality."""
    
    def __init__(self, db_path: str = "data/f1_dataset.db"):
        """
        Initialize data validator.
        
        Args:
            db_path: Path to SQLite database
        """
        self.logger = logger
        self.db_path = db_path
        self.errors = []
        self.warnings = []
        
        self.logger.info(f"Initialized data validator (database: {db_path})")
    
    def validate_foreign_keys(self) -> Dict[str, List[str]]:
        """
        Validate foreign key relationships.
        
        Returns:
            Dictionary mapping table names to lists of errors
        """
        self.logger.info("Validating foreign keys...")
        
        errors = defaultdict(list)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check races -> seasons
            cursor.execute("""
                SELECT r.race_id, r.season_id
                FROM races r
                LEFT JOIN seasons s ON r.season_id = s.season_id
                WHERE s.season_id IS NULL
            """)
            for row in cursor.fetchall():
                errors['races'].append(f"Race {row[0]} references non-existent season {row[1]}")
            
            # Check races -> circuits
            cursor.execute("""
                SELECT r.race_id, r.circuit_id
                FROM races r
                LEFT JOIN circuits c ON r.circuit_id = c.circuit_id
                WHERE c.circuit_id IS NULL
            """)
            for row in cursor.fetchall():
                errors['races'].append(f"Race {row[0]} references non-existent circuit {row[1]}")
            
            # Check race_results -> races
            cursor.execute("""
                SELECT rr.result_id, rr.race_id
                FROM race_results rr
                LEFT JOIN races r ON rr.race_id = r.race_id
                WHERE r.race_id IS NULL
            """)
            for row in cursor.fetchall():
                errors['race_results'].append(f"Result {row[0]} references non-existent race {row[1]}")
            
            # Check race_results -> drivers
            cursor.execute("""
                SELECT rr.result_id, rr.driver_id
                FROM race_results rr
                LEFT JOIN drivers d ON rr.driver_id = d.driver_id
                WHERE d.driver_id IS NULL
            """)
            for row in cursor.fetchall():
                errors['race_results'].append(f"Result {row[0]} references non-existent driver {row[1]}")
            
            # Check race_results -> constructors
            cursor.execute("""
                SELECT rr.result_id, rr.constructor_id
                FROM race_results rr
                LEFT JOIN constructors c ON rr.constructor_id = c.constructor_id
                WHERE c.constructor_id IS NULL
            """)
            for row in cursor.fetchall():
                errors['race_results'].append(f"Result {row[0]} references non-existent constructor {row[1]}")
            
            # Check lap_times -> races
            cursor.execute("""
                SELECT lt.lap_time_id, lt.race_id
                FROM lap_times lt
                LEFT JOIN races r ON lt.race_id = r.race_id
                WHERE r.race_id IS NULL
            """)
            for row in cursor.fetchall():
                errors['lap_times'].append(f"Lap time {row[0]} references non-existent race {row[1]}")
            
            # Check lap_times -> drivers
            cursor.execute("""
                SELECT lt.lap_time_id, lt.driver_id
                FROM lap_times lt
                LEFT JOIN drivers d ON lt.driver_id = d.driver_id
                WHERE d.driver_id IS NULL
            """)
            for row in cursor.fetchall():
                errors['lap_times'].append(f"Lap time {row[0]} references non-existent driver {row[1]}")
            
            conn.close()
        
        except Exception as e:
            self.logger.error(f"Error validating foreign keys: {e}")
            errors['system'].append(str(e))
        
        self.logger.info(f"Found {sum(len(v) for v in errors.values())} foreign key errors")
        return dict(errors)
    
    def validate_data_completeness(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate data completeness.
        
        Returns:
            Dictionary with completeness statistics
        """
        self.logger.info("Validating data completeness...")
        
        completeness = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count records in each table
            tables = [
                'seasons', 'circuits', 'constructors', 'drivers', 'races',
                'sessions', 'race_results', 'lap_times', 'sector_times',
                'pit_stops', 'tyre_stints', 'weather', 'telemetry'
            ]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                completeness[table] = {
                    'count': count,
                    'has_data': count > 0
                }
            
            # Check for missing race results
            cursor.execute("""
                SELECT COUNT(*) 
                FROM races r
                LEFT JOIN race_results rr ON r.race_id = rr.race_id
                WHERE rr.race_id IS NULL
            """)
            races_without_results = cursor.fetchone()[0]
            completeness['races_without_results'] = races_without_results
            
            # Check for missing lap times
            cursor.execute("""
                SELECT COUNT(DISTINCT r.race_id)
                FROM races r
                LEFT JOIN lap_times lt ON r.race_id = lt.race_id
                WHERE lt.race_id IS NULL AND r.date >= '1980-01-01'
            """)
            races_without_lap_times = cursor.fetchone()[0]
            completeness['races_without_lap_times'] = races_without_lap_times
            
            conn.close()
        
        except Exception as e:
            self.logger.error(f"Error validating completeness: {e}")
            completeness['error'] = str(e)
        
        return completeness
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect data anomalies.
        
        Returns:
            List of anomaly dictionaries
        """
        self.logger.info("Detecting anomalies...")
        
        anomalies = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for impossible lap times (< 10 seconds or > 10 minutes)
            cursor.execute("""
                SELECT lap_time_id, race_id, driver_id, lap, milliseconds
                FROM lap_times
                WHERE milliseconds < 10000 OR milliseconds > 600000
            """)
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'impossible_lap_time',
                    'table': 'lap_times',
                    'id': row[0],
                    'race_id': row[1],
                    'driver_id': row[2],
                    'lap': row[3],
                    'value': row[4],
                    'message': f"Lap time {row[4]}ms seems impossible"
                })
            
            # Check for duplicate positions in race results
            cursor.execute("""
                SELECT race_id, position, COUNT(*) as count
                FROM race_results
                WHERE position IS NOT NULL
                GROUP BY race_id, position
                HAVING count > 1
            """)
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'duplicate_position',
                    'table': 'race_results',
                    'race_id': row[0],
                    'position': row[1],
                    'count': row[2],
                    'message': f"Duplicate position {row[1]} in race {row[0]}"
                })
            
            # Check for negative positions
            cursor.execute("""
                SELECT result_id, race_id, position
                FROM race_results
                WHERE position < 1
            """)
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'invalid_position',
                    'table': 'race_results',
                    'id': row[0],
                    'race_id': row[1],
                    'value': row[2],
                    'message': f"Invalid position {row[2]}"
                })
            
            # Check for future dates
            cursor.execute("""
                SELECT race_id, date
                FROM races
                WHERE date > date('now', '+1 year')
            """)
            for row in cursor.fetchall():
                anomalies.append({
                    'type': 'future_date',
                    'table': 'races',
                    'race_id': row[0],
                    'date': row[1],
                    'message': f"Race date {row[1]} is in the future"
                })
            
            conn.close()
        
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            anomalies.append({
                'type': 'system_error',
                'message': str(e)
            })
        
        self.logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report.
        
        Returns:
            Dictionary with quality report
        """
        self.logger.info("Generating data quality report...")
        
        report = {
            'foreign_key_errors': self.validate_foreign_keys(),
            'completeness': self.validate_data_completeness(),
            'anomalies': self.detect_anomalies(),
            'summary': {}
        }
        
        # Generate summary
        fk_error_count = sum(len(v) for v in report['foreign_key_errors'].values())
        anomaly_count = len(report['anomalies'])
        
        report['summary'] = {
            'foreign_key_errors': fk_error_count,
            'anomalies': anomaly_count,
            'tables_with_data': sum(
                1 for v in report['completeness'].values()
                if isinstance(v, dict) and v.get('has_data', False)
            ),
            'races_without_results': report['completeness'].get('races_without_results', 0),
            'races_without_lap_times': report['completeness'].get('races_without_lap_times', 0)
        }
        
        self.logger.info("Generated data quality report")
        return report

