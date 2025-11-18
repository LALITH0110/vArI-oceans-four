"""
Synthetic demo for presentation, not scientific output.

Animation export system for creating looping MP4 and GIF visualizations.
"""

import numpy as np
import os
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
from PIL import Image
import io

from physics import OceanPhysics
from particles import ParticleSystem, create_particle_system_from_city
from visualization import OceanDriftVisualizer


class AnimationExporter:
    """
    Export animations as MP4 and GIF with multi-chapter structure.
    """

    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize animation exporter.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_chapter(self, city_data: Dict, n_particles: int, n_steps: int,
                      fps: int = 30, quality: str = 'high') -> Tuple[ParticleSystem, List[Image.Image]]:
        """
        Create a single animation chapter for a city.

        Args:
            city_data: City dictionary from seeds.json
            n_particles: Number of particles
            n_steps: Number of simulation steps
            fps: Frames per second
            quality: 'low', 'medium', or 'high'

        Returns:
            ParticleSystem and list of PIL Images
        """
        print(f"Creating chapter for {city_data['city']}...")

        # Create physics and particle system
        physics = OceanPhysics(seed=42)
        particles = create_particle_system_from_city(physics, city_data, n_particles)

        # Run simulation
        print(f"  Simulating {n_steps} steps...")
        particles.simulate(n_steps)

        # Generate frames
        print(f"  Rendering frames...")
        frames = []
        visualizer = OceanDriftVisualizer(figsize=(20, 12), dpi=100 if quality == 'high' else 72)

        # Determine frame sampling based on FPS and duration
        total_frames = fps * 60  # 60 seconds per chapter minimum
        step_interval = max(1, n_steps // total_frames)

        for i in range(0, n_steps, step_interval):
            if i % 20 == 0:
                print(f"    Frame {i}/{n_steps}")

            # Render frame
            fig = visualizer.render_frame(
                particles,
                city_data['city'],
                i,
                show_trajectories=True,
                show_particles=True,
                traj_subsample=5 if quality == 'high' else 10
            )

            # Convert to PIL Image
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100 if quality == 'high' else 72,
                       facecolor='#0a1e2e', bbox_inches='tight')
            buf.seek(0)
            img = Image.open(buf).copy()
            frames.append(img)
            buf.close()

            visualizer.close()

        print(f"  Generated {len(frames)} frames")

        return particles, frames

    def create_multi_chapter_animation(self, chapters: List[Dict], output_name: str = "drift_demo",
                                      n_particles: int = 5000, chapter_duration_weeks: int = 300,
                                      fps: int = 30, quality: str = 'high'):
        """
        Create multi-chapter looping animation.

        Args:
            chapters: List of city data dictionaries
            output_name: Base name for output files
            n_particles: Particles per chapter
            chapter_duration_weeks: Simulation weeks per chapter
            fps: Frames per second
            quality: 'low', 'medium', or 'high'
        """
        all_frames = []
        all_metrics = []

        for chapter_data in chapters:
            particles, frames = self.create_chapter(
                chapter_data,
                n_particles=n_particles,
                n_steps=chapter_duration_weeks,
                fps=fps,
                quality=quality
            )

            all_frames.extend(frames)

            # Collect metrics
            metrics = particles.get_metrics()
            metrics['city'] = chapter_data['city']
            all_metrics.append(metrics)

        # Save frames as MP4 using imageio
        print("\nExporting MP4...")
        self.save_mp4(all_frames, f"{output_name}.mp4", fps=fps)

        # Save as GIF
        print("Exporting GIF...")
        self.save_gif(all_frames, f"{output_name}.gif", fps=fps // 2, optimize=True)

        # Save metrics
        print("Saving metrics...")
        self.save_metrics(all_metrics, f"{output_name}_metrics.json")

        # Save sample snapshots
        print("Saving snapshots...")
        self.save_snapshots(all_frames, output_name, n_snapshots=10)

        print(f"\nAnimation export complete!")
        print(f"  Total frames: {len(all_frames)}")
        print(f"  Duration: {len(all_frames)/fps:.1f} seconds")
        print(f"  Output directory: {self.output_dir}")

    def save_mp4(self, frames: List[Image.Image], filename: str, fps: int = 30):
        """
        Save frames as MP4 video.

        Args:
            frames: List of PIL Images
            filename: Output filename
            fps: Frames per second
        """
        try:
            import imageio
            output_path = os.path.join(self.output_dir, filename)

            # Convert PIL images to numpy arrays
            frame_arrays = [np.array(frame) for frame in frames]

            # Write video
            imageio.mimsave(output_path, frame_arrays, fps=fps, codec='libx264', quality=8)
            print(f"  Saved: {output_path}")
        except ImportError:
            print("  Warning: imageio not available, skipping MP4 export")
            print("  Install with: pip install imageio[ffmpeg]")

    def save_gif(self, frames: List[Image.Image], filename: str, fps: int = 15, optimize: bool = True):
        """
        Save frames as animated GIF.

        Args:
            frames: List of PIL Images
            filename: Output filename
            fps: Frames per second
            optimize: Whether to optimize GIF size
        """
        output_path = os.path.join(self.output_dir, filename)

        # Downsample frames for GIF to reduce size
        if len(frames) > 300:
            step = len(frames) // 300
            frames = frames[::step]

        # Resize frames for smaller GIF
        resized_frames = []
        for frame in frames:
            # Resize to 50% for GIF
            new_size = (frame.width // 2, frame.height // 2)
            resized = frame.resize(new_size, Image.Resampling.LANCZOS)
            resized_frames.append(resized)

        # Save
        duration = int(1000 / fps)  # milliseconds per frame
        resized_frames[0].save(
            output_path,
            save_all=True,
            append_images=resized_frames[1:],
            duration=duration,
            loop=0,
            optimize=optimize
        )
        print(f"  Saved: {output_path}")

    def save_snapshots(self, frames: List[Image.Image], base_name: str, n_snapshots: int = 10):
        """
        Save sample snapshots from animation.

        Args:
            frames: List of PIL Images
            base_name: Base name for files
            n_snapshots: Number of snapshots to save
        """
        snapshot_dir = os.path.join(self.output_dir, "snapshots")
        os.makedirs(snapshot_dir, exist_ok=True)

        indices = np.linspace(0, len(frames) - 1, n_snapshots, dtype=int)

        for i, idx in enumerate(indices):
            filename = f"{base_name}_snapshot_{i:03d}.png"
            output_path = os.path.join(snapshot_dir, filename)
            frames[idx].save(output_path)

        print(f"  Saved {n_snapshots} snapshots to {snapshot_dir}")

    def save_metrics(self, metrics: List[Dict], filename: str):
        """
        Save metrics as JSON.

        Args:
            metrics: List of metric dictionaries
            filename: Output filename
        """
        import json

        output_path = os.path.join(self.output_dir, filename)

        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)

        print(f"  Saved: {output_path}")


def create_demo_animation(seeds_file: str = "seeds.json", output_dir: str = "outputs"):
    """
    Create the full demo animation with 3 chapters.

    Args:
        seeds_file: Path to seeds.json
        output_dir: Output directory
    """
    import json

    # Load seeds
    with open(seeds_file, 'r') as f:
        seeds = json.load(f)

    # Find cities for the 3 chapters
    cities_dict = {city['city']: city for city in seeds}

    # Chapter 1: New York (high probability, captured by gyre)
    # Chapter 2: Lisbon (medium-high, recirculation)
    # Chapter 3: Chicago (low probability, long distance)

    chapters = [
        cities_dict.get('New York, NY, USA', seeds[0]),
        cities_dict.get('Lisbon, Portugal', seeds[12]),
        cities_dict.get('Chicago, IL, USA', seeds[3])
    ]

    # Create exporter
    exporter = AnimationExporter(output_dir=output_dir)

    # Create animation
    # For demo: 300 weeks (~6 years) per chapter, 3 chapters = 18 years total
    # This is scaled down from 20 years for faster rendering
    exporter.create_multi_chapter_animation(
        chapters=chapters,
        output_name="drift_demo",
        n_particles=3000,  # Reduced for performance
        chapter_duration_weeks=300,  # ~6 years per chapter
        fps=30,
        quality='high'
    )


if __name__ == "__main__":
    create_demo_animation()
