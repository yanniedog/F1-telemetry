"""
Update driver names from OpenF1 API.
This script fetches real driver names and updates the database.
"""

import sqlite3
from data_sources.openf1_fetcher import OpenF1Fetcher
from utils.logger import get_logger

logger = get_logger()

def update_driver_names():
    """Update driver names in database from OpenF1 API."""
    conn = sqlite3.connect('data/f1_dataset.db')
    cursor = conn.cursor()
    
    fetcher = OpenF1Fetcher()
    
    # Get all unique session keys
    cursor.execute("SELECT DISTINCT openf1_session_key FROM sessions WHERE openf1_session_key IS NOT NULL")
    sessions = cursor.fetchall()
    
    driver_name_map = {}  # driver_number -> full_name
    
    print(f"Fetching driver names from {len(sessions)} sessions...")
    
    for (session_key,) in sessions[:5]:  # Limit to first 5 sessions for now
        try:
            drivers = fetcher.fetch_drivers(session_key=session_key)
            for driver in drivers:
                driver_num = driver.get('driver_number')
                driver_name = driver.get('full_name') or driver.get('name') or driver.get('acronym')
                if driver_num and driver_name:
                    if driver_num not in driver_name_map:
                        driver_name_map[driver_num] = driver_name
                        print(f"  Found: Driver #{driver_num} = {driver_name}")
        except Exception as e:
            logger.warning(f"Error fetching drivers for session {session_key}: {e}")
    
    # Update database
    print(f"\nUpdating {len(driver_name_map)} drivers in database...")
    
    for driver_num, driver_name in driver_name_map.items():
        parts = driver_name.split(' ', 1)
        forename = parts[0] if len(parts) > 0 else "Driver"
        surname = parts[1] if len(parts) > 1 else str(driver_num)
        
        cursor.execute("""
            UPDATE drivers 
            SET forename = ?, surname = ?, full_name = ?
            WHERE number = ?
        """, (forename, surname, driver_name, driver_num))
        
        if cursor.rowcount > 0:
            print(f"  Updated: Driver #{driver_num} -> {driver_name}")
    
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Updated {len(driver_name_map)} driver names!")

if __name__ == '__main__':
    update_driver_names()

