"""
Story-focused animations for NYC spill scenario.

Creates annotated GIFs and MP4s with overlay text showing metrics.
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


def create_nyc_spill_animation(lon_history, lat_history, beached_history, times,
                                output_path, fps=10, extent=(-100, 20, 0, 60),
                                dark_mode=False, mask_data=None):
    """
    Create NYC spill animation with overlay text (Day, Active, Beached).

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status
    times : ndarray (n_times,)
        Time in days
    output_path : str
        Output path (.gif or .mp4)
    fps : int
        Frames per second (default 10)
    extent : tuple
        Map extent
    dark_mode : bool
        Use dark theme (default False)
    mask_data : tuple, optional
        (grid_lon, grid_lat, ocean_mask, coastal_band)
    """
    print(f"Creating NYC spill animation: {output_path}")

    n_times, n_particles = lon_history.shape

    print(f"  Frames: {n_times}, Particles: {n_particles}, FPS: {fps}")

    # Color scheme
    if dark_mode:
        bg_color = '#1a1a1a'
        land_color = '#404040'
        ocean_color = '#0a0a0a'
        coast_color = '#606060'
        active_color = '#00ffcc'
        beached_color = '#ff6b4a'
        text_color = 'white'
    else:
        bg_color = 'white'
        land_color = '#d0d0d0'
        ocean_color = '#e6f2ff'
        coast_color = '#404040'
        active_color = '#00ff88'
        beached_color = '#ff6b4a'
        text_color = 'black'

    # Create figure
    if HAS_CARTOPY:
        fig = plt.figure(figsize=(16, 12), facecolor=bg_color)
        ax = plt.axes(projection=ccrs.PlateCarree())
        data_transform = ccrs.PlateCarree()
    else:
        fig, ax = plt.subplots(figsize=(16, 12))
        fig.patch.set_facecolor(bg_color)
        data_transform = None

    # Setup base map
    if HAS_CARTOPY:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, facecolor=land_color, edgecolor='none', zorder=1)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor=coast_color, zorder=3)
        ax.set_facecolor(ocean_color)

        gl = ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.4,
                         color='gray', linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
    else:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_xlabel('Longitude', fontsize=14, color=text_color)
        ax.set_ylabel('Latitude', fontsize=14, color=text_color)
        ax.set_facecolor(ocean_color)
        ax.grid(True, alpha=0.3, color='gray', linestyle='--')
        ax.tick_params(colors=text_color)

    # Initialize scatter plots
    if HAS_CARTOPY:
        scatter_beached = ax.scatter([], [], s=1.5, c=beached_color, alpha=0.4,
                                    edgecolors='none', zorder=4,
                                    transform=data_transform)
        scatter_active = ax.scatter([], [], s=3, c=active_color, alpha=0.8,
                                   edgecolors='white', linewidths=0.2, zorder=5,
                                   transform=data_transform)
    else:
        scatter_beached = ax.scatter([], [], s=1.5, c=beached_color, alpha=0.4,
                                    edgecolors='none', zorder=4)
        scatter_active = ax.scatter([], [], s=3, c=active_color, alpha=0.8,
                                   edgecolors='white', linewidths=0.2, zorder=5)

    # Overlay text box
    text_box = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                      fontsize=18, fontweight='bold', color=text_color,
                      verticalalignment='top',
                      bbox=dict(boxstyle='round', facecolor=bg_color, alpha=0.8,
                               edgecolor='gray', linewidth=1))

    def init():
        scatter_active.set_offsets(np.empty((0, 2)))
        scatter_beached.set_offsets(np.empty((0, 2)))
        text_box.set_text('')
        return scatter_active, scatter_beached, text_box

    def update(frame_idx):
        t = times[frame_idx]

        lon = lon_history[frame_idx]
        lat = lat_history[frame_idx]
        beached = beached_history[frame_idx]

        # Active particles
        active = ~beached
        if np.sum(active) > 0:
            points_active = np.column_stack([lon[active], lat[active]])
            scatter_active.set_offsets(points_active)
        else:
            scatter_active.set_offsets(np.empty((0, 2)))

        # Beached particles
        if np.sum(beached) > 0:
            points_beached = np.column_stack([lon[beached], lat[beached]])
            scatter_beached.set_offsets(points_beached)
        else:
            scatter_beached.set_offsets(np.empty((0, 2)))

        # Update text overlay
        n_active = np.sum(active)
        n_beached = np.sum(beached)
        text_box.set_text(f'Day {t:.0f} | Active {n_active:,} | Beached {n_beached:,}')

        return scatter_active, scatter_beached, text_box

    # Create animation
    anim = FuncAnimation(fig, update, init_func=init,
                        frames=n_times, interval=1000/fps,
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


def create_story_mp4(lon_history, lat_history, beached_history, times,
                     output_path, target_minutes=5, fps=30,
                     extent=(-100, 20, 0, 60), dark_mode=False, mask_data=None):
    """
    Create tiled MP4 for stage presentation (5 minutes default).

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status
    times : ndarray (n_times,)
        Time in days
    output_path : str
        Output path (.mp4)
    target_minutes : float
        Target video duration in minutes (default 5)
    fps : int
        Frames per second (default 30)
    extent : tuple
        Map extent
    dark_mode : bool
        Use dark theme
    mask_data : tuple, optional
        Mask data
    """
    print(f"Creating story MP4: {output_path} (target: {target_minutes} min @ {fps} fps)")

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
    create_nyc_spill_animation(
        lon_tiled, lat_tiled, beached_tiled, times_tiled,
        output_path=output_path, fps=fps, extent=extent,
        dark_mode=dark_mode, mask_data=mask_data
    )

    actual_duration = len(times_tiled) / fps / 60
    print(f"  Video duration: {actual_duration:.2f} minutes")

    return output_path


def create_monthly_ensemble_animation(monthly_results, output_path, fps=10,
                                       extent=(-100, 20, 0, 60), dark_mode=False):
    """
    Create animation showing all 12 monthly releases overlaid.

    (Alternative: could show them sequentially or in a grid)

    Parameters
    ----------
    monthly_results : list of dict
        List of 12 monthly simulation results
    output_path : str
        Output path
    fps : int
        Frames per second
    extent : tuple
        Map extent
    dark_mode : bool
        Use dark theme
    """
    print(f"Creating monthly ensemble animation: {output_path}")

    # For simplicity, we'll just overlay all months in different colors
    # (More sophisticated version could animate them sequentially)

    n_times = len(monthly_results[0]['lon'])

    # Color scheme
    if dark_mode:
        bg_color = '#1a1a1a'
        land_color = '#404040'
        ocean_color = '#0a0a0a'
        coast_color = '#606060'
        text_color = 'white'
    else:
        bg_color = 'white'
        land_color = '#d0d0d0'
        ocean_color = '#e6f2ff'
        coast_color = '#404040'
        text_color = 'black'

    # Create figure
    if HAS_CARTOPY:
        fig = plt.figure(figsize=(16, 12), facecolor=bg_color)
        ax = plt.axes(projection=ccrs.PlateCarree())
        data_transform = ccrs.PlateCarree()
    else:
        fig, ax = plt.subplots(figsize=(16, 12))
        fig.patch.set_facecolor(bg_color)
        data_transform = None

    # Setup base map
    if HAS_CARTOPY:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, facecolor=land_color, edgecolor='none', zorder=1)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor=coast_color, zorder=3)
        ax.set_facecolor(ocean_color)
    else:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_facecolor(ocean_color)
        ax.grid(True, alpha=0.3)

    # Create scatter plot for each month (different colors)
    import matplotlib.cm as cm
    colors = cm.tab12(np.linspace(0, 1, 12))

    scatter_plots = []
    for i in range(12):
        if HAS_CARTOPY:
            scatter = ax.scatter([], [], s=2, c=[colors[i]], alpha=0.6,
                               transform=data_transform, label=monthly_results[i]['month_name'][:3])
        else:
            scatter = ax.scatter([], [], s=2, c=[colors[i]], alpha=0.6,
                               label=monthly_results[i]['month_name'][:3])
        scatter_plots.append(scatter)

    # Legend
    ax.legend(loc='upper right', fontsize=8, ncol=2, framealpha=0.9)

    # Title
    title = ax.text(0.5, 0.98, '', transform=ax.transAxes,
                   fontsize=16, fontweight='bold', color=text_color,
                   horizontalalignment='center', verticalalignment='top')

    def init():
        for scatter in scatter_plots:
            scatter.set_offsets(np.empty((0, 2)))
        title.set_text('')
        return scatter_plots + [title]

    def update(frame_idx):
        # Update each month
        for month_idx, result in enumerate(monthly_results):
            lon = result['lon'][frame_idx]
            lat = result['lat'][frame_idx]
            beached = result['beached'][frame_idx]
            active = ~beached

            if np.sum(active) > 0:
                points = np.column_stack([lon[active], lat[active]])
                scatter_plots[month_idx].set_offsets(points)
            else:
                scatter_plots[month_idx].set_offsets(np.empty((0, 2)))

        # Update title with day
        t = monthly_results[0]['times'][frame_idx]
        title.set_text(f'Monthly Ensemble - Day {t:.0f}')

        return scatter_plots + [title]

    # Create animation
    anim = FuncAnimation(fig, update, init_func=init,
                        frames=n_times, interval=1000/fps,
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

    plt.close(fig)

    print(f"  Saved: {output_path}")

    return output_path


if __name__ == '__main__':
    print("NYC story animation functions loaded.")
    print("  - create_nyc_spill_animation")
    print("  - create_story_mp4")
    print("  - create_monthly_ensemble_animation")
