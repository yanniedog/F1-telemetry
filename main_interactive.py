"""
F1 Historical Dataset - Interactive UI
Beautiful, engaging user interface for the F1 dataset builder.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich import box

from ui.cli_ui import CLIInterface
from main import F1DatasetBuilder

console = Console()


def main():
    """Main interactive entry point."""
    ui = CLIInterface()
    builder = None
    
    try:
        # Initialize builder
        ui.show_status("Initializing F1 Dataset Builder...", "working")
        builder = F1DatasetBuilder()
        ui.show_success("F1 Dataset Builder initialized successfully!")
        
        # Main loop
        while True:
            choice = ui.show_menu()
            
            if choice == "1":  # Fetch Data
                fetch_options = ui.show_fetch_menu()
                if fetch_options:
                    ui.show_status("Starting data fetch...", "working")
                    
                    with ui.show_progress("Fetching data") as progress:
                        task = progress.add_task("[cyan]Fetching...", total=100)
                        
                        results = {}
                        if "ergast" in fetch_options.get("sources", []):
                            ui.show_status("Fetching from Ergast API...", "working")
                            try:
                                builder.fetch_ergast_data(
                                    fetch_options.get("start_year"),
                                    fetch_options.get("end_year") or fetch_options.get("year")
                                )
                                results["Ergast"] = {"success": True, "records": 0}
                                ui.show_success("Ergast data fetched successfully!")
                            except Exception as e:
                                ui.show_error(f"Ergast fetch failed: {e}")
                                results["Ergast"] = {"success": False, "records": 0}
                            progress.update(task, advance=33)
                        
                        if "openf1" in fetch_options.get("sources", []):
                            ui.show_status("Fetching from OpenF1 API...", "working")
                            try:
                                builder.fetch_openf1_data(fetch_options.get("year"))
                                results["OpenF1"] = {"success": True, "records": 0}
                                ui.show_success("OpenF1 data fetched successfully!")
                            except Exception as e:
                                ui.show_error(f"OpenF1 fetch failed: {e}")
                                results["OpenF1"] = {"success": False, "records": 0}
                            progress.update(task, advance=33)
                        
                        if "fastf1" in fetch_options.get("sources", []):
                            ui.show_status("Fetching from FastF1...", "working")
                            try:
                                builder.fetch_fastf1_data(fetch_options.get("year"))
                                results["FastF1"] = {"success": True, "records": 0}
                                ui.show_success("FastF1 data fetched successfully!")
                            except Exception as e:
                                ui.show_error(f"FastF1 fetch failed: {e}")
                                results["FastF1"] = {"success": False, "records": 0}
                            progress.update(task, advance=34)
                    
                    ui.show_completion_summary(results)
                    ui.pause()
            
            elif choice == "2":  # Validate
                ui.show_status("Validating dataset...", "working")
                try:
                    report = builder.validate_data()
                    ui.show_validation_results(report)
                    ui.pause()
                except Exception as e:
                    ui.show_error(f"Validation failed: {e}")
                    ui.pause()
            
            elif choice == "3":  # Statistics
                ui.show_status("Loading statistics...", "working")
                try:
                    # Get basic stats from database
                    import sqlite3
                    conn = sqlite3.connect(builder.db_path)
                    cursor = conn.cursor()
                    
                    stats = {}
                    
                    # Count records in each table
                    tables = ['seasons', 'races', 'drivers', 'constructors', 'circuits', 
                             'race_results', 'lap_times', 'sessions']
                    
                    for table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            stats[table] = count
                        except:
                            stats[table] = 0
                    
                    conn.close()
                    
                    ui.show_statistics(stats)
                    ui.pause()
                except Exception as e:
                    ui.show_error(f"Failed to load statistics: {e}")
                    ui.pause()
            
            elif choice == "4":  # Export
                export_options = ui.show_export_menu()
                if export_options:
                    ui.show_status("Exporting data...", "working")
                    
                    try:
                        if export_options["format"] in ["csv", "both"]:
                            ui.show_status("Exporting to CSV...", "working")
                            files = builder.export_csv(export_options.get("output_dir"))
                            ui.show_success(f"Exported {len(files)} files to CSV!")
                        
                        if export_options["format"] in ["parquet", "both"]:
                            ui.show_status("Exporting to Parquet...", "working")
                            files = builder.export_parquet(export_options.get("output_dir"))
                            ui.show_success(f"Exported {len(files)} files to Parquet!")
                        
                        ui.pause()
                    except Exception as e:
                        ui.show_error(f"Export failed: {e}")
                        ui.pause()
            
            elif choice == "5":  # Configuration
                ui.show_info("Configuration options:")
                ui.show_table(
                    "Current Configuration",
                    [
                        {"Setting": "Database", "Value": builder.db_path},
                        {"Setting": "Cache Enabled", "Value": str(builder.config['cache']['enabled'])},
                        {"Setting": "Log Level", "Value": builder.config['logging']['log_level']},
                    ],
                    ["Setting", "Value"]
                )
                ui.pause()
            
            elif choice == "6":  # Documentation
                ui.show_info("Documentation available:")
                docs = [
                    {"Document": "README.md", "Description": "Project overview"},
                    {"Document": "docs/setup_guide.md", "Description": "Setup instructions"},
                    {"Document": "docs/api_examples.md", "Description": "API usage examples"},
                    {"Document": "docs/best_practices.md", "Description": "Best practices"},
                    {"Document": "docs/data_availability_matrix.md", "Description": "Data availability"},
                ]
                ui.show_table("Documentation", docs, ["Document", "Description"])
                ui.pause()
            
            elif choice == "7":  # Exit
                ui.show_success("Thank you for using F1 Historical Dataset Builder!")
                console.print("\n[bold bright_blue]🏎️ Goodbye! 🏎️[/bold bright_blue]\n")
                break
            
    except KeyboardInterrupt:
        ui.show_warning("\nOperation cancelled by user.")
        console.print("\n[bold bright_blue]🏎️ Goodbye! 🏎️[/bold bright_blue]\n")
        sys.exit(0)
    except Exception as e:
        ui.show_error(f"An error occurred: {e}")
        console.print_exception()
        sys.exit(1)


if __name__ == '__main__':
    main()

