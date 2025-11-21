"""
Synthetic demo for presentation, not scientific output.

Interactive UI for ocean drift visualization with city search and playback controls.
"""

import json
import numpy as np
from typing import Dict, List, Optional
from difflib import get_close_matches

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider, TextBox
import matplotlib.animation as animation

from physics import OceanPhysics
from particles import ParticleSystem, create_particle_system_from_city
from visualization import OceanDriftVisualizer
from combobox import ComboBox


class InteractiveUI:
    """
    Interactive visualization UI with city search and playback controls.
    """

    def __init__(self, seeds_file: str = "seeds.json"):
        """
        Initialize interactive UI.

        Args:
            seeds_file: Path to seeds.json
        """
        # Load city data
        with open(seeds_file, 'r') as f:
            self.cities = json.load(f)

        self.city_names = [city['city'] for city in self.cities]
        self.city_dict = {city['city']: city for city in self.cities}

        # Simulation state
        self.physics = OceanPhysics(seed=42)
        self.particle_system: Optional[ParticleSystem] = None
        self.current_city: Optional[str] = None

        # Playback state
        self.current_step = 0
        self.is_playing = False
        self.speed = 1  # Speed multiplier
        self.max_steps = 1040  # 20 years

        # Visualization
        self.visualizer = OceanDriftVisualizer(figsize=(18, 10), dpi=90)
        self.fig = None
        self.anim = None

        # UI widgets
        self.widgets = {}

    def find_city(self, search_text: str) -> Optional[Dict]:
        """
        Fuzzy search for city.

        Args:
            search_text: Search query

        Returns:
            City data dict or None
        """
        if not search_text:
            return None

        # Exact match
        if search_text in self.city_dict:
            return self.city_dict[search_text]

        # Fuzzy match
        matches = get_close_matches(search_text, self.city_names, n=1, cutoff=0.3)

        if matches:
            return self.city_dict[matches[0]]

        # Partial match (case insensitive)
        search_lower = search_text.lower()
        for city_name in self.city_names:
            if search_lower in city_name.lower():
                return self.city_dict[city_name]

        return None

    def load_city(self, city_name: str, n_particles: int = 5000):
        """
        Load and simulate a city.

        Args:
            city_name: City name to search
            n_particles: Number of particles
        """
        city_data = self.find_city(city_name)

        if city_data is None:
            print(f"City '{city_name}' not found. Try: {', '.join(self.city_names[:5])}, ...")
            return

        print(f"\nLoading: {city_data['city']}")
        print(f"  Spawning {n_particles} particles...")

        # Create particle system
        self.particle_system = create_particle_system_from_city(
            self.physics, city_data, n_particles
        )

        self.current_city = city_data['city']

        # Run simulation
        print(f"  Simulating {self.max_steps} weeks (20 years)...")

        def progress_callback(step, particles):
            if step % 100 == 0:
                print(f"    Step {step}/{self.max_steps}")

        self.particle_system.simulate(self.max_steps, callback=progress_callback)

        # Display metrics
        metrics = self.particle_system.get_metrics()
        prob_cat = self.particle_system.get_probability_category()

        print(f"\n  Results:")
        print(f"    Probability: {prob_cat} ({metrics['ocean_reach_prob']:.1%})")
        print(f"    Median distance: {metrics['median_distance_km']:,.0f} km")
        print(f"    Beached: {metrics['n_beached']} / {metrics['n_particles']}")

        # Reset playback
        self.current_step = 0
        self.is_playing = False

    def setup_ui(self):
        """
        Setup interactive UI with controls.
        """
        # Create figure with controls area
        self.fig = plt.figure(figsize=(18, 10), facecolor='#0a1e2e')

        # Main visualization area
        ax_main = plt.axes([0.05, 0.15, 0.9, 0.8])
        self.visualizer.ax = ax_main
        self.visualizer.fig = self.fig

        # Control panel area
        ax_color = '#0f3548'
        text_color = 'white'

        # City picker label
        ax_label = plt.axes([0.05, 0.05, 0.08, 0.04])
        ax_label.set_facecolor('#0a1e2e')
        ax_label.axis('off')
        ax_label.text(0.5, 0.5, 'City:', ha='center', va='center',
                     color=text_color, fontsize=10, weight='bold')

        # City picker combobox (dropdown + type-ahead)
        ax_combobox = plt.axes([0.13, 0.05, 0.22, 0.04])
        ax_dropdown_btn = plt.axes([0.35, 0.05, 0.03, 0.04])

        self.widgets['combobox'] = ComboBox(
            ax_combobox,
            ax_dropdown_btn,
            options=self.city_names,
            on_select=self.on_city_selected,
            initial_text='New York, NY, USA'
        )

        # Plain text input for quick paste (linked to same handler)
        ax_textbox = plt.axes([0.13, 0.095, 0.22, 0.04])
        ax_textbox.set_facecolor(ax_color)
        self.widgets['textbox'] = TextBox(
            ax_textbox, 'Quick:',
            initial='',
            color=ax_color,
            hovercolor='#1a4a5f',
            label_pad=0.01
        )
        self.widgets['textbox'].label.set_color(text_color)
        self.widgets['textbox'].text_disp.set_color(text_color)
        self.widgets['textbox'].on_submit(self.on_city_selected)

        # Load button (manual trigger)
        ax_load = plt.axes([0.39, 0.05, 0.08, 0.04])
        self.widgets['btn_load'] = Button(
            ax_load, 'Load City',
            color=ax_color, hovercolor='#00d9ff'
        )
        self.widgets['btn_load'].label.set_color(text_color)

        # Play/Pause button
        ax_play = plt.axes([0.48, 0.05, 0.06, 0.04])
        self.widgets['btn_play'] = Button(
            ax_play, 'Play',
            color=ax_color, hovercolor='#00d9ff'
        )
        self.widgets['btn_play'].label.set_color(text_color)

        # Pause button (separate for clarity)
        ax_pause = plt.axes([0.55, 0.05, 0.06, 0.04])
        self.widgets['btn_pause'] = Button(
            ax_pause, 'Pause',
            color=ax_color, hovercolor='#00d9ff'
        )
        self.widgets['btn_pause'].label.set_color(text_color)

        # Reset button
        ax_reset = plt.axes([0.62, 0.05, 0.06, 0.04])
        self.widgets['btn_reset'] = Button(
            ax_reset, 'Reset',
            color=ax_color, hovercolor='#00d9ff'
        )
        self.widgets['btn_reset'].label.set_color(text_color)

        # Speed slider with explicit 1x, 5x, 20x markers
        ax_speed = plt.axes([0.70, 0.055, 0.13, 0.03])
        ax_speed.set_facecolor(ax_color)
        self.widgets['slider_speed'] = Slider(
            ax_speed, 'Speed',
            valmin=1, valmax=20, valinit=1, valstep=[1, 5, 20],
            color='#00d9ff', track_color=ax_color
        )
        self.widgets['slider_speed'].label.set_color(text_color)
        self.widgets['slider_speed'].valtext.set_color(text_color)

        # Export GIF button
        ax_export_gif = plt.axes([0.85, 0.05, 0.06, 0.04])
        self.widgets['btn_export_gif'] = Button(
            ax_export_gif, 'Save GIF',
            color=ax_color, hovercolor='#00d9ff'
        )
        self.widgets['btn_export_gif'].label.set_color(text_color)

        # Export MP4 button
        ax_export_mp4 = plt.axes([0.92, 0.05, 0.06, 0.04])
        self.widgets['btn_export_mp4'] = Button(
            ax_export_mp4, 'Save MP4',
            color=ax_color, hovercolor='#00d9ff'
        )
        self.widgets['btn_export_mp4'].label.set_color(text_color)

        # Connect callbacks
        self.widgets['btn_load'].on_clicked(lambda event: self.on_load_city_button())
        self.widgets['btn_play'].on_clicked(lambda event: self.on_play())
        self.widgets['btn_pause'].on_clicked(lambda event: self.on_pause())
        self.widgets['btn_reset'].on_clicked(lambda event: self.on_reset())
        self.widgets['slider_speed'].on_changed(lambda val: self.on_speed_change(val))
        self.widgets['btn_export_gif'].on_clicked(lambda event: self.on_export_gif())
        self.widgets['btn_export_mp4'].on_clicked(lambda event: self.on_export_mp4())

        # Set up animation
        self.anim = animation.FuncAnimation(
            self.fig, self.update_frame,
            interval=50, blit=False, cache_frame_data=False
        )

    def on_city_selected(self, city_name: str):
        """
        Handle city selection from combobox or quick paste input.
        Immediately loads the city and renders initial particle cloud.

        Args:
            city_name: City name from dropdown or text input
        """
        print(f"\nCity selected: {city_name}")
        self.load_city(city_name)
        self.update_display()

    def on_load_city_button(self):
        """Handle manual load city button click."""
        # Try combobox first, then textbox
        city_name = self.widgets['combobox'].get_value()
        if not city_name.strip():
            city_name = self.widgets['textbox'].text

        if city_name.strip():
            self.on_city_selected(city_name)
        else:
            print("Please enter or select a city name")

    def on_play(self):
        """Handle play button click."""
        if self.particle_system is None:
            print("Load a city first!")
            return

        self.is_playing = True
        self.fig.canvas.draw_idle()

    def on_pause(self):
        """Handle pause button click."""
        self.is_playing = False
        self.fig.canvas.draw_idle()

    def on_reset(self):
        """Handle reset button click."""
        self.current_step = 0
        self.is_playing = False
        self.update_display()

    def on_speed_change(self, val):
        """Handle speed slider change."""
        self.speed = int(val)

    def on_export_gif(self):
        """Handle export GIF button click."""
        if self.particle_system is None:
            print("Load a city first!")
            return

        print("\nExporting GIF (this may take a few minutes)...")
        self.export_animation('gif')

    def on_export_mp4(self):
        """Handle export MP4 button click."""
        if self.particle_system is None:
            print("Load a city first!")
            return

        print("\nExporting MP4 (this may take a few minutes)...")
        self.export_animation('mp4')

    def export_animation(self, format: str = 'gif'):
        """
        Export current simulation as animation.

        Args:
            format: 'gif' or 'mp4'
        """
        import os
        from PIL import Image
        import io

        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)

        # Render all frames
        frames = []
        n_export_frames = min(300, self.max_steps // 3)  # Limit for size
        step_interval = self.max_steps // n_export_frames

        print(f"  Rendering {n_export_frames} frames...")

        for i in range(0, self.max_steps, step_interval):
            if i % 20 == 0:
                print(f"    Frame {i}/{self.max_steps}")

            # Create temporary visualizer for export
            export_viz = OceanDriftVisualizer(figsize=(16, 10), dpi=100)
            fig = export_viz.render_frame(
                self.particle_system,
                self.current_city,
                i,
                show_trajectories=True,
                show_particles=True,
                traj_subsample=8
            )

            # Convert to PIL Image
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, facecolor='#0a1e2e', bbox_inches='tight')
            buf.seek(0)
            img = Image.open(buf).copy()
            frames.append(img)
            buf.close()

            export_viz.close()

        # Save
        city_slug = self.current_city.replace(',', '').replace(' ', '_')

        if format == 'gif':
            output_path = os.path.join(output_dir, f"{city_slug}.gif")
            # Downsample for smaller file
            resized_frames = [f.resize((f.width // 2, f.height // 2), Image.Resampling.LANCZOS) for f in frames]
            resized_frames[0].save(
                output_path,
                save_all=True,
                append_images=resized_frames[1:],
                duration=50,
                loop=0,
                optimize=True
            )
            print(f"  Saved: {output_path}")

        elif format == 'mp4':
            try:
                import imageio
                output_path = os.path.join(output_dir, f"{city_slug}.mp4")
                frame_arrays = [np.array(frame) for frame in frames]
                imageio.mimsave(output_path, frame_arrays, fps=20, codec='libx264', quality=8)
                print(f"  Saved: {output_path}")
            except ImportError:
                print("  Error: imageio not available. Install with: pip install imageio[ffmpeg]")

    def update_frame(self, frame):
        """
        Animation update callback.

        Args:
            frame: Frame number (unused, we use internal state)
        """
        # Only update if playing
        if self.is_playing and self.particle_system is not None:
            self.current_step += self.speed

            # Loop at end
            if self.current_step >= len(self.particle_system.history_lat):
                self.current_step = 0

            self.update_display()

        return []

    def update_display(self):
        """Update visualization display."""
        if self.particle_system is None:
            return

        # Clear and redraw
        self.visualizer.fig.clear()

        # Recreate main axis
        ax_main = self.visualizer.fig.add_axes([0.05, 0.15, 0.9, 0.8], projection=None)

        # Need to setup cartopy axis properly
        import cartopy.crs as ccrs
        ax_main.remove()
        ax_main = self.visualizer.fig.add_axes(
            [0.05, 0.15, 0.9, 0.8],
            projection=ccrs.PlateCarree()
        )
        self.visualizer.ax = ax_main
        self.visualizer.ax.set_extent([-100, 20, 5, 65], crs=ccrs.PlateCarree())

        # Render current frame
        self.visualizer.setup_figure()
        self.visualizer.plot_gyre_background()

        # Plot trajectories up to current step
        traj_lat, traj_lon = self.particle_system.get_trajectory_arrays(subsample=1)
        traj_lat_truncated = [t[:self.current_step+1] for t in traj_lat]
        traj_lon_truncated = [t[:self.current_step+1] for t in traj_lon]
        self.visualizer.plot_trajectories(traj_lat_truncated, traj_lon_truncated, subsample=10, alpha=0.04)

        # Plot current particles
        if self.current_step < len(self.particle_system.history_lat):
            lat, lon, beached = self.particle_system.get_positions_at_step(self.current_step)
            self.visualizer.plot_particles(lat, lon, beached)

        # Add labels and info
        self.visualizer.add_labels()

        metrics = self.particle_system.get_metrics()
        prob_category = self.particle_system.get_probability_category()
        self.visualizer.add_info_card(
            city=self.current_city,
            probability=prob_category,
            distance_km=metrics['median_distance_km'],
            step=self.current_step,
            total_steps=len(self.particle_system.history_lat) - 1
        )

        self.visualizer.add_logo()
        self.visualizer.add_scale_bar()

        # Redraw canvas
        self.fig.canvas.draw_idle()

    def run(self):
        """
        Run interactive UI.
        """
        # Setup UI
        self.setup_ui()

        # Load default city
        self.load_city("New York")

        # Show
        plt.show()


def launch_interactive_ui(seeds_file: str = "seeds.json"):
    """
    Launch interactive UI.

    Args:
        seeds_file: Path to seeds.json
    """
    ui = InteractiveUI(seeds_file)
    ui.run()


if __name__ == "__main__":
    launch_interactive_ui()
