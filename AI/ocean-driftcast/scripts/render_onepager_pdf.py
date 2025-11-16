# Copyright (c) 2025 Oceans Four Driftcast Team
# SPDX-License-Identifier: MIT
"""
File Summary:
- Generates docs/onepager.pdf from a minimal PDF template without extras.
- Encodes a concise message mirroring docs/onepager.md.
- Run manually (python scripts/render_onepager_pdf.py) when refreshing the PDF.
"""

from __future__ import annotations

from pathlib import Path

PDF_PATH = Path("docs/onepager.pdf")


def build_pdf() -> bytes:
    """Construct a single-page PDF with simple text content."""
    stream = (
        "BT\n"
        "/F1 24 Tf\n"
        "72 780 Td\n"
        "(Driftcast One-Pager) Tj\n"
        "/F1 12 Tf\n"
        "0 -30 Td\n"
        "(Mission: Produce judge-ready North Atlantic drift forecasts in minutes.) Tj\n"
        "0 -20 Td\n"
        "(Workflow: Configure -> Run -> Manifest -> Animate -> Deliver.) Tj\n"
        "0 -20 Td\n"
        "(One command: `driftcast judge` -> MP4, hero PNG, one-pager.) Tj\n"
        "ET\n"
    ).encode("ascii")

    body = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []

    def add(obj_bytes: bytes) -> None:
        offsets.append(len(body))
        body.extend(obj_bytes)

    add(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    add(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    add(
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    add(
        f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("ascii")
        + stream
        + b"endstream\nendobj\n"
    )
    add(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    xref_offset = len(body)
    xref = ["xref", f"0 {len(offsets) + 1}", "0000000000 65535 f "]
    for off in offsets:
        xref.append(f"{off:010} 00000 n ")
    body.extend(("\n".join(xref) + "\n").encode("ascii"))
    body.extend(
        f"trailer << /Size {len(offsets) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return bytes(body)


def main() -> None:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = build_pdf()
    PDF_PATH.write_bytes(pdf_bytes)
    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    main()
