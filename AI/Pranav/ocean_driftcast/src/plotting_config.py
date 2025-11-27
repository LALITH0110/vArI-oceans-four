"""
Professional plotting configuration for publication-ready figures.

Defines standard styling, colors, marker sizes, and layout parameters
for all visualizations.
"""

import matplotlib.pyplot as plt
import numpy as np

# ============================================================================
# COLORS (colorblind-safe)
# ============================================================================

# Particle states
COLOR_ACTIVE = '#00ffcc'  # Bright cyan for active particles
COLOR_ACTIVE_EDGE = 'white'  # White edge for visibility
COLOR_BEACHED = '#ff6b4a'  # Warm orange for beached particles

# Backgrounds (light theme)
COLOR_LAND_LIGHT = '#d4d4d4'
COLOR_OCEAN_LIGHT = '#e8f4f8'
COLOR_COAST_LIGHT = '#505050'
COLOR_GRID_LIGHT = '#888888'
COLOR_TEXT_LIGHT = '#000000'

# Backgrounds (dark theme)
COLOR_LAND_DARK = '#3a3a3a'
COLOR_OCEAN_DARK = '#0f0f0f'
COLOR_COAST_DARK = '#707070'
COLOR_GRID_DARK = '#555555'
COLOR_TEXT_DARK = '#ffffff'

# Backgrounds (high contrast)
COLOR_LAND_HICON = '#ffffff'
COLOR_OCEAN_HICON = '#000000'
COLOR_COAST_HICON = '#000000'
COLOR_GRID_HICON = '#666666'
COLOR_TEXT_HICON = '#ffffff'

# Colorblind-safe sequential colormaps
CMAP_DENSITY = 'cividis'  # Yellow-blue, colorblind-safe
CMAP_HEATMAP = 'plasma'   # Purple-yellow, alternative
CMAP_DIVERGING = 'RdYlBu_r'  # Red-yellow-blue

# ============================================================================
# MARKER SIZES AND ALPHAS
# ============================================================================

# Marker sizes (in points)
MARKER_SIZE_DENSE = 2.5   # For >1000 particles in view
MARKER_SIZE_SPARSE = 5.5  # For <1000 particles in view
MARKER_SIZE_BEACHED = 1.5  # Beached particles (smaller)

# Alpha transparency
ALPHA_ACTIVE = 0.85
ALPHA_BEACHED = 0.7

# Edge widths
EDGE_WIDTH_ACTIVE = 0.2
EDGE_WIDTH_NONE = 0.0

# ============================================================================
# FIGURE DIMENSIONS AND DPI
# ============================================================================

DPI_HIGH = 180  # High DPI for publication
DPI_MEDIUM = 120  # Medium DPI for web
DPI_MOBILE = 90  # Low DPI for mobile

# Figure sizes (inches)
FIGSIZE_LARGE = (16, 12)  # Large standalone figures
FIGSIZE_MEDIUM = (12, 9)  # Medium figures
FIGSIZE_SMALL = (8, 6)    # Small figures
FIGSIZE_WIDE = (18, 6)    # Wide side-by-side
FIGSIZE_GRID = (20, 14)   # Multi-panel grids

# Animation settings
FPS_GIF = 10
FPS_MP4 = 30

# ============================================================================
# MAP SETTINGS
# ============================================================================

# Gridline spacing (degrees)
GRID_SPACING = 10

# Gridline style
GRID_LINEWIDTH = 0.3
GRID_ALPHA = 0.4
GRID_LINESTYLE = '--'

# Coastline style
COAST_LINEWIDTH = 0.8
LAND_EDGECOLOR = 'none'

# ============================================================================
# LEGEND SETTINGS
# ============================================================================

LEGEND_FONTSIZE = 11
LEGEND_FRAMEALPHA = 0.9
LEGEND_EDGECOLOR = 'gray'
LEGEND_FACECOLOR = 'white'
LEGEND_LOC = 'upper right'  # Default, can be overridden

# Legend marker sizes
LEGEND_MARKERSCALE = 2.0

# ============================================================================
# TEXT SETTINGS
# ============================================================================

TITLE_FONTSIZE = 16
TITLE_FONTWEIGHT = 'bold'

LABEL_FONTSIZE = 12
TICK_FONTSIZE = 10

ANNOTATION_FONTSIZE = 10
ANNOTATION_BBOX = dict(boxstyle='round', facecolor='white', alpha=0.8,
                       edgecolor='gray', linewidth=1)

# ============================================================================
# THEME MANAGEMENT
# ============================================================================

def get_theme_colors(theme='light'):
    """
    Get color scheme for a theme.

    Parameters
    ----------
    theme : str
        Theme name: 'light', 'dark', or 'high_contrast'

    Returns
    -------
    colors : dict
        Dictionary of color settings
    """
    if theme == 'dark':
        return {
            'land': COLOR_LAND_DARK,
            'ocean': COLOR_OCEAN_DARK,
            'coast': COLOR_COAST_DARK,
            'grid': COLOR_GRID_DARK,
            'text': COLOR_TEXT_DARK,
            'bg': '#1a1a1a',
        }
    elif theme == 'high_contrast':
        return {
            'land': COLOR_LAND_HICON,
            'ocean': COLOR_OCEAN_HICON,
            'coast': COLOR_COAST_HICON,
            'grid': COLOR_GRID_HICON,
            'text': COLOR_TEXT_HICON,
            'bg': '#000000',
        }
    else:  # light
        return {
            'land': COLOR_LAND_LIGHT,
            'ocean': COLOR_OCEAN_LIGHT,
            'coast': COLOR_COAST_LIGHT,
            'grid': COLOR_GRID_LIGHT,
            'text': COLOR_TEXT_LIGHT,
            'bg': 'white',
        }


