"""
Ocean mask and coastal band computation using Cartopy Natural Earth.

Builds a precomputed 0.25° raster mask for the North Atlantic domain.
"""

import numpy as np
import os

try:
    import cartopy.io.shapereader as shpreader
    from shapely.geometry import Point, Polygon
    from shapely.prepared import prep
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False


# Domain bounds
LON_MIN, LON_MAX = -100.0, 20.0
LAT_MIN, LAT_MAX = 0.0, 60.0
RESOLUTION = 0.25  # degrees


def build_ocean_mask(resolution=RESOLUTION, output_path='outputs/ocean_mask.npz'):
    """
    Build ocean mask from Cartopy Natural Earth land polygons.

    Parameters
    ----------
    resolution : float
        Grid resolution in degrees
    output_path : str
        Path to save the mask

    Returns
    -------
    grid_lon : ndarray
        Longitude grid centers
    grid_lat : ndarray
        Latitude grid centers
    ocean_mask : ndarray (bool)
        True for ocean, False for land
    """
    if not HAS_CARTOPY:
        raise ImportError("Cartopy is required to build ocean mask. "
                         "Install with: pip install cartopy")

    print(f"Building ocean mask at {resolution}° resolution...")
    print(f"  Domain: lon [{LON_MIN}, {LON_MAX}], lat [{LAT_MIN}, {LAT_MAX}]")

    # Create grid
    grid_lon = np.arange(LON_MIN, LON_MAX + resolution, resolution)
    grid_lat = np.arange(LAT_MIN, LAT_MAX + resolution, resolution)

    n_lon, n_lat = len(grid_lon), len(grid_lat)
    print(f"  Grid size: {n_lon} x {n_lat} = {n_lon * n_lat:,} cells")

    # Initialize as all ocean
    ocean_mask = np.ones((n_lon, n_lat), dtype=bool)

    # Get Natural Earth land polygons at 10m resolution
    print("  Loading Natural Earth land polygons (10m)...")
    try:
        land_shp = shpreader.natural_earth(
            resolution='10m',
            category='physical',
            name='land'
        )
    except Exception:
        # Fallback to 50m if 10m not available
        print("  10m data not available, using 50m resolution...")
        land_shp = shpreader.natural_earth(
            resolution='50m',
            category='physical',
            name='land'
        )

    land_geoms = list(shpreader.Reader(land_shp).geometries())
    print(f"  Loaded {len(land_geoms)} land geometries")

    # Prepare land polygons for faster containment checks
    print("  Preparing land polygons...")
    prepared_land = [prep(geom) for geom in land_geoms]

    # Mark land cells
    print("  Rasterizing land cells...")
    n_land = 0

    for i, lon in enumerate(grid_lon):
        if i % 50 == 0:
            print(f"    Processing lon {lon:.2f} ({i}/{n_lon})...")

        for j, lat in enumerate(grid_lat):
            point = Point(lon, lat)

            # Check if point is in any land polygon
            for prep_geom in prepared_land:
                if prep_geom.contains(point):
                    ocean_mask[i, j] = False
                    n_land += 1
                    break

    n_ocean = np.sum(ocean_mask)
    pct_ocean = 100 * n_ocean / ocean_mask.size

    print(f"  Ocean cells: {n_ocean:,} ({pct_ocean:.1f}%)")
    print(f"  Land cells: {n_land:,} ({100 - pct_ocean:.1f}%)")

    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    np.savez_compressed(
        output_path,
        grid_lon=grid_lon,
        grid_lat=grid_lat,
        ocean_mask=ocean_mask
    )

    print(f"  Saved mask to: {output_path}")

    return grid_lon, grid_lat, ocean_mask


def load_ocean_mask(mask_path='outputs/ocean_mask.npz', rebuild=False):
    """
    Load precomputed ocean mask, building if needed.

    Parameters
    ----------
    mask_path : str
        Path to mask file
    rebuild : bool
        Force rebuild even if file exists

    Returns
    -------
    grid_lon : ndarray
        Longitude grid centers
    grid_lat : ndarray
        Latitude grid centers
    ocean_mask : ndarray (bool)
        True for ocean, False for land
    """
    if rebuild or not os.path.exists(mask_path):
        return build_ocean_mask(output_path=mask_path)

    print(f"Loading ocean mask from: {mask_path}")
    data = np.load(mask_path)
    grid_lon = data['grid_lon']
    grid_lat = data['grid_lat']
    ocean_mask = data['ocean_mask']

    n_ocean = np.sum(ocean_mask)
    pct_ocean = 100 * n_ocean / ocean_mask.size
    print(f"  Grid: {len(grid_lon)} x {len(grid_lat)}, "
          f"Ocean: {n_ocean:,} cells ({pct_ocean:.1f}%)")

    return grid_lon, grid_lat, ocean_mask


def compute_coastal_band(ocean_mask, radius=1):
    """
    Compute coastal band: ocean cells adjacent to land.

    Parameters
    ----------
    ocean_mask : ndarray (bool)
        True for ocean, False for land
    radius : int
        Neighborhood radius (1 = 8-connected)

    Returns
    -------
    coastal_band : ndarray (bool)
        True for coastal ocean cells
    """
    from scipy.ndimage import binary_dilation

    print("Computing coastal band...")

    # Land mask
    land_mask = ~ocean_mask

    # Dilate land by radius
    dilated_land = binary_dilation(land_mask, iterations=radius)

    # Coastal band = ocean cells that overlap with dilated land
    coastal_band = ocean_mask & dilated_land

    n_coastal = np.sum(coastal_band)
    pct_coastal = 100 * n_coastal / np.sum(ocean_mask)

    print(f"  Coastal cells: {n_coastal:,} ({pct_coastal:.1f}% of ocean)")

    return coastal_band


