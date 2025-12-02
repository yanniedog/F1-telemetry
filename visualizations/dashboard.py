"""
Stunning F1 Data Visualizations
Creates beautiful, interactive visualizations of F1 racing data.
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import cm
import seaborn as sns
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

# Try to import plotly for interactive charts
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Set style
sns.set_style("darkgrid")
plt.style.use('dark_background')
F1_COLORS = {
    'red': '#E10600',
    'blue': '#1E41FF',
    'yellow': '#FFD700',
    'green': '#00D2BE',
    'orange': '#FF8700',
    'purple': '#6C00FF',
    'pink': '#FF1493',
    'cyan': '#00FFFF'
}

class F1Visualizer:
    """Creates stunning F1 data visualizations."""
    
    def __init__(self, db_path: str = "data/f1_dataset.db", output_dir: str = "visualizations/output"):
        """
        Initialize F1 visualizer.
        
        Args:
            db_path: Path to SQLite database
            output_dir: Directory to save visualizations
        """
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        
    def _get_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """Execute query and return DataFrame."""
        return pd.read_sql_query(query, self.conn, params=params)
    
    def plot_lap_times_comparison(self, session_id: Optional[int] = None, top_n: int = 10, save: bool = True):
        """
        Create stunning lap times comparison chart.
        
        Args:
            session_id: Specific session ID (None = all sessions)
            top_n: Number of top drivers to show
            save: Whether to save the plot
        """
        if session_id:
            query = """
                SELECT d.full_name, d.number, lt.lap, lt.time, lt.milliseconds, s.session_type, c.name as circuit
                FROM lap_times lt
                JOIN drivers d ON lt.driver_id = d.driver_id
                JOIN races r ON lt.race_id = r.race_id
                JOIN sessions s ON r.race_id = s.race_id
                JOIN circuits c ON r.circuit_id = c.circuit_id
                WHERE s.session_id = ?
                ORDER BY lt.lap, lt.milliseconds
            """
            df = self._get_dataframe(query, params=(session_id,))
            title_suffix = f" - {df['circuit'].iloc[0] if len(df) > 0 else ''}"
        else:
            query = """
                SELECT d.full_name, d.number, lt.lap, lt.time, lt.milliseconds, s.session_type, c.name as circuit
                FROM lap_times lt
                JOIN drivers d ON lt.driver_id = d.driver_id
                JOIN races r ON lt.race_id = r.race_id
                JOIN sessions s ON r.race_id = s.race_id
                JOIN circuits c ON r.circuit_id = c.circuit_id
                ORDER BY lt.lap, lt.milliseconds
            """
            df = self._get_dataframe(query, params=None)
            title_suffix = " - All Sessions"
        
        if df.empty:
            print("No lap time data available")
            return
        
        # Ensure milliseconds is numeric
        df['milliseconds'] = pd.to_numeric(df['milliseconds'], errors='coerce')
        df = df.dropna(subset=['milliseconds'])
        
        # Get top N drivers by average lap time
        driver_stats = df.groupby('full_name').agg({
            'milliseconds': 'mean'
        }).sort_values('milliseconds').head(top_n)
        
        top_drivers = driver_stats.index.tolist()
        df_filtered = df[df['full_name'].isin(top_drivers)]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Color map for drivers
        colors = plt.cm.tab20(np.linspace(0, 1, len(top_drivers)))
        driver_colors = {driver: colors[i] for i, driver in enumerate(top_drivers)}
        
        # Plot each driver's lap times
        for driver in top_drivers:
            driver_data = df_filtered[df_filtered['full_name'] == driver]
            ax.plot(driver_data['lap'], driver_data['milliseconds'] / 1000, 
                   label=driver, color=driver_colors[driver], linewidth=2, alpha=0.8)
        
        ax.set_xlabel('Lap Number', fontsize=14, fontweight='bold', color='white')
        ax.set_ylabel('Lap Time (seconds)', fontsize=14, fontweight='bold', color='white')
        ax.set_title(f'🏎️ Lap Times Comparison{title_suffix}', fontsize=18, fontweight='bold', color='white', pad=20)
        ax.legend(loc='upper left', framealpha=0.9, fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_facecolor('#0a0a0a')
        fig.patch.set_facecolor('#0a0a0a')
        
        plt.tight_layout()
        
        if save:
            filename = f"lap_times_comparison_{session_id or 'all'}.png"
            plt.savefig(self.output_dir / filename, dpi=300, facecolor='#0a0a0a', bbox_inches='tight')
            print(f"✅ Saved: {filename}")
        
        plt.show()
    
    def plot_driver_performance_heatmap(self, save: bool = True):
        """Create heatmap showing driver performance across sessions."""
        query = """
            SELECT d.full_name, c.name as circuit, AVG(lt.milliseconds) as avg_lap_time
            FROM lap_times lt
            JOIN drivers d ON lt.driver_id = d.driver_id
            JOIN races r ON lt.race_id = r.race_id
            JOIN circuits c ON r.circuit_id = c.circuit_id
            GROUP BY d.full_name, c.name
        """
        df = self._get_dataframe(query)
        
        if df.empty:
            print("No data available for heatmap")
            return
        
        # Pivot for heatmap
        heatmap_data = df.pivot(index='full_name', columns='circuit', values='avg_lap_time')
        
        # Create figure
        fig, ax = plt.subplots(figsize=(20, 12))
        
        # Create heatmap
        sns.heatmap(heatmap_data / 1000, annot=True, fmt='.2f', cmap='RdYlGn_r', 
                   cbar_kws={'label': 'Average Lap Time (seconds)'}, 
                   linewidths=0.5, linecolor='gray', ax=ax)
        
        ax.set_title('🔥 Driver Performance Heatmap - Average Lap Times by Circuit', 
                    fontsize=20, fontweight='bold', color='white', pad=20)
        ax.set_xlabel('Circuit', fontsize=14, fontweight='bold', color='white')
        ax.set_ylabel('Driver', fontsize=14, fontweight='bold', color='white')
        
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / "driver_performance_heatmap.png", dpi=300, 
                       facecolor='#0a0a0a', bbox_inches='tight')
            print("✅ Saved: driver_performance_heatmap.png")
        
        plt.show()
    
    def plot_position_changes(self, session_id: int, save: bool = True):
        """Create stunning position change chart during race."""
        query = """
            SELECT d.full_name, tp.timestamp, tp.position
            FROM telemetry_position tp
            JOIN drivers d ON tp.driver_id = d.driver_id
            WHERE tp.session_id = ?
            ORDER BY tp.timestamp
        """
        df = self._get_dataframe(query, params=(session_id,))
        
        if df.empty:
            print("No position data available")
            return
        
        # Convert timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Create figure
        fig, ax = plt.subplots(figsize=(18, 10))
        
        # Get unique drivers
        drivers = df['full_name'].unique()
        colors = plt.cm.tab20(np.linspace(0, 1, len(drivers)))
        
        # Plot position for each driver
        for i, driver in enumerate(drivers):
            driver_data = df[df['full_name'] == driver]
            ax.plot(driver_data['timestamp'], driver_data['position'], 
                   label=driver, color=colors[i], linewidth=2.5, alpha=0.9, marker='o', markersize=3)
        
        ax.set_xlabel('Time', fontsize=14, fontweight='bold', color='white')
        ax.set_ylabel('Position', fontsize=14, fontweight='bold', color='white')
        ax.set_title('📊 Race Position Changes Over Time', fontsize=18, fontweight='bold', color='white', pad=20)
        ax.invert_yaxis()  # Position 1 at top
        ax.legend(loc='upper right', framealpha=0.9, fontsize=9, ncol=2)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_facecolor('#0a0a0a')
        fig.patch.set_facecolor('#0a0a0a')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / f"position_changes_session_{session_id}.png", 
                       dpi=300, facecolor='#0a0a0a', bbox_inches='tight')
            print(f"✅ Saved: position_changes_session_{session_id}.png")
        
        plt.show()
    
    def plot_driver_statistics_dashboard(self, save: bool = True):
        """Create comprehensive driver statistics dashboard."""
        # Get driver statistics - calculate milliseconds from time string if needed
        query = """
            SELECT 
                d.full_name,
                d.number,
                COUNT(DISTINCT lt.race_id) as races,
                COUNT(lt.lap_time_id) as total_laps,
                CASE 
                    WHEN lt.milliseconds IS NOT NULL AND lt.milliseconds > 0 
                    THEN AVG(CAST(lt.milliseconds AS REAL))
                    ELSE NULL
                END as avg_lap_time,
                CASE 
                    WHEN lt.milliseconds IS NOT NULL AND lt.milliseconds > 0 
                    THEN MIN(CAST(lt.milliseconds AS REAL))
                    ELSE NULL
                END as best_lap_time,
                COUNT(DISTINCT CASE WHEN lt.position = 1 THEN lt.lap END) as laps_led
            FROM drivers d
            INNER JOIN lap_times lt ON d.driver_id = lt.driver_id
            WHERE (lt.milliseconds IS NOT NULL AND lt.milliseconds > 0) OR lt.time IS NOT NULL
            GROUP BY d.driver_id, d.full_name, d.number
            HAVING COUNT(lt.lap_time_id) > 0
        """
        df = self._get_dataframe(query)
        
        if df.empty:
            print("No driver statistics available")
            return
        
        # Ensure numeric types - must happen before any operations
        df['avg_lap_time'] = pd.to_numeric(df['avg_lap_time'], errors='coerce')
        df['best_lap_time'] = pd.to_numeric(df['best_lap_time'], errors='coerce')
        df['total_laps'] = pd.to_numeric(df['total_laps'], errors='coerce')
        df['races'] = pd.to_numeric(df['races'], errors='coerce')
        
        # Remove rows with invalid data
        df = df.dropna(subset=['avg_lap_time'])
        
        if df.empty:
            print("No valid driver statistics available")
            return
        
        # Create subplots
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Average Lap Time Bar Chart
        ax1 = fig.add_subplot(gs[0, 0])
        top_10 = df.nsmallest(10, 'avg_lap_time')
        bars = ax1.barh(range(len(top_10)), top_10['avg_lap_time'] / 1000, 
                       color=plt.cm.viridis(np.linspace(0, 1, len(top_10))))
        ax1.set_yticks(range(len(top_10)))
        ax1.set_yticklabels(top_10['full_name'], fontsize=9)
        ax1.set_xlabel('Average Lap Time (s)', fontweight='bold', color='white')
        ax1.set_title('🏆 Top 10 - Average Lap Time', fontweight='bold', color='white')
        ax1.set_facecolor('#0a0a0a')
        ax1.invert_yaxis()
        
        # 2. Total Laps
        ax2 = fig.add_subplot(gs[0, 1])
        top_laps = df.nlargest(10, 'total_laps')
        ax2.barh(range(len(top_laps)), top_laps['total_laps'], 
                color=plt.cm.plasma(np.linspace(0, 1, len(top_laps))))
        ax2.set_yticks(range(len(top_laps)))
        ax2.set_yticklabels(top_laps['full_name'], fontsize=9)
        ax2.set_xlabel('Total Laps', fontweight='bold', color='white')
        ax2.set_title('📊 Top 10 - Total Laps', fontweight='bold', color='white')
        ax2.set_facecolor('#0a0a0a')
        ax2.invert_yaxis()
        
        # 3. Best Lap Times
        ax3 = fig.add_subplot(gs[0, 2])
        best_laps = df.nsmallest(10, 'best_lap_time')
        ax3.barh(range(len(best_laps)), best_laps['best_lap_time'] / 1000,
                color=plt.cm.coolwarm(np.linspace(0, 1, len(best_laps))))
        ax3.set_yticks(range(len(best_laps)))
        ax3.set_yticklabels(best_laps['full_name'], fontsize=9)
        ax3.set_xlabel('Best Lap Time (s)', fontweight='bold', color='white')
        ax3.set_title('⚡ Top 10 - Best Lap Time', fontweight='bold', color='white')
        ax3.set_facecolor('#0a0a0a')
        ax3.invert_yaxis()
        
        # 4. Scatter: Avg Lap Time vs Total Laps
        ax4 = fig.add_subplot(gs[1, :2])
        scatter = ax4.scatter(df['total_laps'], df['avg_lap_time'] / 1000, 
                             s=200, alpha=0.6, c=df['races'], cmap='viridis', edgecolors='white', linewidth=1)
        ax4.set_xlabel('Total Laps', fontweight='bold', color='white', fontsize=12)
        ax4.set_ylabel('Average Lap Time (s)', fontweight='bold', color='white', fontsize=12)
        ax4.set_title('📈 Performance Overview: Lap Time vs Total Laps', fontweight='bold', color='white', fontsize=14)
        ax4.set_facecolor('#0a0a0a')
        cbar = plt.colorbar(scatter, ax=ax4)
        cbar.set_label('Races', fontweight='bold', color='white')
        
        # 5. Races Participated
        ax5 = fig.add_subplot(gs[1, 2])
        race_counts = df['races'].value_counts().sort_index()
        ax5.bar(race_counts.index, race_counts.values, color=plt.cm.Set3(range(len(race_counts))))
        ax5.set_xlabel('Number of Races', fontweight='bold', color='white')
        ax5.set_ylabel('Number of Drivers', fontweight='bold', color='white')
        ax5.set_title('🏁 Race Participation', fontweight='bold', color='white')
        ax5.set_facecolor('#0a0a0a')
        
        # 6. Driver Leaderboard Table
        ax6 = fig.add_subplot(gs[2, :])
        ax6.axis('tight')
        ax6.axis('off')
        
        # Prepare table data
        table_data = df[['full_name', 'number', 'races', 'total_laps', 
                         'avg_lap_time', 'best_lap_time']].head(15).copy()
        table_data['avg_lap_time'] = (table_data['avg_lap_time'] / 1000).round(3)
        table_data['best_lap_time'] = (table_data['best_lap_time'] / 1000).round(3)
        table_data.columns = ['Driver', '#', 'Races', 'Laps', 'Avg Time (s)', 'Best Time (s)']
        
        table = ax6.table(cellText=table_data.values, colLabels=table_data.columns,
                         cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style table
        for i in range(len(table_data.columns)):
            table[(0, i)].set_facecolor('#E10600')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(1, len(table_data) + 1):
            for j in range(len(table_data.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#1a1a1a')
                else:
                    table[(i, j)].set_facecolor('#2a2a2a')
                table[(i, j)].set_text_props(color='white')
        
        fig.suptitle('🏎️ F1 Driver Statistics Dashboard', fontsize=24, fontweight='bold', 
                    color='white', y=0.98)
        fig.patch.set_facecolor('#0a0a0a')
        
        if save:
            plt.savefig(self.output_dir / "driver_statistics_dashboard.png", 
                       dpi=300, facecolor='#0a0a0a', bbox_inches='tight')
            print("✅ Saved: driver_statistics_dashboard.png")
        
        plt.show()
    
    def plot_interactive_race_timeline(self, session_id: int, save_html: bool = True):
        """Create interactive race timeline with Plotly."""
        if not PLOTLY_AVAILABLE:
            print("Plotly not available. Install with: pip install plotly")
            return
        
        query = """
            SELECT d.full_name, tp.timestamp, tp.position
            FROM telemetry_position tp
            JOIN drivers d ON tp.driver_id = d.driver_id
            WHERE tp.session_id = ?
            ORDER BY tp.timestamp
        """
        df = self._get_dataframe(query, params=(session_id,))
        
        if df.empty:
            print("No position data available")
            return
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig = go.Figure()
        
        drivers = df['full_name'].unique()
        colors = px.colors.qualitative.Set3
        
        for i, driver in enumerate(drivers):
            driver_data = df[df['full_name'] == driver]
            fig.add_trace(go.Scatter(
                x=driver_data['timestamp'],
                y=driver_data['position'],
                mode='lines+markers',
                name=driver,
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=4),
                hovertemplate=f'<b>{driver}</b><br>Position: %{{y}}<br>Time: %{{x}}<extra></extra>'
            ))
        
        fig.update_layout(
            title={
                'text': '🏎️ Interactive Race Position Timeline',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24, 'color': 'white'}
            },
            xaxis_title='Time',
            yaxis_title='Position',
            yaxis=dict(autorange='reversed'),
            template='plotly_dark',
            height=800,
            hovermode='closest',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        if save_html:
            filename = f"interactive_race_timeline_{session_id}.html"
            fig.write_html(str(self.output_dir / filename))
            print(f"✅ Saved: {filename}")
        
        fig.show()
    
    def generate_all_visualizations(self):
        """Generate all available visualizations."""
        print("🎨 Generating all F1 visualizations...\n")
        
        # Get session IDs
        query = "SELECT session_id FROM sessions LIMIT 5"
        sessions = self._get_dataframe(query)
        
        # 1. Driver Statistics Dashboard
        print("1. Creating driver statistics dashboard...")
        self.plot_driver_statistics_dashboard()
        
        # 2. Performance Heatmap
        print("\n2. Creating performance heatmap...")
        self.plot_driver_performance_heatmap()
        
        # 3. Lap Times Comparison (all sessions)
        print("\n3. Creating lap times comparison...")
        self.plot_lap_times_comparison()
        
        # 4. Position changes for first few sessions
        if not sessions.empty:
            print("\n4. Creating position change charts...")
            for session_id in sessions['session_id'].head(3):
                self.plot_position_changes(session_id)
        
        # 5. Interactive timelines
        if PLOTLY_AVAILABLE and not sessions.empty:
            print("\n5. Creating interactive race timelines...")
            for session_id in sessions['session_id'].head(2):
                self.plot_interactive_race_timeline(session_id)
        
        print("\n✅ All visualizations generated!")