def get_colorblind_palette(style='default'):
    """
    Get colorblind-safe color palette.

    Parameters
    ----------
    style : str
        Palette style: 'default', 'deuteranopia', 'protanopia', 'tritanopia'

    Returns
    -------
    palette : dict
        Color mappings
    """
    if style == 'deuteranopia':
        # Red-green colorblind (most common)
        return {
            'active': '#0173b2',  # Blue
            'beached': '#de8f05',  # Orange
        }
    elif style == 'protanopia':
        # Another form of red-green
        return {
            'active': '#029e73',  # Teal
            'beached': '#cc78bc',  # Pink
        }
    elif style == 'tritanopia':
        # Blue-yellow colorblind (rare)
        return {
            'active': '#d55e00',  # Vermillion
            'beached': '#009e73',  # Bluish green
        }
    else:  # default
        return {
            'active': COLOR_ACTIVE,
            'beached': COLOR_BEACHED,
        }


def adaptive_marker_size(n_particles, default_dense=MARKER_SIZE_DENSE,
                         default_sparse=MARKER_SIZE_SPARSE, threshold=1000):
    """
    Choose marker size based on particle count.

    Parameters
    ----------
    n_particles : int
        Number of particles to plot
    default_dense : float
        Size for dense plots
    default_sparse : float
        Size for sparse plots
    threshold : int
        Threshold between dense and sparse

    Returns
    -------
    size : float
        Marker size in points
    """
    if n_particles > threshold:
        return default_dense
    else:
        return default_sparse


def setup_map_axes(ax, extent, theme='light', include_gridlines=True):
    """
    Configure map axes with consistent styling.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to configure (Cartopy GeoAxes if available)
    extent : tuple
        Map extent (lon_min, lon_max, lat_min, lat_max)
    theme : str
        Color theme
    include_gridlines : bool
        Whether to add gridlines

    Returns
    -------
    ax : matplotlib.axes.Axes
        Configured axes
    """
    colors = get_theme_colors(theme)

    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature

        # Set extent
        ax.set_extent(extent, crs=ccrs.PlateCarree())

        # Add features
        ax.add_feature(cfeature.LAND, facecolor=colors['land'],
                      edgecolor=LAND_EDGECOLOR, zorder=1)
        ax.add_feature(cfeature.COASTLINE, linewidth=COAST_LINEWIDTH,
                      edgecolor=colors['coast'], zorder=3)

        # Ocean background
        ax.set_facecolor(colors['ocean'])

        # Gridlines
        if include_gridlines:
            gl = ax.gridlines(draw_labels=True, linewidth=GRID_LINEWIDTH,
                            alpha=GRID_ALPHA, color=colors['grid'],
                            linestyle=GRID_LINESTYLE)
            gl.top_labels = False
            gl.right_labels = False

    except ImportError:
        # Fallback without Cartopy
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_xlabel('Longitude', fontsize=LABEL_FONTSIZE, color=colors['text'])
        ax.set_ylabel('Latitude', fontsize=LABEL_FONTSIZE, color=colors['text'])
        ax.set_facecolor(colors['ocean'])

        if include_gridlines:
            ax.grid(True, alpha=GRID_ALPHA, color=colors['grid'],
                   linestyle=GRID_LINESTYLE, linewidth=GRID_LINEWIDTH)

        ax.tick_params(colors=colors['text'])

    return ax


def add_scale_bar(ax, lon, lat, length_km=500, location='lower left'):
    """
    Add a scale bar to the map.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to add scale bar to
    lon : float
        Center longitude for scale bar
    lat : float
        Center latitude for scale bar
    length_km : float
        Length of scale bar in kilometers
    location : str
        Location string
    """
    # Approximate degrees for length_km at given latitude
    deg_per_km_lat = 1.0 / 111.0
    deg_per_km_lon = 1.0 / (111.0 * np.cos(np.radians(lat)))

    length_deg = length_km * deg_per_km_lon

    # Determine position
    if 'lower' in location:
        y = 0.05
    else:
        y = 0.95

    if 'left' in location:
        x = 0.05
    else:
        x = 0.95 - 0.15  # Leave room for bar

    # Draw bar
    ax.plot([x, x + 0.1], [y, y], 'k-', linewidth=3,
           transform=ax.transAxes, zorder=100)

    # Add label
    ax.text(x + 0.05, y + 0.02, f'{length_km} km',
           transform=ax.transAxes, ha='center', va='bottom',
           fontsize=9, fontweight='bold', zorder=100)


if __name__ == '__main__':
    print("Plotting Configuration")
    print("=" * 60)
    print(f"Default active color: {COLOR_ACTIVE}")
    print(f"Default beached color: {COLOR_BEACHED}")
    print(f"Dense marker size: {MARKER_SIZE_DENSE} pt")
    print(f"Sparse marker size: {MARKER_SIZE_SPARSE} pt")
    print(f"High DPI: {DPI_HIGH}")
    print()

    print("Themes available:")
    for theme in ['light', 'dark', 'high_contrast']:
        colors = get_theme_colors(theme)
        print(f"  {theme}: land={colors['land']}, ocean={colors['ocean']}")
    print()

    print("Colorblind palettes:")
    for style in ['default', 'deuteranopia', 'protanopia', 'tritanopia']:
        palette = get_colorblind_palette(style)
        print(f"  {style}: active={palette['active']}, beached={palette['beached']}")
