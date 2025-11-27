"""
Quality control checks for particle simulation results.

Validates that:
1. No active particles are on land (inland_alive = 0)
2. All beached particles are in the coastal band (offshore_beached = 0)
3. All positions are within domain bounds
"""

import numpy as np
import json
import ocean_mask as om


def check_frame(lon, lat, beached, grid_lon, grid_lat, ocean_mask, coastal_band,
                extent=(-100, 20, 0, 60)):
    """
    Run QC checks on a single frame.

    Parameters
    ----------
    lon : ndarray
        Particle longitudes
    lat : ndarray
        Particle latitudes
    beached : ndarray (bool)
        Beached status
    grid_lon : ndarray
        Grid longitude centers
    grid_lat : ndarray
        Grid latitude centers
    ocean_mask : ndarray (bool)
        Ocean mask
    coastal_band : ndarray (bool)
        Coastal band mask
    extent : tuple
        Domain bounds (lon_min, lon_max, lat_min, lat_max)

    Returns
    -------
    qc_result : dict
        Dictionary with QC metrics:
        - inland_alive: count of active particles on land
        - offshore_beached: count of beached particles not in coastal band
        - out_of_domain: count of particles outside domain
        - all_pass: True if all checks pass
    """
    active = ~beached

    # Check 1: Active particles on land (MUST BE 0)
    if np.sum(active) > 0:
        in_ocean_active = om.is_ocean(lon[active], lat[active], grid_lon, grid_lat, ocean_mask)
        inland_alive = np.sum(~in_ocean_active)
    else:
        inland_alive = 0

    # Check 2: Beached particles outside coastal band (MUST BE 0)
    if np.sum(beached) > 0:
        i, j = om.get_grid_indices(lon[beached], lat[beached], grid_lon, grid_lat)
        in_coastal_beached = coastal_band[i, j]
        offshore_beached = np.sum(~in_coastal_beached)
    else:
        offshore_beached = 0

    # Check 3: Particles outside domain
    lon_min, lon_max, lat_min, lat_max = extent
    out_of_domain = np.sum(
        (lon < lon_min) | (lon > lon_max) |
        (lat < lat_min) | (lat > lat_max)
    )

    # Overall pass
    all_pass = (inland_alive == 0) and (offshore_beached == 0) and (out_of_domain == 0)

    qc_result = {
        'inland_alive': int(inland_alive),
        'offshore_beached': int(offshore_beached),
        'out_of_domain': int(out_of_domain),
        'all_pass': bool(all_pass),
    }

    return qc_result


def check_all_frames(lon_history, lat_history, beached_history,
                     grid_lon, grid_lat, ocean_mask, coastal_band,
                     extent=(-100, 20, 0, 60)):
    """
    Run QC checks on all frames.

    Parameters
    ----------
    lon_history : ndarray (n_frames, n_particles)
        Longitude history
    lat_history : ndarray (n_frames, n_particles)
        Latitude history
    beached_history : ndarray (n_frames, n_particles)
        Beached status history
    grid_lon : ndarray
        Grid longitude centers
    grid_lat : ndarray
        Grid latitude centers
    ocean_mask : ndarray (bool)
        Ocean mask
    coastal_band : ndarray (bool)
        Coastal band mask
    extent : tuple
        Domain bounds

    Returns
    -------
    qc_report : dict
        Full QC report with per-frame and aggregate statistics
    """
    print("\nRunning QC checks on all frames...")

    n_frames, n_particles = lon_history.shape

    # Per-frame results
    frame_results = []

    # Aggregate counters
    total_inland_alive = 0
    total_offshore_beached = 0
    total_out_of_domain = 0
    n_frames_failed = 0

    for frame_idx in range(n_frames):
        lon = lon_history[frame_idx]
        lat = lat_history[frame_idx]
        beached = beached_history[frame_idx]

        qc = check_frame(lon, lat, beached,
                        grid_lon, grid_lat, ocean_mask, coastal_band,
                        extent)

        frame_results.append(qc)

        total_inland_alive += qc['inland_alive']
        total_offshore_beached += qc['offshore_beached']
        total_out_of_domain += qc['out_of_domain']

        if not qc['all_pass']:
            n_frames_failed += 1

    # Find worst frames
    inland_alive_counts = [r['inland_alive'] for r in frame_results]
    offshore_beached_counts = [r['offshore_beached'] for r in frame_results]

    max_inland_alive = max(inland_alive_counts)
    max_offshore_beached = max(offshore_beached_counts)

    # Overall pass
    all_frames_pass = (n_frames_failed == 0)

    # Summary
    qc_report = {
        'summary': {
            'n_frames': n_frames,
            'n_particles': n_particles,
            'all_frames_pass': all_frames_pass,
            'n_frames_failed': n_frames_failed,
            'total_inland_alive_violations': total_inland_alive,
            'total_offshore_beached_violations': total_offshore_beached,
            'total_out_of_domain_violations': total_out_of_domain,
            'max_inland_alive_per_frame': max_inland_alive,
            'max_offshore_beached_per_frame': max_offshore_beached,
        },
        'per_frame': frame_results,
        'pass_flags': {
            'no_inland_alive': (max_inland_alive == 0),
            'no_offshore_beached': (max_offshore_beached == 0),
            'all_in_domain': (total_out_of_domain == 0),
        }
    }

    # Print summary
    print(f"  Total frames: {n_frames}")
    print(f"  Frames passed: {n_frames - n_frames_failed}/{n_frames}")
    print(f"\n  QC Metrics:")
    print(f"    inland_alive (max): {max_inland_alive} (MUST BE 0)")
    print(f"    offshore_beached (max): {max_offshore_beached} (MUST BE 0)")
    print(f"    out_of_domain (total): {total_out_of_domain}")

    if all_frames_pass:
        print(f"\n  [PASS] ALL QC CHECKS PASSED!")
    else:
        print(f"\n  [FAIL] QC CHECKS FAILED ({n_frames_failed} frames)")
        if max_inland_alive > 0:
            print(f"    - Active particles on land detected!")
        if max_offshore_beached > 0:
            print(f"    - Beached particles offshore detected!")

    return qc_report


