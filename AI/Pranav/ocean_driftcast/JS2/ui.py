"""
Synthetic demo for presentation, not scientific output.

North Atlantic Plastic Drift Visualization - Interactive UI
Web-based interface using Streamlit for easy city selection and visualization.

Usage:
    streamlit run ui.py
"""

import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
import imageio
import io
from difflib import get_close_matches
import time

# Use Cartopy if available, fallback to simple polygons
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False
    import matplotlib.patches as mpatches
    from matplotlib.collections import PatchCollection

# Configuration
SEEDS_FILE = "seeds.json"
OUTPUT_DIR = Path("./outputs")  # Relative path for cross-platform compatibility
OUTPUT_DIR.mkdir(exist_ok=True)

N_PARTICLES = 800
YEARS = 10
WEEKS_PER_YEAR = 52
TOTAL_STEPS = YEARS * WEEKS_PER_YEAR
DT = 7 * 24 * 3600

# Physics parameters - TUNED for realistic ocean retention
GYRE_CENTER_LAT = 30.0
GYRE_CENTER_LON = -40.0
GYRE_RADIUS = 20.0
DIFFUSION_COEF = 0.08  # Increased turbulence
WINDAGE = 0.05  # Stronger wind effect
BEACHING_PROB = 0.01  # Much lower beaching (particles stay in ocean longer)

# Visual style
BG_COLOR = '#0a1e2e'
WATER_COLOR = '#0f2942'
LAND_COLOR = '#1a1a1a'
TRAJECTORY_COLOR = '#00ffff'
TEXT_COLOR = '#ffffff'
PANEL_COLOR = '#163a52'

np.random.seed(42)


