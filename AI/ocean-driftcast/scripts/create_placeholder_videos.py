"""
File Summary:
- Generates lightweight placeholder MP4 videos for preview and final cut slots.
- Useful for CI smoke tests when the full animation pipeline is unavailable.
- Produces simple text-based frames at 24 fps using Matplotlib + FFmpeg.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.animation import FFMpegWriter


def render_placeholder(path: Path, title: str, subtitle: str, frames: int) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    writer = FFMpegWriter(fps=24)
    path.parent.mkdir(parents=True, exist_ok=True)
    with writer.saving(fig, str(path), 100):
        for idx in range(frames):
            ax.clear()
            ax.set_facecolor("#0b1d3a")
            fig.patch.set_facecolor("#0b1d3a")
            ax.text(
                0.5,
                0.6,
                title,
                ha="center",
                va="center",
                color="#f1f0ea",
                fontsize=36,
                weight="bold",
            )
            ax.text(
                0.5,
                0.45,
                f"{subtitle} {idx + 1}",
                ha="center",
                va="center",
                color="#cdd1c4",
                fontsize=20,
            )
            ax.axis("off")
            writer.grab_frame()
    plt.close(fig)


def main() -> None:
    render_placeholder(
        Path("results/videos/preview.mp4"),
        "Driftcast Preview",
        "Placeholder frame",
        frames=72,
    )
    render_placeholder(
        Path("results/videos/final_cut.mp4"),
        "Driftcast Final Cut",
        "Storyboard frame",
        frames=180,
    )


if __name__ == "__main__":
    main()
