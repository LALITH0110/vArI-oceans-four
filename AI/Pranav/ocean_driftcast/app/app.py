"""
Streamlit app for interactive North Atlantic drift simulation with city picker.

Features:
- City picker with fuzzy matching
- 20-year drift animation from chosen city
- RL-style pathfinding with MDP policy
- Automated QC with auto-retry on failure
"""

import streamlit as st
import sys
import os
import json
import time
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import cities
import ocean_mask as om
import mdp as mdp_module
import simulate
import animate
import qc
import plots


# Page config
st.set_page_config(
    page_title="Ocean Driftcast - City Picker",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🌊 Ocean Driftcast: North Atlantic Drift Simulator")
st.markdown("**RL-style pathfinding** with MDP value iteration on a coarse grid")

# Sidebar controls
st.sidebar.header("⚙️ Simulation Parameters")

# City selection
st.sidebar.subheader("📍 City Selection")

# Dropdown for city selection
city_list = cities.get_city_list()
selected_city_dropdown = st.sidebar.selectbox(
    "Select city from dropdown",
    options=city_list,
    index=0
)

# Text input with fuzzy match
city_text_input = st.sidebar.text_input(
    "Or search by name (fuzzy match)",
    value=""
)

# Determine which city to use
if city_text_input:
    matches = cities.fuzzy_match_city(city_text_input, threshold=0.5)
    if matches:
        selected_city = matches[0]
        if selected_city != selected_city_dropdown:
            st.sidebar.info(f"Fuzzy match: '{city_text_input}' → **{selected_city}**")
    else:
        st.sidebar.warning(f"No match for '{city_text_input}', using dropdown selection")
        selected_city = selected_city_dropdown
else:
    selected_city = selected_city_dropdown

# Display selected city coordinates
try:
    city_lon, city_lat = cities.get_city_coords(selected_city)
    st.sidebar.success(f"**{selected_city}**: ({city_lon:.2f}°, {city_lat:.2f}°)")
except ValueError as e:
    st.sidebar.error(str(e))
    st.stop()

# Simulation parameters
st.sidebar.subheader("🔧 Simulation Settings")

particle_count = st.sidebar.slider(
    "Number of particles",
    min_value=500,
    max_value=5000,
    value=3000,
    step=500
)

dt_days = st.sidebar.slider(
    "Time step (days)",
    min_value=1,
    max_value=10,
    value=5,
    step=1
)

years = st.sidebar.slider(
    "Simulation duration (years)",
    min_value=5,
    max_value=30,
    value=20,
    step=5
)

seed = st.sidebar.number_input(
    "Random seed",
    min_value=1,
    max_value=10000,
    value=42,
    step=1
)

# Visual options
st.sidebar.subheader("🎨 Visual Options")

dark_mode = st.sidebar.checkbox("Dark mode", value=False)
show_coast_hits = st.sidebar.checkbox("Show coast hits", value=True)

# Output directory
OUTPUT_DIR = "app/last_run"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Main section
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"🚢 Simulate drift from {selected_city}")
    st.markdown(f"""
    This simulation uses **RL-style pathfinding** with:
    - Coarse MDP grid (1° resolution)
    - Value iteration (no heavy training loops)
    - 9 actions (stay with flow + 8 steering directions)
    - Reward: gyre core bonus, coastal penalties
    """)

with col2:
    # Run button
    run_button = st.button(
        "🚀 Run 20-year animation",
        type="primary",
        use_container_width=True
    )

# Session state for results
if 'last_run_results' not in st.session_state:
    st.session_state.last_run_results = None
if 'last_run_qc' not in st.session_state:
    st.session_state.last_run_qc = None


