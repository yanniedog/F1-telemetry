"""
FIA PDF parser.
Downloads and parses FIA race classification PDFs for detailed results and timing data.
"""

import requests
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import re

from utils.logger import get_logger
from utils.cache_manager import get_cache_manager
from utils.rate_limiter import get_rate_limiter

logger = get_logger()


class FIAPDFParser:
    """Downloads and parses FIA PDF documents."""
    
    def __init__(self, config_path: str = "config/data_sources.yaml"):
        """
        Initialize FIA PDF parser.
        
        Args:
            config_path: Path to data sources configuration
        """
        self.logger = logger
        self.cache = get_cache_manager()
        self.rate_limiter = get_rate_limiter().get_limiter('fia')
        
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.base_url = config['fia']['base_url']
        self.endpoints = config['fia']['endpoints']
        self.user_agent = config['fia']['user_agent']
        self.pdf_dir = Path(config['fia']['pdf_dir'])
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        self.logger.info(f"Initialized FIA PDF parser (PDF dir: {self.pdf_dir})")
    
    def _download_pdf(
        self,
        url: str,
        filename: str
    ) -> Optional[Path]:
        """
        Download PDF file.
        
        Args:
            url: PDF URL
            filename: Local filename
            
        Returns:
            Path to downloaded file or None
        """
        filepath = self.pdf_dir / filename
        
        # Check if already downloaded
        if filepath.exists():
            self.logger.debug(f"PDF already exists: {filename}")
            return filepath
        
        # Rate limiting
        self.rate_limiter._wait_if_needed('fia')
        
        try:
            self.rate_limiter.record_call('fia')
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Downloaded PDF: {filename}")
            return filepath
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to download PDF {url}: {e}")
            return None
    
    def _parse_pdf(
        self,
        filepath: Path
    ) -> Dict[str, Any]:
        """
        Parse PDF file.
        
        Args:
            filepath: Path to PDF file
            
        Returns:
            Dictionary with parsed data
        """
        self.logger.info(f"Parsing PDF: {filepath.name}")
        
        data = {
            'filename': filepath.name,
            'results': [],
            'timing': []
        }
        
        try:
            with pdfplumber.open(filepath) as pdf:
                # Extract text from all pages
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
                
                # Try to extract tables
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        # Parse classification table
                        if len(table) > 0 and 'Pos' in str(table[0]).lower():
                            # This is likely a classification table
                            for row in table[1:]:
                                if len(row) >= 4:
                                    result = {
                                        'position': row[0].strip() if row[0] else None,
                                        'driver': row[1].strip() if len(row) > 1 and row[1] else None,
                                        'constructor': row[2].strip() if len(row) > 2 and row[2] else None,
                                        'time': row[3].strip() if len(row) > 3 and row[3] else None
                                    }
                                    data['results'].append(result)
                
                data['full_text'] = full_text
        
        except Exception as e:
            self.logger.error(f"Failed to parse PDF {filepath}: {e}")
        
        return data
    
    def find_race_classification_pdf(
        self,
        year: int,
        round_num: int
    ) -> Optional[str]:
        """
        Find URL for race classification PDF.
        
        Args:
            year: Season year
            round_num: Round number
            
        Returns:
            PDF URL or None
        """
        # FIA document URLs are not always predictable
        # This would require scraping the FIA documents page
        # or maintaining a mapping of known URLs
        
        # Placeholder - in practice, you'd need to:
        # 1. Scrape the FIA documents page for the year
        # 2. Find the race classification document
        # 3. Extract the PDF URL
        
        self.logger.warning(f"PDF URL lookup not fully implemented for {year} round {round_num}")
        return None
    
    def download_and_parse(
        self,
        year: int,
        round_num: int
    ) -> Dict[str, Any]:
        """
        Download and parse race classification PDF.
        
        Args:
            year: Season year
            round_num: Round number
            
        Returns:
            Dictionary with parsed data
        """
        self.logger.info(f"Downloading and parsing FIA PDF for {year} round {round_num}...")
        
        # Find PDF URL
        pdf_url = self.find_race_classification_pdf(year, round_num)
        if not pdf_url:
            return {}
        
        # Download PDF
        filename = f"fia_classification_{year}_{round_num}.pdf"
        filepath = self._download_pdf(pdf_url, filename)
        
        if not filepath:
            return {}
        
        # Parse PDF
        data = self._parse_pdf(filepath)
        data['year'] = year
        data['round'] = round_num
        
        return data

