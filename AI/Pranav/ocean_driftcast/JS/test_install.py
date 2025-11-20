#!/usr/bin/env python3
"""
Test script to verify installation and basic functionality.
Synthetic demo for presentation, not scientific output.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    modules = [
        ('numpy', 'NumPy'),
        ('matplotlib', 'Matplotlib'),
        ('cartopy', 'Cartopy'),
        ('PIL', 'Pillow'),
        ('imageio', 'imageio'),
        ('scipy', 'SciPy'),
    ]

    failed = []
    for module, name in modules:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ✗ {name} - {e}")
            failed.append(name)

    if failed:
        print(f"\nError: Missing modules: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False

    print("  All imports successful!\n")
    return True


def test_seeds():
    """Test that seeds.json exists and is valid."""
    print("Testing seeds.json...")

    if not os.path.exists('seeds.json'):
        print("  ✗ seeds.json not found")
        return False

    try:
        import json
        with open('seeds.json', 'r') as f:
            seeds = json.load(f)

        if not isinstance(seeds, list):
            print("  ✗ seeds.json should contain a list")
            return False

        if len(seeds) == 0:
            print("  ✗ seeds.json is empty")
            return False

        # Check structure
        required_keys = ['city', 'lat', 'lon', 'region', 'type']
        first_city = seeds[0]

        for key in required_keys:
            if key not in first_city:
                print(f"  ✗ Missing required key: {key}")
                return False

        print(f"  ✓ Found {len(seeds)} cities")
        print(f"  ✓ Structure valid\n")
        return True

    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error reading seeds.json: {e}")
        return False


def test_physics():
    """Test basic physics simulation."""
    print("Testing physics engine...")

    try:
        from physics import OceanPhysics
        import numpy as np

        # Create physics engine
        physics = OceanPhysics(seed=42)

        # Test velocity field
        lat = np.array([30.0, 35.0, 40.0])
        lon = np.array([-40.0, -50.0, -60.0])
        u, v = physics.velocity_field(lat, lon)

        if not isinstance(u, np.ndarray) or not isinstance(v, np.ndarray):
            print("  ✗ Velocity field should return numpy arrays")
            return False

        if len(u) != len(lat):
            print("  ✗ Velocity field size mismatch")
            return False

        # Test diffusion
        du, dv = physics.diffusion_step(100)

        if len(du) != 100 or len(dv) != 100:
            print("  ✗ Diffusion step size mismatch")
            return False

        # Test RK4
        lat_test = np.array([30.0])
        lon_test = np.array([-40.0])
        beached = np.array([False])

        new_lat, new_lon = physics.rk4_step(lat_test, lon_test, beached)

        if len(new_lat) != 1 or len(new_lon) != 1:
            print("  ✗ RK4 step size mismatch")
            return False

        print("  ✓ Velocity field computation")
        print("  ✓ Diffusion step")
        print("  ✓ RK4 integration")
        print("  ✓ Physics engine working\n")
        return True

    except Exception as e:
        print(f"  ✗ Physics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_particles():
    """Test particle system."""
    print("Testing particle system...")

    try:
        from physics import OceanPhysics
        from particles import ParticleSystem

        # Create system
        physics = OceanPhysics(seed=42)
        particles = ParticleSystem(physics, n_particles=100, release_lat=40.0, release_lon=-74.0)

        # Test initial state
        if len(particles.lat) != 100:
            print("  ✗ Incorrect particle count")
            return False

        # Test simulation step
        initial_step = particles.step_count
        particles.step()

        if particles.step_count != initial_step + 1:
            print("  ✗ Step counter not incremented")
            return False

        # Test metrics
        particles.simulate(10)
        metrics = particles.get_metrics()

        required_metrics = ['n_particles', 'ocean_reach_prob', 'median_distance_km']
        for key in required_metrics:
            if key not in metrics:
                print(f"  ✗ Missing metric: {key}")
                return False

        # Test probability category
        category = particles.get_probability_category()
        if category not in ['LOW', 'MEDIUM', 'HIGH']:
            print(f"  ✗ Invalid probability category: {category}")
            return False

        print("  ✓ Particle initialization")
        print("  ✓ Simulation step")
        print("  ✓ Metrics calculation")
        print("  ✓ Particle system working\n")
        return True

    except Exception as e:
        print(f"  ✗ Particle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visualization():
    """Test visualization setup."""
    print("Testing visualization...")

    try:
        from visualization import OceanDriftVisualizer
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend

        # Create visualizer
        viz = OceanDriftVisualizer(figsize=(10, 6), dpi=50)

        # Setup figure
        fig, ax = viz.setup_figure()

        if fig is None or ax is None:
            print("  ✗ Failed to create figure")
            return False

        # Test gyre background
        viz.plot_gyre_background()

        # Clean up
        viz.close()

        print("  ✓ Visualizer creation")
        print("  ✓ Figure setup")
        print("  ✓ Gyre background")
        print("  ✓ Visualization working\n")
        return True

    except Exception as e:
        print(f"  ✗ Visualization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_simulation():
    """Test a small end-to-end simulation."""
    print("Testing full simulation...")

    try:
        import json
        from physics import OceanPhysics
        from particles import create_particle_system_from_city

        # Load a city
        with open('seeds.json', 'r') as f:
            seeds = json.load(f)

        city_data = seeds[0]  # First city

        # Create and simulate
        physics = OceanPhysics(seed=42)
        particles = create_particle_system_from_city(physics, city_data, n_particles=100)

        print(f"  Running 52-week simulation for {city_data['city']}...")
        particles.simulate(52)  # 1 year

        # Get metrics
        metrics = particles.get_metrics()

        print(f"  ✓ Simulated {metrics['n_particles']} particles")
        print(f"  ✓ Ocean reach: {metrics['ocean_reach_prob']:.1%}")
        print(f"  ✓ Median distance: {metrics['median_distance_km']:,.0f} km")
        print("  ✓ Full simulation working\n")
        return True

    except Exception as e:
        print(f"  ✗ Full simulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  OCEAN DRIFT DEMO - INSTALLATION TEST")
    print("="*60 + "\n")

    tests = [
        ("Dependencies", test_imports),
        ("Seeds Data", test_seeds),
        ("Physics Engine", test_physics),
        ("Particle System", test_particles),
        ("Visualization", test_visualization),
        ("Full Simulation", test_full_simulation),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"  ✗ {name} test crashed: {e}")
            results[name] = False

    # Summary
    print("="*60)
    print("  TEST SUMMARY")
    print("="*60)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")

    print("="*60)
    print(f"  {passed}/{total} tests passed")
    print("="*60 + "\n")

    if passed == total:
        print("✓ All tests passed! Installation is working correctly.")
        print("\nYou can now run:")
        print("  python main.py              # Interactive UI")
        print("  python main.py --city 'New York'  # Single city")
        print("  python main.py --animate    # Create demo animation")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("  1. Make sure all dependencies are installed:")
        print("     pip install -r requirements.txt")
        print("  2. Check that seeds.json is in the current directory")
        print("  3. Try running from project root directory")
        return 1


if __name__ == "__main__":
    sys.exit(main())
