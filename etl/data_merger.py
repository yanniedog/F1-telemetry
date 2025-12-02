"""
Data merger for combining data from all sources.
Resolves conflicts and creates unified driver/constructor IDs.
"""

from typing import Dict, List, Optional, Any
from collections import defaultdict

from utils.logger import get_logger
from etl.data_normalizer import DataNormalizer
from etl.driver_matcher import DriverMatcher

logger = get_logger()


class DataMerger:
    """Merges data from multiple sources."""
    
    def __init__(self):
        """Initialize data merger."""
        self.logger = logger
        self.normalizer = DataNormalizer()
        self.driver_matcher = DriverMatcher()
        
        # Source priority (higher = more authoritative)
        self.source_priority = {
            'ergast': 10,  # Most comprehensive historical data
            'openf1': 8,   # Official telemetry
            'fastf1': 8,   # Official timing data
            'fia': 9,      # Official FIA documents
            'f1com': 7,    # Official website
            'statsf1': 6,  # Third-party statistics
            'wikipedia': 3 # Cross-reference only
        }
        
        self.logger.info("Initialized data merger")
    
    def merge_drivers(
        self,
        drivers_by_source: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Merge drivers from multiple sources.
        
        Args:
            drivers_by_source: Dictionary mapping source names to driver lists
            
        Returns:
            List of merged driver dictionaries
        """
        self.logger.info("Merging drivers from multiple sources...")
        
        # Use driver matcher to create unified drivers
        unified_drivers = self.driver_matcher.create_unified_driver(drivers_by_source)
        
        self.logger.info(f"Merged {len(unified_drivers)} drivers")
        return unified_drivers
    
    def merge_constructors(
        self,
        constructors_by_source: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Merge constructors from multiple sources.
        
        Args:
            constructors_by_source: Dictionary mapping source names to constructor lists
            
        Returns:
            List of merged constructor dictionaries
        """
        self.logger.info("Merging constructors from multiple sources...")
        
        unified_constructors = []
        constructor_id_counter = 1
        seen_names = {}
        
        # Process constructors from each source (prioritized)
        sources_sorted = sorted(
            constructors_by_source.items(),
            key=lambda x: self.source_priority.get(x[0], 0),
            reverse=True
        )
        
        for source, constructors in sources_sorted:
            for constructor in constructors:
                constructor_name = constructor.get('name') or ''
                normalized_name = self.normalizer.normalize_name(constructor_name)
                
                if not normalized_name:
                    continue
                
                # Check if we've seen this constructor
                if normalized_name in seen_names:
                    # Update existing constructor
                    existing_id = seen_names[normalized_name]
                    for unified in unified_constructors:
                        if unified['constructor_id'] == existing_id:
                            # Add source-specific ID
                            unified[f'{source}_id'] = constructor.get('id') or constructor.get('constructor_id')
                            # Update data if more complete
                            if not unified.get('nationality') and constructor.get('nationality'):
                                unified['nationality'] = constructor.get('nationality')
                            break
                else:
                    # Create new unified constructor
                    unified_constructor = {
                        'constructor_id': constructor_id_counter,
                        'constructor_ref': constructor.get('constructor_ref') or f"constructor_{constructor_id_counter}",
                        'name': constructor_name,
                        'nationality': constructor.get('nationality'),
                        f'{source}_id': constructor.get('id') or constructor.get('constructor_id')
                    }
                    
                    unified_constructors.append(unified_constructor)
                    seen_names[normalized_name] = constructor_id_counter
                    constructor_id_counter += 1
        
        self.logger.info(f"Merged {len(unified_constructors)} constructors")
        return unified_constructors
    
    def merge_races(
        self,
        races_by_source: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Merge races from multiple sources.
        
        Args:
            races_by_source: Dictionary mapping source names to race lists
            
        Returns:
            List of merged race dictionaries
        """
        self.logger.info("Merging races from multiple sources...")
        
        unified_races = []
        race_key_map = {}  # (year, round) -> race_id
        
        # Process races from each source (prioritized)
        sources_sorted = sorted(
            races_by_source.items(),
            key=lambda x: self.source_priority.get(x[0], 0),
            reverse=True
        )
        
        for source, races in sources_sorted:
            for race in races:
                year = race.get('year') or race.get('season')
                round_num = race.get('round')
                
                if not year or not round_num:
                    continue
                
                race_key = (int(year), int(round_num))
                
                if race_key in race_key_map:
                    # Update existing race
                    race_id = race_key_map[race_key]
                    for unified in unified_races:
                        if unified['race_id'] == race_id:
                            # Merge data (prefer higher priority source)
                            if not unified.get('name') and race.get('name'):
                                unified['name'] = race.get('name')
                            if not unified.get('date') and race.get('date'):
                                unified['date'] = race.get('date')
                            # Add source-specific data
                            unified[f'{source}_race_id'] = race.get('id') or race.get('race_id')
                            break
                else:
                    # Create new unified race
                    unified_race = {
                        'race_id': len(unified_races) + 1,
                        'year': int(year),
                        'round': int(round_num),
                        'name': race.get('name') or race.get('raceName'),
                        'date': race.get('date'),
                        'circuit_id': race.get('circuit_id'),
                        'circuit_ref': race.get('circuit', {}).get('circuitId') if isinstance(race.get('circuit'), dict) else race.get('circuit'),
                        f'{source}_race_id': race.get('id') or race.get('raceId')
                    }
                    
                    unified_races.append(unified_race)
                    race_key_map[race_key] = unified_race['race_id']
        
        self.logger.info(f"Merged {len(unified_races)} races")
        return unified_races
    
    def resolve_conflict(
        self,
        values: List[Any],
        source_priorities: List[int]
    ) -> Any:
        """
        Resolve conflict between multiple values using source priority.
        
        Args:
            values: List of conflicting values
            source_priorities: List of source priority scores (same order as values)
            
        Returns:
            Resolved value
        """
        if not values:
            return None
        
        # Remove None values
        valid_values = [(v, p) for v, p in zip(values, source_priorities) if v is not None]
        
        if not valid_values:
            return None
        
        # Return value from highest priority source
        valid_values.sort(key=lambda x: x[1], reverse=True)
        return valid_values[0][0]
    
    def merge_results(
        self,
        results_by_source: Dict[str, List[Dict]],
        race_id: int
    ) -> List[Dict]:
        """
        Merge race results from multiple sources.
        
        Args:
            results_by_source: Dictionary mapping source names to result lists
            race_id: Unified race ID
            
        Returns:
            List of merged result dictionaries
        """
        self.logger.info(f"Merging results for race {race_id}...")
        
        unified_results = []
        
        # Group results by driver
        results_by_driver = defaultdict(list)
        
        for source, results in results_by_source.items():
            for result in results:
                driver_id = result.get('driver_id')
                if driver_id:
                    results_by_driver[driver_id].append((result, source))
        
        # Merge results for each driver
        for driver_id, driver_results in results_by_driver.items():
            if len(driver_results) == 1:
                # Single source
                result, source = driver_results[0]
                unified_result = {
                    'race_id': race_id,
                    'driver_id': driver_id,
                    'position': result.get('position'),
                    'points': result.get('points'),
                    'status': self.normalizer.normalize_status(result.get('status', '')),
                    'laps': result.get('laps'),
                    'time': result.get('time'),
                    'source': source
                }
            else:
                # Multiple sources - resolve conflicts
                positions = [r.get('position') for r, s in driver_results]
                priorities = [self.source_priority.get(s, 0) for r, s in driver_results]
                
                unified_result = {
                    'race_id': race_id,
                    'driver_id': driver_id,
                    'position': self.resolve_conflict(positions, priorities),
                    'points': self.resolve_conflict(
                        [r.get('points') for r, s in driver_results],
                        priorities
                    ),
                    'status': self.normalizer.normalize_status(
                        self.resolve_conflict(
                            [r.get('status', '') for r, s in driver_results],
                            priorities
                        ) or ''
                    ),
                    'laps': self.resolve_conflict(
                        [r.get('laps') for r, s in driver_results],
                        priorities
                    ),
                    'time': self.resolve_conflict(
                        [r.get('time') for r, s in driver_results],
                        priorities
                    ),
                    'sources': [s for r, s in driver_results]
                }
            
            unified_results.append(unified_result)
        
        self.logger.info(f"Merged {len(unified_results)} results")
        return unified_results

