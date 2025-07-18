from __future__ import annotations

import re
from typing import Any, Literal
import uuid
from collections.abc import Mapping, Sequence
from functools import cached_property
from itertools import chain

from rsb.models.base_model import BaseModel
from rsb.models.field import Field

from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.parsing.chunk import Chunk
from agentle.parsing.section_content import SectionContent


class ParsedFile(BaseModel):
    """
    Represents a fully parsed document with its sections and metadata.

    The ParsedFile class is the main output of the document parsing process.
    It contains the document's name and a collection of sections representing
    the content of the document. This structured representation makes it easy
    to work with parsed content from any supported file type in a consistent way.

    **Attributes:**

    *   `name` (str):
        The name of the document, typically derived from the original file name.

        **Example:**
        ```python
        doc = ParsedFile(name="report.pdf", sections=[])
        print(doc.name)  # Output: report.pdf
        ```

    *   `sections` (Sequence[SectionContent]):
        A sequence of SectionContent objects representing the document's content
        divided into logical sections or pages.

        **Example:**
        ```python
        from agentle.parsing.section_content import SectionContent

        section1 = SectionContent(number=1, text="First section content")
        section2 = SectionContent(number=2, text="Second section content")

        doc = ParsedFile(name="document.txt", sections=[section1, section2])

        for section in doc.sections:
            print(f"Section {section.number}: {section.text[:20]}...")
        ```

    **Usage Examples:**

    Creating a ParsedFile with multiple sections:
    ```python
    from agentle.parsing.section_content import SectionContent

    # Create sections
    intro = SectionContent(
        number=1,
        text="Introduction to the topic",
        md="# Introduction\n\nThis document covers..."
    )

    body = SectionContent(
        number=2,
        text="Main content of the document",
        md="## Main Content\n\nThe details of..."
    )

    conclusion = SectionContent(
        number=3,
        text="Conclusion of the document",
        md="## Conclusion\n\nIn summary..."
    )

    # Create the parsed document
    doc = ParsedFile(
        name="example_document.docx",
        sections=[intro, body, conclusion]
    )

    # Access the document content
    print(f"Document: {doc.name}")
    print(f"Number of sections: {len(doc.sections)}")
    print(f"First section heading: {doc.sections[0].md.split('\\n')[0]}")
    ```
    """

    name: str = Field(
        description="Name of the file",
    )

    sections: Sequence[SectionContent] = Field(
        description="Pages of the document",
    )

    metadata: Mapping[str, Any] = Field(
        default_factory=dict, description="Additional metadata of the document."
    )

    @cached_property
    def id(self) -> str:
        # Sanitize name
        base_name = self._sanitize_name()

        # Generate UUID5 based on name and content for some determinism
        namespace = uuid.NAMESPACE_OID
        content_str = f"{self.name}:{len(self.sections)}:{hash(tuple(s.text for s in self.sections))}"
        content_uuid = uuid.uuid5(namespace, content_str)

        return f"{base_name}_{str(content_uuid)[:8]}"

    @property
    def llm_described_text(self) -> str:
        """
        Generate a description of the document suitable for LLM processing.

        This property formats the document content in a structured XML-like format
        that is optimized for large language models to understand the document's
        structure and content.

        Returns:
            str: A structured string representation of the document

        Example:
            ```python
            from agentle.parsing.section_content import SectionContent

            doc = ParsedFile(
                name="example.txt",
                sections=[
                    SectionContent(number=1, text="First section", md="# First section"),
                    SectionContent(number=2, text="Second section", md="# Second section")
                ]
            )

            llm_text = doc.llm_described_text
            print(llm_text)
            # Output:
            # <file>
            #
            # **name:** example.txt
            # **sections:** <section_0> # First section </section_0> <section_1> # Second section </section_1>
            #
            # </file>
            ```
        """
        sections = " ".join(
            [
                f"<section_{num}> {section.md} </section_{num}>"
                for num, section in enumerate(self.sections)
            ]
        )
        return f"<file>\n\n**name:** {self.name} \n**sections:** {sections}\n\n</file>"

    def chunkify(
        self,
        strategy: Literal[
            "auto",
            "semantic_chunking",
            "recursive_character",
        ],
        generation_provider: GenerationProvider | None = None,
    ) -> Sequence[Chunk]:
        match strategy:
            case "auto":
                if generation_provider is None:
                    raise ValueError(
                        'Instance of GenerationProvider needs to be passed if strategy == "auto"'
                    )
            case "semantic_chunking":
                ...
            case _:
                ...

        return []

    def merge_all(self, others: Sequence[ParsedFile]) -> ParsedFile:
        """
        Merge this document with a sequence of other ParsedFile objects.

        This method combines the current document with other ParsedFile objects,
        keeping the name of the current document but merging all sections from all documents.

        Args:
            others (Sequence[ParsedFile]): Other parsed documents to merge with this one

        Returns:
            ParsedFile: A new document containing all sections from this document
                           and the other documents

        Example:
            ```python
            from agentle.parsing.section_content import SectionContent

            # Create sample documents
            doc1 = ParsedFile(
                name="doc1.txt",
                sections=[SectionContent(number=1, text="Content from doc1")]
            )

            doc2 = ParsedFile(
                name="doc2.txt",
                sections=[SectionContent(number=1, text="Content from doc2")]
            )

            doc3 = ParsedFile(
                name="doc3.txt",
                sections=[SectionContent(number=1, text="Content from doc3")]
            )

            # Merge documents with doc1 as the base
            merged = doc1.merge_all([doc2, doc3])

            print(merged.name)  # Output: doc1.txt
            print(len(merged.sections))  # Output: 3
            ```
        """
        from itertools import chain

        # Merge all metadata dicts, with self.metadata taking precedence over others
        merged_metadata: Mapping[str, Any] = {}
        for other in others:
            merged_metadata.update(other.metadata)

        merged_metadata.update(self.metadata)

        return ParsedFile(
            name=self.name,
            sections=list(chain(self.sections, *[other.sections for other in others])),
            metadata=merged_metadata,
        )

    @classmethod
    def from_sections(
        cls,
        name: str,
        sections: Sequence[SectionContent],
        metadata: Mapping[str, Any] | None = None,
    ) -> ParsedFile:
        """
        Create a ParsedFile from a name and a sequence of sections.

        This factory method provides a convenient way to create a ParsedFile
        by specifying the document name and its sections.

        Args:
            name (str): The name to give to the document
            sections (Sequence[SectionContent]): The sections to include in the document

        Returns:
            ParsedFile: A new ParsedFile instance with the specified name and sections

        Example:
            ```python
            from agentle.parsing.section_content import SectionContent

            sections = [
                SectionContent(number=1, text="First section"),
                SectionContent(number=2, text="Second section"),
                SectionContent(number=3, text="Third section")
            ]

            doc = ParsedFile.from_sections("compiled_document.txt", sections)

            print(doc.name)  # Output: compiled_document.txt
            print(len(doc.sections))  # Output: 3
            ```
        """
        return cls(name=name, sections=sections, metadata=metadata or {})

    @classmethod
    def from_parsed_files(cls, files: Sequence[ParsedFile]) -> ParsedFile:
        """
        Create a merged ParsedFile from multiple existing ParsedFile objects.

        This factory method provides a convenient way to combine multiple documents
        into a single document. The resulting document will have the name "MergedFile"
        and will contain all sections from all input files.

        Args:
            files (Sequence[ParsedFile]): The ParsedFile objects to merge

        Returns:
            ParsedFile: A new ParsedFile containing all sections from the input files

        Example:
            ```python
            from agentle.parsing.section_content import SectionContent

            # Create sample documents
            doc1 = ParsedFile(
                name="chapter1.txt",
                sections=[SectionContent(number=1, text="Chapter 1 content")]
            )

            doc2 = ParsedFile(
                name="chapter2.txt",
                sections=[SectionContent(number=1, text="Chapter 2 content")]
            )

            # Merge documents
            book = ParsedFile.from_parsed_files([doc1, doc2])

            print(book.name)  # Output: MergedFile
            print(len(book.sections))  # Output: 2
            ```
        """
        # Merge all sections
        merged_sections = list(chain(*[file.sections for file in files]))

        # Merge metadata from all files (later files override earlier ones on key conflict)
        merged_metadata: Mapping[str, Any] = {}
        for file in files:
            merged_metadata.update(file.metadata)

        return cls(
            name="MergedFile",
            sections=merged_sections,
            metadata=merged_metadata,
        )

    @property
    def md(self) -> str:
        """
        Generate a complete markdown representation of the document.

        This property combines the markdown content of all sections into a single
        markdown string, making it easy to get a complete markdown version of the
        document's content.

        Returns:
            str: The combined markdown content of all sections

        Example:
            ```python
            from agentle.parsing.section_content import SectionContent

            doc = ParsedFile(
                name="document.md",
                sections=[
                    SectionContent(number=1, text="First section", md="# First section\nContent"),
                    SectionContent(number=2, text="Second section", md="# Second section\nMore content")
                ]
            )

            markdown = doc.md
            print(markdown)
            # Output:
            # # First section
            # Content
            # # Second section
            # More content
            ```
        """
        return "\n".join([sec.md or "" for sec in self.sections])

    def _sanitize_name(self) -> str:
        """Extract name sanitization into reusable method."""
        if not self.name:
            return "unnamed_file"

        # Remove file extension
        base_name = self.name.rsplit(".", 1)[0] if "." in self.name else self.name

        # Convert to lowercase and replace non-alphanumeric characters with underscores
        base_name = re.sub(r"[^a-zA-Z0-9_]", "_", base_name.lower())

        # Remove consecutive underscores and strip leading/trailing underscores
        base_name = re.sub(r"_+", "_", base_name).strip("_")

        # Ensure it doesn't start with a number
        if base_name and base_name[0].isdigit():
            base_name = f"file_{base_name}"

        return base_name if base_name else "unnamed_file"


