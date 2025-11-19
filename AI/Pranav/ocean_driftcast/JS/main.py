#!/usr/bin/env python3
"""
Synthetic demo for presentation, not scientific output.

Ocean Drift Visualization Demo
Main entry point for interactive UI and batch simulation.
"""

import argparse
import json
import sys
from typing import Optional

from physics import OceanPhysics
from particles import create_particle_system_from_city
from visualization import OceanDriftVisualizer
from ui import launch_interactive_ui
from animation import create_demo_animation


def single_city_demo(city_name: str, n_particles: int = 5000, n_steps: int = 1040,
                     output_file: Optional[str] = None):
    """
    Run simulation for a single city and display result.

    Args:
        city_name: City name to simulate
        n_particles: Number of particles
        n_steps: Simulation steps (weeks)
        output_file: Optional output image file
    """
    print(f"\n{'='*60}")
    print(f"  OCEAN DRIFT DEMO - {city_name.upper()}")
    print(f"{'='*60}\n")

    # Load seeds
    with open('seeds.json', 'r') as f:
        seeds = json.load(f)

    # Find city
    city_data = None
    for city in seeds:
        if city_name.lower() in city['city'].lower():
            city_data = city
            break

    if city_data is None:
        print(f"Error: City '{city_name}' not found.")
        print(f"Available cities: {', '.join([c['city'] for c in seeds[:5]])}, ...")
        return

    print(f"City: {city_data['city']}")
    print(f"Location: {city_data['lat']:.2f}°N, {abs(city_data['lon']):.2f}°W")
    print(f"Type: {city_data['type']}")
    print()

    # Create physics and particles
    print("Initializing simulation...")
    physics = OceanPhysics(seed=42)
    particles = create_particle_system_from_city(physics, city_data, n_particles)

    # Run simulation
    print(f"Simulating {n_steps} weeks (~{n_steps/52:.1f} years) with {n_particles} particles...")

    def progress(step, ps):
        if step % 100 == 0:
            pct = (step / n_steps) * 100
            print(f"  Progress: {pct:.0f}% ({step}/{n_steps} steps)")

    particles.simulate(n_steps, callback=progress)

    # Display metrics
    metrics = particles.get_metrics()
    prob_category = particles.get_probability_category()

    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"Probability Category: {prob_category}")
    print(f"Ocean Reach Probability: {metrics['ocean_reach_prob']:.1%}")
    print(f"Particles Beached: {metrics['n_beached']:,} / {metrics['n_particles']:,}")
    print(f"Particles in Ocean: {metrics['n_ocean']:,} / {metrics['n_particles']:,}")
    print(f"Median Distance: {metrics['median_distance_km']:,.0f} km")
    print(f"Mean Distance: {metrics['mean_distance_km']:,.0f} km")
    print(f"Max Distance: {metrics['max_distance_km']:,.0f} km")
    print(f"Simulation Duration: {metrics['years']:.1f} years")
    print(f"{'='*60}\n")

    # Visualize
    print("Generating visualization...")
    viz = OceanDriftVisualizer(figsize=(20, 12), dpi=100)
    fig = viz.render_frame(
        particles,
        city_data['city'],
        step=n_steps-1,
        show_trajectories=True,
        show_particles=True,
        traj_subsample=5
    )

    # Save or show
    if output_file:
        print(f"Saving to {output_file}...")
        viz.save_frame(output_file)
        print("Done!")
    else:
        print("Displaying visualization (close window to exit)...")
        import matplotlib.pyplot as plt
        plt.show()

    viz.close()


def batch_all_cities(n_particles: int = 3000, n_steps: int = 1040):
    """
    Run simulation for all cities and save metrics.

    Args:
        n_particles: Number of particles per city
        n_steps: Simulation steps
    """
    import os

    print(f"\n{'='*60}")
    print(f"  BATCH SIMULATION - ALL CITIES")
    print(f"{'='*60}\n")

    # Load seeds
    with open('seeds.json', 'r') as f:
        seeds = json.load(f)

    print(f"Simulating {len(seeds)} cities...")
    print(f"Particles per city: {n_particles}")
    print(f"Simulation length: {n_steps/52:.1f} years\n")

    # Create output directory
    output_dir = "outputs/batch"
    os.makedirs(output_dir, exist_ok=True)

    # Results storage
    all_metrics = []

    # Run each city
    physics = OceanPhysics(seed=42)

    for i, city_data in enumerate(seeds):
        print(f"[{i+1}/{len(seeds)}] {city_data['city']}...")

        # Create and simulate
        particles = create_particle_system_from_city(physics, city_data, n_particles)
        particles.simulate(n_steps)

        # Get metrics
        metrics = particles.get_metrics()
        metrics['city'] = city_data['city']
        metrics['lat'] = city_data['lat']
        metrics['lon'] = city_data['lon']
        metrics['region'] = city_data['region']
        metrics['type'] = city_data['type']
        metrics['probability_category'] = particles.get_probability_category()

        all_metrics.append(metrics)

        print(f"  → {metrics['probability_category']} probability, "
              f"{metrics['median_distance_km']:,.0f} km median distance\n")

    # Save metrics
    output_file = os.path.join(output_dir, "all_cities_metrics.json")
    with open(output_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Batch simulation complete!")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}\n")


def main():
    """
    Main entry point with CLI argument parsing.
    """
    parser = argparse.ArgumentParser(
        description="Ocean Drift Visualization Demo - Interactive particle simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch interactive UI (default)
  python main.py

  # Simulate single city
  python main.py --city "New York"

  # Save single city visualization
  python main.py --city "Lisbon" --output lisbon_drift.png

  # Create 3-chapter demo animation (MP4 + GIF)
  python main.py --animate

  # Batch simulate all cities
  python main.py --batch

  # Show help
  python main.py --help
        """
    )

    parser.add_argument(
        '--city', '-c',
        type=str,
        help='Simulate specific city (e.g., "New York", "Chicago", "Lisbon")'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file for single city visualization (PNG)'
    )

    parser.add_argument(
        '--particles', '-p',
        type=int,
        default=5000,
        help='Number of particles (default: 5000)'
    )

    parser.add_argument(
        '--years', '-y',
        type=float,
        default=20.0,
        help='Simulation duration in years (default: 20.0)'
    )

    parser.add_argument(
        '--animate', '-a',
        action='store_true',
        help='Create 3-chapter demo animation (MP4 + GIF)'
    )

    parser.add_argument(
        '--batch', '-b',
        action='store_true',
        help='Run batch simulation for all cities'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Launch interactive UI (default if no other mode specified)'
    )

    args = parser.parse_args()

    # Calculate steps from years
    n_steps = int(args.years * 52)  # weeks

    # Mode selection
    if args.animate:
        # Create demo animation
        create_demo_animation()

    elif args.batch:
        # Batch mode
        batch_all_cities(n_particles=args.particles, n_steps=n_steps)

    elif args.city:
        # Single city mode
        single_city_demo(
            city_name=args.city,
            n_particles=args.particles,
            n_steps=n_steps,
            output_file=args.output
        )

    else:
        # Interactive mode (default)
        print("\n" + "="*60)
        print("  OCEAN DRIFT DEMO - INTERACTIVE MODE")
        print("="*60)
        print("\nLaunching interactive UI...")
        print("  - Type a city name and click 'Load City'")
        print("  - Use Play/Pause to control animation")
        print("  - Adjust speed with slider")
        print("  - Export GIF or MP4 with buttons")
        print("\n" + "="*60 + "\n")

        launch_interactive_ui()


if __name__ == "__main__":
    main()
