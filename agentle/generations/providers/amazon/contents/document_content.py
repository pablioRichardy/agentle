# Document content block
from typing import TypedDict

from agentle.generations.providers.amazon.contents.document_block import DocumentBlock


class DocumentContent(TypedDict):
    document: DocumentBlock
