"""
File Summary:
- Ensures the project root is importable during pytest execution.
- Adds the repository path to sys.path ahead of tests that import driftcast.
- Prevents ModuleNotFoundError when dependencies are not installed globally.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

