# Copyright (c) 2025 Oceans Four Driftcast Team
# SPDX-License-Identifier: MIT
"""
File Summary:
- Validates that the animation pipeline renders stable golden frames.
- Generates deterministic frames without writing video files to disk.
- Guards against accidental styling regressions in overlays and density layers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

from matplotlib import image as mpimg
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt

from driftcast.config import load_config
from driftcast.viz.animate import AnimationSettings, create_animation_scene

GOLDEN_DIR = Path("tests/data/golden_frames")


def _build_fixture_dataset() -> xr.Dataset:
    times = np.array(
        [
            np.datetime64("2025-01-01T00:00:00"),
            np.datetime64("2025-01-01T06:00:00"),
            np.datetime64("2025-01-01T12:00:00"),
            np.datetime64("2025-01-01T18:00:00"),
        ]
    )
    particle = np.arange(6)
    lon = np.array(
        [
            [-60.0, -58.0, -56.5, -55.0, -53.5, -52.0],
            [-59.5, -57.5, -56.2, -54.7, -53.1, -51.5],
            [-59.0, -57.0, -55.9, -54.4, -52.7, -51.1],
            [-58.4, -56.6, -55.5, -53.9, -52.2, -50.6],
        ],
        dtype=float,
    )
    lat = np.array(
        [
            [28.0, 29.0, 31.0, 32.0, 33.0, 34.0],
            [28.6, 29.4, 31.4, 32.1, 33.2, 34.2],
            [29.1, 29.8, 31.6, 32.2, 33.4, 34.3],
            [29.7, 30.1, 31.9, 32.6, 33.6, 34.6],
        ],
        dtype=float,
    )
    age_days = np.linspace(0, 2, lon.size).reshape(lon.shape) / 2.0
    beached = np.zeros_like(lon, dtype=bool)
    dataset = xr.Dataset(
        data_vars={
            "lon": (("time", "particle"), lon),
            "lat": (("time", "particle"), lat),
            "age_days": (("time", "particle"), age_days),
            "beached": (("time", "particle"), beached),
        },
        coords={
            "time": times,
            "particle": particle,
            "class_name": ("particle", np.array(["micro"] * 6, dtype="U10")),
            "source_name": (
                "particle",
                np.array(["river", "river", "shipping", "shipping", "coast", "coast"], dtype="U16"),
            ),
        },
    )
    return dataset


def _capture_frames(scene, frame_indices: Iterable[int]) -> Dict[int, np.ndarray]:
    scene.init_func()
    targets = set(idx for idx in frame_indices if 0 <= idx < len(scene.frames))
    captured: Dict[int, np.ndarray] = {}
    for idx, frame_info in enumerate(scene.frames):
        scene.update_func(frame_info)
        if idx in targets:
            scene.fig.canvas.draw()
            captured[idx] = np.asarray(scene.fig.canvas.buffer_rgba()).copy()
            if len(captured) == len(targets):
                break
    return captured


def _rms_error(img_a: np.ndarray, img_b: np.ndarray) -> float:
    def _to_float255(arr: np.ndarray) -> np.ndarray:
        if arr.dtype.kind == "f":
            return (arr * 255.0).astype(np.float32)
        return arr.astype(np.float32)

    a = _to_float255(img_a)
    b = _to_float255(img_b)
    diff = a - b
    return float(np.sqrt(np.mean(diff ** 2)))


def test_golden_frames_stable() -> None:
    cfg = load_config("configs/natl_subtropical_gyre.yaml")
    dataset = _build_fixture_dataset()
    settings = AnimationSettings(
        fps=10,
        frame_repeat=1,
        width_px=640,
        height_px=360,
        dpi=100,
        title_seconds=0.5,
        credit_seconds=0.5,
        trails_length=4,
        show_density=True,
        density_alpha=0.4,
        bitrate=2000,
    )
    scene = create_animation_scene(cfg, dataset, settings, scenario_name="golden-fixture")

    captured = _capture_frames(scene, [0, 10])
    frame0 = captured.get(0)
    frame10 = captured.get(10 if 10 < len(scene.frames) else max(captured))
    plt.close(scene.fig)

    assert frame0 is not None
    assert frame10 is not None

    golden0 = mpimg.imread(GOLDEN_DIR / "frame0.png")
    golden10 = mpimg.imread(GOLDEN_DIR / "frame10.png")

    assert _rms_error(frame0, golden0) < 3.0
    assert _rms_error(frame10, golden10) < 4.5
