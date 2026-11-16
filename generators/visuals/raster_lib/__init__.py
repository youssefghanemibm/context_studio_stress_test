"""Raster drawing kit for the image-led visuals (VS029-VS050).

Everything here is deterministic: no randomness except what callers pass in from
``generators.common.util.rng``, no wall clock, fonts from ``util.font`` (DejaVu Sans).

Modules
-------
core      Canvas (PIL) with text wrapping, boxes, arrows, label pills
diagrams  node/edge diagrams, ERDs, swimlanes, org charts, table images, roadmaps, maps
screens   mock UIs: Claims Hub web screens, CLARA 3270 maps, Sentinel dashboard
charts    matplotlib charts rendered to PIL images (data lives only in pixels)
docx_kit  python-docx builder: cover, document control, figures with captions/alt text,
          comments, headers/footers, fact locators
pdf_kit   reportlab raster PDF builder (raster pages + title-only text layer)
phrases   rng-driven phrase banks for neutral surrounding prose
"""
