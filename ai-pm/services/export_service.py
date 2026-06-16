"""Convert generated markdown documents (PRD, BDD stories) into Word and PDF.

Both conversions start from the same markdown the pipeline produced, so the
document's structure and formatting are preserved — we never regenerate or
reflow content. Pure-Python only (pandoc binary is bundled via the
`pypandoc-binary` wheel; xhtml2pdf needs no system libraries), so this deploys
on Streamlit Cloud with pip alone.

The UI layer (app.py) wraps these in st.cache_data so each document is converted
once rather than on every rerun.
"""
from __future__ import annotations

import io
import os
import tempfile

import markdown as _markdown

# Markdown extensions that cover everything the PRD/BDD prompts emit:
# tables, fenced code (Gherkin blocks), and correctly-nested bullet/number lists.
_MD_EXTENSIONS = ["extra", "sane_lists", "tables", "fenced_code", "nl2br"]

# Print stylesheet for the PDF. xhtml2pdf supports a CSS subset; this keeps the
# document looking like a clean office document (margins, heading sizes, tables).
_PDF_CSS = """
@page { size: A4; margin: 2cm 2cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; color: #111827;
       line-height: 1.4; }
h1 { font-size: 20pt; margin: 0 0 10pt 0; }
h2 { font-size: 15pt; margin: 16pt 0 6pt 0; border-bottom: 1px solid #d1d5db;
     padding-bottom: 3pt; }
h3 { font-size: 13pt; margin: 12pt 0 4pt 0; }
h4 { font-size: 11.5pt; margin: 10pt 0 4pt 0; }
p { margin: 0 0 7pt 0; }
ul, ol { margin: 0 0 7pt 18pt; }
li { margin: 0 0 2pt 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; }
th, td { border: 1px solid #cbd5e1; padding: 4pt 6pt; font-size: 10pt; text-align: left; }
th { background: #f3f4f6; }
code { font-family: Courier, monospace; font-size: 10pt; background: #f3f4f6; }
pre { background: #f8fafc; border: 1px solid #e5e7eb; padding: 6pt; font-size: 9.5pt;
      white-space: pre-wrap; }
hr { border: none; border-top: 1px solid #d1d5db; margin: 12pt 0; }
"""


def md_to_docx_bytes(md_text: str) -> bytes:
    """Convert markdown to a .docx byte string via pandoc (bundled binary)."""
    import pypandoc

    # pandoc must write binary formats to a file, so round-trip through a temp.
    fd, tmp_path = tempfile.mkstemp(suffix=".docx")
    os.close(fd)
    try:
        pypandoc.convert_text(md_text, "docx", format="markdown", outputfile=tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def md_to_pdf_bytes(md_text: str) -> bytes:
    """Convert markdown to a PDF byte string (markdown → HTML → xhtml2pdf)."""
    from xhtml2pdf import pisa

    body = _markdown.markdown(md_text, extensions=_MD_EXTENSIONS)
    html = f"<html><head><style>{_PDF_CSS}</style></head><body>{body}</body></html>"
    buf = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buf, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"PDF generation failed ({result.err} error(s)).")
    return buf.getvalue()
