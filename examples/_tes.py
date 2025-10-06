"""Simple PDF to text example (marker-pdf removed).

This replaces the previous Marker PDF example with a lightweight
implementation using PyPDF2, which is already a project dependency.

If you need richer layout-aware Markdown conversion in the future,
consider integrating another maintained library or a hosted service.
"""

from pathlib import Path

from typing import List

from PyPDF2 import PdfReader  # type: ignore

PDF_PATH = Path(__file__).parent / "curriculum.pdf"


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    texts: List[str] = []
    for page in reader.pages:
        # extract_text can return None
        txt = page.extract_text() or ""
        texts.append(txt.strip())
    filtered: List[str] = [t for t in texts if t]
    return "\n\n".join(filtered)


def main() -> None:
    if not PDF_PATH.exists():
        raise SystemExit(f"PDF not found: {PDF_PATH}")
    text = extract_pdf_text(PDF_PATH)
    # Show only the first 1000 chars to avoid dumping huge output
    preview = text[:1000]
    print(preview)
    if len(text) > 1000:
        print("\n... (truncated) ...")


if __name__ == "__main__":
    main()
