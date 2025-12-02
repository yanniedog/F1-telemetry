"""
FastF1 library data fetcher.
Extracts session telemetry, sector times, tyre compounds, weather data, and micro-sector times.
Uses the FastF1 Python library for modern F1 data (2018+).
"""

import fastf1
import pandas as pd
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

from utils.logger import get_logger
from utils.rate_limiter import get_rate_limiter

logger = get_logger()


class FastF1Fetcher:
    """Fetches data using FastF1 library."""
    
    def __init__(self, config_path: str = "config/data_sources.yaml"):
        """
        Initialize FastF1 fetcher.
        
        Args:
            config_path: Path to data sources configuration
        """
        self.logger = logger
        self.rate_limiter = get_rate_limiter().get_limiter('fastf1')
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        fastf1_config = config.get('fastf1', {})
        self.cache_dir = fastf1_config.get('cache_dir', 'cache/fastf1')
        self.data_dir = fastf1_config.get('data_dir', 'cache/fastf1_data')
        
        # Configure FastF1 cache
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        
        fastf1.Cache.enable_cache(self.cache_dir)
        
        self.logger.info(f"Initialized FastF1 fetcher (cache: {self.cache_dir})")
    
    def get_session(
        self,
        year: int,
        circuit: str,
        session_type: str
    ) -> Optional[fastf1.core.Session]:
        """
        Get FastF1 session object.
        
        Args:
            year: Season year
            circuit: Circuit name (e.g., 'Monza', 'Silverstone')
            session_type: Session type ('FP1', 'FP2', 'FP3', 'Q', 'Sprint', 'R')
            
        Returns:
            FastF1 session object or None
        """
        try:
            self.logger.info(f"Loading session: {year} {circuit} {session_type}")
            session = fastf1.get_session(year, circuit, session_type)
            session.load()
            return session
        except Exception as e:
            self.logger.error(f"Failed to load session {year} {circuit} {session_type}: {e}")
            return None
    
    def fetch_laps(
        self,
        session: fastf1.core.Session
    ) -> pd.DataFrame:
        """
        Fetch lap data.
        
        Args:
            session: FastF1 session object
            
        Returns:
            DataFrame with lap data
        """
        try:
            laps = session.laps
            self.logger.info(f"Fetched {len(laps)} lap records")
            return laps
        except Exception as e:
            self.logger.error(f"Failed to fetch laps: {e}")
            return pd.DataFrame()
    
    def fetch_sector_times(
        self,
        session: fastf1.core.Session
    ) -> pd.DataFrame:
        """
        Fetch sector times.
        
        Args:
            session: FastF1 session object
            
        Returns:
            DataFrame with sector times
        """
        try:
            laps = session.laps
            if 'Sector1Time' in laps.columns:
                sector_times = laps[['DriverNumber', 'LapNumber', 'Sector1Time', 'Sector2Time', 'Sector3Time']].copy()
                self.logger.info(f"Fetched sector times for {len(sector_times)} laps")
                return sector_times
            else:
                self.logger.warning("Sector times not available for this session")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to fetch sector times: {e}")
            return pd.DataFrame()
    
    def fetch_tyre_compounds(
        self,
        session: fastf1.core.Session
    ) -> pd.DataFrame:
        """
        Fetch tyre compound information.
        
        Args:
            session: FastF1 session object
            
        Returns:
            DataFrame with tyre compound data
        """
        try:
            laps = session.laps
            if 'Compound' in laps.columns:
                tyre_data = laps[['DriverNumber', 'LapNumber', 'Compound', 'TyreLife', 'Stint']].copy()
                self.logger.info(f"Fetched tyre data for {len(tyre_data)} laps")
                return tyre_data
            else:
                self.logger.warning("Tyre compound data not available for this session")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to fetch tyre compounds: {e}")
            return pd.DataFrame()
    
    def fetch_weather(
        self,
        session: fastf1.core.Session
    ) -> pd.DataFrame:
        """
        Fetch weather data.
        
        Args:
            session: FastF1 session object
            
        Returns:
            DataFrame with weather data
        """
        try:
            weather = session.weather_data
            if weather is not None and len(weather) > 0:
                self.logger.info(f"Fetched {len(weather)} weather records")
                return weather
            else:
                self.logger.warning("Weather data not available for this session")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to fetch weather: {e}")
            return pd.DataFrame()
    
    def fetch_telemetry(
        self,
        session: fastf1.core.Session,
        driver: Optional[str] = None,
        lap: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch telemetry data.
        
        Args:
            session: FastF1 session object
            driver: Driver abbreviation (None = all drivers)
            lap: Lap number (None = all laps)
            
        Returns:
            DataFrame with telemetry data
        """
        try:
            if driver and lap:
                # Specific driver and lap
                driver_laps = session.laps.pick_driver(driver)
                if len(driver_laps) > 0:
                    specific_lap = driver_laps[driver_laps['LapNumber'] == lap]
                    if len(specific_lap) > 0:
                        telemetry = specific_lap.iloc[0].get_car_data()
                        return telemetry
            elif driver:
                # All laps for specific driver
                driver_laps = session.laps.pick_driver(driver)
                if len(driver_laps) > 0:
                    fastest_lap = driver_laps.pick_fastest()
                    telemetry = fastest_lap.get_car_data()
                    return telemetry
            else:
                # All drivers, fastest lap each
                telemetry_list = []
                for driver_abbr in session.laps['Driver'].unique():
                    try:
                        driver_laps = session.laps.pick_driver(driver_abbr)
                        if len(driver_laps) > 0:
                            fastest_lap = driver_laps.pick_fastest()
                            tel = fastest_lap.get_car_data()
                            tel['Driver'] = driver_abbr
                            telemetry_list.append(tel)
                    except Exception as e:
                        self.logger.warning(f"Failed to get telemetry for {driver_abbr}: {e}")
                
                if telemetry_list:
                    return pd.concat(telemetry_list, ignore_index=True)
            
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to fetch telemetry: {e}")
            return pd.DataFrame()
    
    def fetch_position_data(
        self,
        session: fastf1.core.Session,
        driver: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch position data (GPS coordinates).
        
        Args:
            session: FastF1 session object
            driver: Driver abbreviation (None = all drivers)
            
        Returns:
            DataFrame with position data
        """
        try:
            if driver:
                driver_laps = session.laps.pick_driver(driver)
                if len(driver_laps) > 0:
                    fastest_lap = driver_laps.pick_fastest()
                    position = fastest_lap.get_pos_data()
                    return position
            else:
                # All drivers
                position_list = []
                for driver_abbr in session.laps['Driver'].unique():
                    try:
                        driver_laps = session.laps.pick_driver(driver_abbr)
                        if len(driver_laps) > 0:
                            fastest_lap = driver_laps.pick_fastest()
                            pos = fastest_lap.get_pos_data()
                            pos['Driver'] = driver_abbr
                            position_list.append(pos)
                    except Exception as e:
                        self.logger.warning(f"Failed to get position for {driver_abbr}: {e}")
                
                if position_list:
                    return pd.concat(position_list, ignore_index=True)
            
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to fetch position data: {e}")
            return pd.DataFrame()
    
    def fetch_micro_sectors(
        self,
        session: fastf1.core.Session
    ) -> pd.DataFrame:
        """
        Fetch micro-sector times.
        
        Args:
            session: FastF1 session object
            
        Returns:
            DataFrame with micro-sector data
        """
        try:
            # FastF1 doesn't have direct micro-sector support
            # We can calculate from telemetry data
            laps = session.laps
            micro_sectors = []
            
            for idx, lap in laps.iterrows():
                try:
                    tel = lap.get_car_data()
                    if len(tel) > 0:
                        # Calculate micro-sectors (e.g., 100m segments)
                        # This is a simplified approach
                        tel['MicroSector'] = pd.cut(
                            tel['Distance'],
                            bins=100,
                            labels=False
                        )
                        tel['LapNumber'] = lap['LapNumber']
                        tel['DriverNumber'] = lap['DriverNumber']
                        micro_sectors.append(tel[['LapNumber', 'DriverNumber', 'MicroSector', 'Time', 'Speed']])
                except Exception as e:
                    continue
            
            if micro_sectors:
                result = pd.concat(micro_sectors, ignore_index=True)
                self.logger.info(f"Fetched micro-sector data for {len(result)} records")
                return result
            else:
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to fetch micro-sectors: {e}")
            return pd.DataFrame()
    
    def fetch_session_data(
        self,
        year: int,
        circuit: str,
        session_type: str
    ) -> Dict[str, Any]:
        """
        Fetch complete session data.
        
        Args:
            year: Season year
            circuit: Circuit name
            session_type: Session type
            
        Returns:
            Dictionary with all session data
        """
        self.logger.info(f"Fetching complete session data: {year} {circuit} {session_type}")
        
        session = self.get_session(year, circuit, session_type)
        if session is None:
            return {}
        
        data = {
            'year': year,
            'circuit': circuit,
            'session_type': session_type,
            'laps': self.fetch_laps(session),
            'sector_times': self.fetch_sector_times(session),
            'tyre_compounds': self.fetch_tyre_compounds(session),
            'weather': self.fetch_weather(session),
            'telemetry': self.fetch_telemetry(session),
            'position': self.fetch_position_data(session),
            'micro_sectors': self.fetch_micro_sectors(session)
        }
        
        # Add session metadata
        try:
            data['session_info'] = {
                'session_name': session.session_info.get('Name', ''),
                'session_date': str(session.date),
                'session_start': str(session.session_start_time) if hasattr(session, 'session_start_time') else None,
                'session_end': str(session.session_end_time) if hasattr(session, 'session_end_time') else None
            }
        except Exception as e:
            self.logger.warning(f"Could not fetch session info: {e}")
            data['session_info'] = {}
        
        self.logger.info(f"Completed fetching session data: {year} {circuit} {session_type}")
        return data

