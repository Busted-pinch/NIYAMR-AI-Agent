# src/extract_text.py
"""
Extract text from PDFs in data/ and write structured sections to outputs/extracted_sections.json.
Assumes PDFs are in data/ (host) and outputs/ is writable.
"""
from pathlib import Path
import pdfplumber
import re
import json

# Paths (consistent)
DATA_DIR = Path("data")
PDF = DATA_DIR / "ukpga_20250022_en.pdf"
OUT_DIR = Path("outputs")
OUT = OUT_DIR / "extracted_sections.json"

def normalize_whitespace(s):
    return re.sub(r'\s+', ' ', s).strip()

def split_into_sections(text):
    # split at headings likely to be used in UK Acts (Section, SCHEDULE, CHAPTER, CONTENTS, Schedule)
    parts = re.split(r'\n(?=(?:Section|SECTION|SCHEDULE|Schedule|CHAPTER|CONTENTS|Short title)\b)', text)
    sections = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # attempt a title from first line up to 200 chars
        first_line = p.split('\n', 1)[0].strip()
        title = first_line[:200]
        sections.append({"title": title, "text": normalize_whitespace(p)})
    return sections

def extract_pdf_text(pdf_path):
    pages = []
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            txt = page.extract_text() or ""
            pages.append({"page": i + 1, "text": txt})
    return pages

def aggregate_pages(pages):
    return "\n".join(p["text"] or "" for p in pages)

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pages = extract_pdf_text(PDF)
    whole = aggregate_pages(pages)
    sections = split_into_sections(whole)
    OUT.write_text(json.dumps({"sections": sections}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT}, sections: {len(sections)}")

if __name__ == "__main__":
    main()

