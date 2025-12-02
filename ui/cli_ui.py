"""
Engaging CLI interface for F1 Historical Dataset.
Uses Rich library for beautiful terminal output.
"""

import sys
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich import box
from rich.live import Live
from rich.align import Align
import time

from utils.logger import get_logger

console = Console()
logger = get_logger()


class CLIInterface:
    """Beautiful CLI interface for F1 dataset operations."""
    
    def __init__(self):
        """Initialize CLI interface."""
        self.console = console
        self.show_banner()
    
    def show_banner(self):
        """Display welcome banner."""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     🏎️  F1 HISTORICAL DATASET BUILDER  🏎️                   ║
║                                                               ║
║     Complete Formula 1 Racing Data (1950 - Present)          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        self.console.print(Panel(
            banner,
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2)
        ))
    
    def show_menu(self) -> str:
        """Display main menu and get user choice."""
        menu_text = """
[bold cyan]Main Menu[/bold cyan]

[bold]1.[/bold] 📥 Fetch Data
[bold]2.[/bold] ✅ Validate Dataset
[bold]3.[/bold] 📊 View Statistics
[bold]4.[/bold] 📤 Export Data
[bold]5.[/bold] ⚙️  Configuration
[bold]6.[/bold] 📚 Documentation
[bold]7.[/bold] 🚪 Exit

"""
        self.console.print(Panel(
            menu_text,
            title="[bold bright_blue]F1 Dataset Manager[/bold bright_blue]",
            border_style="bright_blue",
            box=box.ROUNDED
        ))
        
        choice = Prompt.ask(
            "\n[bold cyan]Select an option[/bold cyan]",
            choices=["1", "2", "3", "4", "5", "6", "7"],
            default="1"
        )
        return choice
    
    def show_fetch_menu(self) -> Dict[str, Any]:
        """Display fetch data menu."""
        self.console.print("\n[bold cyan]📥 Fetch Data[/bold cyan]\n")
        
        sources = []
        if Confirm.ask("[bold]Fetch from Ergast API?[/bold] (Historical data 1950-2024)", default=True):
            sources.append("ergast")
        if Confirm.ask("[bold]Fetch from OpenF1 API?[/bold] (Modern telemetry 2018+)", default=True):
            sources.append("openf1")
        if Confirm.ask("[bold]Fetch from FastF1?[/bold] (Session data 2018+)", default=True):
            sources.append("fastf1")
        
        if not sources:
            self.console.print("[yellow]No sources selected. Returning to main menu.[/yellow]")
            return {}
        
        # Year selection
        year_type = Prompt.ask(
            "\n[bold]Year selection:[/bold]",
            choices=["single", "range", "all"],
            default="single"
        )
        
        start_year = None
        end_year = None
        year = None
        
        if year_type == "single":
            year = int(Prompt.ask("[bold]Enter year[/bold]", default="2023"))
        elif year_type == "range":
            start_year = int(Prompt.ask("[bold]Start year[/bold]", default="2020"))
            end_year = int(Prompt.ask("[bold]End year[/bold]", default="2023"))
        
        return {
            "sources": sources,
            "year": year,
            "start_year": start_year,
            "end_year": end_year
        }
    
    def show_progress(self, task_description: str):
        """Create and return a progress context manager."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        )
    
    def show_status(self, message: str, status: str = "info"):
        """Display status message with icon."""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "working": "🔄"
        }
        colors = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "working": "cyan"
        }
        
        icon = icons.get(status, "•")
        color = colors.get(status, "white")
        
        self.console.print(f"[{color}]{icon} {message}[/{color}]")
    
    def show_table(self, title: str, data: List[Dict], columns: List[str]):
        """Display data in a beautiful table."""
        table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold magenta")
        
        # Add columns
        for col in columns:
            table.add_column(col, style="cyan", no_wrap=False)
        
        # Add rows
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        
        self.console.print(table)
    
    def show_statistics(self, stats: Dict[str, Any]):
        """Display dataset statistics."""
        self.console.print("\n[bold cyan]📊 Dataset Statistics[/bold cyan]\n")
        
        # Create a grid layout
        grid = Table.grid(padding=1, pad_edge=True)
        grid.add_column("Metric", style="bold cyan", justify="left")
        grid.add_column("Value", style="green", justify="right")
        
        for key, value in stats.items():
            grid.add_row(key.replace("_", " ").title(), str(value))
        
        self.console.print(Panel(grid, title="[bold]Statistics[/bold]", border_style="green"))
    
    def show_export_menu(self) -> Dict[str, Any]:
        """Display export menu."""
        self.console.print("\n[bold cyan]📤 Export Data[/bold cyan]\n")
        
        format_choice = Prompt.ask(
            "[bold]Export format:[/bold]",
            choices=["csv", "parquet", "both"],
            default="both"
        )
        
        output_dir = Prompt.ask(
            "[bold]Output directory[/bold]",
            default="exports"
        )
        
        return {
            "format": format_choice,
            "output_dir": output_dir
        }
    
    def show_data_tree(self, data: Dict[str, Any]):
        """Display data structure as a tree."""
        tree = Tree("📁 F1 Dataset")
        
        if "seasons" in data:
            seasons_branch = tree.add("📅 Seasons")
            for season in data["seasons"][:5]:  # Show first 5
                seasons_branch.add(f"Year: {season.get('season', 'N/A')}")
        
        if "races" in data:
            races_branch = tree.add("🏁 Races")
            races_branch.add(f"Total: {len(data['races'])} races")
        
        if "drivers" in data:
            drivers_branch = tree.add("👤 Drivers")
            drivers_branch.add(f"Total: {len(data['drivers'])} drivers")
        
        self.console.print(tree)
    
    def show_validation_results(self, report: Dict[str, Any]):
        """Display validation report."""
        self.console.print("\n[bold cyan]✅ Validation Results[/bold cyan]\n")
        
        summary = report.get("summary", {})
        
        # Create summary table
        summary_table = Table(title="Validation Summary", box=box.ROUNDED)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green", justify="right")
        
        summary_table.add_row("Foreign Key Errors", str(summary.get("foreign_key_errors", 0)))
        summary_table.add_row("Anomalies", str(summary.get("anomalies", 0)))
        summary_table.add_row("Tables with Data", str(summary.get("tables_with_data", 0)))
        summary_table.add_row("Races without Results", str(summary.get("races_without_results", 0)))
        
        self.console.print(summary_table)
        
        # Show errors if any
        fk_errors = report.get("foreign_key_errors", {})
        if fk_errors:
            self.console.print("\n[bold yellow]⚠️ Foreign Key Errors:[/bold yellow]")
            for table, errors in fk_errors.items():
                if errors:
                    self.console.print(f"[red]  {table}: {len(errors)} errors[/red]")
        
        anomalies = report.get("anomalies", [])
        if anomalies:
            self.console.print("\n[bold yellow]⚠️ Anomalies Detected:[/bold yellow]")
            for anomaly in anomalies[:10]:  # Show first 10
                self.console.print(f"[yellow]  {anomaly.get('type', 'Unknown')}: {anomaly.get('message', '')}[/yellow]")
    
    def show_success(self, message: str):
        """Display success message."""
        self.console.print(f"[bold green]✅ {message}[/bold green]")
    
    def show_error(self, message: str):
        """Display error message."""
        self.console.print(f"[bold red]❌ {message}[/bold red]")
    
    def show_warning(self, message: str):
        """Display warning message."""
        self.console.print(f"[bold yellow]⚠️ {message}[/bold yellow]")
    
    def show_info(self, message: str):
        """Display info message."""
        self.console.print(f"[bold blue]ℹ️ {message}[/bold blue]")
    
    def show_fetching_progress(self, source: str, current: int, total: int):
        """Show fetching progress for a source."""
        percentage = (current / total * 100) if total > 0 else 0
        self.console.print(
            f"[cyan]🔄 Fetching from {source}:[/cyan] "
            f"[green]{current}/{total}[/green] "
            f"([yellow]{percentage:.1f}%[/yellow])"
        )
    
    def show_completion_summary(self, results: Dict[str, Any]):
        """Show completion summary after operations."""
        self.console.print("\n[bold green]✅ Operation Complete![/bold green]\n")
        
        summary_table = Table(title="Summary", box=box.ROUNDED)
        summary_table.add_column("Operation", style="cyan")
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Records", style="yellow", justify="right")
        
        for operation, data in results.items():
            status = "✅ Success" if data.get("success", False) else "❌ Failed"
            records = data.get("records", 0)
            summary_table.add_row(operation, status, str(records))
        
        self.console.print(summary_table)
    
    def confirm_action(self, message: str) -> bool:
        """Ask for confirmation."""
        return Confirm.ask(f"[bold yellow]{message}[/bold yellow]")
    
    def get_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Get user input."""
        if default:
            return Prompt.ask(f"[bold cyan]{prompt}[/bold cyan]", default=default)
        return Prompt.ask(f"[bold cyan]{prompt}[/bold cyan]")
    
    def clear_screen(self):
        """Clear the console."""
        self.console.clear()
    
    def pause(self):
        """Pause and wait for user input."""
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")

