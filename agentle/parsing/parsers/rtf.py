"""RTF (Rich Text Format) Document Parser Module

This module provides functionality for parsing RTF documents (.rtf) into a
structured representation. RTF is a plaintext markup format that encodes text
styling using control words (e.g. \\b, \\i, \\par) and groups enclosed in braces.
For the purposes of most LLM and downstream text processing tasks we only need
the plain textual content. This parser performs a best‑effort extraction of the
visible text while discarding formatting directives.

Design goals:
1. Zero heavy dependencies (pure‑python fallback) while leveraging MarkItDown
   if available for richer markdown output.
2. Resilient to malformed / truncated RTF (skips over unmatched braces and
   unknown control words instead of failing).
3. Unicode escape handling for the common \\uNNNN? pattern, hex escaped bytes
    (\\'hh) decoded as latin1 and re‑encoded to unicode.
4. Single section output (similar to .txt parser) – most RTF files are short
   documents; structural pagination is not inherent in RTF.

Limitations / Non‑Goals:
* Advanced table, list, or image extraction is intentionally not implemented.
* Embedded pictures (\\pict) are skipped – implementing full decoding adds
  complexity and usually offers little value for text‑centric workflows.

Usage Example:
```python
from agentle.parsing.parsers.rtf import RtfFileParser

parser = RtfFileParser()
parsed = parser.parse("example.rtf")
print(parsed.sections[0].text[:200])
```
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Literal

from agentle.parsing.document_parser import DocumentParser
from agentle.parsing.parsed_file import ParsedFile
from agentle.parsing.section_content import SectionContent
from agentle.utils.file_validation import (
    FileValidationError,
    resolve_file_path,
    validate_file_exists,
)

logger = logging.getLogger(__name__)


class RtfFileParser(DocumentParser):
    """Parser for processing Rich Text Format (.rtf) documents.

    The parser performs a lightweight conversion of RTF to plain text / markdown
    by removing control words and decoding common escape sequences. If the
    optional dependency `markitdown` is available it is used first to obtain a
    markdown representation; otherwise a built‑in fallback routine `_rtf_to_text`
    is used.
    """

    type: Literal["rtf"] = "rtf"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def parse_async(self, document_path: str) -> ParsedFile:  # noqa: D401
        """Parse an RTF file into a single section.

        Steps:
        1. Validate & resolve path.
        2. Try high‑fidelity conversion with `markitdown` (best effort).
        3. If unavailable / fails, fall back to internal lightweight parser.
        4. Return a single `SectionContent` section with both `text` & `md`.
        """
        try:
            resolved_path = resolve_file_path(document_path)
            validate_file_exists(resolved_path)
        except FileValidationError as e:  # pragma: no cover - validation paths
            logger.error("RTF file validation failed: %s", e)
            raise ValueError(f"RTF file validation failed: {e}") from e

        path = Path(resolved_path)
        logger.debug("Parsing RTF file: %s", resolved_path)

        raw_bytes: bytes
        try:
            raw_bytes = path.read_bytes()
        except PermissionError as e:
            raise ValueError(
                f"Permission denied: Cannot read file '{document_path}'."
            ) from e
        except OSError as e:
            raise ValueError(f"Failed to read RTF file '{document_path}': {e}") from e

        # Decode as latin-1 to preserve byte values; RTF escapes will be handled.
        raw_text = raw_bytes.decode("latin-1", errors="replace")
        # Normalize escape variants
        raw_text = raw_text.replace(
            "\\\\u", "\\u"
        )  # double backslash unicode -> single
        raw_text = raw_text.replace(
            "\\n", "\n"
        )  # literal backslash-n sequences -> newline

        # Always use internal fallback for now (striprtf caused token loss in tests)
        chosen = self._rtf_to_text(raw_text)

        # Optional markdown conversion (best effort)
        markdown: str | None = None
        try:  # pragma: no cover
            from markitdown import MarkItDown  # type: ignore

            md_converter = MarkItDown(enable_plugins=False)
            md_result = md_converter.convert(str(path))
            md_val = getattr(md_result, "markdown", None)  # type: ignore[attr-defined]
            if md_val and not str(md_val).lstrip().lower().startswith("{\\rtf"):
                markdown = str(md_val)
        except Exception:
            pass

        if markdown is None:
            markdown = chosen

        if not chosen.strip():  # empty after parsing
            logger.warning("RTF file appears empty after parsing: %s", resolved_path)

        section = SectionContent(number=1, text=chosen, md=markdown)
        return ParsedFile(name=path.name, sections=[section])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    _CONTROL_WORD_RE = re.compile(r"\\[a-zA-Z]{1,32}(?:-?\d+)? ?")
    _UNICODE_RE = re.compile(r"\\u(-?\d+)(?:\\'..)?")  # \uN optional fallback
    _HEX_RE = re.compile(r"\\'[0-9a-fA-F]{2}")

    def _rtf_to_text(self, data: str) -> str:
        """Minimal fallback RTF->text implementation (pure Python)."""
        head = data.lower()[:15]
        if "{\\rtf" not in head:
            return data

        skip_groups = {"fonttbl", "colortbl", "stylesheet", "info", "pict"}
        out: list[str] = []
        stack: list[bool] = []  # track whether current group is skipped
        i = 0
        L = len(data)
        while i < L:
            ch = data[i]
            if ch == "{":
                # Determine if this group should be skipped
                j = i + 1
                dest = None
                if j < L and data[j] == "\\":
                    m_dest = re.match(r"\\([a-zA-Z]+)", data[j:])
                    if m_dest:
                        dest = m_dest.group(1)
                skip = dest in skip_groups if dest else False
                stack.append(skip or (stack[-1] if stack else False))
                i += 1
                continue
            if ch == "}":
                if stack:
                    stack.pop()
                i += 1
                continue
            if stack and stack[-1]:
                i += 1
                continue
            if ch == "\\":
                # Escaped literal
                if i + 1 < L and data[i + 1] in ("\\", "{", "}"):
                    out.append(data[i + 1])
                    i += 2
                    continue
                # Hex escape \'hh
                if (
                    i + 3 < L
                    and data[i + 1] == "'"
                    and all(c in "0123456789abcdefABCDEF" for c in data[i + 2 : i + 4])
                ):
                    try:
                        out.append(bytes.fromhex(data[i + 2 : i + 4]).decode("latin-1"))
                    except Exception:
                        pass
                    i += 4
                    continue
                # Unicode \uNNNN?
                m_u = re.match(r"\\u(-?\d+)(?:\\'..)?", data[i:])
                if m_u:
                    try:
                        val = int(m_u.group(1))
                        if val < 0:
                            val += 1 << 16
                        out.append(chr(val))
                    except Exception:
                        pass
                    i += len(m_u.group(0))
                    continue
                # Control word
                m_cw = re.match(r"\\([A-Za-z]+)(-?\d+)? ?", data[i:])
                if m_cw:
                    word = m_cw.group(1)
                    if word in {"par", "line"}:
                        out.append("\n")
                    elif word == "tab":
                        out.append("\t")
                    i += len(m_cw.group(0))
                    continue
                # Lone backslash fallback
                i += 1
                continue
            out.append(ch)
            i += 1

        text = "".join(out)
        text = text.replace("\r", "")
        lines = [ln.rstrip() for ln in text.splitlines()]
        collapsed: list[str] = []
        blank = False
        for ln in lines:
            if not ln.strip():
                if not blank:
                    collapsed.append("")
                blank = True
            else:
                collapsed.append(ln.strip())
                blank = False
        return "\n".join(collapsed).strip()

    def _markdown_to_plain(self, md: str) -> str:
        # Extremely small helper – reuse logic similar to PDF whitespace collapse
        text = re.sub(r"`{3}.*?`{3}", "", md, flags=re.DOTALL)  # remove fenced code
        text = re.sub(r"`([^`]+)`", r"\1", text)  # inline code
        text = re.sub(r"\s+", " ", text)
        return text.strip()
