"""Quick test of visualizations."""

import sys
sys.path.insert(0, '.')

try:
    from visualizations.dashboard import F1Visualizer
    print("✅ Visualizer imported successfully")
    
    v = F1Visualizer()
    print("✅ Visualizer initialized")
    
    # Test driver statistics dashboard
    print("\n🎨 Generating driver statistics dashboard...")
    v.plot_driver_statistics_dashboard(save=True)
    print("✅ Dashboard generated!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

