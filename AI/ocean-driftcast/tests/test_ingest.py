"""
File Summary:
- Tests crowdsourced JSON ingestion pipeline and schema validation.
- Confirms Parquet output structure and data types.
- Uses the bundled mock JSON file for deterministic results.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from driftcast.ingest.normalize import ingest_json_file
from driftcast.ingest.schema import CrowdSchema


def test_ingest_mock_crowd_json(tmp_path: Path) -> None:
    schema = CrowdSchema.load("schemas/crowd_drifters.schema.json")
    output_path = ingest_json_file("data/raw/mock_crowd.json", schema=schema, output_dir=tmp_path)
    assert output_path.exists()
    frame = pd.read_parquet(output_path)
    assert "timestamp" in frame.columns
    assert frame["lat"].between(-90, 90).all()
    assert frame["lon"].between(-180, 180).all()
