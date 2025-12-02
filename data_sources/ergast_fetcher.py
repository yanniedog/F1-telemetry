"""
Ergast API data fetcher.
Fetches all historical F1 data from Ergast API (1950-present).
Note: Ergast API is deprecated end of 2024. Migration to Jolpica F1 API recommended.
"""

import requests
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

from utils.logger import get_logger
from utils.cache_manager import get_cache_manager
from utils.rate_limiter import get_rate_limiter

logger = get_logger()


class ErgastFetcher:
    """Fetches data from Ergast API."""
    
    def __init__(self, config_path: str = "config/data_sources.yaml"):
        """
        Initialize Ergast fetcher.
        
        Args:
            config_path: Path to data sources configuration
        """
        self.logger = logger
        self.cache = get_cache_manager()
        self.rate_limiter = get_rate_limiter().get_limiter('ergast')
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.base_url = config['ergast']['base_url']
        self.endpoints = config['ergast']['endpoints']
        self.rate_limit = config['ergast']['rate_limit']
        
        self.logger.info(f"Initialized Ergast fetcher (base URL: {self.base_url})")
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Make API request with caching and rate limiting.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            use_cache: Whether to use cache
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        # Check cache
        if use_cache:
            cached_data = self.cache.get(url, params)
            if cached_data is not None:
                self.logger.debug(f"Cache hit for {url}")
                return cached_data
        
        # Rate limiting
        self.rate_limiter._wait_if_needed('ergast')
        
        try:
            self.rate_limiter.record_call('ergast')
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache response
            if use_cache:
                self.cache.set(url, data, params)
            
            return data
        
        except requests.exceptions.ConnectionError as e:
            # Network connectivity issues (firewall, proxy, API down)
            self.logger.warning(
                f"Connection failed for {url}: {e}. "
                "This may be due to network/firewall configuration or API unavailability. "
                "Check your network settings or try again later."
            )
            return None
        except requests.exceptions.Timeout as e:
            self.logger.warning(f"Request timeout for {url}: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Endpoint not found: {url} (404)")
            elif e.response.status_code >= 500:
                self.logger.warning(f"Server error for {url}: {e.response.status_code} - API may be temporarily unavailable")
            else:
                self.logger.error(f"HTTP error for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
    
    def fetch_seasons(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> List[Dict]:
        """
        Fetch all seasons.
        
        Args:
            start_year: Start year (None = all)
            end_year: End year (None = all)
            
        Returns:
            List of season dictionaries
        """
        self.logger.info("Fetching seasons...")
        endpoint = self.endpoints['seasons']
        
        data = self._make_request(endpoint)
        if not data or 'MRData' not in data:
            return []
        
        seasons = data['MRData']['SeasonTable']['Seasons']
        
        # Filter by year range if specified
        if start_year or end_year:
            filtered_seasons = []
            for season in seasons:
                year = int(season['season'])
                if start_year and year < start_year:
                    continue
                if end_year and year > end_year:
                    continue
                filtered_seasons.append(season)
            seasons = filtered_seasons
        
        self.logger.info(f"Fetched {len(seasons)} seasons")
        return seasons
    
    def fetch_races(
        self,
        year: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch races for a season or specific race.
        
        Args:
            year: Season year (None = all years)
            round_num: Round number (None = all rounds)
            
        Returns:
            List of race dictionaries
        """
        if year:
            endpoint = self.endpoints['races'].format(year=year)
            if round_num:
                # Fetch specific race
                endpoint = f"/{year}/{round_num}.json"
        else:
            endpoint = "/races.json?limit=1000"
        
        self.logger.info(f"Fetching races for year={year}, round={round_num}...")
        
        races = []
        offset = 0
        limit = 100
        
        while True:
            params = {'offset': offset, 'limit': limit}
            data = self._make_request(endpoint, params)
            
            if not data or 'MRData' not in data:
                break
            
            race_data = data['MRData']['RaceTable']
            if 'Races' not in race_data:
                break
            
            races.extend(race_data['Races'])
            
            total = int(data['MRData']['total'])
            if offset + limit >= total:
                break
            
            offset += limit
        
        self.logger.info(f"Fetched {len(races)} races")
        return races
    
    def fetch_drivers(self) -> List[Dict]:
        """
        Fetch all drivers.
        
        Returns:
            List of driver dictionaries
        """
        self.logger.info("Fetching drivers...")
        endpoint = self.endpoints['drivers']
        
        drivers = []
        offset = 0
        limit = 100
        
        while True:
            params = {'offset': offset, 'limit': limit}
            data = self._make_request(endpoint, params)
            
            if not data or 'MRData' not in data:
                break
            
            driver_data = data['MRData']['DriverTable']
            if 'Drivers' not in driver_data:
                break
            
            drivers.extend(driver_data['Drivers'])
            
            total = int(data['MRData']['total'])
            if offset + limit >= total:
                break
            
            offset += limit
        
        self.logger.info(f"Fetched {len(drivers)} drivers")
        return drivers
    
    def fetch_constructors(self) -> List[Dict]:
        """
        Fetch all constructors.
        
        Returns:
            List of constructor dictionaries
        """
        self.logger.info("Fetching constructors...")
        endpoint = self.endpoints['constructors']
        
        constructors = []
        offset = 0
        limit = 100
        
        while True:
            params = {'offset': offset, 'limit': limit}
            data = self._make_request(endpoint, params)
            
            if not data or 'MRData' not in data:
                break
            
            constructor_data = data['MRData']['ConstructorTable']
            if 'Constructors' not in constructor_data:
                break
            
            constructors.extend(constructor_data['Constructors'])
            
            total = int(data['MRData']['total'])
            if offset + limit >= total:
                break
            
            offset += limit
        
        self.logger.info(f"Fetched {len(constructors)} constructors")
        return constructors
    
    def fetch_circuits(self) -> List[Dict]:
        """
        Fetch all circuits.
        
        Returns:
            List of circuit dictionaries
        """
        self.logger.info("Fetching circuits...")
        endpoint = self.endpoints['circuits']
        
        circuits = []
        offset = 0
        limit = 100
        
        while True:
            params = {'offset': offset, 'limit': limit}
            data = self._make_request(endpoint, params)
            
            if not data or 'MRData' not in data:
                break
            
            circuit_data = data['MRData']['CircuitTable']
            if 'Circuits' not in circuit_data:
                break
            
            circuits.extend(circuit_data['Circuits'])
            
            total = int(data['MRData']['total'])
            if offset + limit >= total:
                break
            
            offset += limit
        
        self.logger.info(f"Fetched {len(circuits)} circuits")
        return circuits
    
    def fetch_results(
        self,
        year: int,
        round_num: int
    ) -> List[Dict]:
        """
        Fetch race results.
        
        Args:
            year: Season year
            round_num: Round number
            
        Returns:
            List of result dictionaries
        """
        self.logger.info(f"Fetching results for {year} round {round_num}...")
        endpoint = self.endpoints['results'].format(year=year, round=round_num)
        
        data = self._make_request(endpoint)
        if not data or 'MRData' not in data:
            return []
        
        race_data = data['MRData']['RaceTable']
        if 'Races' not in race_data or len(race_data['Races']) == 0:
            return []
        
        race = race_data['Races'][0]
        if 'Results' not in race:
            return []
        
        results = race['Results']
        self.logger.info(f"Fetched {len(results)} results")
        return results
    
    def fetch_lap_times(
        self,
        year: int,
        round_num: int,
        driver_id: Optional[str] = None,
        lap: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch lap times.
        
        Args:
            year: Season year
            round_num: Round number
            driver_id: Driver ID (None = all drivers)
            lap: Lap number (None = all laps)
            
        Returns:
            List of lap time dictionaries
        """
        self.logger.info(f"Fetching lap times for {year} round {round_num}...")
        endpoint = self.endpoints['lap_times'].format(year=year, round=round_num)
        
        if driver_id:
            endpoint = f"/{year}/{round_num}/drivers/{driver_id}/laps.json"
        elif lap:
            endpoint = f"/{year}/{round_num}/laps/{lap}.json"
        
        data = self._make_request(endpoint)
        if not data or 'MRData' not in data:
            return []
        
        race_data = data['MRData']['RaceTable']
        if 'Races' not in race_data or len(race_data['Races']) == 0:
            return []
        
        race = race_data['Races'][0]
        if 'Laps' not in race:
            return []
        
        lap_times = []
        for lap_data in race['Laps']:
            if 'Timings' in lap_data:
                for timing in lap_data['Timings']:
                    timing['lap'] = lap_data['number']
                    lap_times.append(timing)
        
        self.logger.info(f"Fetched {len(lap_times)} lap times")
        return lap_times
    
    def fetch_pit_stops(
        self,
        year: int,
        round_num: int
    ) -> List[Dict]:
        """
        Fetch pit stops.
        
        Args:
            year: Season year
            round_num: Round number
            
        Returns:
            List of pit stop dictionaries
        """
        self.logger.info(f"Fetching pit stops for {year} round {round_num}...")
        endpoint = self.endpoints['pit_stops'].format(year=year, round=round_num)
        
        data = self._make_request(endpoint)
        if not data or 'MRData' not in data:
            return []
        
        race_data = data['MRData']['RaceTable']
        if 'Races' not in race_data or len(race_data['Races']) == 0:
            return []
        
        race = race_data['Races'][0]
        if 'PitStops' not in race:
            return []
        
        pit_stops = race['PitStops']
        self.logger.info(f"Fetched {len(pit_stops)} pit stops")
        return pit_stops
    
    def fetch_qualifying(
        self,
        year: int,
        round_num: int
    ) -> List[Dict]:
        """
        Fetch qualifying results.
        
        Args:
            year: Season year
            round_num: Round number
            
        Returns:
            List of qualifying result dictionaries
        """
        self.logger.info(f"Fetching qualifying for {year} round {round_num}...")
        endpoint = self.endpoints['qualifying'].format(year=year, round=round_num)
        
        data = self._make_request(endpoint)
        if not data or 'MRData' not in data:
            return []
        
        race_data = data['MRData']['RaceTable']
        if 'Races' not in race_data or len(race_data['Races']) == 0:
            return []
        
        race = race_data['Races'][0]
        if 'QualifyingResults' not in race:
            return []
        
        qualifying = race['QualifyingResults']
        self.logger.info(f"Fetched {len(qualifying)} qualifying results")
        return qualifying
    
    def fetch_all_historical_data(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch all historical data.
        
        Args:
            start_year: Start year (None = 1950)
            end_year: End year (None = current year)
            
        Returns:
            Dictionary with all fetched data
        """
        self.logger.info("Starting full historical data fetch...")
        
        data = {
            'seasons': [],
            'races': [],
            'drivers': [],
            'constructors': [],
            'circuits': [],
            'results': {},
            'lap_times': {},
            'pit_stops': {},
            'qualifying': {}
        }
        
        # Fetch reference data
        data['seasons'] = self.fetch_seasons(start_year, end_year)
        data['drivers'] = self.fetch_drivers()
        data['constructors'] = self.fetch_constructors()
        data['circuits'] = self.fetch_circuits()
        
        # Fetch races
        if start_year and end_year:
            for year in range(start_year, end_year + 1):
                races = self.fetch_races(year=year)
                data['races'].extend(races)
        else:
            data['races'] = self.fetch_races()
        
        # Fetch race-specific data
        for race in data['races']:
            year = int(race['season'])
            round_num = int(race['round'])
            
            # Results
            results = self.fetch_results(year, round_num)
            data['results'][f"{year}_{round_num}"] = results
            
            # Lap times (may not be available for all races)
            try:
                lap_times = self.fetch_lap_times(year, round_num)
                if lap_times:
                    data['lap_times'][f"{year}_{round_num}"] = lap_times
            except Exception as e:
                self.logger.warning(f"Could not fetch lap times for {year} round {round_num}: {e}")
            
            # Pit stops (may not be available for all races)
            try:
                pit_stops = self.fetch_pit_stops(year, round_num)
                if pit_stops:
                    data['pit_stops'][f"{year}_{round_num}"] = pit_stops
            except Exception as e:
                self.logger.warning(f"Could not fetch pit stops for {year} round {round_num}: {e}")
            
            # Qualifying
            try:
                qualifying = self.fetch_qualifying(year, round_num)
                if qualifying:
                    data['qualifying'][f"{year}_{round_num}"] = qualifying
            except Exception as e:
                self.logger.warning(f"Could not fetch qualifying for {year} round {round_num}: {e}")
        
        self.logger.info("Completed full historical data fetch")
        return data

