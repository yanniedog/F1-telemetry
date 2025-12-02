"""
Interactive dashboard for F1 dataset.
Provides real-time status and statistics.
"""

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich import box
import time
from typing import Dict, Any

console = Console()


class Dashboard:
    """Real-time dashboard for F1 dataset operations."""
    
    def __init__(self):
        """Initialize dashboard."""
        self.console = console
    
    def create_layout(self) -> Layout:
        """Create dashboard layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="stats"),
            Layout(name="progress")
        )
        
        layout["right"].split_column(
            Layout(name="status"),
            Layout(name="logs")
        )
        
        return layout
    
    def update_header(self, layout: Layout):
        """Update header panel."""
        header_text = Text("🏎️ F1 Historical Dataset Builder", style="bold bright_blue", justify="center")
        layout["header"].update(Panel(header_text, box=box.ROUNDED))
    
    def update_stats(self, layout: Layout, stats: Dict[str, Any]):
        """Update statistics panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        for key, value in stats.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        layout["stats"].update(Panel(table, title="📊 Statistics", border_style="green", box=box.ROUNDED))
    
    def update_progress(self, layout: Layout, progress: Dict[str, Any]):
        """Update progress panel."""
        progress_text = ""
        for task, status in progress.items():
            icon = "✅" if status.get("complete", False) else "🔄"
            progress_text += f"{icon} {task}: {status.get('current', 0)}/{status.get('total', 0)}\n"
        
        layout["progress"].update(Panel(progress_text, title="🔄 Progress", border_style="cyan", box=box.ROUNDED))
    
    def update_status(self, layout: Layout, status: str, message: str):
        """Update status panel."""
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
        
        status_text = Text(f"{icon} {message}", style=color)
        layout["status"].update(Panel(status_text, title="Status", border_style=color, box=box.ROUNDED))
    
    def update_logs(self, layout: Layout, logs: list):
        """Update logs panel."""
        log_text = "\n".join(logs[-10:])  # Show last 10 logs
        layout["logs"].update(Panel(log_text, title="📝 Recent Logs", border_style="yellow", box=box.ROUNDED))
    
    def update_footer(self, layout: Layout, message: str):
        """Update footer panel."""
        footer_text = Text(message, style="dim", justify="center")
        layout["footer"].update(Panel(footer_text, box=box.ROUNDED))
    
    def show(self, stats: Dict[str, Any], progress: Dict[str, Any], status: str, message: str, logs: list):
        """Display dashboard."""
        layout = self.create_layout()
        
        self.update_header(layout)
        self.update_stats(layout, stats)
        self.update_progress(layout, progress)
        self.update_status(layout, status, message)
        self.update_logs(layout, logs)
        self.update_footer(layout, "Press Ctrl+C to exit")
        
        return layout

