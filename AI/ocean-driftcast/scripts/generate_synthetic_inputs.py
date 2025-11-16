"""
File Summary:
- Generates mock processed datasets to populate data/processed for demos.
- Creates simple particle catalog and coastline mask placeholders.
- Used by the `make data` target to ensure directories contain sample files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_DIR = Path("data/processed")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    n = 500
    frame = pd.DataFrame(
        {
            "lon": rng.uniform(-80, -10, size=n),
            "lat": rng.uniform(5, 60, size=n),
            "class": rng.choice(["microfiber", "fragment", "pellet"], size=n),
            "source": rng.choice(["river", "shipping", "coastal"], size=n),
        }
    )
    out_path = OUTPUT_DIR / "synthetic_particles.parquet"
    frame.to_parquet(out_path, index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
