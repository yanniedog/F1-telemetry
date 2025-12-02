"""
F1 Historical Dataset - Main Orchestration Script
Coordinates data fetching, ETL pipeline, validation, and exports.
"""

import argparse
import sqlite3
from pathlib import Path
import yaml
from typing import Optional

from utils.logger import get_logger
from data_sources.ergast_fetcher import ErgastFetcher
from data_sources.openf1_fetcher import OpenF1Fetcher
from data_sources.fastf1_fetcher import FastF1Fetcher
from etl.data_normalizer import DataNormalizer
from etl.driver_matcher import DriverMatcher
from etl.data_merger import DataMerger
from etl.data_validator import DataValidator
from etl.database_inserter import DatabaseInserter
from exports.export_to_csv import CSVExporter
from exports.export_to_parquet import ParquetExporter

logger = get_logger()


class F1DatasetBuilder:
    """Main class for building F1 historical dataset."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize F1 dataset builder.
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = logger
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.db_path = self.config['database']['sqlite_path']
        self.normalizer = DataNormalizer(
            timezone=self.config['etl']['normalize_timezone']
        )
        self.driver_matcher = DriverMatcher(
            similarity_threshold=self.config['etl']['driver_matching_threshold']
        )
        self.merger = DataMerger()
        self.validator = DataValidator(db_path=self.db_path)
        self.inserter = DatabaseInserter(db_path=self.db_path)
        
        # Initialize data fetchers
        self.ergast_fetcher = ErgastFetcher() if self.config['fetching']['sources']['ergast'] else None
        self.openf1_fetcher = OpenF1Fetcher() if self.config['fetching']['sources']['openf1'] else None
        self.fastf1_fetcher = FastF1Fetcher() if self.config['fetching']['sources']['fastf1'] else None
        
        # Ensure database exists
        self._initialize_database()
        
        self.logger.info("F1 Dataset Builder initialized")
    
    def _initialize_database(self):
        """Initialize database schema if it doesn't exist."""
        db_path = Path(self.db_path)
        if not db_path.exists():
            self.logger.info("Initializing database...")
            schema_path = Path("schema/schema.sql")
            if schema_path.exists():
                conn = sqlite3.connect(self.db_path)
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
                conn.close()
                self.logger.info("Database initialized successfully")
            else:
                self.logger.warning("Schema file not found, database will be created on first use")
    
    def fetch_ergast_data(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ):
        """
        Fetch data from Ergast API.
        
        Args:
            start_year: Start year (None = from config or all)
            end_year: End year (None = from config or current)
        """
        if not self.ergast_fetcher:
            self.logger.warning("Ergast fetcher not enabled")
            return
        
        self.logger.info("Fetching data from Ergast API...")
        
        start_year = start_year or self.config['fetching'].get('start_year')
        end_year = end_year or self.config['fetching'].get('end_year')
        
        # Fetch all historical data
        data = self.ergast_fetcher.fetch_all_historical_data(start_year, end_year)
        
        # TODO: Insert data into database
        # This would involve:
        # 1. Normalize data using DataNormalizer
        # 2. Match drivers using DriverMatcher
        # 3. Merge with existing data using DataMerger
        # 4. Insert into database
        
        self.logger.info("Ergast data fetch completed")
    
    def fetch_openf1_data(self, year: Optional[int] = None):
        """
        Fetch telemetry data from OpenF1 API.
        
        Args:
            year: Year to fetch (None = from config or all modern years)
        """
        if not self.openf1_fetcher:
            self.logger.warning("OpenF1 fetcher not enabled")
            return
        
        self.logger.info("Fetching data from OpenF1 API...")
        
        year = year or 2023  # Default to recent year
        
        # Fetch sessions for the year
        sessions = self.openf1_fetcher.fetch_sessions(year=year, session_name='Race')
        
        # Insert sessions first and get session_id mapping
        session_map = self.inserter.insert_sessions(sessions)
        self.logger.info(f"Inserted/updated {len(session_map)} sessions into database")
        
        total_laps = 0
        total_positions = 0
        
        for session in sessions:
            session_key = session.get('session_key')
            if not session_key:
                continue
                
            session_id = session_map.get(session_key)
            if not session_id:
                self.logger.warning(f"Session {session_key} not found in database, skipping")
                continue
            
            self.logger.info(f"Fetching telemetry for session {session_key} (ID: {session_id})...")
            
            # Fetch complete telemetry
            telemetry = self.openf1_fetcher.fetch_session_telemetry(session_key)
            
            # Insert telemetry into database
            if telemetry:
                results = self.inserter.insert_openf1_telemetry(telemetry, session_id)
                total_laps += results.get('lap_times', 0)
                total_positions += results.get('positions', 0)
        
        self.logger.info(f"OpenF1 data fetch completed: {total_laps} lap times, {total_positions} position records inserted")
    
    def fetch_fastf1_data(
        self,
        year: Optional[int] = None,
        circuit: Optional[str] = None,
        session_type: Optional[str] = None
    ):
        """
        Fetch data using FastF1 library.
        
        Args:
            year: Year to fetch
            circuit: Circuit name (None = all circuits)
            session_type: Session type (None = all sessions)
        """
        if not self.fastf1_fetcher:
            self.logger.warning("FastF1 fetcher not enabled")
            return
        
        self.logger.info("Fetching data using FastF1 library...")
        
        year = year or 2023  # Default to recent year
        
        # TODO: Get list of circuits for the year
        # For now, example with known circuit
        if circuit and session_type:
            session_data = self.fastf1_fetcher.fetch_session_data(year, circuit, session_type)
            # TODO: Insert session data into database
        else:
            self.logger.info("Circuit and session type required for FastF1 fetch")
        
        self.logger.info("FastF1 data fetch completed")
    
    def fetch_all_data(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ):
        """
        Fetch data from all enabled sources.
        
        Args:
            start_year: Start year
            end_year: End year
        """
        self.logger.info("Fetching data from all sources...")
        
        # Fetch historical data
        if self.config['fetching']['sources']['ergast']:
            self.fetch_ergast_data(start_year, end_year)
        
        # Fetch modern telemetry (2018+)
        if self.config['fetching']['sources']['openf1']:
            if not end_year or end_year >= 2018:
                fetch_year = end_year or 2023
                self.fetch_openf1_data(fetch_year)
        
        # Fetch FastF1 data (2018+)
        if self.config['fetching']['sources']['fastf1']:
            if not end_year or end_year >= 2018:
                fetch_year = end_year or 2023
                self.fetch_fastf1_data(fetch_year)
        
        self.logger.info("All data fetch completed")
    
    def validate_data(self):
        """Validate dataset and generate quality report."""
        self.logger.info("Validating dataset...")
        
        report = self.validator.generate_quality_report()
        
        # Print summary (will be enhanced by UI if available)
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box
            
            console = Console()
            table = Table(title="Data Quality Report", box=box.ROUNDED, show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")
            
            summary = report['summary']
            table.add_row("Foreign Key Errors", str(summary.get('foreign_key_errors', 0)))
            table.add_row("Anomalies", str(summary.get('anomalies', 0)))
            table.add_row("Tables with Data", str(summary.get('tables_with_data', 0)))
            table.add_row("Races without Results", str(summary.get('races_without_results', 0)))
            table.add_row("Races without Lap Times", str(summary.get('races_without_lap_times', 0)))
            
            console.print("\n")
            console.print(table)
            console.print("\n")
        except ImportError:
            # Fallback to plain text
            print("\n=== Data Quality Report ===")
            print(f"Foreign Key Errors: {report['summary']['foreign_key_errors']}")
            print(f"Anomalies: {report['summary']['anomalies']}")
            print(f"Tables with Data: {report['summary']['tables_with_data']}")
            print(f"Races without Results: {report['summary']['races_without_results']}")
            print(f"Races without Lap Times: {report['summary']['races_without_lap_times']}")
        
        return report
    
    def export_csv(self, output_dir: Optional[str] = None):
        """Export dataset to CSV files."""
        self.logger.info("Exporting to CSV...")
        
        exporter = CSVExporter(
            db_path=self.db_path,
            output_dir=output_dir or self.config['export']['csv']['output_dir']
        )
        
        files = exporter.export()
        self.logger.info(f"Exported {len(files)} files to CSV")
        return files
    
    def export_parquet(
        self,
        output_dir: Optional[str] = None,
        partition_by: Optional[str] = None,
        compression: Optional[str] = None
    ):
        """Export dataset to Parquet files."""
        self.logger.info("Exporting to Parquet...")
        
        exporter = ParquetExporter(
            db_path=self.db_path,
            output_dir=output_dir or self.config['export']['parquet']['output_dir'],
            partition_by=partition_by or self.config['export']['parquet']['partition_by'],
            compression=compression or self.config['export']['parquet']['compression']
        )
        
        files = exporter.export()
        self.logger.info(f"Exported {len(files)} files to Parquet")
        return files


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='F1 Historical Dataset Builder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --interactive          # Launch interactive UI
  python main.py --fetch-openf1 --year 2023
  python main.py --validate
  python main.py --export-csv
        """
    )
    
    # Interactive mode
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Launch interactive UI (recommended)')
    
    # Data fetching options
    parser.add_argument('--fetch-all', action='store_true', help='Fetch data from all sources')
    parser.add_argument('--fetch-ergast', action='store_true', help='Fetch data from Ergast API')
    parser.add_argument('--fetch-openf1', action='store_true', help='Fetch data from OpenF1 API')
    parser.add_argument('--fetch-fastf1', action='store_true', help='Fetch data using FastF1')
    
    # Year range
    parser.add_argument('--start-year', type=int, help='Start year for data fetching')
    parser.add_argument('--end-year', type=int, help='End year for data fetching')
    parser.add_argument('--year', type=int, help='Single year for data fetching')
    
    # Other options
    parser.add_argument('--incremental', action='store_true', help='Incremental update (only new data)')
    parser.add_argument('--validate', action='store_true', help='Validate dataset')
    parser.add_argument('--export-csv', action='store_true', help='Export to CSV')
    parser.add_argument('--export-parquet', action='store_true', help='Export to Parquet')
    parser.add_argument('--config', type=str, default='config/config.yaml', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Launch interactive mode if requested or no args
    if args.interactive or not any([
        args.fetch_all, args.fetch_ergast, args.fetch_openf1, args.fetch_fastf1,
        args.validate, args.export_csv, args.export_parquet
    ]):
        try:
            from main_interactive import main as interactive_main
            interactive_main()
            return
        except ImportError:
            logger.warning("Interactive UI not available. Install 'rich' package: pip install rich")
            if not any([args.fetch_all, args.fetch_ergast, args.fetch_openf1, args.fetch_fastf1,
                       args.validate, args.export_csv, args.export_parquet]):
                parser.print_help()
                return
    
    # Initialize builder
    builder = F1DatasetBuilder(config_path=args.config)
    
    # Determine year range
    start_year = args.start_year
    end_year = args.end_year or args.year
    if args.year:
        start_year = args.year
        end_year = args.year
    
    # Execute requested operations
    if args.fetch_all:
        builder.fetch_all_data(start_year, end_year)
    elif args.fetch_ergast:
        builder.fetch_ergast_data(start_year, end_year)
    elif args.fetch_openf1:
        builder.fetch_openf1_data(end_year or args.year)
    elif args.fetch_fastf1:
        builder.fetch_fastf1_data(end_year or args.year)
    
    if args.validate:
        builder.validate_data()
    
    if args.export_csv:
        builder.export_csv()
    
    if args.export_parquet:
        builder.export_parquet()


if __name__ == '__main__':
    main()