class PlasticDriftSimulator:
    """Core simulation engine"""
    
    def __init__(self, seeds_data):
        self.seeds = seeds_data
        self.city_lookup = {s['city']: s for s in seeds_data}
    
    def get_velocity_field(self, lat, lon):
        """Ocean current velocity field - ENHANCED to keep particles offshore"""
        dlat = lat - GYRE_CENTER_LAT
        dlon = lon - GYRE_CENTER_LON
        r = np.sqrt(dlat**2 + dlon**2)
        
        # Stronger gyre circulation
        strength = 1.2 * np.exp(-r**2 / (2 * GYRE_RADIUS**2))
        u = -strength * dlat / (r + 0.1)
        v = strength * dlon / (r + 0.1)
        
        # POWERFUL Gulf Stream - push particles offshore
        gs_mask = (lon < -60) & (lat > 25) & (lat < 45)
        gs_strength = 2.0 * np.exp(-(lon + 70)**2 / 50)
        v = np.where(gs_mask, v + gs_strength * 4.0, v)  # Strong northward
        u = np.where(gs_mask, u + gs_strength * 2.0, u)  # Push eastward
        
        # Trade winds
        wind_mask = (lat > 10) & (lat < 30)
        u = np.where(wind_mask, u + WINDAGE * 1.2, u)
        v = np.where(wind_mask, v - WINDAGE * 0.4, v)
        
        # CRITICAL: Push away from US coast (prevent beaching)
        if hasattr(lon, '__iter__'):
            coast_mask = (lon > -75) & (lon < -70) & (lat > 35) & (lat < 42)
            u = np.where(coast_mask, u + 1.5, u)  # Strong push eastward away from coast
        else:
            if lon > -75 and lon < -70 and lat > 35 and lat < 42:
                u += 1.5
        
        return u, v
    
    def is_land(self, lat, lon):
        """Strict land mask - more conservative to keep particles in ocean"""
        lat = np.atleast_1d(lat)
        lon = np.atleast_1d(lon)
        land = np.zeros(lat.shape, dtype=bool)
        
        # More restrictive land boundaries to keep particles offshore
        # North America - tighter boundary
        land |= (lon < -50) & (lat > 30) & (lat < 48) & (lon > -90)
        
        # Europe/Africa - tighter boundary  
        land |= (lon > -8) & (lat > 36) & (lat < 58)
        land |= (lon > -12) & (lat > 31) & (lat < 36)
        
        # Out of simulation bounds
        land |= (lat < 12) | (lat > 63) | (lon < -95) | (lon > 15)
        
        return land if land.shape[0] > 1 else land[0]
    
    def route_inland_to_ocean(self, city_data):
        """Route inland cities to ocean"""
        lat, lon = city_data['lat'], city_data['lon']
        if city_data['type'] == 'coastal':
            return lat, lon
        if 'Chicago' in city_data['city'] or 'Toronto' in city_data['city'] or 'Montreal' in city_data['city']:
            return 48.0, -61.0
        return lat, lon - 5.0
    
    def simulate_particles(self, start_lat, start_lon, progress_callback=None):
        """Run particle simulation with progress updates"""
        angles = np.random.uniform(0, 2*np.pi, N_PARTICLES)
        radii = np.random.uniform(0, 0.3, N_PARTICLES)
        lats = start_lat + radii * np.cos(angles)
        lons = start_lon + radii * np.sin(angles)
        
        trajectories = np.zeros((N_PARTICLES, TOTAL_STEPS, 2))
        trajectories[:, 0, 0] = lats
        trajectories[:, 0, 1] = lons
        
        beached = np.zeros(N_PARTICLES, dtype=bool)
        active = np.ones(N_PARTICLES, dtype=bool)
        
        for step in range(1, TOTAL_STEPS):
            if progress_callback and step % 50 == 0:
                progress_callback(step / TOTAL_STEPS)
            
            for i in range(N_PARTICLES):
                if not active[i]:
                    trajectories[i, step, :] = trajectories[i, step-1, :]
                    continue
                
                lat_curr = trajectories[i, step-1, 0]
                lon_curr = trajectories[i, step-1, 1]
                
                u, v = self.get_velocity_field(lat_curr, lon_curr)
                u += np.random.normal(0, DIFFUSION_COEF)
                v += np.random.normal(0, DIFFUSION_COEF)
                
                new_lat = lat_curr + v * DT / 111000
                new_lon = lon_curr + u * DT / (111000 * np.cos(np.deg2rad(lat_curr)))
                
                if self.is_land(new_lat, new_lon):
                    if np.random.random() < BEACHING_PROB:
                        beached[i] = True
                        active[i] = False
                        trajectories[i, step, :] = trajectories[i, step-1, :]
                        continue
                
                trajectories[i, step, 0] = new_lat
                trajectories[i, step, 1] = new_lon
        
        if progress_callback:
            progress_callback(1.0)
        
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
        query_lower = query.lower()
        for city_name in self.city_lookup.keys():
            if query_lower in city_name.lower():
                return self.city_lookup[city_name]
        
        cities = list(self.city_lookup.keys())
        matches = get_close_matches(query, cities, n=1, cutoff=0.3)
        return self.city_lookup[matches[0]] if matches else None


def draw_basemap_cartopy(ax):
    """Draw basemap using Cartopy with Natural Earth features"""
    ax.add_feature(cfeature.OCEAN, facecolor=WATER_COLOR, zorder=0)
    ax.add_feature(cfeature.LAND, facecolor=LAND_COLOR, edgecolor='#333333', linewidth=0.5, zorder=1)
    ax.add_feature(cfeature.COASTLINE, edgecolor='#444444', linewidth=0.8, zorder=2)
    ax.add_feature(cfeature.BORDERS, edgecolor='#333333', linewidth=0.3, alpha=0.5, zorder=2)
    ax.gridlines(draw_labels=False, linewidth=0.3, color='#2a4a5a', alpha=0.5)


def draw_basemap_simple(ax):
    """Fallback basemap without Cartopy"""
    # Simplified North America east coast
    na_lons = [-80, -81, -76, -74, -68, -66, -64, -58, -52, -52, -68, -70, -75, -78, -80]
    na_lats = [25, 30, 35, 40, 45, 48, 50, 48, 45, 30, 28, 26, 25, 24, 25]
    ax.fill(na_lons, na_lats, color=LAND_COLOR, edgecolor='#444444', linewidth=1, zorder=1)
    
    # Europe
    eu_lons = [-6, -9, -3, -5, -3, -4, -1, 5, 10, 10, 5, 0, -6]
    eu_lats = [35, 40, 43, 48, 53, 56, 60, 58, 55, 40, 37, 35, 35]
    ax.fill(eu_lons, eu_lats, color=LAND_COLOR, edgecolor='#444444', linewidth=1, zorder=1)
    
    # Northwest Africa
    af_lons = [-15, -17, -10, -6, -8, -12, -15]
    af_lats = [10, 20, 30, 35, 33, 25, 10]
    ax.fill(af_lons, af_lats, color=LAND_COLOR, edgecolor='#444444', linewidth=1, zorder=1)


