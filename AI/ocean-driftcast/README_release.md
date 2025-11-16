# Driftcast Release Bundle

Thank you for evaluating Driftcast. This folder contains the condensed package we hand over to judges and partners. Each file is intentionally small enough for quick sharing while preserving visual fidelity.

## Folder Layout
- `hero.png` – 1080p still frame used as the hero image.
- `videos/` – Long-cut and highlight animations (H.264 MP4, 24 fps).
- `figures/` – Top dozen publication-grade figures (1600×900 PNGs).
- `docs/onepager.pdf` – One-page overview of the scenario and physics choices.
- `validation/report.json` – Golden-number sanity metrics with manifest echo.

## Reproducing the Bundle
From the repo root:
```bash
conda activate driftcast
python -m driftcast.cli publish bundle --out release/
```

The command re-renders the contents by copying the latest hero frame, videos, figures, validation report, and documentation.

## Contacts
- Oceans Four Driftcast Team – driftcast@oceansfour.example
- Project repository – https://github.com/oceans-four-driftcast

Enjoy exploring the North Atlantic subtropical gyre!
