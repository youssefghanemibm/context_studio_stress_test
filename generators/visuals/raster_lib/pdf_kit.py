"""Raster PDF builder: each page is one full-bleed raster image plus a title-only text layer.

reportlab with invariant=1; then pikepdf stamps the document date into /CreationDate and
/ModDate and saves with a deterministic /ID, so the output is byte-stable.
"""
from __future__ import annotations

import io
import pathlib
from typing import Sequence

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

A3_LAND = (1190.55, 841.89)
A4_LAND = (841.89, 595.28)
A4_PORT = (595.28, 841.89)
TITLE_BAND_PT = 34


def page_pixels(page_size, dpi: int = 200, title_band: bool = True) -> tuple[int, int]:
    """Pixel size of the raster area for a page (excluding the text-layer title band)."""
    w_pt, h_pt = page_size
    h_area = h_pt - (TITLE_BAND_PT if title_band else 0)
    return (int(round(w_pt / 72 * dpi)), int(round(h_area / 72 * dpi)))


def build_raster_pdf(path: pathlib.Path, pages: Sequence[tuple[Image.Image, str]], page_size, title: str,
                     author: str, subject: str, date: str, keywords: str = "", jpeg_quality: int | None = None) -> int:
    """pages: (image, title_text). The image fills the page below a thin text-layer title band."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=page_size, invariant=1, pageCompression=1)
    c.setTitle(title)
    c.setAuthor(author)
    c.setSubject(subject)
    c.setKeywords(keywords)
    c.setCreator("Corvane Mutual document services")
    w_pt, h_pt = page_size
    for im, ttl in pages:
        im = im.convert("RGB")
        if jpeg_quality:
            jb = io.BytesIO()
            im.save(jb, format="JPEG", quality=jpeg_quality, optimize=False, subsampling=0)
            jb.seek(0)
            reader = ImageReader(jb)
        else:
            reader = ImageReader(im)
        area_h = h_pt - TITLE_BAND_PT
        c.drawImage(reader, 0, 0, width=w_pt, height=area_h)
        c.setFillColorRGB(0.08, 0.2, 0.36)
        c.rect(0, area_h, w_pt, TITLE_BAND_PT, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(18, area_h + 11, ttl)
        c.showPage()
    c.save()
    _finalise(buf.getvalue(), path, date)
    return len(pages)


def _finalise(data: bytes, path: pathlib.Path, date: str) -> None:
    import pikepdf
    pdf = pikepdf.open(io.BytesIO(data))
    stamp = "D:" + date.replace("-", "") + "090000Z"
    pdf.docinfo["/CreationDate"] = stamp
    pdf.docinfo["/ModDate"] = stamp
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = io.BytesIO()
    pdf.save(out, deterministic_id=True, compress_streams=True)
    path.write_bytes(out.getvalue())