class Visualizer:
    """Creates visualizations"""
    
    def __init__(self, simulator):
        self.simulator = simulator
        self.use_cartopy = CARTOPY_AVAILABLE
    
    def create_figure(self):
        """Create base figure with proper basemap"""
        if self.use_cartopy:
            fig = plt.figure(figsize=(16, 9), facecolor=BG_COLOR)
            ax = fig.add_subplot(111, projection=ccrs.PlateCarree(), facecolor=WATER_COLOR)
            ax.set_extent([-100, 20, 10, 65], crs=ccrs.PlateCarree())
            draw_basemap_cartopy(ax)
        else:
            fig, ax = plt.subplots(figsize=(16, 9), facecolor=BG_COLOR)
            ax.set_xlim(-100, 20)
            ax.set_ylim(10, 65)
            ax.set_facecolor(WATER_COLOR)
            draw_basemap_simple(ax)
        
        ax.set_xlabel('Longitude', color=TEXT_COLOR, fontsize=10)
        ax.set_ylabel('Latitude', color=TEXT_COLOR, fontsize=10)
        ax.tick_params(colors=TEXT_COLOR, labelsize=8)
        
        return fig, ax
    
    def add_info_panel(self, fig, city_name, metrics, year):
        """Add info panel overlay"""
        panel_x, panel_y = 0.72, 0.50
        panel_w, panel_h = 0.25, 0.40
        
        panel = Rectangle((panel_x, panel_y), panel_w, panel_h,
                         transform=fig.transFigure,
                         facecolor=PANEL_COLOR, edgecolor=TRAJECTORY_COLOR,
                         linewidth=2, alpha=0.95, zorder=100)
        fig.patches.append(panel)
        
        fig.text(panel_x + panel_w/2, panel_y + 0.34, city_name.upper(),
                ha='center', va='center', color=TEXT_COLOR, fontsize=14,
                weight='bold', transform=fig.transFigure)
        
        # Color-code the probability class
        prob_color = {
            'HIGH': '#00ff00',
            'MEDIUM': '#ffaa00',
            'LOW': '#ff6b6b'
        }.get(metrics['prob_class'], TRAJECTORY_COLOR)
        
        fig.text(panel_x + panel_w/2, panel_y + 0.28, metrics['prob_class'],
                ha='center', va='center', color=prob_color, fontsize=20,
                weight='bold', transform=fig.transFigure)
        
        fig.text(panel_x + panel_w/2, panel_y + 0.22,
                'probability of plastic to reach the ocean',
                ha='center', va='center', color=TEXT_COLOR, fontsize=8,
                transform=fig.transFigure)
        
        fig.text(panel_x + panel_w/2, panel_y + 0.14,
                f"{metrics['median_distance_km']:,.0f} KM",
                ha='center', va='center', color=TRAJECTORY_COLOR, fontsize=16,
                weight='bold', transform=fig.transFigure)
        
        fig.text(panel_x + panel_w/2, panel_y + 0.09, 'of trajectory distance',
                ha='center', va='center', color=TEXT_COLOR, fontsize=8,
                transform=fig.transFigure)
        
        fig.text(0.02, 0.95, f"Year {year:.1f} / {YEARS}",
                color=TEXT_COLOR, fontsize=12, weight='bold',
                transform=fig.transFigure)
        
        # Gyre label
        if self.use_cartopy:
            ax = fig.axes[0]
            ax.text(GYRE_CENTER_LON, GYRE_CENTER_LAT, 'North Atlantic\nGarbage Patch',
                   ha='center', va='center', color='#ff6b6b', fontsize=10,
                   weight='bold', bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
                   transform=ccrs.PlateCarree(), zorder=50)
        else:
            ax = fig.axes[0]
            ax.text(GYRE_CENTER_LON, GYRE_CENTER_LAT, 'North Atlantic\nGarbage Patch',
                   ha='center', va='center', color='#ff6b6b', fontsize=10,
                   weight='bold', bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
                   zorder=50)
    
    def render_frame(self, trajectories, beached, step, city_name, metrics):
        """Render a single frame with animated pointer"""
        fig, ax = self.create_figure()
        
        # Calculate particle centroid for pointer
        active_particles = ~beached
        if step > 0 and active_particles.sum() > 0:
            current_positions = trajectories[active_particles, step, :]
            centroid_lat = current_positions[:, 0].mean()
            centroid_lon = current_positions[:, 1].mean()
        else:
            centroid_lat, centroid_lon = None, None
        
        # Draw trajectories with enhanced visibility
        sample_rate = max(1, N_PARTICLES // 400)
        for i in range(0, N_PARTICLES, sample_rate):
            traj = trajectories[i, :step+1]
            if len(traj) > 1:
                alpha = 0.25 if beached[i] else 0.45  # Dimmer beached trails
                linewidth = 0.5 if beached[i] else 0.8
                
                if self.use_cartopy:
                    ax.plot(traj[:, 1], traj[:, 0],
                           color=TRAJECTORY_COLOR, alpha=alpha,
                           linewidth=linewidth, transform=ccrs.PlateCarree(), zorder=3)
                else:
                    ax.plot(traj[:, 1], traj[:, 0],
                           color=TRAJECTORY_COLOR, alpha=alpha,
                           linewidth=linewidth, zorder=3)
        
        # Draw active particle positions (brighter, ocean only)
        if step > 0:
            active_positions = trajectories[active_particles, step, :]
            if len(active_positions) > 0:
                if self.use_cartopy:
                    ax.scatter(active_positions[:, 1], active_positions[:, 0],
                              c=TRAJECTORY_COLOR, s=3, alpha=0.9,
                              transform=ccrs.PlateCarree(), zorder=4,
                              edgecolors='white', linewidths=0.3)
                else:
                    ax.scatter(active_positions[:, 1], active_positions[:, 0],
                              c=TRAJECTORY_COLOR, s=3, alpha=0.9, zorder=4,
                              edgecolors='white', linewidths=0.3)
        
        # Draw animated pointer at particle centroid
        if centroid_lat is not None:
            if self.use_cartopy:
                # Large marker for centroid
                ax.plot(centroid_lon, centroid_lat, 'o',
                       color='#ff00ff', markersize=12, alpha=0.8,
                       markeredgecolor='white', markeredgewidth=2,
                       transform=ccrs.PlateCarree(), zorder=10)
                # Pulsing circle
                circle = plt.Circle((centroid_lon, centroid_lat), 0.5,
                                  color='#ff00ff', alpha=0.3, fill=False,
                                  linewidth=3, transform=ccrs.PlateCarree(), zorder=9)
                ax.add_patch(circle)
            else:
                ax.plot(centroid_lon, centroid_lat, 'o',
                       color='#ff00ff', markersize=12, alpha=0.8,
                       markeredgecolor='white', markeredgewidth=2, zorder=10)
                circle = plt.Circle((centroid_lon, centroid_lat), 0.5,
                                  color='#ff00ff', alpha=0.3, fill=False,
                                  linewidth=3, zorder=9)
                ax.add_patch(circle)
        
        year = step / WEEKS_PER_YEAR
        self.add_info_panel(fig, city_name, metrics, year)
        
        return fig


# Streamlit App
def main():
    st.set_page_config(
        page_title="North Atlantic Plastic Drift Simulator",
        page_icon="🌊",
        layout="wide"
    )
    
    # Custom CSS for dark theme
    st.markdown("""
        <style>
        .stApp {
            background-color: #0a1e2e;
        }
        .metric-card {
            background-color: #163a52;
            padding: 15px;
            border-radius: 5px;
            border: 2px solid #00ffff;
            margin: 10px 0;
        }
        .status-high {
            background-color: #00ff00;
            color: black;
            padding: 5px 15px;
            border-radius: 15px;
            font-weight: bold;
        }
        .status-medium {
            background-color: #ffaa00;
            color: black;
            padding: 5px 15px;
            border-radius: 15px;
            font-weight: bold;
        }
        .status-low {
            background-color: #ff6b6b;
            color: white;
            padding: 5px 15px;
            border-radius: 15px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🌊 North Atlantic Plastic Drift Simulator")
    st.markdown("*Synthetic demo for presentation, not scientific output*")
    
    # Load seeds
    with open(SEEDS_FILE, 'r') as f:
        seeds = json.load(f)
    
    simulator = PlasticDriftSimulator(seeds)
    visualizer = Visualizer(simulator)
    
    # Sidebar for city selection
    st.sidebar.header("🎯 City Selection")
    
    city_names = [s['city'] for s in seeds]
    
    # Dropdown
    selected_city_dropdown = st.sidebar.selectbox(
        "Choose a city from dropdown:",
        options=[""] + city_names,
        index=0
    )
    
    # Type-to-search
    city_search = st.sidebar.text_input(
        "Or type to search:",
        placeholder="e.g., New York, Lisbon, Chicago"
    )
    
    # Determine which city to use
    if city_search:
        city_data = simulator.find_city(city_search)
        if city_data:
            selected_city = city_data['city']
            if city_search.lower() not in selected_city.lower():
                st.sidebar.info(f"💡 Did you mean: **{selected_city}**?")
        else:
            st.sidebar.error("❌ City not found. Try another name.")
            selected_city = None
    elif selected_city_dropdown:
        selected_city = selected_city_dropdown
    else:
        selected_city = None
    
    if selected_city:
        city_data = simulator.city_lookup[selected_city]
        
        st.sidebar.success(f"✅ Selected: **{selected_city}**")
        st.sidebar.markdown(f"**Type:** {city_data['type'].title()}")
        st.sidebar.markdown(f"**Region:** {city_data['region'].upper()}")
        
        # Initialize session state
        if 'simulation_data' not in st.session_state or st.session_state.get('current_city') != selected_city:
            st.session_state.simulation_data = None
            st.session_state.current_city = selected_city
            st.session_state.current_frame = 0
            st.session_state.is_playing = False
        
        # Run simulation button
        if st.sidebar.button("🚀 Run Simulation", type="primary"):
            with st.spinner(f"Simulating {selected_city}..."):
                progress_bar = st.progress(0)
                
                def update_progress(pct):
                    progress_bar.progress(pct)
                
                start_lat, start_lon = simulator.route_inland_to_ocean(city_data)
                trajectories, beached = simulator.simulate_particles(
                    start_lat, start_lon, progress_callback=update_progress
                )
                metrics = simulator.calculate_metrics(trajectories, beached, city_data)
                
                st.session_state.simulation_data = {
                    'trajectories': trajectories,
                    'beached': beached,
                    'metrics': metrics,
                    'city_data': city_data
                }
                st.session_state.current_frame = 0
                progress_bar.empty()
            
            st.success("✅ Simulation complete!")
        
        # Display results if simulation has been run
        if st.session_state.simulation_data:
            data = st.session_state.simulation_data
            metrics = data['metrics']
            
            # Metrics display
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_class = f"status-{metrics['prob_class'].lower()}"
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>Ocean Reach</h3>
                        <div class="{status_class}">{metrics['prob_class']}</div>
                        <p>{metrics['ocean_reach_prob']:.1%}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>Median Distance</h3>
                        <h2 style="color: #00ffff;">{metrics['median_distance_km']:,.0f} km</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3>Particles</h3>
                        <h2 style="color: #00ffff;">{N_PARTICLES}</h2>
                        <p>Beached: {metrics['beached']:.1%}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            # Playback controls
            st.markdown("---")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            n_frames = 60
            max_frame = n_frames - 1
            
            with col1:
                if st.button("▶️ Play" if not st.session_state.is_playing else "⏸️ Pause"):
                    st.session_state.is_playing = not st.session_state.is_playing
            
            with col2:
                if st.button("🔄 Reset"):
                    st.session_state.current_frame = 0
                    st.session_state.is_playing = False
            
            with col3:
                if st.button("💾 Export MP4"):
                    with st.spinner("Exporting MP4..."):
                        frames = []
                        frame_skip = max(1, TOTAL_STEPS // n_frames)
                        
                        progress_bar = st.progress(0)
                        for idx, step in enumerate(range(0, TOTAL_STEPS, frame_skip)):
                            fig = visualizer.render_frame(
                                data['trajectories'], data['beached'], 
                                step, data['city_data']['city'], metrics
                            )
                            
                            fig.canvas.draw()
                            image = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
                            image = image.reshape(fig.canvas.get_width_height()[::-1] + (4,))
                            frames.append(image[:, :, :3])
                            plt.close(fig)
                            
                            progress_bar.progress((idx + 1) / n_frames)
                        
                        mp4_path = OUTPUT_DIR / f"drift_{selected_city.replace(' ', '_').replace(',', '').lower()}.mp4"
                        imageio.mimsave(mp4_path, frames, fps=20, codec='libx264', quality=8)
                        
                        progress_bar.empty()
                        st.success(f"✅ Saved: {mp4_path}")
            
            with col4:
                if st.button("🎨 Export GIF"):
                    with st.spinner("Exporting GIF..."):
                        frames = []
                        frame_skip = max(1, TOTAL_STEPS // (n_frames // 2))
                        
                        progress_bar = st.progress(0)
                        for idx, step in enumerate(range(0, TOTAL_STEPS, frame_skip)):
                            fig = visualizer.render_frame(
                                data['trajectories'], data['beached'],
                                step, data['city_data']['city'], metrics
                            )
                            
                            fig.canvas.draw()
                            image = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
                            image = image.reshape(fig.canvas.get_width_height()[::-1] + (4,))
                            frames.append(image[:, :, :3])
                            plt.close(fig)
                            
                            progress_bar.progress((idx + 1) / (n_frames // 2))
                        
                        gif_path = OUTPUT_DIR / f"drift_{selected_city.replace(' ', '_').replace(',', '').lower()}.gif"
                        imageio.mimsave(gif_path, frames, fps=10, loop=0)
                        
                        progress_bar.empty()
                        st.success(f"✅ Saved: {gif_path}")
            
            # Frame slider
            frame_slider = st.slider(
                "Simulation Progress",
                0, max_frame,
                st.session_state.current_frame,
                format=f"Year %d / {YEARS}"
            )
            
            if frame_slider != st.session_state.current_frame:
                st.session_state.current_frame = frame_slider
            
            # Auto-play
            if st.session_state.is_playing:
                st.session_state.current_frame = (st.session_state.current_frame + 1) % (max_frame + 1)
                time.sleep(0.1)
                st.rerun()
            
            # Render current frame
            frame_skip = max(1, TOTAL_STEPS // n_frames)
            current_step = st.session_state.current_frame * frame_skip
            
            with st.spinner("Rendering..."):
                fig = visualizer.render_frame(
                    data['trajectories'], data['beached'],
                    current_step, data['city_data']['city'], metrics
                )
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
    
    else:
        st.info("👆 Select a city from the sidebar to begin")
        
        # Show available cities
        st.subheader("Available Cities")
        
        regions = {}
        for seed in seeds:
            region = seed['region']
            if region not in regions:
                regions[region] = []
            regions[region].append(seed['city'])
        
        cols = st.columns(len(regions))
        for idx, (region, cities) in enumerate(sorted(regions.items())):
            with cols[idx]:
                st.markdown(f"**{region.upper()}**")
                for city in sorted(cities):
                    st.markdown(f"- {city}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
        **Note:** This is a presentation demo using simplified physics.  
        Not for scientific research or policy decisions.  
        *Cartopy basemap: {}*
    """.format("✅ Enabled" if CARTOPY_AVAILABLE else "❌ Using fallback"))


if __name__ == "__main__":
    main()
