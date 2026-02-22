#!/usr/bin/env python3
"""Extrae páginas específicas de un PDF a PNG para documentación Just the Docs.

Uso:
  python scripts/extract_pdf_images.py --pdf "Proyecto Terminal (1).pdf"
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    import fitz  # PyMuPDF
except Exception as exc:  # noqa: BLE001
    print("ERROR: PyMuPDF no está disponible. Instala con: pip install pymupdf", file=sys.stderr)
    print(f"Detalle: {exc}", file=sys.stderr)
    sys.exit(1)


EXPORT_MAP = {
    "full-contexto-ecommerce-2019-2024.png": [2, 3, 4],
    "full-ciclo-vida-ecommerce.png": [2, 3, 4, 5],
    "full-contexto-automatizacion-metricas.png": [3, 4, 5, 6],
    "full-problematica-costos.png": [5, 6, 7, 8],
    "full-problematica-discapacidad.png": [6, 7, 8, 9, 10],
    "full-cronograma.png": [10, 11, 12, 13, 14, 15],
    "full-tabla-tareas.png": [11, 12, 13, 14, 15, 16],
    "full-arquitectura-sistema.png": [12, 13, 14, 15, 16, 17, 18],
}


def page_text(doc: fitz.Document, page_index: int) -> str:
    if page_index < 0 or page_index >= len(doc):
        return ""
    return doc[page_index].get_text("text").strip().lower()


def select_page(doc: fitz.Document, candidates: list[int], target_name: str) -> int | None:
    """Selecciona página candidata por heurística textual simple."""
    keywords = {
        "full-contexto-ecommerce-2019-2024.png": ["e-commerce", "retail", "2019", "2024"],
        "full-ciclo-vida-ecommerce.png": ["ciclo", "vida", "e-commerce", "logística"],
        "full-contexto-automatizacion-metricas.png": ["hot sale", "automatización", "robots"],
        "full-problematica-costos.png": ["costos", "logísticos", "última milla"],
        "full-problematica-discapacidad.png": ["discapacidad", "desempleo", "méxico"],
        "full-cronograma.png": ["cronograma", "semanas", "meses"],
        "full-tabla-tareas.png": ["análisis", "tareas", "logísticas"],
        "full-arquitectura-sistema.png": ["arquitectura", "servidor", "robot", "sensores"],
    }
    wanted = keywords.get(target_name, [])

    best_idx = None
    best_score = -1
    for p in candidates:
        idx = p - 1
        txt = page_text(doc, idx)
        score = sum(1 for k in wanted if k in txt)
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx is None and candidates:
        return candidates[0] - 1
    return best_idx


def render_page(doc: fitz.Document, page_index: int, out_file: Path, dpi: int = 180) -> None:
    page = doc[page_index]
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    pix.save(out_file)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Ruta al PDF fuente")
    parser.add_argument("--out", default="assets/img", help="Directorio de salida")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    out_dir = Path(args.out)

    if not pdf_path.exists():
        print(f"ERROR: No se encontró el PDF: {pdf_path}", file=sys.stderr)
        return 2

    doc = fitz.open(pdf_path)
    print(f"PDF cargado: {pdf_path} ({len(doc)} páginas)")

    for target_name, candidates in EXPORT_MAP.items():
        page_idx = select_page(doc, candidates, target_name)
        if page_idx is None or page_idx < 0 or page_idx >= len(doc):
            print(f"[SKIP] {target_name}: no se encontró página válida (candidatas={candidates})")
            continue
        out_file = out_dir / target_name
        render_page(doc, page_idx, out_file)
        print(f"[OK] página {page_idx + 1} -> {out_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
