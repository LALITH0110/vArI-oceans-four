"""
Animation creation (GIF and MP4) for particle drift.

Uses PlateCarree projection consistently to avoid map transform errors.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import os

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False

try:
    from matplotlib.animation import FFMpegWriter
    HAS_FFMPEG = True
except (ImportError, RuntimeError):
    HAS_FFMPEG = False


def create_animation(lon_history, lat_history, beached_history, times,
                     output_path='animation.gif', fps=15,
                     extent=(-100, 20, 0, 60), skip_frames=1,
                     mask_data=None):
    """
    Create looping animation of particle drift.

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status history
    times : ndarray (n_times,)
        Time in days
    output_path : str
        Output file path (.gif or .mp4)
    fps : int
        Frames per second
    extent : tuple
        Map extent (lon_min, lon_max, lat_min, lat_max)
    skip_frames : int
        Use every Nth frame to reduce file size
    mask_data : tuple, optional
        (grid_lon, grid_lat, ocean_mask, coastal_band) for verification
    """
    print(f"Creating animation: {output_path}")

    n_times, n_particles = lon_history.shape

    # Subsample frames if needed
    frame_indices = np.arange(0, n_times, skip_frames)
    n_frames = len(frame_indices)

    print(f"  Frames: {n_frames}, Particles: {n_particles}")

    # Create figure with PlateCarree projection
    if HAS_CARTOPY:
        fig = plt.figure(figsize=(16, 12))
        ax = plt.axes(projection=ccrs.PlateCarree())
        data_transform = ccrs.PlateCarree()
    else:
        fig, ax = plt.subplots(figsize=(16, 12))
        data_transform = None

    # Setup base map
    if HAS_CARTOPY:
        ax.set_extent(extent, crs=ccrs.PlateCarree())

        # Land: light gray fill
        ax.add_feature(cfeature.LAND, facecolor='#d0d0d0', edgecolor='none',
                      linewidth=0, zorder=1)
        # Coastline: thin dark line on top
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='#404040',
                      zorder=3)

        # Ocean background
        ax.set_facecolor('#e6f2ff')  # Light blue ocean

        # Gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.4,
                         color='gray', linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
    else:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_xlabel('Longitude', fontsize=14)
        ax.set_ylabel('Latitude', fontsize=14)
        ax.set_facecolor('#e6f2ff')
        ax.grid(True, alpha=0.3, color='gray', linestyle='--')

    fig.patch.set_facecolor('white')

    # Initialize scatter plots with PlateCarree transform
    # Beached particles: small warm dots (below alive particles)
    if HAS_CARTOPY:
        scatter_beached = ax.scatter([], [], s=1.5, c='#ff6b4a', alpha=0.4,
                                    edgecolors='none', zorder=4,
                                    transform=data_transform)
        # Active particles: bright green/cyan with tiny white outline
        scatter_active = ax.scatter([], [], s=3, c='#00ff88', alpha=0.8,
                                   edgecolors='white', linewidths=0.2, zorder=5,
                                   transform=data_transform)
    else:
        scatter_beached = ax.scatter([], [], s=1.5, c='#ff6b4a', alpha=0.4,
                                    edgecolors='none', zorder=4)
        scatter_active = ax.scatter([], [], s=3, c='#00ff88', alpha=0.8,
                                   edgecolors='white', linewidths=0.2, zorder=5)

    # Title
    title = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                   fontsize=16, fontweight='bold', color='#000000',
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8,
                            edgecolor='gray', linewidth=1))

    def init():
        scatter_active.set_offsets(np.empty((0, 2)))
        scatter_beached.set_offsets(np.empty((0, 2)))
        title.set_text('')
        return scatter_active, scatter_beached, title

    def update(frame_idx):
        idx = frame_indices[frame_idx]
        t = times[idx]

        lon = lon_history[idx]
        lat = lat_history[idx]
        beached = beached_history[idx]

        # Active particles (never on land)
        active = ~beached
        if np.sum(active) > 0:
            points_active = np.column_stack([lon[active], lat[active]])
            scatter_active.set_offsets(points_active)
        else:
            scatter_active.set_offsets(np.empty((0, 2)))

        # Beached particles (at coastal cells only)
        if np.sum(beached) > 0:
            points_beached = np.column_stack([lon[beached], lat[beached]])
            scatter_beached.set_offsets(points_beached)
        else:
            scatter_beached.set_offsets(np.empty((0, 2)))

        # Update title
        n_active = np.sum(active)
        n_beached = np.sum(beached)
        title.set_text(f'North Atlantic Drift - Day {t:.0f}\n'
                      f'Active: {n_active:,} | Beached: {n_beached:,}')

        return scatter_active, scatter_beached, title

    # Create animation
    anim = FuncAnimation(fig, update, init_func=init,
                        frames=n_frames, interval=1000/fps,
                        blit=True, repeat=True)

    # Save
    ext = os.path.splitext(output_path)[1].lower()

    if ext == '.gif':
        writer = PillowWriter(fps=fps)
        anim.save(output_path, writer=writer)
    elif ext == '.mp4':
        if HAS_FFMPEG:
            writer = FFMpegWriter(fps=fps, bitrate=2000)
            anim.save(output_path, writer=writer)
        else:
            print("  WARNING: FFMpeg not available, saving as GIF instead")
            gif_path = output_path.replace('.mp4', '.gif')
            writer = PillowWriter(fps=fps)
            anim.save(gif_path, writer=writer)
            output_path = gif_path
    else:
        raise ValueError(f"Unknown format: {ext}. Use .gif or .mp4")

    plt.close(fig)

    print(f"  Saved: {output_path}")

    return output_path


def create_tiled_video(lon_history, lat_history, beached_history, times,
                       output_path='animation.mp4', target_minutes=7, fps=30,
                       extent=(-100, 20, 0, 60), mask_data=None):
    """
    Create MP4 by looping/tiling the simulation to reach target duration.

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status history
    times : ndarray (n_times,)
        Time in days
    output_path : str
        Output file path
    target_minutes : float
        Target video duration in minutes
    fps : int
        Frames per second
    extent : tuple
        Map extent
    mask_data : tuple, optional
        Mask data for verification
    """
    print(f"Creating tiled video: {output_path} (target: {target_minutes} min @ {fps} fps)")

    n_times = len(times)
    target_frames = int(target_minutes * 60 * fps)

    # Calculate how many loops we need
    n_loops = int(np.ceil(target_frames / n_times))
    print(f"  Will loop {n_loops} times to reach {target_frames} frames")

    # Tile the data
    lon_tiled = np.tile(lon_history, (n_loops, 1))[:target_frames]
    lat_tiled = np.tile(lat_history, (n_loops, 1))[:target_frames]
    beached_tiled = np.tile(beached_history, (n_loops, 1))[:target_frames]

    # Create times with offset for each loop
    times_tiled = []
    for loop in range(n_loops):
        offset = loop * times[-1]
        times_tiled.extend(times + offset)
    times_tiled = np.array(times_tiled[:target_frames])

    # Create animation
    create_animation(lon_tiled, lat_tiled, beached_tiled, times_tiled,
                    output_path=output_path, fps=fps, extent=extent,
                    skip_frames=1, mask_data=mask_data)

    actual_duration = len(times_tiled) / fps / 60
    print(f"  Video duration: {actual_duration:.2f} minutes")

    return output_path


def create_frame_image(lon, lat, beached, output_path, time_day,
                      extent=(-100, 20, 0, 60), mask_data=None):
    """
    Create a single frame as an image.

    Parameters
    ----------
    lon : ndarray
        Longitudes
    lat : ndarray
        Latitudes
    beached : ndarray (bool)
        Beached status
    output_path : str
        Output file path
    time_day : float
        Time in days for title
    extent : tuple
        Map extent
    mask_data : tuple, optional
        Mask data for verification
    """
    if HAS_CARTOPY:
        fig = plt.figure(figsize=(16, 12))
        ax = plt.axes(projection=ccrs.PlateCarree())
        data_transform = ccrs.PlateCarree()
    else:
        fig, ax = plt.subplots(figsize=(16, 12))
        data_transform = None

    # Setup base map
    if HAS_CARTOPY:
        ax.set_extent(extent, crs=ccrs.PlateCarree())

        # Land
        ax.add_feature(cfeature.LAND, facecolor='#d0d0d0', edgecolor='none', zorder=1)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='#404040', zorder=3)

        ax.set_facecolor('#e6f2ff')

        gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False
    else:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_xlabel('Longitude', fontsize=14)
        ax.set_ylabel('Latitude', fontsize=14)
        ax.set_facecolor('#e6f2ff')
        ax.grid(True, alpha=0.3)

    # Plot particles with correct transform
    active = ~beached
    if np.sum(beached) > 0:
        if HAS_CARTOPY:
            ax.scatter(lon[beached], lat[beached], s=2, c='#ff6b4a', alpha=0.5,
                      edgecolors='none', label=f'Beached: {np.sum(beached):,}',
                      zorder=4, transform=data_transform)
        else:
            ax.scatter(lon[beached], lat[beached], s=2, c='#ff6b4a', alpha=0.5,
                      edgecolors='none', label=f'Beached: {np.sum(beached):,}',
                      zorder=4)

    if np.sum(active) > 0:
        if HAS_CARTOPY:
            ax.scatter(lon[active], lat[active], s=4, c='#00cc66', alpha=0.7,
                      edgecolors='white', linewidths=0.2,
                      label=f'Active: {np.sum(active):,}',
                      zorder=5, transform=data_transform)
        else:
            ax.scatter(lon[active], lat[active], s=4, c='#00cc66', alpha=0.7,
                      edgecolors='white', linewidths=0.2,
                      label=f'Active: {np.sum(active):,}',
                      zorder=5)

    ax.set_title(f'Particle Distribution - Day {time_day:.0f}',
                fontsize=18, fontweight='bold')
    ax.legend(loc='upper right', fontsize=12, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved frame: {output_path}")
