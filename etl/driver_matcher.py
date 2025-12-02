"""
Driver matcher for cross-linking drivers across multiple sources.
Handles name variations and creates unified driver reference.
"""

from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
import re

from utils.logger import get_logger

logger = get_logger()


class DriverMatcher:
    """Matches drivers across different data sources."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize driver matcher.
        
        Args:
            similarity_threshold: Minimum similarity score for matching (0-1)
        """
        self.logger = logger
        self.similarity_threshold = similarity_threshold
        self.driver_mappings = {}  # Unified driver ID -> source IDs
        self.name_variations = {}  # Name variations cache
        
        self.logger.info(f"Initialized driver matcher (threshold: {similarity_threshold})")
    
    def _normalize_name_for_matching(self, name: str) -> str:
        """
        Normalize name for matching (remove accents, lowercase, etc.).
        
        Args:
            name: Driver name
            
        Returns:
            Normalized name
        """
        if not name:
            return ''
        
        # Lowercase
        name = name.lower()
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove common suffixes
        name = re.sub(r'\s+(jr|sr|ii|iii|iv)$', '', name)
        
        # Remove accents (simplified - would need unidecode for full support)
        # For now, just handle common cases
        replacements = {
            'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        return name.strip()
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score (0-1)
        """
        norm1 = self._normalize_name_for_matching(name1)
        norm2 = self._normalize_name_for_matching(name2)
        
        # Exact match
        if norm1 == norm2:
            return 1.0
        
        # Sequence matcher
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Check if one name contains the other (for nicknames/abbreviations)
        if norm1 in norm2 or norm2 in norm1:
            similarity = max(similarity, 0.9)
        
        return similarity
    
    def _extract_name_parts(self, full_name: str) -> Tuple[str, str]:
        """
        Extract forename and surname from full name.
        
        Args:
            full_name: Full driver name
            
        Returns:
            Tuple of (forename, surname)
        """
        parts = full_name.split()
        if len(parts) >= 2:
            forename = ' '.join(parts[:-1])
            surname = parts[-1]
        elif len(parts) == 1:
            forename = ''
            surname = parts[0]
        else:
            forename = ''
            surname = ''
        
        return (forename, surname)
    
    def match_driver(
        self,
        driver_data: Dict,
        source: str,
        existing_drivers: List[Dict]
    ) -> Optional[int]:
        """
        Match a driver against existing drivers.
        
        Args:
            driver_data: Driver data dictionary with name, code, number, etc.
            source: Source name (e.g., 'ergast', 'openf1')
            existing_drivers: List of existing driver dictionaries
            
        Returns:
            Matched driver ID or None
        """
        driver_name = driver_data.get('name') or driver_data.get('full_name') or ''
        driver_code = driver_data.get('code') or driver_data.get('driver_code')
        driver_number = driver_data.get('number') or driver_data.get('driver_number')
        
        if not driver_name:
            return None
        
        # Try exact match by code first
        if driver_code:
            for existing in existing_drivers:
                if existing.get('code') == driver_code:
                    return existing.get('driver_id')
        
        # Try exact match by number
        if driver_number:
            for existing in existing_drivers:
                if existing.get('number') == driver_number:
                    # Verify name similarity
                    existing_name = existing.get('name') or existing.get('full_name') or ''
                    similarity = self._calculate_similarity(driver_name, existing_name)
                    if similarity >= self.similarity_threshold:
                        return existing.get('driver_id')
        
        # Try name matching
        best_match = None
        best_similarity = 0.0
        
        for existing in existing_drivers:
            existing_name = existing.get('name') or existing.get('full_name') or ''
            if not existing_name:
                continue
            
            similarity = self._calculate_similarity(driver_name, existing_name)
            
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = existing.get('driver_id')
        
        if best_match:
            self.logger.debug(
                f"Matched driver '{driver_name}' to existing driver ID {best_match} "
                f"(similarity: {best_similarity:.2f})"
            )
        
        return best_match
    
    def create_unified_driver(
        self,
        drivers_by_source: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Create unified driver list from multiple sources.
        
        Args:
            drivers_by_source: Dictionary mapping source names to driver lists
            
        Returns:
            List of unified driver dictionaries
        """
        self.logger.info("Creating unified driver list...")
        
        unified_drivers = []
        driver_id_counter = 1
        
        # Process drivers from each source
        for source, drivers in drivers_by_source.items():
            for driver in drivers:
                # Try to match with existing unified drivers
                matched_id = self.match_driver(driver, source, unified_drivers)
                
                if matched_id:
                    # Update existing driver with cross-source IDs
                    for unified in unified_drivers:
                        if unified['driver_id'] == matched_id:
                            # Add source-specific ID
                            unified[f'{source}_id'] = driver.get('id') or driver.get('driver_id')
                            # Update name if more complete
                            if not unified.get('full_name') and driver.get('name'):
                                unified['full_name'] = driver.get('name')
                            break
                else:
                    # Create new unified driver
                    driver_name = driver.get('name') or driver.get('full_name') or ''
                    forename, surname = self._extract_name_parts(driver_name)
                    
                    unified_driver = {
                        'driver_id': driver_id_counter,
                        'driver_ref': driver.get('driver_ref') or f"driver_{driver_id_counter}",
                        'forename': forename,
                        'surname': surname,
                        'full_name': driver_name,
                        'code': driver.get('code') or driver.get('driver_code'),
                        'number': driver.get('number') or driver.get('driver_number'),
                        'nationality': driver.get('nationality'),
                        'date_of_birth': driver.get('date_of_birth') or driver.get('dob'),
                        f'{source}_id': driver.get('id') or driver.get('driver_id')
                    }
                    
                    unified_drivers.append(unified_driver)
                    driver_id_counter += 1
        
        self.logger.info(f"Created {len(unified_drivers)} unified drivers")
        return unified_drivers
    
    def get_driver_mapping(
        self,
        source: str,
        source_id: Any
    ) -> Optional[int]:
        """
        Get unified driver ID from source-specific ID.
        
        Args:
            source: Source name
            source_id: Source-specific driver ID
            
        Returns:
            Unified driver ID or None
        """
        for driver_id, mappings in self.driver_mappings.items():
            if mappings.get(source) == source_id:
                return driver_id
        return None

