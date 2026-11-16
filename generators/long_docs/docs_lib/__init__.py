"""Long-document builders for LD013-LD020 and LD024-LD030 (manifest 'long_docs.docs').

Modules
-------
core     world helpers (as-of names, exclusivity guard), document model, fact registry
prose    phrase banks used for realistic filler that never states new world facts
figures  raster diagrams and charts (PIL), text sized for OCR
docx_r   DOCX renderer (python-docx + raw WordprocessingML for speed)
pdf_r    PDF renderer (reportlab, invariant)
locate   post-render fact location (docx paragraphs/tables/parts, pdf pages)
b_*      one builder module per document
"""
