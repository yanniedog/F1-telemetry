"""
StatsF1 web scraper.
Scrapes race reports, safety car periods, VSC periods, and red flag data.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml
import time

from utils.logger import get_logger
from utils.cache_manager import get_cache_manager
from utils.rate_limiter import get_rate_limiter

logger = get_logger()


class StatsF1Scraper:
    """Scrapes data from StatsF1 website."""
    
    def __init__(self, config_path: str = "config/data_sources.yaml"):
        """
        Initialize StatsF1 scraper.
        
        Args:
            config_path: Path to data sources configuration
        """
        self.logger = logger
        self.cache = get_cache_manager()
        self.rate_limiter = get_rate_limiter().get_limiter('statsf1')
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.base_url = config['statsf1']['base_url']
        self.endpoints = config['statsf1']['endpoints']
        self.user_agent = config['statsf1']['user_agent']
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        self.logger.info(f"Initialized StatsF1 scraper (base URL: {self.base_url})")
    
    def _make_request(
        self,
        url: str,
        use_cache: bool = True
    ) -> Optional[BeautifulSoup]:
        """
        Make HTTP request and parse HTML.
        
        Args:
            url: URL to scrape
            use_cache: Whether to use cache
            
        Returns:
            BeautifulSoup object or None
        """
        # Check cache
        if use_cache:
            cached_data = self.cache.get(url)
            if cached_data is not None:
                self.logger.debug(f"Cache hit for {url}")
                return BeautifulSoup(cached_data, 'html.parser')
        
        # Rate limiting
        self.rate_limiter._wait_if_needed('statsf1')
        
        try:
            self.rate_limiter.record_call('statsf1')
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Cache raw HTML
            if use_cache:
                self.cache.set(url, response.text)
            
            return BeautifulSoup(response.text, 'html.parser')
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _get_circuit_name(self, year: int, round_num: int) -> Optional[str]:
        """
        Get circuit name for a race (simplified - would need mapping).
        
        Args:
            year: Season year
            round_num: Round number
            
        Returns:
            Circuit name or None
        """
        # This is a simplified version - in practice, you'd need a mapping
        # from year/round to circuit names
        # For now, return None and let the caller provide circuit name
        return None
    
    def scrape_race_report(
        self,
        year: int,
        circuit_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape race report.
        
        Args:
            year: Season year
            circuit_name: Circuit name (if known)
            
        Returns:
            Dictionary with race report data
        """
        self.logger.info(f"Scraping race report for {year} {circuit_name}...")
        
        # StatsF1 URL structure varies, this is a simplified approach
        if circuit_name:
            # Convert circuit name to StatsF1 format (lowercase, hyphens)
            circuit_slug = circuit_name.lower().replace(' ', '-')
            url = self.endpoints['race_reports'].format(year=year, circuit=circuit_slug)
        else:
            # Try to find race page
            url = f"{self.base_url}/en/{year}.aspx"
        
        soup = self._make_request(url)
        if soup is None:
            return {}
        
        report = {
            'year': year,
            'circuit': circuit_name,
            'url': url,
            'safety_car_periods': [],
            'red_flags': [],
            'incidents': []
        }
        
        # Parse safety car periods (example - actual parsing depends on page structure)
        sc_section = soup.find('div', class_=re.compile('safety.*car', re.I))
        if sc_section:
            # Extract SC periods from table or list
            # This is a placeholder - actual parsing would depend on HTML structure
            pass
        
        # Parse red flags
        rf_section = soup.find('div', class_=re.compile('red.*flag', re.I))
        if rf_section:
            # Extract red flag data
            pass
        
        self.logger.info(f"Scraped race report for {year} {circuit_name}")
        return report
    
    def scrape_safety_car_periods(
        self,
        year: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape safety car period statistics.
        
        Args:
            year: Season year (None = all years)
            
        Returns:
            List of safety car period dictionaries
        """
        self.logger.info(f"Scraping safety car periods (year={year})...")
        
        url = self.endpoints['safety_car']
        if year:
            url = f"{url}?year={year}"
        
        soup = self._make_request(url)
        if soup is None:
            return []
        
        sc_periods = []
        
        # Find table with safety car data
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    period = {
                        'year': int(cols[0].text.strip()) if cols[0].text.strip().isdigit() else None,
                        'race': cols[1].text.strip(),
                        'lap': cols[2].text.strip() if len(cols) > 2 else None,
                        'duration': cols[3].text.strip() if len(cols) > 3 else None
                    }
                    sc_periods.append(period)
        
        self.logger.info(f"Scraped {len(sc_periods)} safety car periods")
        return sc_periods
    
    def scrape_red_flags(
        self,
        year: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape red flag statistics.
        
        Args:
            year: Season year (None = all years)
            
        Returns:
            List of red flag dictionaries
        """
        self.logger.info(f"Scraping red flags (year={year})...")
        
        url = self.endpoints['red_flags']
        if year:
            url = f"{url}?year={year}"
        
        soup = self._make_request(url)
        if soup is None:
            return []
        
        red_flags = []
        
        # Find table with red flag data
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    flag = {
                        'year': int(cols[0].text.strip()) if cols[0].text.strip().isdigit() else None,
                        'race': cols[1].text.strip(),
                        'reason': cols[2].text.strip() if len(cols) > 2 else None
                    }
                    red_flags.append(flag)
        
        self.logger.info(f"Scraped {len(red_flags)} red flags")
        return red_flags
    
    def scrape_vsc_periods(
        self,
        year: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape Virtual Safety Car periods.
        
        Args:
            year: Season year (None = all years)
            
        Returns:
            List of VSC period dictionaries
        """
        self.logger.info(f"Scraping VSC periods (year={year})...")
        
        # VSC data may be on a different page or embedded in race reports
        # This is a placeholder - actual implementation would depend on page structure
        vsc_periods = []
        
        # Try to find VSC data in race reports
        # This would require iterating through races and parsing reports
        
        self.logger.info(f"Scraped {len(vsc_periods)} VSC periods")
        return vsc_periods

