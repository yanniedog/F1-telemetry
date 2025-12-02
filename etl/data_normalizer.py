"""
Data normalizer for F1 dataset.
Normalizes timestamps to UTC, aligns lap numbers, standardizes status codes, and normalizes names.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import pytz
import re

from utils.logger import get_logger

logger = get_logger()


class DataNormalizer:
    """Normalizes F1 data for consistency."""
    
    def __init__(self, timezone: str = "UTC"):
        """
        Initialize data normalizer.
        
        Args:
            timezone: Target timezone for normalization (default: UTC)
        """
        self.logger = logger
        self.target_timezone = pytz.timezone(timezone)
        
        # Status code mappings
        self.status_mappings = {
            'Finished': 'Finished',
            'F': 'Finished',
            'DNF': 'DNF',
            'Did not finish': 'DNF',
            'Not classified': 'DNF',
            'NC': 'DNF',
            'DNS': 'DNS',
            'Did not start': 'DNS',
            'DSQ': 'DSQ',
            'Disqualified': 'DSQ',
            'EX': 'DSQ',
            'WD': 'Withdrew',
            'Withdrew': 'Withdrew',
            'Retired': 'DNF',
            'R': 'DNF'
        }
        
        self.logger.info(f"Initialized data normalizer (timezone: {timezone})")
    
    def normalize_timestamp(
        self,
        timestamp: Any,
        source_timezone: Optional[str] = None
    ) -> Optional[datetime]:
        """
        Normalize timestamp to UTC.
        
        Args:
            timestamp: Timestamp (datetime, string, or None)
            source_timezone: Source timezone (if known)
            
        Returns:
            Normalized datetime in UTC or None
        """
        if timestamp is None:
            return None
        
        # If already datetime
        if isinstance(timestamp, datetime):
            dt = timestamp
        # If string, try to parse
        elif isinstance(timestamp, str):
            try:
                # Try ISO format first
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try common formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                        try:
                            dt = datetime.strptime(timestamp, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        self.logger.warning(f"Could not parse timestamp: {timestamp}")
                        return None
                except Exception as e:
                    self.logger.warning(f"Error parsing timestamp {timestamp}: {e}")
                    return None
        else:
            self.logger.warning(f"Unknown timestamp type: {type(timestamp)}")
            return None
        
        # Handle timezone
        if dt.tzinfo is None:
            # No timezone info - assume source timezone or UTC
            if source_timezone:
                source_tz = pytz.timezone(source_timezone)
                dt = source_tz.localize(dt)
            else:
                # Assume UTC
                dt = pytz.UTC.localize(dt)
        
        # Convert to target timezone (UTC)
        dt_utc = dt.astimezone(pytz.UTC)
        return dt_utc
    
    def normalize_status(self, status: str) -> str:
        """
        Normalize status code.
        
        Args:
            status: Status string
            
        Returns:
            Normalized status code
        """
        if not status:
            return 'Unknown'
        
        status_upper = status.strip().upper()
        
        # Direct mapping
        if status_upper in self.status_mappings:
            return self.status_mappings[status_upper]
        
        # Pattern matching
        if 'DNF' in status_upper or 'NOT FINISH' in status_upper:
            return 'DNF'
        elif 'DNS' in status_upper or 'NOT START' in status_upper:
            return 'DNS'
        elif 'DSQ' in status_upper or 'DISQUAL' in status_upper:
            return 'DSQ'
        elif 'FINISH' in status_upper or 'COMPLETED' in status_upper:
            return 'Finished'
        
        # Return original if no match
        return status.strip()
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize name (driver, constructor, circuit).
        
        Args:
            name: Name string
            
        Returns:
            Normalized name
        """
        if not name:
            return ''
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Title case (but preserve known abbreviations)
        # This is a simplified approach - may need more sophisticated handling
        words = name.split()
        normalized_words = []
        
        for word in words:
            # Preserve all-caps abbreviations (e.g., "F1", "GP")
            if word.isupper() and len(word) <= 3:
                normalized_words.append(word)
            else:
                normalized_words.append(word.capitalize())
        
        return ' '.join(normalized_words)
    
    def normalize_circuit_name(self, name: str) -> str:
        """
        Normalize circuit name.
        
        Args:
            name: Circuit name
            
        Returns:
            Normalized circuit name
        """
        if not name:
            return ''
        
        # Circuit names often have specific formats
        name = self.normalize_name(name)
        
        # Common variations
        name = name.replace('Grand Prix', 'GP')
        name = name.replace('International Circuit', 'Circuit')
        name = name.replace('Racing Circuit', 'Circuit')
        
        return name.strip()
    
    def align_lap_number(
        self,
        lap: Any,
        source: str = "unknown"
    ) -> Optional[int]:
        """
        Align lap number across sources.
        
        Args:
            lap: Lap number (int, string, or None)
            source: Data source name
            
        Returns:
            Normalized lap number or None
        """
        if lap is None:
            return None
        
        try:
            # Convert to int
            if isinstance(lap, str):
                # Remove non-numeric characters
                lap_str = re.sub(r'[^0-9]', '', lap)
                if lap_str:
                    return int(lap_str)
                else:
                    return None
            elif isinstance(lap, (int, float)):
                return int(lap)
            else:
                self.logger.warning(f"Unknown lap type: {type(lap)} for source {source}")
                return None
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Could not normalize lap number {lap} from {source}: {e}")
            return None
    
    def normalize_time_string(self, time_str: str) -> Optional[str]:
        """
        Normalize time string (lap time, sector time, etc.).
        
        Args:
            time_str: Time string (e.g., "1:23.456", "1:23:45.678")
            
        Returns:
            Normalized time string or None
        """
        if not time_str:
            return None
        
        time_str = time_str.strip()
        
        # Remove common prefixes/suffixes
        time_str = re.sub(r'^\+', '', time_str)  # Remove leading +
        time_str = re.sub(r'[^\d:.]', '', time_str)  # Keep only digits, :, and .
        
        # Validate format (should be M:SS.mmm or H:MM:SS.mmm)
        if re.match(r'^\d+:\d{2}(:\d{2})?(\.\d+)?$', time_str):
            return time_str
        
        return None
    
    def normalize_driver_code(self, code: str) -> Optional[str]:
        """
        Normalize driver code (3-letter abbreviation).
        
        Args:
            code: Driver code
            
        Returns:
            Normalized driver code (uppercase, 3 letters) or None
        """
        if not code:
            return None
        
        code = code.strip().upper()
        
        # Should be 3 letters
        if len(code) == 3 and code.isalpha():
            return code
        elif len(code) > 3:
            # Take first 3 letters
            return code[:3]
        else:
            return None
    
    def normalize_tyre_compound(self, compound: str) -> Optional[str]:
        """
        Normalize tyre compound name.
        
        Args:
            compound: Tyre compound string
            
        Returns:
            Normalized compound name or None
        """
        if not compound:
            return None
        
        compound = compound.strip().upper()
        
        # Standard compounds
        compound_mappings = {
            'SOFT': 'SOFT',
            'MEDIUM': 'MEDIUM',
            'HARD': 'HARD',
            'INTERMEDIATE': 'INTERMEDIATE',
            'WET': 'WET',
            'C1': 'C1',
            'C2': 'C2',
            'C3': 'C3',
            'C4': 'C4',
            'C5': 'C5',
            'SUPERSOFT': 'C5',
            'ULTRASOFT': 'C5',
            'HYPERSOFT': 'C5'
        }
        
        return compound_mappings.get(compound, compound)
    
    def normalize_position(self, position: Any) -> Optional[int]:
        """
        Normalize position number.
        
        Args:
            position: Position (int, string, or None)
            
        Returns:
            Normalized position integer or None
        """
        if position is None:
            return None
        
        try:
            if isinstance(position, str):
                # Remove non-numeric characters
                pos_str = re.sub(r'[^0-9]', '', position)
                if pos_str:
                    return int(pos_str)
                else:
                    return None
            elif isinstance(position, (int, float)):
                pos = int(position)
                if pos > 0:
                    return pos
                else:
                    return None
            else:
                return None
        except (ValueError, TypeError):
            return None

