from pathlib import Path
from typing import Literal

from agentle.generations.providers.base.generation_provider import (
    GenerationProvider,
)
from agentle.parsing.parsed_file import ParsedFile
from agentle.parsing.parse_async import parse_async
from agentle.parsing.parses import parser_registry
from rsb.coroutines.run_sync import run_sync


def parse(
    document_path: str,
    strategy: Literal["low", "high"] = "high",
    visual_description_provider: GenerationProvider | None = None,
    audio_description_provider: GenerationProvider | None = None,
) -> ParsedFile:
    """
    Parse any supported document type into a structured ParsedFile representation.

    This function serves as the main entry point for document parsing in the Agentle framework.
    It automatically selects the appropriate parser based on the file extension and applies
    the requested parsing strategy.

    Args:
        document_path (str): Path to the document file to be parsed. The file extension
            is used to determine which parser to use.

        strategy (Literal["low", "high"], optional): Parsing strategy to use. Defaults to "high".
            - "high": More thorough parsing that may include OCR, image analysis,
                      and other CPU-intensive operations
            - "low": Faster parsing that skips some intensive operations

        visual_description_provider (GenerationProvider | None, optional):
            Custom provider for analyzing visual content. If provided, this provider will be used
            instead of the default visual description provider. Useful for customizing
            the image analysis behavior and model selection. Defaults to None.

        audio_description_provider (GenerationProvider | None, optional):
            Custom provider for analyzing audio content. If provided, this provider will be used
            instead of the default audio description provider. Useful for customizing
            the audio analysis behavior and model selection. Defaults to None.

    Returns:
        ParsedFile: A structured representation of the parsed document with:
            - sections: list of content sections
            - images: extracted images with optional OCR text
            - structured items: headings, tables, and text blocks

    Raises:
        ValueError: If the file extension is not supported by any registered parser

    Examples:
        Parse a PDF document with default settings:
        ```python
        from agentle.parsing.parse import parse

        parsed_doc = parse("document.pdf")
        print(f"Document name: {parsed_doc.name}")
        print(f"Number of sections: {len(parsed_doc.sections)}")
        ```

        Parse an image with a "low" strategy (faster processing):
        ```python
        parsed_image = parse("image.jpg", strategy="low")
        ```

        Parse with a custom visual description agent:
        ```python
        from agentle.generations.providers.google.google_generation_provider import GoogleGenerationProvider

        custom_provider = GoogleGenerationProvider()

        parsed_image = parse("image.png", visual_description_provider=custom_provider)
        ```
    """
    path = Path(document_path)
    # Make extension lookup case-insensitive and dot-stripped
    parser_cls = parser_registry.get(path.suffix.lstrip(".").lower())

    if not parser_cls:
        raise ValueError(f"Unsupported extension: {path.suffix}")

    return run_sync(
        parse_async,
        document_path=document_path,
        strategy=strategy,
        visual_description_provider=visual_description_provider,
        audio_description_provider=audio_description_provider,
    )
