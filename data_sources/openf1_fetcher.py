"""
OpenF1 API data fetcher.
Fetches telemetry data from OpenF1 API (2018+).
Includes speed, throttle, brake, gear, RPM, DRS, GPS position, track status.
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml

from utils.logger import get_logger
from utils.cache_manager import get_cache_manager
from utils.rate_limiter import get_rate_limiter

logger = get_logger()


class OpenF1Fetcher:
    """Fetches telemetry data from OpenF1 API."""
    
    def __init__(self, config_path: str = "config/data_sources.yaml"):
        """
        Initialize OpenF1 fetcher.
        
        Args:
            config_path: Path to data sources configuration
        """
        self.logger = logger
        self.cache = get_cache_manager()
        self.rate_limiter = get_rate_limiter().get_limiter('openf1')
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.base_url = config['openf1']['base_url']
        self.endpoints = config['openf1']['endpoints']
        self.rate_limit = config['openf1']['rate_limit']
        
        self.logger.info(f"Initialized OpenF1 fetcher (base URL: {self.base_url})")
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Optional[List[Dict]]:
        """
        Make API request with caching and rate limiting.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            use_cache: Whether to use cache
            
        Returns:
            API response as list of dictionaries
        """
        url = f"{self.base_url}{endpoint}"
        
        # Check cache
        if use_cache:
            cached_data = self.cache.get(url, params)
            if cached_data is not None:
                self.logger.debug(f"Cache hit for {url}")
                return cached_data
        
        # Rate limiting
        self.rate_limiter._wait_if_needed('openf1')
        
        try:
            self.rate_limiter.record_call('openf1')
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache response
            if use_cache:
                self.cache.set(url, data, params)
            
            return data
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                # 422 Unprocessable Entity - data might not be available for this session
                self.logger.warning(f"Data not available for {url} (422) - this is normal for some sessions")
            elif e.response.status_code == 404:
                self.logger.warning(f"Endpoint not found: {url} (404)")
            else:
                self.logger.error(f"Request failed for {url}: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
    
    def fetch_sessions(
        self,
        year: Optional[int] = None,
        circuit_key: Optional[int] = None,
        session_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch session information.
        
        Args:
            year: Season year
            circuit_key: Circuit key
            session_name: Session name (e.g., 'Race', 'Qualifying')
            
        Returns:
            List of session dictionaries
        """
        self.logger.info(f"Fetching sessions (year={year}, circuit={circuit_key}, session={session_name})...")
        
        params = {}
        if year:
            params['year'] = year
        if circuit_key:
            params['circuit_key'] = circuit_key
        if session_name:
            params['session_name'] = session_name
        
        data = self._make_request(self.endpoints['sessions'], params)
        if data is None:
            return []
        
        self.logger.info(f"Fetched {len(data)} sessions")
        return data
    
    def fetch_laps(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch lap data.
        
        Args:
            session_key: Session key
            driver_number: Driver number (None = all drivers)
            lap_number: Lap number (None = all laps)
            
        Returns:
            List of lap dictionaries
        """
        self.logger.info(f"Fetching laps (session={session_key}, driver={driver_number}, lap={lap_number})...")
        
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        if lap_number:
            params['lap_number'] = lap_number
        
        data = self._make_request(self.endpoints['laps'], params)
        if data is None:
            return []
        
        self.logger.info(f"Fetched {len(data)} lap records")
        return data
    
    def fetch_drivers(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch driver information.
        
        Args:
            session_key: Session key
            driver_number: Driver number
            
        Returns:
            List of driver dictionaries
        """
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
        
        data = self._make_request(self.endpoints['drivers'], params)
        if data is None:
            return []
        
        return data
    
    def fetch_car_data(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch car telemetry data (speed, throttle, brake, gear, RPM, DRS).
        
        Args:
            session_key: Session key
            driver_number: Driver number (None = all drivers)
            date_start: Start timestamp (ISO format)
            date_end: End timestamp (ISO format)
            
        Returns:
            List of car data dictionaries
        """
        self.logger.info(f"Fetching car data (session={session_key}, driver={driver_number})...")
        
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        if date_start:
            params['date_start'] = date_start
        if date_end:
            params['date_end'] = date_end
        
        data = self._make_request(self.endpoints['car_data'], params)
        if data is None:
            return []
        
        self.logger.info(f"Fetched {len(data)} car data records")
        return data
    
    def fetch_position(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch GPS position data.
        
        Args:
            session_key: Session key
            driver_number: Driver number (None = all drivers)
            date_start: Start timestamp (ISO format)
            date_end: End timestamp (ISO format)
            
        Returns:
            List of position dictionaries
        """
        self.logger.info(f"Fetching position data (session={session_key}, driver={driver_number})...")
        
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        if date_start:
            params['date_start'] = date_start
        if date_end:
            params['date_end'] = date_end
        
        data = self._make_request(self.endpoints['position'], params)
        if data is None:
            return []
        
        self.logger.info(f"Fetched {len(data)} position records")
        return data
    
    def fetch_track_status(
        self,
        session_key: int,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch track status (green, yellow, SC, VSC, red).
        
        Args:
            session_key: Session key
            date_start: Start timestamp (ISO format)
            date_end: End timestamp (ISO format)
            
        Returns:
            List of track status dictionaries
        """
        self.logger.info(f"Fetching track status (session={session_key})...")
        
        params = {'session_key': session_key}
        if date_start:
            params['date_start'] = date_start
        if date_end:
            params['date_end'] = date_end
        
        data = self._make_request(self.endpoints['track_status'], params)
        if data is None:
            return []
        
        self.logger.info(f"Fetched {len(data)} track status records")
        return data
    
    def fetch_stints(
        self,
        session_key: int,
        driver_number: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch stint information.
        
        Args:
            session_key: Session key
            driver_number: Driver number (None = all drivers)
            
        Returns:
            List of stint dictionaries
        """
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        
        data = self._make_request(self.endpoints['stints'], params)
        if data is None:
            return []
        
        return data
    
    def fetch_weather(
        self,
        session_key: int,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch weather data.
        
        Args:
            session_key: Session key
            date_start: Start timestamp (ISO format)
            date_end: End timestamp (ISO format)
            
        Returns:
            List of weather dictionaries
        """
        params = {'session_key': session_key}
        if date_start:
            params['date_start'] = date_start
        if date_end:
            params['date_end'] = date_end
        
        data = self._make_request(self.endpoints['weather'], params)
        if data is None:
            return []
        
        return data
    
    def fetch_location(
        self,
        session_key: int
    ) -> List[Dict]:
        """
        Fetch location/marshal sector flags.
        
        Args:
            session_key: Session key
            
        Returns:
            List of location dictionaries
        """
        params = {'session_key': session_key}
        
        data = self._make_request(self.endpoints['location'], params)
        if data is None:
            return []
        
        return data
    
    def fetch_session_telemetry(
        self,
        session_key: int,
        driver_numbers: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Fetch complete telemetry for a session.
        
        Args:
            session_key: Session key
            driver_numbers: List of driver numbers (None = all drivers)
            
        Returns:
            Dictionary with all telemetry data
        """
        self.logger.info(f"Fetching complete telemetry for session {session_key}...")
        
        telemetry = {
            'session_key': session_key,
            'laps': [],
            'car_data': [],
            'position': [],
            'track_status': [],
            'stints': [],
            'weather': [],
            'location': []
        }
        
        # Fetch laps
        if driver_numbers:
            for driver_num in driver_numbers:
                laps = self.fetch_laps(session_key, driver_number=driver_num)
                telemetry['laps'].extend(laps)
        else:
            telemetry['laps'] = self.fetch_laps(session_key)
        
        # Fetch car data
        if driver_numbers:
            for driver_num in driver_numbers:
                car_data = self.fetch_car_data(session_key, driver_number=driver_num)
                telemetry['car_data'].extend(car_data)
        else:
            telemetry['car_data'] = self.fetch_car_data(session_key)
        
        # Fetch position data
        if driver_numbers:
            for driver_num in driver_numbers:
                position = self.fetch_position(session_key, driver_number=driver_num)
                telemetry['position'].extend(position)
        else:
            telemetry['position'] = self.fetch_position(session_key)
        
        # Fetch track status
        telemetry['track_status'] = self.fetch_track_status(session_key)
        
        # Fetch stints
        telemetry['stints'] = self.fetch_stints(session_key)
        
        # Fetch weather
        telemetry['weather'] = self.fetch_weather(session_key)
        
        # Fetch location/marshal flags
        telemetry['location'] = self.fetch_location(session_key)
        
        self.logger.info(f"Fetched complete telemetry for session {session_key}")
        return telemetry

