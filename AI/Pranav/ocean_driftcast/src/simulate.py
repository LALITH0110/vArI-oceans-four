"""
Main simulation loop for particle tracking with strict ocean-only integration.

Implements land avoidance with half-step retry and nearest ocean cell projection.
"""

import numpy as np
import flow
import beaching
import ocean_mask as om


def run_simulation(lon_init, lat_init, n_steps, dt=1.0, save_every=1, mask_data=None):
    """
    Run particle tracking simulation with ocean-only constraint.

    Parameters
    ----------
    lon_init : ndarray
        Initial longitudes in degrees
    lat_init : ndarray
        Initial latitudes in degrees
    n_steps : int
        Number of time steps
    dt : float
        Time step in days
    save_every : int
        Save positions every N steps
    mask_data : tuple, optional
        (grid_lon, grid_lat, ocean_mask, coastal_band) - loaded externally

    Returns
    -------
    results : dict
        Dictionary containing:
        - 'lon': ndarray (n_saved, n_particles) - longitudes over time
        - 'lat': ndarray (n_saved, n_particles) - latitudes over time
        - 'beached': ndarray (n_saved, n_particles) - beached status
        - 'times': ndarray (n_saved,) - time in days
        - 'stats': dict - simulation statistics
    """
    n_particles = len(lon_init)

    # Load or use provided ocean mask
    if mask_data is None:
        print("Loading ocean mask...")
        grid_lon, grid_lat, ocean_mask = om.load_ocean_mask()
        coastal_band = om.compute_coastal_band(ocean_mask)
    else:
        grid_lon, grid_lat, ocean_mask, coastal_band = mask_data

    # Initialize arrays
    lon = lon_init.copy()
    lat = lat_init.copy()
    beached = np.zeros(n_particles, dtype=bool)

    # Ensure initial positions are in ocean
    print("Checking initial positions...")
    in_ocean = om.is_ocean(lon, lat, grid_lon, grid_lat, ocean_mask)
    if not np.all(in_ocean):
        n_land = np.sum(~in_ocean)
        print(f"  WARNING: {n_land} particles initialized on land, moving to nearest ocean cell")
        lon, lat, found = om.nearest_ocean_cell(
            lon, lat, grid_lon, grid_lat, ocean_mask, search_radius=5
        )
        if not np.all(found):
            raise ValueError(f"Could not find ocean cells for {np.sum(~found)} particles")

    # Storage arrays
    n_saved = (n_steps // save_every) + 1
    lon_history = np.zeros((n_saved, n_particles))
    lat_history = np.zeros((n_saved, n_particles))
    beached_history = np.zeros((n_saved, n_particles), dtype=bool)
    times = np.zeros(n_saved)

    # Save initial state
    lon_history[0] = lon
    lat_history[0] = lat
    beached_history[0] = beached
    times[0] = 0

    save_idx = 1

    # Statistics
    total_beached = 0
    total_land_corrections = 0
    total_half_step_success = 0
    total_projection_success = 0
    total_failed_corrections = 0

    print(f"Starting simulation: {n_particles} particles, {n_steps} steps, dt={dt} days")

    # Main time loop
    for step in range(1, n_steps + 1):
        day_of_year = (step * dt) % 365.0

        # Only move active particles
        active = ~beached
        n_active = np.sum(active)

        if n_active == 0:
            print(f"  Step {step}/{n_steps}: All particles beached")
            # Fill remaining history with current state
            if save_idx < n_saved:
                for i in range(save_idx, n_saved):
                    lon_history[i] = lon
                    lat_history[i] = lat
                    beached_history[i] = beached
                    times[i] = step * dt
            break

        # Get velocities for active particles
        u, v = flow.get_velocity(lon[active], lat[active], day_of_year)

        # Add windage
        u_wind = flow.get_windage(lat[active], day_of_year)
        u += u_wind

        # Add diffusion
        du, dv = flow.get_diffusion(n_active, dt)

        # Proposed new positions
        lon_new = lon[active] + (u + du) * dt
        lat_new = lat[active] + (v + dv) * dt

        # Clamp to domain bounds (with margin to keep well inside)
        lon_new = np.clip(lon_new, om.LON_MIN + 0.1, om.LON_MAX - 0.1)
        lat_new = np.clip(lat_new, om.LAT_MIN + 0.1, om.LAT_MAX - 0.1)

        # Check if new positions are in ocean
        in_ocean_new = om.is_ocean(lon_new, lat_new, grid_lon, grid_lat, ocean_mask)
        on_land = ~in_ocean_new

        # Apply land correction for particles that stepped onto land
        if np.any(on_land):
            total_land_corrections += np.sum(on_land)

            # Try half-step backtracking (up to 3 attempts)
            for attempt in range(3):
                if not np.any(on_land):
                    break

                # Compute velocity at midpoint
                lon_mid = 0.5 * (lon[active][on_land] + lon_new[on_land])
                lat_mid = 0.5 * (lat[active][on_land] + lat_new[on_land])
                u_mid, v_mid = flow.get_velocity(lon_mid, lat_mid, day_of_year)
                u_wind_mid = flow.get_windage(lat_mid, day_of_year)
                u_mid += u_wind_mid

                # Half-step update
                lon_retry = lon[active][on_land] + 0.5 * (u_mid + du[on_land]) * dt
                lat_retry = lat[active][on_land] + 0.5 * (v_mid + dv[on_land]) * dt

                # Check if retry is in ocean
                in_ocean_retry = om.is_ocean(lon_retry, lat_retry, grid_lon, grid_lat, ocean_mask)

                # Update successful retries
                lon_new[on_land] = np.where(in_ocean_retry, lon_retry, lon_new[on_land])
                lat_new[on_land] = np.where(in_ocean_retry, lat_retry, lat_new[on_land])

                # Update on_land mask
                in_ocean_new = om.is_ocean(lon_new, lat_new, grid_lon, grid_lat, ocean_mask)
                still_on_land = on_land.copy()
                on_land = ~in_ocean_new

                n_fixed = np.sum(still_on_land & ~on_land)
                if n_fixed > 0:
                    total_half_step_success += n_fixed

            # For remaining land particles, project to nearest ocean cell
            if np.any(on_land):
                lon_ocean, lat_ocean, found = om.nearest_ocean_cell(
                    lon_new[on_land], lat_new[on_land],
                    grid_lon, grid_lat, ocean_mask,
                    search_radius=3
                )

                # Update positions for found ocean cells
                lon_new[on_land] = np.where(found, lon_ocean, lon_new[on_land])
                lat_new[on_land] = np.where(found, lat_ocean, lat_new[on_land])

                n_projected = np.sum(found)
                total_projection_success += n_projected

                # Mark particles that couldn't be fixed as beached at nearest coastal cell
                if not np.all(found):
                    failed_mask = on_land.copy()
                    failed_idx = np.where(active)[0][failed_mask]
                    failed_idx = failed_idx[~found]

                    # Find nearest coastal band cell for failed particles
                    actually_beached = []
                    for f_idx in failed_idx:
                        # Search for nearest coastal band cell
                        i_center, j_center = om.get_grid_indices(
                            np.array([lon[f_idx]]), np.array([lat[f_idx]]),
                            grid_lon, grid_lat
                        )
                        i_center, j_center = i_center[0], j_center[0]

                        # Search in expanding radius
                        found_coastal = False
                        for search_radius in range(1, 15):  # Increased search radius
                            min_dist = np.inf
                            best_i, best_j = i_center, j_center

                            for di in range(-search_radius, search_radius + 1):
                                for dj in range(-search_radius, search_radius + 1):
                                    i_test = i_center + di
                                    j_test = j_center + dj

                                    if (i_test < 0 or i_test >= len(grid_lon) or
                                        j_test < 0 or j_test >= len(grid_lat)):
                                        continue

                                    if coastal_band[i_test, j_test]:
                                        dist = np.sqrt(di**2 + dj**2)
                                        if dist < min_dist:
                                            min_dist = dist
                                            best_i, best_j = i_test, j_test
                                            found_coastal = True

                            if found_coastal:
                                lon[f_idx] = grid_lon[best_i]
                                lat[f_idx] = grid_lat[best_j]
                                actually_beached.append(f_idx)
                                break

                        # If still no coastal cell found, leave particle active
                        # (it will try again next step)

                    # Mark only successfully placed particles as beached
                    if actually_beached:
                        beached[actually_beached] = True
                        total_failed_corrections += len(actually_beached)

        # Update positions for active particles that are still active
        still_active = active & ~beached
        active_indices = np.where(active)[0]
        still_active_in_active = np.arange(n_active)[~beached[active_indices]]

        lon[active_indices[still_active_in_active]] = lon_new[still_active_in_active]
        lat[active_indices[still_active_in_active]] = lat_new[still_active_in_active]

        # Apply beaching (only for particles in coastal band)
        beached, newly_beached, beached_lons, beached_lats = beaching.apply_beaching(
            lon, lat, beached, day_of_year,
            grid_lon, grid_lat, ocean_mask, coastal_band
        )

        # Update beached particle positions to their beaching locations
        if np.any(newly_beached):
            lon[newly_beached] = beached_lons[newly_beached]
            lat[newly_beached] = beached_lats[newly_beached]
            total_beached += np.sum(newly_beached)

        # Final check: ensure all active particles are in ocean
        final_active = ~beached
        if np.sum(final_active) > 0:
            final_in_ocean = om.is_ocean(
                lon[final_active], lat[final_active],
                grid_lon, grid_lat, ocean_mask
            )
            if not np.all(final_in_ocean):
                n_bad = np.sum(~final_in_ocean)
                print(f"  WARNING: Step {step}: {n_bad} active particles on land after corrections!")
                # Emergency fix: move to nearest ocean
                bad_idx = np.where(final_active)[0][~final_in_ocean]
                lon[bad_idx], lat[bad_idx], _ = om.nearest_ocean_cell(
                    lon[bad_idx], lat[bad_idx],
                    grid_lon, grid_lat, ocean_mask,
                    search_radius=5
                )

        # Final domain clamp for all particles (safety check)
        lon = np.clip(lon, om.LON_MIN + 0.05, om.LON_MAX - 0.05)
        lat = np.clip(lat, om.LAT_MIN + 0.05, om.LAT_MAX - 0.05)

        # Save if needed
        if step % save_every == 0:
            lon_history[save_idx] = lon
            lat_history[save_idx] = lat
            beached_history[save_idx] = beached
            times[save_idx] = step * dt
            save_idx += 1

        # Progress update
        if step % max(1, n_steps // 10) == 0:
            pct = 100 * step / n_steps
            n_beached = np.sum(beached)
            n_active = np.sum(~beached)
            print(f"  Step {step}/{n_steps} ({pct:.0f}%): "
                  f"{n_active} active, {n_beached} beached")

    # Compile statistics
    stats = {
        'n_particles': n_particles,
        'n_steps': n_steps,
        'dt': dt,
        'total_time_days': n_steps * dt,
        'final_active': int(np.sum(~beached)),
        'final_beached': int(np.sum(beached)),
        'total_beached_events': int(total_beached),
        'total_land_corrections': int(total_land_corrections),
        'total_half_step_success': int(total_half_step_success),
        'total_projection_success': int(total_projection_success),
        'total_failed_corrections': int(total_failed_corrections),
    }

    print(f"\nSimulation complete!")
    print(f"  Final: {stats['final_active']} active, {stats['final_beached']} beached")
    print(f"  Land corrections: {stats['total_land_corrections']}")
    print(f"    Half-step successes: {stats['total_half_step_success']}")
    print(f"    Projection successes: {stats['total_projection_success']}")
    print(f"    Failed corrections (beached): {stats['total_failed_corrections']}")

    results = {
        'lon': lon_history[:save_idx],
        'lat': lat_history[:save_idx],
        'beached': beached_history[:save_idx],
        'times': times[:save_idx],
        'stats': stats,
        'mask_data': (grid_lon, grid_lat, ocean_mask, coastal_band),
    }

    return results
