# Adapter for Agentle part to OpenRouter part
"""
Adapter for converting Agentle message parts to OpenRouter content parts.

This module handles the conversion of various Agentle message part types
(text, images, files, audio) into the corresponding OpenRouter API format.
"""

from __future__ import annotations

import base64
from typing import override

from rsb.adapters.adapter import Adapter

from agentle.generations.models.message_parts.file import FilePart
from agentle.generations.models.message_parts.text import TextPart

from agentle.generations.providers.openrouter._types import (
    OpenRouterTextPart,
    OpenRouterImageUrlPart,
    OpenRouterFilePart,
    OpenRouterInputAudioPart,
)


class AgentlePartToOpenRouterPartAdapter(
    Adapter[
        TextPart | FilePart,
        OpenRouterTextPart
        | OpenRouterImageUrlPart
        | OpenRouterFilePart
        | OpenRouterInputAudioPart,
    ]
):
    """
    Adapter for converting Agentle message parts to OpenRouter content parts.

    Handles conversion of:
    - TextPart -> OpenRouterTextPart
    - FilePart (image/*) -> OpenRouterImageUrlPart
    - FilePart (application/pdf) -> OpenRouterFilePart
    - FilePart (audio/*) -> OpenRouterInputAudioPart
    """

    @override
    def adapt(
        self,
        _f: TextPart | FilePart,
    ) -> (
        OpenRouterTextPart
        | OpenRouterImageUrlPart
        | OpenRouterFilePart
        | OpenRouterInputAudioPart
    ):
        """
        Convert an Agentle message part to OpenRouter format.

        Args:
            _f: The Agentle message part to convert.

        Returns:
            The corresponding OpenRouter content part.
        """
        part = _f

        match part:
            case TextPart():
                return OpenRouterTextPart(
                    type="text",
                    text=str(part.text),
                )

            case FilePart():
                mime_type = part.mime_type

                # Handle images
                if mime_type.startswith("image/"):
                    data = part.data
                    if isinstance(data, str):
                        # Assume it's already base64 or a URL
                        if data.startswith(("http://", "https://")):
                            url = data
                        elif data.startswith("data:"):
                            url = data
                        else:
                            # Raw base64, need to add data URL prefix
                            url = f"data:{mime_type};base64,{data}"
                    else:
                        # Binary data, encode to base64
                        b64_data = base64.b64encode(data).decode()
                        url = f"data:{mime_type};base64,{b64_data}"

                    return OpenRouterImageUrlPart(
                        type="image_url",
                        image_url={"url": url, "detail": "auto"},
                    )

                # Handle PDFs
                elif mime_type == "application/pdf":
                    data = part.data
                    if isinstance(data, str):
                        # Could be URL or base64
                        if data.startswith(("http://", "https://")):
                            file_data = data
                        elif data.startswith("data:"):
                            file_data = data
                        else:
                            # Raw base64
                            file_data = f"data:application/pdf;base64,{data}"
                    else:
                        # Binary data
                        b64_data = base64.b64encode(data).decode()
                        file_data = f"data:application/pdf;base64,{b64_data}"

                    filename = getattr(part, "filename", "document.pdf")
                    return OpenRouterFilePart(
                        type="file",
                        file={
                            "filename": filename,
                            "file_data": file_data,
                        },
                    )

                # Handle audio
                elif mime_type.startswith("audio/"):
                    data = part.data
                    if isinstance(data, str):
                        b64_data = data
                    else:
                        b64_data = base64.b64encode(data).decode()

                    # Determine format from mime type
                    audio_format = "mp3" if "mp3" in mime_type else "wav"

                    return OpenRouterInputAudioPart(
                        type="input_audio",
                        input_audio={
                            "data": b64_data,
                            "format": audio_format,
                        },
                    )

                # Fallback for other file types - treat as generic file
                else:
                    data = part.data
                    if isinstance(data, str):
                        if data.startswith(("http://", "https://", "data:")):
                            file_data = data
                        else:
                            file_data = f"data:{mime_type};base64,{data}"
                    else:
                        b64_data = base64.b64encode(data).decode()
                        file_data = f"data:{mime_type};base64,{b64_data}"

                    filename = getattr(part, "filename", "file")
                    return OpenRouterFilePart(
                        type="file",
                        file={
                            "filename": filename,
                            "file_data": file_data,
                        },
                    )
