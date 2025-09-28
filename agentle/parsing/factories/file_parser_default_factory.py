from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentle.generations.providers.base.generation_provider import (
        GenerationProvider,
    )
    from agentle.parsing.parsers.file_parser import FileParser


def file_parser_default_factory(
    visual_description_provider: GenerationProvider | None = None,
    audio_description_provider: GenerationProvider | None = None,
    parse_timeout: float = 30,
) -> FileParser:
    from agentle.generations.providers.google.google_generation_provider import (
        GoogleGenerationProvider,
    )
    from agentle.parsing.parsers.file_parser import FileParser

    return FileParser(
        visual_description_provider=visual_description_provider
        or GoogleGenerationProvider(),
        audio_description_provider=audio_description_provider
        or GoogleGenerationProvider(),
        parse_timeout=parse_timeout,
    )
