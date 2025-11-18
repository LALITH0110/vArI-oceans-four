"""
File Summary:
- Verifies longcut animation utilities render with optional captions.
- Uses a tiny config and monkeypatched writer for lightweight execution.
"""

from __future__ import annotations

from pathlib import Path

from driftcast.viz import animate as animate_mod
from driftcast.viz.ffmpeg import WriterConfig


def _write_toy_config(path: Path) -> Path:
    path.write_text(
        """
domain:
  lon_min: -80.0
  lon_max: -40.0
  lat_min: 20.0
  lat_max: 50.0
  resolution_deg: 1.0
gyre_box:
  lon_min: -70.0
  lon_max: -30.0
  lat_min: 20.0
  lat_max: 40.0
time:
  start: 2025-01-01T00:00:00Z
  end: 2025-01-04T00:00:00Z
  dt_minutes: 60.0
  output_interval_hours: 6.0
physics:
  diffusivity_m2s: 25.0
  windage_coeff: 0.002
  stokes_coeff: 0.05
  vertical_enabled: false
  beaching:
    probability: 0.02
    resuspension_days: 500.0
    sticky_coastline_buffer_km: 15.0
  seasonal:
    enabled: false
  ekman:
    enabled: false
output:
  directory: results/outputs
  format: netcdf
sources:
  - type: rivers
    name: toy_river
    rate_per_day: 10.0
    params:
      locations:
        - {name: toy, lon: -60.0, lat: 30.0, weight: 1.0}
      jitter_deg: 0.1
""".strip(),
        encoding="utf8",
    )
    return path


def _write_captions(path: Path) -> Path:
    path.write_text(
        """1
00:00:00,000 --> 00:00:05,000
Atlantic overview

2
00:00:05,000 --> 00:00:10,000
Source contributions

3
00:00:10,000 --> 00:00:15,000
Gyre convergence

4
00:00:15,000 --> 00:00:20,000
Beaching hotspots
""".strip(),
        encoding="utf8",
    )
    return path


def test_longcut_captions_smoke(tmp_path: Path, monkeypatch) -> None:
    config_path = _write_toy_config(tmp_path / "toy_longcut.yaml")
    captions_path = _write_captions(tmp_path / "script.srt")

    def _fake_writer(fps: int, bitrate: int, codec: str) -> WriterConfig:
        return WriterConfig(backend="matplotlib", options={"fps": fps})

    monkeypatch.setattr(animate_mod, "safe_writer", _fake_writer)

    out_path = tmp_path / "longcut.mp4"
    animate_mod.animate_longcut_captions(
        config_path=config_path,
        preset="microplastic_default",
        out=out_path,
        minutes=2.0,
        captions=captions_path,
        seed=123,
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 0
