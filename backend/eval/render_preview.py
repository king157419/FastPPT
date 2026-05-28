"""Render a .pptx to per-slide PNGs so the design can be visually inspected.

Pipeline: pptx --(LibreOffice headless)--> pdf --(PyMuPDF)--> PNG per page.
Usage:
    python eval/render_preview.py <deck.pptx> [out_dir] [dpi]
Prints the produced PNG paths (one per slide) for visual review.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

import fitz  # PyMuPDF

_SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "soffice",
    "libreoffice",
]


def _find_soffice() -> str:
    for cand in _SOFFICE_CANDIDATES:
        if os.path.isabs(cand) and os.path.exists(cand):
            return cand
    # fall back to PATH lookup
    from shutil import which

    for name in ("soffice", "libreoffice"):
        found = which(name)
        if found:
            return found
    raise FileNotFoundError("LibreOffice (soffice) not found. Install it first.")


def pptx_to_pdf(pptx_path: str, out_dir: str) -> str:
    soffice = _find_soffice()
    os.makedirs(out_dir, exist_ok=True)
    # Isolated profile avoids 'soffice already running' profile locks.
    profile_dir = os.path.join(tempfile.gettempdir(), "fastppt_lo_profile")
    profile_uri = "file:///" + os.path.abspath(profile_dir).replace("\\", "/")
    cmd = [
        soffice,
        "--headless",
        "--norestore",
        "--nolockcheck",
        f"-env:UserInstallation={profile_uri}",
        "--convert-to",
        "pdf",
        "--outdir",
        out_dir,
        pptx_path,
    ]
    subprocess.run(cmd, check=True, timeout=180, capture_output=True)
    base = os.path.splitext(os.path.basename(pptx_path))[0]
    pdf_path = os.path.join(out_dir, base + ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"PDF not produced at {pdf_path}")
    return pdf_path


def pdf_to_pngs(pdf_path: str, out_dir: str, dpi: int = 120) -> list[str]:
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    doc = fitz.open(pdf_path)
    paths: list[str] = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        png = os.path.join(out_dir, f"{base}_p{i + 1:02d}.png")
        pix.save(png)
        paths.append(png)
    doc.close()
    return paths


def render(pptx_path: str, out_dir: str | None = None, dpi: int = 120) -> list[str]:
    out_dir = out_dir or os.path.join(os.path.dirname(os.path.abspath(pptx_path)), "_preview")
    pdf_path = pptx_to_pdf(pptx_path, out_dir)
    return pdf_to_pngs(pdf_path, out_dir, dpi=dpi)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python eval/render_preview.py <deck.pptx> [out_dir] [dpi]")
    deck = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    dpi_arg = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    pngs = render(deck, out, dpi_arg)
    print(f"rendered {len(pngs)} slides:")
    for p in pngs:
        print(p)
