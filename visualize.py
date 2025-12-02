"""
F1 Data Visualization Script
Run this to generate stunning visualizations of F1 data.
"""

import argparse
from visualizations.dashboard import F1Visualizer

def main():
    parser = argparse.ArgumentParser(description='Generate F1 data visualizations')
    parser.add_argument('--db', default='data/f1_dataset.db', help='Database path')
    parser.add_argument('--output', default='visualizations/output', help='Output directory')
    parser.add_argument('--all', action='store_true', help='Generate all visualizations')
    parser.add_argument('--dashboard', action='store_true', help='Generate driver statistics dashboard')
    parser.add_argument('--heatmap', action='store_true', help='Generate performance heatmap')
    parser.add_argument('--lap-times', type=int, metavar='SESSION_ID', help='Generate lap times comparison (optional session_id)')
    parser.add_argument('--positions', type=int, metavar='SESSION_ID', help='Generate position changes chart')
    parser.add_argument('--interactive', type=int, metavar='SESSION_ID', help='Generate interactive race timeline')
    
    args = parser.parse_args()
    
    visualizer = F1Visualizer(db_path=args.db, output_dir=args.output)
    
    if args.all:
        visualizer.generate_all_visualizations()
    elif args.dashboard:
        visualizer.plot_driver_statistics_dashboard()
    elif args.heatmap:
        visualizer.plot_driver_performance_heatmap()
    elif args.lap_times is not None:
        visualizer.plot_lap_times_comparison(session_id=args.lap_times if args.lap_times > 0 else None)
    elif args.positions:
        visualizer.plot_position_changes(args.positions)
    elif args.interactive:
        visualizer.plot_interactive_race_timeline(args.interactive)
    else:
        print("No visualization specified. Use --all to generate all, or specify a specific visualization.")
        parser.print_help()

if __name__ == '__main__':
    main()

