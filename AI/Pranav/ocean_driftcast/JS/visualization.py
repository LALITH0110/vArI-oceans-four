"""
Synthetic demo for presentation, not scientific output.

Visualization layer with Ocean Cleanup style dark theme and cyan trajectories.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from typing import Optional, Tuple, Dict, List
from particles import ParticleSystem

# Ocean Cleanup style colors
COLORS = {
    'background': '#0a1e2e',
    'ocean': '#0d2a3f',
    'land': '#1a3a4f',
    'trajectory': '#00d9ff',
    'trajectory_faint': '#00d9ff',
    'gyre': '#ff6b35',
    'text': '#ffffff',
    'text_secondary': '#a0c4d9',
    'accent': '#00ffcc',
    'info_bg': '#0f3548',
}


class OceanDriftVisualizer:
    """
    Visualization engine for ocean drift simulation.
    """

    def __init__(self, figsize: Tuple[float, float] = (20, 12), dpi: int = 100):
        """
        Initialize visualizer.

        Args:
            figsize: Figure size in inches
            dpi: Resolution
        """
        self.figsize = figsize
        self.dpi = dpi
        self.fig = None
        self.ax = None

    def setup_figure(self, extent: Optional[Tuple] = None):
        """
        Setup figure with dark Ocean Cleanup style and Natural Earth features.

        Args:
            extent: Map extent [lon_min, lon_max, lat_min, lat_max]
        """
        if extent is None:
            extent = [-100, 20, 5, 65]

        # Create figure
        self.fig = plt.figure(figsize=self.figsize, dpi=self.dpi, facecolor=COLORS['background'])

        # Create map axis
        self.ax = plt.axes(projection=ccrs.PlateCarree())
        self.ax.set_extent(extent, crs=ccrs.PlateCarree())

        # OCEAN - slightly darker background for water
        self.ax.set_facecolor(COLORS['ocean'])
        ocean = cfeature.OCEAN
        self.ax.add_feature(ocean, facecolor=COLORS['ocean'], zorder=0)

        # LAND - lighter than ocean so trajectories pop
        land = cfeature.LAND
        self.ax.add_feature(land, facecolor=COLORS['land'], edgecolor='none', zorder=1)

        # COASTLINES - clear boundary between land and water
        self.ax.coastlines(
            resolution='50m',
            color=COLORS['text_secondary'],
            linewidth=0.8,
            alpha=0.7,
            zorder=3
        )

        # LAKES - show major lakes
        lakes = cfeature.LAKES
        self.ax.add_feature(
            lakes,
            facecolor=COLORS['ocean'],
            edgecolor=COLORS['text_secondary'],
            linewidth=0.3,
            alpha=0.5,
            zorder=2
        )

        # RIVERS - show major rivers
        rivers = cfeature.RIVERS
        self.ax.add_feature(
            rivers,
            edgecolor=COLORS['text_secondary'],
            linewidth=0.4,
            alpha=0.4,
            zorder=2
        )

        # GRATICULES - 10-degree grid for reference
        gl = self.ax.gridlines(
            draw_labels=True,
            linewidth=0.4,
            color=COLORS['text_secondary'],
            alpha=0.4,
            linestyle='--',
            zorder=0,
            x_inline=False,
            y_inline=False
        )

        # Configure graticule labels
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 8, 'color': COLORS['text_secondary']}
        gl.ylabel_style = {'size': 8, 'color': COLORS['text_secondary']}

        # Set 10-degree intervals
        import matplotlib.ticker as mticker
        gl.xlocator = mticker.FixedLocator(range(-180, 181, 10))
        gl.ylocator = mticker.FixedLocator(range(-90, 91, 10))

        # Remove axis spines
        self.ax.spines['geo'].set_edgecolor(COLORS['text_secondary'])
        self.ax.spines['geo'].set_linewidth(0.5)

        return self.fig, self.ax

    def plot_gyre_background(self, alpha: float = 0.15):
        """
        Add subtle gyre heatmap background.

        Args:
            alpha: Transparency
        """
        # Create gyre density field
        lat = np.linspace(5, 65, 200)
        lon = np.linspace(-100, 20, 300)
        lon_grid, lat_grid = np.meshgrid(lon, lat)

        # Gyre center
        gyre_lat = 30.0
        gyre_lon = -40.0

        # Distance from gyre center
        dlat = lat_grid - gyre_lat
        dlon = lon_grid - gyre_lon
        r = np.sqrt(dlat**2 + dlon**2)

        # Gaussian density
        density = np.exp(-(r / 20.0)**2)

        # Custom colormap (transparent to cyan/orange)
        colors_map = ['#00000000', COLORS['trajectory_faint'], COLORS['gyre']]
        n_bins = 100
        cmap = LinearSegmentedColormap.from_list('gyre', colors_map, N=n_bins)

        # Plot
        self.ax.contourf(
            lon_grid, lat_grid, density,
            levels=20,
            cmap=cmap,
            alpha=alpha,
            transform=ccrs.PlateCarree(),
            zorder=0.5
        )

    def plot_trajectories(self, trajectories_lat: List[np.ndarray], trajectories_lon: List[np.ndarray],
                          alpha: float = 0.03, linewidth: float = 0.5, subsample: int = 10):
        """
        Plot particle trajectories with alpha blending for glow effect.

        Args:
            trajectories_lat: List of latitude arrays
            trajectories_lon: List of longitude arrays
            alpha: Line transparency
            linewidth: Line width
            subsample: Plot every N trajectories
        """
        # Subsample trajectories for performance
        n_traj = len(trajectories_lat)
        indices = range(0, n_traj, subsample)

        for i in indices:
            lat_traj = trajectories_lat[i]
            lon_traj = trajectories_lon[i]

            # Only plot if trajectory has movement
            if len(lat_traj) > 1:
                self.ax.plot(
                    lon_traj, lat_traj,
                    color=COLORS['trajectory'],
                    alpha=alpha,
                    linewidth=linewidth,
                    transform=ccrs.PlateCarree(),
                    zorder=3
                )

    def plot_particles(self, lat: np.ndarray, lon: np.ndarray, is_beached: np.ndarray,
                       active_size: float = 1.5, beached_size: float = 0.5):
        """
        Plot current particle positions.

        Args:
            lat: Particle latitudes
            lon: Particle longitudes
            is_beached: Beaching status
            active_size: Size for active particles
            beached_size: Size for beached particles
        """
        # Active particles
        active = ~is_beached
        if np.any(active):
            self.ax.scatter(
                lon[active], lat[active],
                s=active_size,
                color=COLORS['trajectory'],
                alpha=0.8,
                transform=ccrs.PlateCarree(),
                zorder=4
            )

        # Beached particles
        if np.any(is_beached):
            self.ax.scatter(
                lon[is_beached], lat[is_beached],
                s=beached_size,
                color=COLORS['gyre'],
                alpha=0.3,
                transform=ccrs.PlateCarree(),
                zorder=3.5
            )

    def add_labels(self):
        """
        Add location labels.
        """
        # Cities
        cities = [
            ("New York", 40.7, -74.0),
            ("Lisbon", 38.7, -9.1),
            ("Miami", 25.8, -80.2),
        ]

        for name, lat, lon in cities:
            self.ax.plot(lon, lat, 'o', color=COLORS['accent'], markersize=4,
                        transform=ccrs.PlateCarree(), zorder=5)
            self.ax.text(lon, lat + 1.5, name, color=COLORS['text'],
                        fontsize=8, ha='center', weight='bold',
                        transform=ccrs.PlateCarree(), zorder=5)

        # North Atlantic Garbage Patch
        self.ax.text(-40, 30, "North Atlantic\nGarbage Patch",
                    color=COLORS['gyre'], fontsize=10, ha='center',
                    weight='bold', style='italic', alpha=0.7,
                    transform=ccrs.PlateCarree(), zorder=5)

    def add_info_card(self, city: str, probability: str, distance_km: float, step: int, total_steps: int):
        """
        Add info card overlay.

        Args:
            city: City name
            probability: Probability category (LOW/MEDIUM/HIGH)
            distance_km: Total trajectory distance
            step: Current step
            total_steps: Total simulation steps
        """
        # Position in figure coordinates
        card_x = 0.75
        card_y = 0.70
        card_width = 0.22
        card_height = 0.25

        # Add background box
        card_bg = mpatches.FancyBboxPatch(
            (card_x, card_y), card_width, card_height,
            boxstyle="round,pad=0.01",
            transform=self.fig.transFigure,
            facecolor=COLORS['info_bg'],
            edgecolor=COLORS['trajectory'],
            linewidth=2,
            alpha=0.95,
            zorder=100
        )
        self.fig.patches.append(card_bg)

        # Add text content
        text_x = card_x + 0.02
        text_y_start = card_y + card_height - 0.03

        # Location icon and city
        self.fig.text(
            text_x, text_y_start, "📍",
            fontsize=14, color=COLORS['text'], weight='bold',
            transform=self.fig.transFigure, zorder=101, family='DejaVu Sans'
        )
        self.fig.text(
            text_x + 0.03, text_y_start, city.upper(),
            fontsize=12, color=COLORS['text'], weight='bold',
            transform=self.fig.transFigure, zorder=101
        )

        # Probability
        prob_color = {
            'LOW': '#4a9eff',
            'MEDIUM': '#ffaa00',
            'HIGH': '#ff4444'
        }.get(probability, COLORS['text'])

        self.fig.text(
            text_x, text_y_start - 0.06, probability,
            fontsize=20, color=prob_color, weight='bold',
            transform=self.fig.transFigure, zorder=101
        )
        self.fig.text(
            text_x, text_y_start - 0.09, "probability of plastic to reach the ocean",
            fontsize=7, color=COLORS['text_secondary'],
            transform=self.fig.transFigure, zorder=101
        )

        # Distance
        self.fig.text(
            text_x, text_y_start - 0.14, f"{distance_km:,.0f} KM",
            fontsize=16, color=COLORS['trajectory'], weight='bold',
            transform=self.fig.transFigure, zorder=101
        )
        self.fig.text(
            text_x, text_y_start - 0.17, "of trajectory distance",
            fontsize=7, color=COLORS['text_secondary'],
            transform=self.fig.transFigure, zorder=101
        )

        # Time counter
        years = step / 52.0
        self.fig.text(
            text_x, text_y_start - 0.22, f"Year {years:.1f} / 20.0",
            fontsize=8, color=COLORS['text'],
            transform=self.fig.transFigure, zorder=101
        )

    def add_logo(self):
        """
        Add Ocean Cleanup logo text.
        """
        self.fig.text(
            0.02, 0.97, "THE OCEAN CLEANUP",
            fontsize=14, color=COLORS['text'], weight='bold',
            transform=self.fig.transFigure, zorder=101,
            family='sans-serif'
        )

    def add_scale_bar(self):
        """
        Add scale bar.
        """
        # 1000 km scale bar
        scale_length_km = 1000
        scale_length_deg = scale_length_km / 111.32  # degrees

        # Position
        x_start = -95
        y_start = 8

        # Draw line
        self.ax.plot(
            [x_start, x_start + scale_length_deg],
            [y_start, y_start],
            color=COLORS['text'],
            linewidth=2,
            transform=ccrs.PlateCarree(),
            zorder=5
        )

        # Add ticks
        for x in [x_start, x_start + scale_length_deg]:
            self.ax.plot(
                [x, x], [y_start - 0.3, y_start + 0.3],
                color=COLORS['text'],
                linewidth=2,
                transform=ccrs.PlateCarree(),
                zorder=5
            )

        # Add label
        self.ax.text(
            x_start + scale_length_deg / 2, y_start - 1.5,
            f"{scale_length_km} km",
            color=COLORS['text'],
            fontsize=8,
            ha='center',
            weight='bold',
            transform=ccrs.PlateCarree(),
            zorder=5
        )

    def render_frame(self, particle_system: ParticleSystem, city_name: str, step: int,
                     show_trajectories: bool = True, show_particles: bool = True,
                     traj_subsample: int = 10) -> plt.Figure:
        """
        Render a complete frame.

        Args:
            particle_system: ParticleSystem instance
            city_name: City name for info card
            step: Current time step
            show_trajectories: Whether to show full trajectories
            show_particles: Whether to show current particles
            traj_subsample: Subsample factor for trajectories

        Returns:
            Figure
        """
        # Setup figure
        self.setup_figure()

        # Add gyre background
        self.plot_gyre_background()

        # Add trajectories
        if show_trajectories:
            traj_lat, traj_lon = particle_system.get_trajectory_arrays(subsample=1)
            # Truncate to current step
            traj_lat_truncated = [t[:step+1] for t in traj_lat]
            traj_lon_truncated = [t[:step+1] for t in traj_lon]
            self.plot_trajectories(traj_lat_truncated, traj_lon_truncated, subsample=traj_subsample)

        # Add current particles
        if show_particles and step < len(particle_system.history_lat):
            lat, lon, beached = particle_system.get_positions_at_step(step)
            self.plot_particles(lat, lon, beached)

        # Add labels
        self.add_labels()

        # Add info card
        metrics = particle_system.get_metrics()
        prob_category = particle_system.get_probability_category()
        self.add_info_card(
            city=city_name,
            probability=prob_category,
            distance_km=metrics['median_distance_km'],
            step=step,
            total_steps=len(particle_system.history_lat) - 1
        )

        # Add logo
        self.add_logo()

        # Add scale bar
        self.add_scale_bar()

        # Adjust layout
        plt.tight_layout(pad=0.5)

        return self.fig

    def save_frame(self, filename: str):
        """
        Save current frame.

        Args:
            filename: Output filename
        """
        if self.fig is not None:
            self.fig.savefig(
                filename,
                dpi=self.dpi,
                facecolor=COLORS['background'],
                edgecolor='none',
                bbox_inches='tight',
                pad_inches=0.1
            )

    def close(self):
        """
        Close figure.
        """
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
