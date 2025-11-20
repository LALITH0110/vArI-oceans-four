#!/usr/bin/env python3
"""
UI Widget Test - Programmatic verification of widget references and handlers.

Tests:
1. UI initialization without crashes
2. All widgets accessible
3. Handlers can be called programmatically
4. Figure and canvas exist and remain valid
"""

import sys
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

print("="*60)
print("  UI WIDGET TEST - PROGRAMMATIC VERIFICATION")
print("="*60)
print()

# Test 1: UI Initialization
print("[TEST 1] UI Initialization")
print("-" * 60)

try:
    from ui import InteractiveUI

    print("Creating InteractiveUI instance...")
    ui = InteractiveUI(seeds_file='seeds.json')
    print("[OK] UI instance created")

    print("Setting up UI widgets...")
    ui.setup_ui()
    print("[OK] UI setup complete")

    # Verify figure exists
    if ui.fig is None:
        print("[FAIL] FAIL: Figure is None!")
        sys.exit(1)
    print("[OK] Figure exists")

    # Verify canvas exists
    if ui.fig.canvas is None:
        print("[FAIL] FAIL: Canvas is None!")
        sys.exit(1)
    print("[OK] Canvas exists")

    print()
    print("[TEST 1] PASSED - UI Initialization")
    print()

except Exception as e:
    print(f"[FAIL] FAIL: UI initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Widget Accessibility
print("[TEST 2] Widget Accessibility")
print("-" * 60)

try:
    required_widgets = [
        'combobox',
        'textbox',
        'btn_load',
        'btn_play',
        'btn_pause',
        'btn_reset',
        'slider_speed',
        'btn_export_gif',
        'btn_export_mp4'
    ]

    for widget_name in required_widgets:
        if widget_name not in ui.widgets:
            print(f"[FAIL] FAIL: Widget '{widget_name}' not found!")
            sys.exit(1)

        widget = ui.widgets[widget_name]
        if widget is None:
            print(f"[FAIL] FAIL: Widget '{widget_name}' is None!")
            sys.exit(1)

        print(f"[OK] Widget '{widget_name}' accessible")

    print()
    print("[TEST 2] PASSED - Widget Accessibility")
    print()

except Exception as e:
    print(f"[FAIL] FAIL: Widget accessibility test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Handler Calls
print("[TEST 3] Handler Calls (Programmatic)")
print("-" * 60)

try:
    # Test speed slider (should not crash)
    print("Testing speed slider handler...")
    ui.on_speed_change(5)
    if ui.speed != 5:
        print(f"[FAIL] FAIL: Speed not updated (expected 5, got {ui.speed})")
        sys.exit(1)
    print("[OK] Speed slider handler works")

    # Test reset (should not crash)
    print("Testing reset handler...")
    ui.on_reset()
    if ui.current_step != 0 or ui.is_playing != False:
        print("[FAIL] FAIL: Reset did not reset state")
        sys.exit(1)
    print("[OK] Reset handler works")

    # Test play/pause (should not crash when no city loaded)
    print("Testing play handler (no city)...")
    ui.on_play()  # Should print "Load a city first!" but not crash
    print("[OK] Play handler works")

    print("Testing pause handler...")
    ui.on_pause()
    if ui.is_playing != False:
        print("[FAIL] FAIL: Pause did not stop playback")
        sys.exit(1)
    print("[OK] Pause handler works")

    print()
    print("[TEST 3] PASSED - Handler Calls")
    print()

except Exception as e:
    print(f"[FAIL] FAIL: Handler call test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Figure/Canvas Persistence
print("[TEST 4] Figure/Canvas Persistence")
print("-" * 60)

try:
    # After all operations, figure and canvas should still exist
    if ui.fig is None:
        print("[FAIL] FAIL: Figure became None after operations!")
        sys.exit(1)
    print("[OK] Figure persists")

    if ui.fig.canvas is None:
        print("[FAIL] FAIL: Canvas became None after operations!")
        sys.exit(1)
    print("[OK] Canvas persists")

    # Check DPI attribute (this was the AttributeError in the bug)
    try:
        dpi = ui.fig.dpi
        print(f"[OK] Figure DPI accessible: {dpi}")
    except AttributeError as e:
        print(f"[FAIL] FAIL: AttributeError accessing DPI: {e}")
        sys.exit(1)

    print()
    print("[TEST 4] PASSED - Figure/Canvas Persistence")
    print()

except Exception as e:
    print(f"[FAIL] FAIL: Figure/canvas persistence test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: City Loading (Lightweight)
print("[TEST 5] City Loading (100 particles, 52 weeks)")
print("-" * 60)

try:
    print("Loading NYC with reduced parameters...")

    # Override max_steps for faster test
    ui.max_steps = 52  # 1 year instead of 20

    # Load city
    ui.load_city("New York", n_particles=100)

    if ui.particle_system is None:
        print("[FAIL] FAIL: Particle system not created!")
        sys.exit(1)
    print("[OK] Particle system created")

    if ui.current_city is None:
        print("[FAIL] FAIL: Current city not set!")
        sys.exit(1)
    print(f"[OK] Current city: {ui.current_city}")

    # Verify simulation ran
    if ui.particle_system.step_count != 52:
        print(f"[FAIL] FAIL: Expected 52 steps, got {ui.particle_system.step_count}")
        sys.exit(1)
    print("[OK] Simulation completed (52 steps)")

    # Get metrics
    metrics = ui.particle_system.get_metrics()
    print(f"[OK] Ocean reach: {metrics['ocean_reach_prob']:.1%}")
    print(f"[OK] Median distance: {metrics['median_distance_km']:,.0f} km")

    print()
    print("[TEST 5] PASSED - City Loading")
    print()

except Exception as e:
    print(f"[FAIL] FAIL: City loading test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Display Update (No Crash)
print("[TEST 6] Display Update")
print("-" * 60)

try:
    print("Updating display...")
    ui.update_display()
    print("[OK] Display update completed without crash")

    # Verify figure still valid after update
    if ui.fig is None or ui.fig.canvas is None:
        print("[FAIL] FAIL: Figure/canvas lost after display update!")
        sys.exit(1)
    print("[OK] Figure/canvas still valid after update")

    print()
    print("[TEST 6] PASSED - Display Update")
    print()

except Exception as e:
    print(f"[FAIL] FAIL: Display update test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("="*60)
print("  ALL UI TESTS PASSED [OK]")
print("="*60)
print()
print("UI verification complete:")
print("  [OK] UI initializes without errors")
print("  [OK] All 9 widgets accessible")
print("  [OK] Handlers callable programmatically")
print("  [OK] Figure and canvas persist through operations")
print("  [OK] City loading works (NYC)")
print("  [OK] Display updates without crashes")
print()
print("Next step: Run interactive mode with 'python main.py'")
print()

sys.exit(0)
