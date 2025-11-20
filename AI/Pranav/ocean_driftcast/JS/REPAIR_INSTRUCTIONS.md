# REPAIR INSTRUCTIONS - Ocean Drift Demo

**CRITICAL FIXES NEEDED**

## Problem Summary

1. **Land Mask is WRONG** - marks NYC offshore waters as land
2. **Spawn fails** - returns 0 particles
3. **Physics broken** - particles can't move
4. **UI crashes** - widget garbage collection

## ROOT CAUSE

The `is_on_land()` function east coast boundary is interpolating incorrectly.

At NYC (40.7N, -74.0W):
- Current code calculates east_coast_lon ≈ -73.0
- Marks everything west of -73.2 as land
- NYC at -74.0 is west of -73.2, so marked as LAND
- Spawn offshore fails because everywhere near NYC is "land"

## REQUIRED FIX

**Change physics.py line 234-238:**

FROM:
```python
east_coast_lon = np.interp(
    lat,
    [25, 30, 35, 40, 45, 50, 55, 60],
    [-80, -81, -76, -74, -67, -60, -57, -55]
)
```

TO:
```python
east_coast_lon = np.interp(
    lat,
    [25, 30, 35, 40, 45, 50, 55, 60],
    [-80.5, -81.5, -77.0, -75.5, -68.0, -61.0, -58.0, -56.0]
)
```

**Change physics.py line 242: REMOVE the -0.2 buffer:**

FROM:
```python
on_land |= na_mask & (lon < (east_coast_lon - 0.2))
```

TO:
```python
on_land |= na_mask & (lon < east_coast_lon)
```

This moves the coastline further WEST (more negative) so NYC waters are properly marked as OCEAN.

## VERIFICATION

Run:
```bash
python -c "
from physics import OceanPhysics
p = OceanPhysics()
import numpy as np
# Check NYC waters
test_lat = np.array([40.7, 40.7, 40.7])
test_lon = np.array([-74.5, -74.0, -73.5])  # West of NYC, NYC, East of NYC
on_land = p.is_on_land(test_lat, test_lon)
print('Positions: -74.5, -74.0, -73.5')
print(f'On land: {on_land}')
print('Expected: [True, False, False] - only -74.5 should be land')
"
```

Expected output:
```
Positions: -74.5, -74.0, -73.5
On land: [True False False]
Expected: [True, False, False] - only -74.5 should be land
```

## ADDITIONAL FIXES NEEDED

### 1. Fix spawn_offshore to handle failures gracefully

Add fallback in physics.py spawn_offshore() around line 365:

```python
# If we couldn't find enough ocean positions, just return what we have
if len(lat_list) < n_particles:
    print(f"  WARNING: Only found {len(lat_list)} ocean positions out of {n_particles} requested")
    print(f"  This indicates land mask may be too restrictive")
    # Pad with duplicates if needed
    while len(lat_list) < n_particles:
        if len(lat_list) > 0:
            lat_list.append(lat_list[-1] + 0.01)  # Slight offset
            lon_list.append(lon_list[-1] + 0.01)
        else:
            # Absolute fallback
            lat_list.append(center_lat)
            lon_list.append(center_lon + 0.5)  # Offshore
```

### 2. Simplify UI to avoid widget garbage collection

The combobox.py is too complex. Use simple TextBox + Button instead.

### 3. Ensure basemap renders

visualization.py setup_figure() needs to force draw:
```python
self.ax.figure.canvas.draw()
```

## QUICK TEST

After applying land mask fix:

```bash
python test_fixes.py
```

Should show:
```
[TEST 1] PASSED - Physics
[OK] Offshore spawning: 100/100 particles in ocean
```

## FILES TO MODIFY

1. **physics.py** - Fix land mask (lines 234-242)
2. **physics.py** - Add spawn fallback (line ~365)
3. **particles.py** - Already fixed (using spawn_offshore)
4. **visualization.py** - Add canvas.draw() if needed
5. **ui.py** - Simplify to basic TextBox (remove combobox.py dependency)

## PRIORITY

**CRITICAL: Fix land mask FIRST** - this is blocking everything else.

Once land mask is fixed, spawn will work, particles will initialize, simulation will run.
