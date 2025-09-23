from pathlib import Path

import pytest

from agentle.parsing.parsers.file_parser import FileParser
from agentle.parsing.parses import parser_registry


@pytest.mark.asyncio
async def test_uppercase_extension_supported(tmp_path: Path):
    # Create a dummy empty PDF file
    test_file = tmp_path / "sample.PDF"
    test_file.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    # Sanity: parser for pdf is registered
    assert "pdf" in parser_registry

    parser = FileParser()
    # Should not raise
    result = await parser.parse_async(str(test_file))

    assert result is not None
    assert result.name.lower().endswith(".pdf")