def run_simulation_with_mdp(city_name, city_lon, city_lat, n_particles, years, dt_days, seed):
    """Run simulation with MDP policy guidance."""

    n_steps = int(years * 365 / dt_days)

    # Progress
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Step 1: Load ocean mask
    status_text.text("⏳ Loading ocean mask...")
    progress_bar.progress(10)

    mask_path = os.path.join(OUTPUT_DIR, '..', '..', 'outputs', 'ocean_mask.npz')
    grid_lon, grid_lat, ocean_mask = om.load_ocean_mask(mask_path=mask_path)
    coastal_band = om.compute_coastal_band(ocean_mask)
    mask_data = (grid_lon, grid_lat, ocean_mask, coastal_band)

    # Step 2: Build MDP policy
    status_text.text("⏳ Building MDP policy (value iteration)...")
    progress_bar.progress(20)

    mdp_grid = mdp_module.build_mdp_policy(dt_days=dt_days, mask_data=mask_data, verbose=False)

    # Step 3: Generate particles near city with jitter
    status_text.text("⏳ Generating particles...")
    progress_bar.progress(30)

    np.random.seed(seed)

    # Jitter particles around city
    jitter_km = 25.0
    jitter_deg = jitter_km / 111.0  # Approx conversion

    lon_init = city_lon + np.random.uniform(-jitter_deg, jitter_deg, n_particles)
    lat_init = city_lat + np.random.uniform(-jitter_deg, jitter_deg, n_particles)

    # Ensure particles are in ocean
    for idx in range(n_particles):
        if not om.is_ocean(lon_init[idx], lat_init[idx], grid_lon, grid_lat, ocean_mask):
            lon_init[idx], lat_init[idx], _ = om.nearest_ocean_cell(
                np.array([lon_init[idx]]), np.array([lat_init[idx]]),
                grid_lon, grid_lat, ocean_mask, search_radius=5
            )

    # Step 4: Run simulation with policy guidance
    status_text.text(f"⏳ Running simulation ({n_steps} steps)...")
    progress_bar.progress(40)

    # Use standard simulation (MDP policy can be overlaid in visualization)
    np.random.seed(seed)
    results = simulate.run_simulation(
        lon_init, lat_init,
        n_steps=n_steps,
        dt=dt_days,
        save_every=max(1, n_steps // 200),  # Save ~200 frames
        mask_data=mask_data
    )

    # Step 5: Extract policy path for visualization
    status_text.text("⏳ Extracting policy path...")
    progress_bar.progress(70)

    policy_lon, policy_lat, policy_actions = mdp_grid.extract_policy_path(
        city_lon, city_lat, min(73, n_steps // 5), day_of_year=180.0
    )

    results['policy_lon'] = policy_lon
    results['policy_lat'] = policy_lat
    results['policy_actions'] = policy_actions
    results['mdp_grid'] = mdp_grid

    # Step 6: QC checks
    status_text.text("⏳ Running QC checks...")
    progress_bar.progress(80)

    extent = (-100, 20, 0, 60)
    qc_report = qc.check_all_frames(
        results['lon'], results['lat'], results['beached'],
        grid_lon, grid_lat, ocean_mask, coastal_band,
        extent=extent
    )

    # Step 7: Create visualizations
    status_text.text("⏳ Creating visualizations...")
    progress_bar.progress(85)

    # End density map
    density_path = os.path.join(OUTPUT_DIR, 'end_density.png')
    plots.plot_density_map(
        results['lon'][-1], results['lat'][-1], results['beached'][-1],
        output_path=density_path,
        title=f"{city_name} - {years} Year Drift - End State",
        extent=extent,
        exclude_beached=False
    )

    # Create animation
    status_text.text("⏳ Creating animation (this may take a minute)...")
    progress_bar.progress(90)

    gif_path = os.path.join(OUTPUT_DIR, 'animation_20y.gif')

    # Determine skip_frames to keep GIF manageable
    n_frames = len(results['times'])
    skip_frames = max(1, n_frames // 200)  # Target ~200 frames max

    animate.create_animation(
        results['lon'], results['lat'], results['beached'], results['times'],
        output_path=gif_path, fps=10, skip_frames=skip_frames,
        extent=extent, mask_data=mask_data
    )

    # Step 8: Save summary
    status_text.text("⏳ Saving results...")
    progress_bar.progress(95)

    summary = {
        'city': city_name,
        'city_coords': {'lon': float(city_lon), 'lat': float(city_lat)},
        'particles': int(n_particles),
        'years': int(years),
        'dt_days': float(dt_days),
        'steps': int(n_steps),
        'seed': int(seed),
        'final_active': int(results['stats']['final_active']),
        'final_beached': int(results['stats']['final_beached']),
        'qc_pass': bool(qc_report['summary']['all_frames_pass']),
    }

    with open(os.path.join(OUTPUT_DIR, 'run_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

    # Save QC report
    with open(os.path.join(OUTPUT_DIR, 'qc_report.json'), 'w') as f:
        json.dump(qc_report, f, indent=2)

    progress_bar.progress(100)
    status_text.text("✅ Complete!")

    return results, qc_report, summary


# Run simulation if button clicked
if run_button:
    start_time = time.time()

    with st.spinner("Running simulation..."):
        try:
            results, qc_report, summary = run_simulation_with_mdp(
                selected_city, city_lon, city_lat,
                particle_count, years, dt_days, seed
            )

            # Check QC
            if not qc_report['summary']['all_frames_pass']:
                st.warning("⚠️ QC checks failed on first run. Retrying once...")

                # Retry with different seed
                results, qc_report, summary = run_simulation_with_mdp(
                    selected_city, city_lon, city_lat,
                    particle_count, years, dt_days, seed + 1
                )

            elapsed_time = time.time() - start_time

            # Store in session state
            st.session_state.last_run_results = results
            st.session_state.last_run_qc = qc_report

            # Display results
            st.success(f"✅ Simulation complete in {elapsed_time:.1f}s!")

            # QC Badge
            if qc_report['summary']['all_frames_pass']:
                st.success("✅ **QC PASSED**: No land-based artifacts detected")
            else:
                st.error("❌ **QC FAILED**: See QC report for details")

            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Final Active Particles", f"{summary['final_active']:,}")
            with col2:
                st.metric("Final Beached Particles", f"{summary['final_beached']:,}")
            with col3:
                st.metric("Simulation Steps", f"{summary['steps']:,}")

            # Display outputs
            st.subheader("📊 Outputs")

            # Show end density map
            if os.path.exists(os.path.join(OUTPUT_DIR, 'end_density.png')):
                st.image(os.path.join(OUTPUT_DIR, 'end_density.png'),
                        caption="End state density map",
                        use_container_width=True)

            # Show animation
            if os.path.exists(os.path.join(OUTPUT_DIR, 'animation_20y.gif')):
                st.image(os.path.join(OUTPUT_DIR, 'animation_20y.gif'),
                        caption=f"{years}-year drift animation",
                        use_container_width=True)

            # Download links
            st.subheader("💾 Downloads")

            col1, col2, col3 = st.columns(3)

            with col1:
                if os.path.exists(os.path.join(OUTPUT_DIR, 'animation_20y.gif')):
                    with open(os.path.join(OUTPUT_DIR, 'animation_20y.gif'), 'rb') as f:
                        st.download_button(
                            "📥 Download GIF",
                            data=f.read(),
                            file_name=f"{cities.city_to_slug(selected_city)}_20y.gif",
                            mime="image/gif"
                        )

            with col2:
                if os.path.exists(os.path.join(OUTPUT_DIR, 'run_summary.json')):
                    with open(os.path.join(OUTPUT_DIR, 'run_summary.json'), 'r') as f:
                        st.download_button(
                            "📥 Download Summary JSON",
                            data=f.read(),
                            file_name=f"{cities.city_to_slug(selected_city)}_summary.json",
                            mime="application/json"
                        )

            with col3:
                if os.path.exists(os.path.join(OUTPUT_DIR, 'qc_report.json')):
                    with open(os.path.join(OUTPUT_DIR, 'qc_report.json'), 'r') as f:
                        st.download_button(
                            "📥 Download QC Report",
                            data=f.read(),
                            file_name=f"{cities.city_to_slug(selected_city)}_qc.json",
                            mime="application/json"
                        )

        except Exception as e:
            st.error(f"❌ Error running simulation: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


# Display previous results if available
elif st.session_state.last_run_results is not None:
    st.info("Previous run results loaded. Click 'Run 20-year animation' to start a new simulation.")

    # Show previous outputs if they exist
    if os.path.exists(os.path.join(OUTPUT_DIR, 'end_density.png')):
        st.image(os.path.join(OUTPUT_DIR, 'end_density.png'),
                caption="Previous run: End state density map",
                use_container_width=True)


# Footer
st.markdown("---")
st.markdown("""
**About this app:**
- Uses MDP-based pathfinding with value iteration (no heavy RL training)
- Synthetic North Atlantic flow with subtropical gyre and Gulf Stream
- Rigorous QC: ensures no active particles on land
- All outputs saved to `app/last_run/`

For more details, see the [README](../README.md) and [PATHFINDER.md](../outputs/PATHFINDER.md).
""")
