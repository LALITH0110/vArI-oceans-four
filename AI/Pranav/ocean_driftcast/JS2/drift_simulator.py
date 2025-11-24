"""
Synthetic demo for presentation, not scientific output.

North Atlantic Plastic Drift Visualization - Simplified Version
A self-contained demo that simulates plastic particle drift using matplotlib only.

Requirements:
    pip install numpy matplotlib pillow imageio --break-system-packages
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
import imageio
from difflib import get_close_matches

# Configuration
SEEDS_FILE = "seeds.json"
OUTPUT_DIR = Path("./outputs")  # Relative path for cross-platform compatibility
OUTPUT_DIR.mkdir(exist_ok=True)

N_PARTICLES = 800  # Particles per city
YEARS = 10
WEEKS_PER_YEAR = 52
TOTAL_STEPS = YEARS * WEEKS_PER_YEAR
DT = 7 * 24 * 3600  # 1 week in seconds

# Physics parameters - TUNED for realistic ocean retention
GYRE_CENTER_LAT = 30.0
GYRE_CENTER_LON = -40.0
GYRE_RADIUS = 20.0
DIFFUSION_COEF = 0.08
WINDAGE = 0.05
BEACHING_PROB = 0.01  # Much lower - particles stay in ocean  # Reduced beaching probability

# Visual style
BG_COLOR = '#0a1e2e'
WATER_COLOR = '#0f2942'
TRAJECTORY_COLOR = '#00ffff'
TEXT_COLOR = '#ffffff'
PANEL_COLOR = '#163a52'

np.random.seed(42)


class PlasticDriftSimulator:
    """Simulates plastic particle drift in the North Atlantic"""
    
    def __init__(self, seeds_data):
        self.seeds = seeds_data
        self.city_lookup = {s['city']: s for s in seeds_data}
        
    def get_velocity_field(self, lat, lon):
        """Analytic velocity field for North Atlantic gyre - ENHANCED"""
        dlat = lat - GYRE_CENTER_LAT
        dlon = lon - GYRE_CENTER_LON
        r = np.sqrt(dlat**2 + dlon**2)
        
        # Stronger gyre circulation
        strength = 1.2 * np.exp(-r**2 / (2 * GYRE_RADIUS**2))
        u = -strength * dlat / (r + 0.1)
        v = strength * dlon / (r + 0.1)
        
        # Powerful Gulf Stream
        gs_mask = (lon < -60) & (lat > 25) & (lat < 45)
        gs_strength = 2.0 * np.exp(-(lon + 70)**2 / 50)
        v = np.where(gs_mask, v + gs_strength * 4.0, v)
        u = np.where(gs_mask, u + gs_strength * 2.0, u)
        
        # Trade winds
        wind_mask = (lat > 10) & (lat < 30)
        u = np.where(wind_mask, u + WINDAGE * 1.2, u)
        v = np.where(wind_mask, v - WINDAGE * 0.4, v)
        
        # Push away from coast
        if hasattr(lon, '__iter__'):
            coast_mask = (lon > -75) & (lon < -70) & (lat > 35) & (lat < 42)
            u = np.where(coast_mask, u + 1.5, u)
        else:
            if lon > -75 and lon < -70 and lat > 35 and lat < 42:
                u += 1.5
        
        return u, v
    
    def is_land(self, lat, lon):
        """Strict land mask - keep particles in ocean"""
        lat = np.atleast_1d(lat)
        lon = np.atleast_1d(lon)
        land = np.zeros(lat.shape, dtype=bool)
        
        # Tighter boundaries
        land |= (lon < -50) & (lat > 30) & (lat < 48) & (lon > -90)
        land |= (lon > -8) & (lat > 36) & (lat < 58)
        land |= (lon > -12) & (lat > 31) & (lat < 36)
        land |= (lat < 12) | (lat > 63) | (lon < -95) | (lon > 15)
        
        return land if land.shape[0] > 1 else land[0]
    
    def route_inland_to_ocean(self, city_data):
        """Route inland cities to ocean"""
        lat, lon = city_data['lat'], city_data['lon']
        if city_data['type'] == 'coastal':
            return lat, lon
        # Great Lakes -> St. Lawrence
        if 'Chicago' in city_data['city'] or 'Toronto' in city_data['city'] or 'Montreal' in city_data['city']:
            return 48.0, -61.0
        return lat, lon - 5.0
    
    def simulate_particles(self, start_lat, start_lon):
        """Simulate particle trajectories"""
        print(f"    Simulating {N_PARTICLES} particles...")
        
        # Initialize particles
        angles = np.random.uniform(0, 2*np.pi, N_PARTICLES)
        radii = np.random.uniform(0, 0.3, N_PARTICLES)
        lats = start_lat + radii * np.cos(angles)
        lons = start_lon + radii * np.sin(angles)
        
        trajectories = np.zeros((N_PARTICLES, TOTAL_STEPS, 2))
        trajectories[:, 0, 0] = lats
        trajectories[:, 0, 1] = lons
        
        beached = np.zeros(N_PARTICLES, dtype=bool)
        active = np.ones(N_PARTICLES, dtype=bool)
        
        # Simulate with progress
        for step in range(1, TOTAL_STEPS):
            if step % 100 == 0:
                print(f"      Step {step}/{TOTAL_STEPS}")
            
            for i in range(N_PARTICLES):
                if not active[i]:
                    trajectories[i, step, :] = trajectories[i, step-1, :]
                    continue
                
                lat_curr = trajectories[i, step-1, 0]
                lon_curr = trajectories[i, step-1, 1]
                
                # Simple Euler integration (faster than RK4 for demo)
                u, v = self.get_velocity_field(lat_curr, lon_curr)
                u += np.random.normal(0, DIFFUSION_COEF)
                v += np.random.normal(0, DIFFUSION_COEF)
                
                new_lat = lat_curr + v * DT / 111000
                new_lon = lon_curr + u * DT / (111000 * np.cos(np.deg2rad(lat_curr)))
                
                # Check land collision
                if self.is_land(new_lat, new_lon):
                    if np.random.random() < BEACHING_PROB:
                        beached[i] = True
                        active[i] = False
                        trajectories[i, step, :] = trajectories[i, step-1, :]
                        continue
                
                trajectories[i, step, 0] = new_lat
                trajectories[i, step, 1] = new_lon
        
        return trajectories, beached
    
    def calculate_metrics(self, trajectories, beached, city_data):
        """Calculate summary metrics"""
        ocean_reach_prob = 1 - (beached.sum() / len(beached))
        
        distances = np.zeros(N_PARTICLES)
        for i in range(N_PARTICLES):
            traj = trajectories[i]
            dlat = np.diff(traj[:, 0])
            dlon = np.diff(traj[:, 1])
            dist_km = np.sqrt(dlat**2 + dlon**2) * 111
            distances[i] = dist_km.sum()
        
        median_distance = np.median(distances)
        
        if ocean_reach_prob > 0.7:
            prob_class = "HIGH"
        elif ocean_reach_prob > 0.4:
            prob_class = "MEDIUM"
        else:
            prob_class = "LOW"
        
        return {
            "city": city_data['city'],
            "n_particles": N_PARTICLES,
            "beached": float(beached.sum() / len(beached)),
            "ocean_reach_prob": float(ocean_reach_prob),
            "median_distance_km": float(median_distance),
            "prob_class": prob_class
        }
    
    def find_city(self, query):
        """Fuzzy match city name"""
        # Try exact substring match first
        query_lower = query.lower()
        for city_name in self.city_lookup.keys():
            if query_lower in city_name.lower():
                return self.city_lookup[city_name]
        
        # Fall back to fuzzy match
        cities = list(self.city_lookup.keys())
        matches = get_close_matches(query, cities, n=1, cutoff=0.3)
        return self.city_lookup[matches[0]] if matches else None


def draw_simple_coastlines(ax):
    """Draw simplified coastlines"""
    # North America east coast
    na_coast_lat = [25, 30, 35, 40, 45, 48, 50, 48, 45]
    na_coast_lon = [-80, -81, -76, -74, -68, -66, -64, -58, -52]
    ax.plot(na_coast_lon, na_coast_lat, color='#444444', linewidth=2, zorder=1)
    
    # Europe west coast
    eu_coast_lat = [35, 40, 43, 48, 53, 56, 60]
    eu_coast_lon = [-6, -9, -3, -5, -3, -4, -1]
    ax.plot(eu_coast_lon, eu_coast_lat, color='#444444', linewidth=2, zorder=1)
    
    # Africa northwest coast
    af_coast_lat = [10, 20, 30, 35]
    af_coast_lon = [-15, -17, -10, -6]
    ax.plot(af_coast_lon, af_coast_lat, color='#444444', linewidth=2, zorder=1)


class Visualizer:
    """Creates animations"""
    
    def __init__(self, simulator):
        self.simulator = simulator
        
    def create_figure(self):
        """Create base figure"""
        fig, ax = plt.subplots(figsize=(16, 9), facecolor=BG_COLOR)
        ax.set_xlim(-100, 20)
        ax.set_ylim(10, 65)
        ax.set_facecolor(WATER_COLOR)
        ax.set_xlabel('Longitude', color=TEXT_COLOR)
        ax.set_ylabel('Latitude', color=TEXT_COLOR)
        ax.tick_params(colors=TEXT_COLOR)
        ax.grid(True, alpha=0.2, color='#2a4a5a')
        
        # Draw coastlines
        draw_simple_coastlines(ax)
        
        return fig, ax
    
    def add_info_panel(self, fig, city_name, metrics, year):
        """Add info panel"""
        panel_x, panel_y = 0.72, 0.50
        panel_w, panel_h = 0.25, 0.40
        
        # Background
        panel = Rectangle((panel_x, panel_y), panel_w, panel_h,
                         transform=fig.transFigure,
                         facecolor=PANEL_COLOR, edgecolor=TRAJECTORY_COLOR,
                         linewidth=2, alpha=0.95, zorder=100)
        fig.patches.append(panel)
        
        # City name
        fig.text(panel_x + panel_w/2, panel_y + 0.34, city_name.upper(),
                ha='center', va='center', color=TEXT_COLOR, fontsize=14,
                weight='bold', transform=fig.transFigure)
        
        # Probability class
        fig.text(panel_x + panel_w/2, panel_y + 0.28, metrics['prob_class'],
                ha='center', va='center', color=TRAJECTORY_COLOR, fontsize=20,
                weight='bold', transform=fig.transFigure)
        
        fig.text(panel_x + panel_w/2, panel_y + 0.22,
                'probability of plastic to reach the ocean',
                ha='center', va='center', color=TEXT_COLOR, fontsize=8,
                transform=fig.transFigure, wrap=True)
        
        # Distance
        fig.text(panel_x + panel_w/2, panel_y + 0.14,
                f"{metrics['median_distance_km']:,.0f} KM",
                ha='center', va='center', color=TRAJECTORY_COLOR, fontsize=16,
                weight='bold', transform=fig.transFigure)
        
        fig.text(panel_x + panel_w/2, panel_y + 0.09, 'of trajectory distance',
                ha='center', va='center', color=TEXT_COLOR, fontsize=8,
                transform=fig.transFigure)
        
        # Time counter
        fig.text(0.02, 0.95, f"Year {year:.1f} / {YEARS}",
                color=TEXT_COLOR, fontsize=12, weight='bold',
                transform=fig.transFigure)
        
        # Gyre label
        ax = fig.axes[0]
        ax.text(GYRE_CENTER_LON, GYRE_CENTER_LAT, 'North Atlantic\nGarbage Patch',
               ha='center', va='center', color='#ff6b6b', fontsize=10,
               weight='bold', bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
    
    def create_animation(self, city_name):
        """Create animation for a city"""
        city_data = self.simulator.find_city(city_name)
        if not city_data:
            print(f"City '{city_name}' not found")
            return None, None
        
        print(f"\n{'='*50}")
        print(f"Processing: {city_data['city']}")
        print(f"{'='*50}")
        
        start_lat, start_lon = self.simulator.route_inland_to_ocean(city_data)
        trajectories, beached = self.simulator.simulate_particles(start_lat, start_lon)
        metrics = self.simulator.calculate_metrics(trajectories, beached, city_data)
        
        print(f"  Ocean reach: {metrics['ocean_reach_prob']:.1%}")
        print(f"  Distance: {metrics['median_distance_km']:,.0f} km")
        
        # Create frames
        print("  Creating frames...")
        frames = []
        n_frames = 50
        frame_skip = max(1, TOTAL_STEPS // n_frames)
        
        for frame_idx, step in enumerate(range(0, TOTAL_STEPS, frame_skip)):
            if frame_idx % 10 == 0:
                print(f"    Frame {frame_idx}/{n_frames}")
            
            fig, ax = self.create_figure()
            
            # Draw trajectories
            for i in range(0, N_PARTICLES, 2):  # Sample every 2nd for performance
                traj = trajectories[i, :step+1]
                if len(traj) > 1:
                    alpha = 0.2 if beached[i] else 0.4
                    ax.plot(traj[:, 1], traj[:, 0],
                           color=TRAJECTORY_COLOR, alpha=alpha,
                           linewidth=0.5, zorder=2)
            
            # Current positions
            if step > 0:
                curr_pos = trajectories[:, step, :]
                ax.scatter(curr_pos[:, 1], curr_pos[:, 0],
                          c=TRAJECTORY_COLOR, s=1, alpha=0.6, zorder=3)
            
            # Info panel
            year = step / WEEKS_PER_YEAR
            self.add_info_panel(fig, city_data['city'], metrics, year)
            
            # Convert to image
            fig.canvas.draw()
            image = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (4,))
            image = image[:, :, :3]  # Drop alpha channel
            frames.append(image)
            plt.close(fig)
        
        return frames, metrics


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("NORTH ATLANTIC PLASTIC DRIFT SIMULATOR")
    print("Synthetic demo for presentation, not scientific output")
    print("="*60)
    
    with open(SEEDS_FILE, 'r') as f:
        seeds = json.load(f)
    
    simulator = PlasticDriftSimulator(seeds)
    visualizer = Visualizer(simulator)
    
    # Create animations for 3 cities
    cities = ["New York", "Lisbon", "Chicago"]
    all_frames = []
    all_metrics = []
    
    for city in cities:
        frames, metrics = visualizer.create_animation(city)
        if frames:
            all_frames.extend(frames)
            all_metrics.append(metrics)
            # Add pause
            for _ in range(15):
                all_frames.append(frames[-1])
    
    # Export
    print("\n" + "="*60)
    print("EXPORTING ANIMATIONS")
    print("="*60)
    
    print("  Creating MP4...")
    mp4_path = OUTPUT_DIR / "drift_demo.mp4"
    imageio.mimsave(mp4_path, all_frames, fps=20, codec='libx264', quality=8)
    print(f"    ✓ {mp4_path}")
    
    print("  Creating GIF...")
    gif_path = OUTPUT_DIR / "drift_demo.gif"
    gif_frames = all_frames[::2]  # Every 2nd frame
    imageio.mimsave(gif_path, gif_frames, fps=10, loop=0)
    print(f"    ✓ {gif_path}")
    
    # Save metrics
    with open(OUTPUT_DIR / "metrics.json", 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    print(f"\nOutputs in: {OUTPUT_DIR}")
    print("  • drift_demo.mp4")
    print("  • drift_demo.gif")
    print("  • metrics.json")
    
    print("\nSUMMARY:")
    for m in all_metrics:
        print(f"  {m['city']:20s} - {m['prob_class']:6s} ocean reach, {m['median_distance_km']:,.0f} km")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2 and sys.argv[1] == '--city':
        city_query = sys.argv[2]
        with open(SEEDS_FILE, 'r') as f:
            seeds = json.load(f)
        simulator = PlasticDriftSimulator(seeds)
        visualizer = Visualizer(simulator)
        frames, metrics = visualizer.create_animation(city_query)
        if frames:
            mp4_path = OUTPUT_DIR / f"drift_{city_query.replace(' ', '_').lower()}.mp4"
            imageio.mimsave(mp4_path, frames, fps=20, codec='libx264', quality=8)
            print(f"\nSaved: {mp4_path}")
    else:
        main()
