"""
F1.com web scraper.
Scrapes session summaries, sector times, stint data, and circuit metadata.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Any
import yaml
import json

from utils.logger import get_logger
from utils.cache_manager import get_cache_manager
from utils.rate_limiter import get_rate_limiter

logger = get_logger()


class F1ComScraper:
    """Scrapes data from F1.com website."""
    
    def __init__(self, config_path: str = "config/data_sources.yaml"):
        """
        Initialize F1.com scraper.
        
        Args:
            config_path: Path to data sources configuration
        """
        self.logger = logger
        self.cache = get_cache_manager()
        self.rate_limiter = get_rate_limiter().get_limiter('f1com')
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.base_url = config['f1com']['base_url']
        self.api_base = config['f1com']['api_base']
        self.endpoints = config['f1com']['endpoints']
        self.user_agent = config['f1com']['user_agent']
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        self.logger.info(f"Initialized F1.com scraper (base URL: {self.base_url})")
    
    def _make_request(
        self,
        url: str,
        use_cache: bool = True,
        use_api: bool = False
    ) -> Optional[Any]:
        """
        Make HTTP request.
        
        Args:
            url: URL to request
            use_cache: Whether to use cache
            use_api: Whether this is an API request (returns JSON)
            
        Returns:
            Response data (BeautifulSoup for HTML, dict for JSON)
        """
        # Check cache
        if use_cache:
            cached_data = self.cache.get(url)
            if cached_data is not None:
                self.logger.debug(f"Cache hit for {url}")
                if use_api:
                    return cached_data
                else:
                    return BeautifulSoup(cached_data, 'html.parser')
        
        # Rate limiting
        self.rate_limiter._wait_if_needed('f1com')
        
        try:
            self.rate_limiter.record_call('f1com')
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            if use_api:
                data = response.json()
            else:
                data = response.text
                # Cache raw HTML
                if use_cache:
                    self.cache.set(url, data)
                return BeautifulSoup(data, 'html.parser')
            
            # Cache API response
            if use_cache:
                self.cache.set(url, data)
            
            return data
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
    
    def scrape_race_results(
        self,
        year: int,
        round_num: int,
        circuit: str
    ) -> Dict[str, Any]:
        """
        Scrape race results page.
        
        Args:
            year: Season year
            round_num: Round number
            circuit: Circuit name/slug
            
        Returns:
            Dictionary with race results data
        """
        self.logger.info(f"Scraping race results: {year} round {round_num} {circuit}...")
        
        url = self.endpoints['race_results'].format(
            year=year,
            round=round_num,
            circuit=circuit
        )
        
        soup = self._make_request(url)
        if soup is None:
            return {}
        
        results = {
            'year': year,
            'round': round_num,
            'circuit': circuit,
            'results': []
        }
        
        # Find results table
        table = soup.find('table', class_=re.compile('results', re.I))
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    result = {
                        'position': cols[0].text.strip(),
                        'driver': cols[1].text.strip() if len(cols) > 1 else None,
                        'constructor': cols[2].text.strip() if len(cols) > 2 else None,
                        'time': cols[3].text.strip() if len(cols) > 3 else None,
                        'points': cols[4].text.strip() if len(cols) > 4 else None
                    }
                    results['results'].append(result)
        
        self.logger.info(f"Scraped {len(results['results'])} race results")
        return results
    
    def scrape_session_data(
        self,
        year: int,
        round_num: int,
        circuit: str,
        session: str
    ) -> Dict[str, Any]:
        """
        Scrape session data (FP1, FP2, FP3, Q, Sprint, Race).
        
        Args:
            year: Season year
            round_num: Round number
            circuit: Circuit name/slug
            session: Session type (fp1, fp2, fp3, qualifying, sprint, race)
            
        Returns:
            Dictionary with session data
        """
        self.logger.info(f"Scraping session data: {year} {circuit} {session}...")
        
        url = self.endpoints['session_data'].format(
            year=year,
            round=round_num,
            circuit=circuit,
            session=session
        )
        
        soup = self._make_request(url)
        if soup is None:
            return {}
        
        session_data = {
            'year': year,
            'round': round_num,
            'circuit': circuit,
            'session': session,
            'sector_times': [],
            'stints': []
        }
        
        # Try to find sector times
        sector_section = soup.find('div', class_=re.compile('sector', re.I))
        if sector_section:
            # Parse sector times
            pass
        
        # Try to find stint data
        stint_section = soup.find('div', class_=re.compile('stint', re.I))
        if stint_section:
            # Parse stint data
            pass
        
        return session_data
    
    def scrape_circuit_info(
        self,
        year: int,
        circuit: str
    ) -> Dict[str, Any]:
        """
        Scrape circuit information.
        
        Args:
            year: Season year
            circuit: Circuit name/slug
            
        Returns:
            Dictionary with circuit metadata
        """
        self.logger.info(f"Scraping circuit info: {year} {circuit}...")
        
        url = self.endpoints['circuit_info'].format(
            year=year,
            circuit=circuit
        )
        
        soup = self._make_request(url)
        if soup is None:
            return {}
        
        circuit_info = {
            'year': year,
            'circuit': circuit,
            'lap_length': None,
            'number_of_corners': None,
            'drs_zones': []
        }
        
        # Try to find circuit metadata
        # This would require parsing the circuit page structure
        
        return circuit_info
    
    def get_api_data(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Get data from F1.com API (if available).
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            API response as dictionary
        """
        url = f"{self.api_base}{endpoint}"
        
        data = self._make_request(url, use_api=True, params=params)
        return data