def is_ocean(lon, lat, grid_lon, grid_lat, ocean_mask):
    """
    Check if positions are in ocean cells.

    Parameters
    ----------
    lon : array-like
        Longitudes
    lat : array-like
        Latitudes
    grid_lon : ndarray
        Grid longitude centers
    grid_lat : ndarray
        Grid latitude centers
    ocean_mask : ndarray (bool)
        Ocean mask

    Returns
    -------
    in_ocean : ndarray (bool)
        True if position is in ocean
    """
    lon = np.asarray(lon)
    lat = np.asarray(lat)

    # Convert to grid indices
    i = np.floor((lon - grid_lon[0]) / RESOLUTION).astype(int)
    j = np.floor((lat - grid_lat[0]) / RESOLUTION).astype(int)

    # Clamp to valid range
    i = np.clip(i, 0, len(grid_lon) - 1)
    j = np.clip(j, 0, len(grid_lat) - 1)

    # Check ocean mask
    in_ocean = ocean_mask[i, j]

    return in_ocean


def nearest_ocean_cell(lon, lat, grid_lon, grid_lat, ocean_mask, search_radius=3):
    """
    Find nearest ocean cell for positions on land.

    Parameters
    ----------
    lon : array-like
        Longitudes
    lat : array-like
        Latitudes
    grid_lon : ndarray
        Grid longitude centers
    grid_lat : ndarray
        Grid latitude centers
    ocean_mask : ndarray (bool)
        Ocean mask
    search_radius : int
        Search radius in grid cells

    Returns
    -------
    lon_ocean : ndarray
        Nearest ocean longitude
    lat_ocean : ndarray
        Nearest ocean latitude
    found : ndarray (bool)
        True if ocean cell found within search radius
    """
    lon = np.asarray(lon)
    lat = np.asarray(lat)

    lon_ocean = lon.copy()
    lat_ocean = lat.copy()
    found = np.ones(len(lon), dtype=bool)

    # Convert to grid indices
    i = np.floor((lon - grid_lon[0]) / RESOLUTION).astype(int)
    j = np.floor((lat - grid_lat[0]) / RESOLUTION).astype(int)

    # Clamp to valid range
    i = np.clip(i, 0, len(grid_lon) - 1)
    j = np.clip(j, 0, len(grid_lat) - 1)

    # Find particles on land
    on_land = ~ocean_mask[i, j]

    if not np.any(on_land):
        return lon_ocean, lat_ocean, found

    # For each land particle, search nearby cells
    for idx in np.where(on_land)[0]:
        i_center = i[idx]
        j_center = j[idx]

        # Search in expanding radius
        found_ocean = False
        min_dist = np.inf
        best_i, best_j = i_center, j_center

        for di in range(-search_radius, search_radius + 1):
            for dj in range(-search_radius, search_radius + 1):
                i_test = i_center + di
                j_test = j_center + dj

                # Check bounds
                if (i_test < 0 or i_test >= len(grid_lon) or
                    j_test < 0 or j_test >= len(grid_lat)):
                    continue

                # Check if ocean
                if ocean_mask[i_test, j_test]:
                    dist = np.sqrt(di**2 + dj**2)
                    if dist < min_dist:
                        min_dist = dist
                        best_i, best_j = i_test, j_test
                        found_ocean = True

        if found_ocean:
            lon_ocean[idx] = grid_lon[best_i]
            lat_ocean[idx] = grid_lat[best_j]
        else:
            found[idx] = False

    return lon_ocean, lat_ocean, found


def get_grid_indices(lon, lat, grid_lon, grid_lat):
    """
    Convert lon/lat to grid indices.

    Parameters
    ----------
    lon : array-like
        Longitudes
    lat : array-like
        Latitudes
    grid_lon : ndarray
        Grid longitude centers
    grid_lat : ndarray
        Grid latitude centers

    Returns
    -------
    i : ndarray (int)
        Longitude indices
    j : ndarray (int)
        Latitude indices
    """
    lon = np.asarray(lon)
    lat = np.asarray(lat)

    i = np.floor((lon - grid_lon[0]) / RESOLUTION).astype(int)
    j = np.floor((lat - grid_lat[0]) / RESOLUTION).astype(int)

    # Clamp to valid range
    i = np.clip(i, 0, len(grid_lon) - 1)
    j = np.clip(j, 0, len(grid_lat) - 1)

    return i, j


if __name__ == '__main__':
    # Build mask if run directly
    grid_lon, grid_lat, ocean_mask = build_ocean_mask()
    coastal_band = compute_coastal_band(ocean_mask)

    # Test some known points
    print("\nTesting known locations:")
    test_points = [
        (-40.0, 30.0, "Mid-Atlantic (ocean)"),
        (-74.0, 40.7, "New York City (land)"),
        (-9.0, 38.7, "Lisbon coast"),
    ]

    for lon, lat, name in test_points:
        in_ocean = is_ocean(lon, lat, grid_lon, grid_lat, ocean_mask)
        i, j = get_grid_indices(lon, lat, grid_lon, grid_lat)
        is_coastal = coastal_band[i, j]
        print(f"  {name}: ocean={in_ocean}, coastal={is_coastal}")
