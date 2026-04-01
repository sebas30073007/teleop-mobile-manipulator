# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Preview

```bash
bundle install                  # install Ruby dependencies
bundle exec jekyll serve        # build and serve at http://localhost:4000
bundle exec jekyll build        # build only (output to _site/)
```

Deployment to GitHub Pages is handled automatically by `.github/workflows/pages.yml` on push to `main`.

## Stack

- **Jekyll 4.4.1** static site generator
- **Just the Docs 0.12.0** theme (gem-based)
- All content is Markdown; no Node.js, no npm

## Navigation Architecture (Just the Docs)

Page hierarchy is controlled entirely via front matter — not directory structure. Key fields:

```yaml
---
title: "Page Title"
nav_order: 1          # ordering within a level
parent: "Parent Title" # exact title string of parent page
has_children: true    # required on pages that have children
nav_exclude: true     # hides from nav (used on docs/index.md)
---
```

The `parent:` value must match the `title:` of the parent page exactly (string match). Missing or mismatched `parent:` will break the hierarchy silently.

All pages must have `layout: default` — this is applied globally via `_config.yml` defaults so explicit front matter is not needed.

## Content Structure

```
index.md                        # root homepage (served at /)
docs/
  index.md                      # nav_exclude: true duplicate homepage
  01-reporte/                   # project research report (12 pages)
  03-implementacion/
    01-robot-agv/               # mobile robot + manipulator (6 pages)
      index.md, plataforma-movil.md, manipulador.md,
      electronica.md, software.md, pruebas.md
    02-servidor/                # server/middleware (4 pages)
      index.md, middleware.md, percepcion.md, pruebas.md
    03-xr-metaquest/            # XR / Meta Quest (4 pages)
      index.md, unity.md, interfaz.md, pruebas.md
  04-integracion-validacion/    # integration testing & results (4 pages)
```

Documentation is written in Spanish.

## Assets

```
assets/
  img/          # web images — all with clean snake_case names
  downloads/    # downloadable files (PDF datasheets, KiCad zip)
  models/       # 3D models for model-viewer (GLB/STL)
  raw_assets/   # originals — do NOT serve directly; too large for web
```

Use `{{ "/assets/img/filename.jpg" | relative_url }}` for all asset paths in Markdown to handle GitHub Pages subpath correctly.

## Jekyll Includes

Two reusable includes in `_includes/`:

```liquid
{% include video_youtube.html id="YOUTUBE_VIDEO_ID" title="Optional title" %}
{% include model_viewer.html src="/assets/models/file.glb" alt="Description" %}
```

`model_viewer.html` uses the `<model-viewer>` Google web component (loaded from CDN). Supports `.glb` and `.gltf` natively.

## Download Buttons

Use Just the Docs button classes:

```markdown
[⬇ Texto del botón](/assets/downloads/file.pdf){: .btn .btn-outline }
```

## `_config.yml` Notes

The `title`, `description`, `url`, and `aux_links` fields are still set to the upstream template defaults and should be updated to reflect the actual project.

## Utility Script

`scripts/extract_pdf_images.py` extracts specific pages from PDFs and saves them as PNGs to `assets/img/`. Requires `PyMuPDF` (`pip install pymupdf`). Edit the `EXPORT_MAPS` dict inside the script to add new PDF → image mappings.
