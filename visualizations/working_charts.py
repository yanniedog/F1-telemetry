"""
Working F1 Visualizations using available data.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("darkgrid")
plt.style.use('dark_background')

class F1WorkingVisualizer:
    """Creates visualizations using available data."""
    
    def __init__(self, db_path: str = "data/f1_dataset.db", output_dir: str = "visualizations/output"):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        
    def _get_dataframe(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """Execute query and return DataFrame."""
        return pd.read_sql_query(query, self.conn, params=params)
    
    def plot_driver_participation(self, save: bool = True):
        """Plot driver participation across sessions."""
        query = """
            SELECT 
                d.full_name,
                d.number,
                COUNT(DISTINCT tp.session_id) as sessions,
                COUNT(tp.position_id) as position_records
            FROM drivers d
            INNER JOIN telemetry_position tp ON d.driver_id = tp.driver_id
            GROUP BY d.driver_id, d.full_name, d.number
            ORDER BY sessions DESC, position_records DESC
        """
        df = self._get_dataframe(query)
        
        if df.empty:
            print("No position data available")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # Sessions participated
        top_drivers = df.nlargest(15, 'sessions')
        ax1.barh(range(len(top_drivers)), top_drivers['sessions'], 
                color=plt.cm.viridis(np.linspace(0, 1, len(top_drivers))))
        ax1.set_yticks(range(len(top_drivers)))
        ax1.set_yticklabels(top_drivers['full_name'], fontsize=10)
        ax1.set_xlabel('Sessions Participated', fontweight='bold', color='white', fontsize=12)
        ax1.set_title('Driver Participation - Sessions', fontweight='bold', color='white', fontsize=14)
        ax1.set_facecolor('#0a0a0a')
        ax1.invert_yaxis()
        
        # Position records
        top_records = df.nlargest(15, 'position_records')
        ax2.barh(range(len(top_records)), top_records['position_records'], 
                color=plt.cm.plasma(np.linspace(0, 1, len(top_records))))
        ax2.set_yticks(range(len(top_records)))
        ax2.set_yticklabels(top_records['full_name'], fontsize=10)
        ax2.set_xlabel('Position Records', fontweight='bold', color='white', fontsize=12)
        ax2.set_title('Driver Participation - Position Records', fontweight='bold', color='white', fontsize=14)
        ax2.set_facecolor('#0a0a0a')
        ax2.invert_yaxis()
        
        fig.suptitle('F1 Driver Participation Analysis', fontsize=18, fontweight='bold', color='white', y=0.98)
        fig.patch.set_facecolor('#0a0a0a')
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / "driver_participation.png", dpi=300, facecolor='#0a0a0a', bbox_inches='tight')
            print(f"[OK] Saved: driver_participation.png")
        
        plt.show()
    
    def plot_position_timeline(self, session_id: int, save: bool = True):
        """Plot position timeline for a session."""
        query = """
            SELECT 
                d.full_name,
                tp.time,
                tp.timestamp
            FROM telemetry_position tp
            JOIN drivers d ON tp.driver_id = d.driver_id
            WHERE tp.session_id = ?
            ORDER BY tp.time
            LIMIT 1000
        """
        df = self._get_dataframe(query, params=(session_id,))
        
        if df.empty:
            print(f"No position data for session {session_id}")
            return
        
        # Convert timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        
        if df.empty:
            print(f"No valid timestamp data for session {session_id}")
            return
        
        # Get unique drivers (limit to top 10 for readability)
        drivers = df['full_name'].unique()[:10]
        df_filtered = df[df['full_name'].isin(drivers)]
        
        fig, ax = plt.subplots(figsize=(16, 10))
        
        colors = plt.cm.tab20(range(len(drivers)))
        for i, driver in enumerate(drivers):
            driver_data = df_filtered[df_filtered['full_name'] == driver]
            ax.plot(driver_data['timestamp'], range(len(driver_data)), 
                   label=driver, color=colors[i], linewidth=2, alpha=0.8)
        
        ax.set_xlabel('Time', fontweight='bold', color='white', fontsize=12)
        ax.set_ylabel('Record Index', fontweight='bold', color='white', fontsize=12)
        ax.set_title(f'Position Timeline - Session {session_id}', 
                    fontsize=16, fontweight='bold', color='white', pad=20)
        ax.legend(loc='best', framealpha=0.9, fontsize=9)
        ax.set_facecolor('#0a0a0a')
        fig.patch.set_facecolor('#0a0a0a')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / f"position_timeline_session_{session_id}.png", 
                       dpi=300, facecolor='#0a0a0a', bbox_inches='tight')
            print(f"[OK] Saved: position_timeline_session_{session_id}.png")
        
        plt.show()
    
    def plot_session_summary(self, save: bool = True):
        """Plot summary of all sessions."""
        query = """
            SELECT 
                s.session_id,
                s.session_type,
                c.name as circuit,
                se.year,
                COUNT(DISTINCT tp.driver_id) as drivers,
                COUNT(tp.position_id) as position_records
            FROM sessions s
            JOIN races r ON s.race_id = r.race_id
            JOIN circuits c ON r.circuit_id = c.circuit_id
            JOIN seasons se ON r.season_id = se.season_id
            LEFT JOIN telemetry_position tp ON s.session_id = tp.session_id
            GROUP BY s.session_id, s.session_type, c.name, se.year
            ORDER BY se.year, s.session_id
        """
        df = self._get_dataframe(query)
        
        if df.empty:
            print("No session data available")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
        
        # Drivers per session
        ax1.bar(range(len(df)), df['drivers'], color=plt.cm.tab20(range(len(df))))
        ax1.set_xlabel('Session', fontweight='bold', color='white', fontsize=12)
        ax1.set_ylabel('Number of Drivers', fontweight='bold', color='white', fontsize=12)
        ax1.set_title('Drivers per Session', fontweight='bold', color='white', fontsize=14)
        ax1.set_facecolor('#0a0a0a')
        ax1.set_xticks(range(len(df)))
        ax1.set_xticklabels([f"{row['circuit']}\n{row['year']}" for _, row in df.iterrows()], 
                           rotation=45, ha='right', fontsize=8)
        
        # Position records per session
        ax2.bar(range(len(df)), df['position_records'], color=plt.cm.plasma(range(len(df))))
        ax2.set_xlabel('Session', fontweight='bold', color='white', fontsize=12)
        ax2.set_ylabel('Position Records', fontweight='bold', color='white', fontsize=12)
        ax2.set_title('Position Records per Session', fontweight='bold', color='white', fontsize=14)
        ax2.set_facecolor('#0a0a0a')
        ax2.set_xticks(range(len(df)))
        ax2.set_xticklabels([f"{row['circuit']}\n{row['year']}" for _, row in df.iterrows()], 
                           rotation=45, ha='right', fontsize=8)
        
        fig.suptitle('F1 Session Summary', fontsize=18, fontweight='bold', color='white', y=0.98)
        fig.patch.set_facecolor('#0a0a0a')
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / "session_summary.png", dpi=300, facecolor='#0a0a0a', bbox_inches='tight')
            print(f"[OK] Saved: session_summary.png")
        
        plt.show()
    
    def generate_all(self):
        """Generate all available visualizations."""
        print("[INFO] Generating visualizations from available data...\n")
        
        print("1. Driver participation...")
        self.plot_driver_participation()
        
        print("\n2. Session summary...")
        self.plot_session_summary()
        
        # Get first session for position timeline
        query = "SELECT session_id FROM sessions LIMIT 1"
        result = self._get_dataframe(query)
        if not result.empty:
            session_id = result['session_id'].iloc[0]
            print(f"\n3. Position timeline for session {session_id}...")
            self.plot_position_timeline(session_id)
        
        print("\n[OK] All visualizations generated!")

if __name__ == '__main__':
    import numpy as np
    visualizer = F1WorkingVisualizer()
    visualizer.generate_all()