def save_qc_report(qc_report, output_path='outputs/qc_report.json'):
    """
    Save QC report to JSON file.

    Parameters
    ----------
    qc_report : dict
        QC report from check_all_frames
    output_path : str
        Output file path
    """
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(qc_report, f, indent=2)

    print(f"\n  QC report saved: {output_path}")


def print_qc_summary(qc_report):
    """
    Print one-line QC summary.

    Parameters
    ----------
    qc_report : dict
        QC report from check_all_frames
    """
    summary = qc_report['summary']

    status = "PASS" if summary['all_frames_pass'] else "FAIL"

    print(f"\nQC Summary: {status} | "
          f"inland_alive={summary['max_inland_alive_per_frame']} | "
          f"offshore_beached={summary['max_offshore_beached_per_frame']} | "
          f"out_of_domain={summary['total_out_of_domain_violations']}")


def diagnose_failures(qc_report, lon_history, lat_history, beached_history,
                      grid_lon, grid_lat, ocean_mask, coastal_band):
    """
    Diagnose which particles/frames are failing QC.

    Parameters
    ----------
    qc_report : dict
        QC report
    lon_history : ndarray
        Longitude history
    lat_history : ndarray
        Latitude history
    beached_history : ndarray
        Beached status history
    grid_lon : ndarray
        Grid longitude centers
    grid_lat : ndarray
        Grid latitude centers
    ocean_mask : ndarray
        Ocean mask
    coastal_band : ndarray
        Coastal band mask
    """
    summary = qc_report['summary']

    if summary['all_frames_pass']:
        print("\nNo QC failures to diagnose.")
        return

    print("\n" + "="*70)
    print("QC FAILURE DIAGNOSIS")
    print("="*70)

    # Find failing frames
    failing_frames = []
    for frame_idx, result in enumerate(qc_report['per_frame']):
        if not result['all_pass']:
            failing_frames.append((frame_idx, result))

    print(f"\nFound {len(failing_frames)} failing frames:")

    for frame_idx, result in failing_frames[:10]:  # Show first 10
        print(f"\n  Frame {frame_idx}:")
        print(f"    inland_alive: {result['inland_alive']}")
        print(f"    offshore_beached: {result['offshore_beached']}")
        print(f"    out_of_domain: {result['out_of_domain']}")

        # Show particle details for this frame
        lon = lon_history[frame_idx]
        lat = lat_history[frame_idx]
        beached = beached_history[frame_idx]
        active = ~beached

        if result['inland_alive'] > 0:
            in_ocean = om.is_ocean(lon[active], lat[active], grid_lon, grid_lat, ocean_mask)
            bad_idx = np.where(active)[0][~in_ocean]
            print(f"    Particles on land: {bad_idx[:5].tolist()} (showing first 5)")
            print(f"      Positions: {list(zip(lon[bad_idx[:3]], lat[bad_idx[:3]]))}")

    if len(failing_frames) > 10:
        print(f"\n  ... and {len(failing_frames) - 10} more failing frames")

    print("\n" + "="*70)