# strategy: Literal[
#             # Intelligent Strategy Selection
#             "auto",  # LLM-powered automatic strategy selection
#             # Semantic & AI-Powered Approaches
#             "semantic_chunking",  # Embedding-based semantic similarity
#             "contextual",  # AI-powered contextual chunking (Anthropic-style)
#             "late_chunking",  # Query-time dynamic chunking
#             # Structure-Aware Strategies
#             "recursive_character",  # Hierarchical separator-based (most common)
#             "document_structure",  # Header/section-based chunking
#             "hierarchical",  # Multi-level document structure
#             # Content-Type Specific
#             "code_aware",  # Syntax-preserving for code documents
#             "markdown_aware",  # Markdown structure preservation
#             "html_aware",  # HTML tag-based chunking
#             # Basic Splitting Methods
#             "fixed_size",  # Fixed character/token count
#             "sentence_based",  # Split by sentence boundaries
#             "paragraph_based",  # Split by paragraph boundaries
#             "token_based",  # Split by token count
#             # Advanced Techniques
#             "sliding_window",  # Overlapping window approach
#             "hybrid",  # Multiple strategy combination
#             "adaptive",  # Content-complexity adaptive sizing
#             # Domain-Specific
#             "academic_paper",  # Research paper structure-aware
#             "legal_document",  # Legal clause-aware chunking
#             "business_report",  # Business document structure
#             "technical_manual",  # Technical documentation optimized
#             # Performance Optimized
#             "fast_fixed",  # Optimized for speed
#             "balanced",  # Speed-accuracy balance
#             "high_quality",  # Accuracy-optimized regardless of speed
#         ],
