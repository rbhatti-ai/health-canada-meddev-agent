"""
Text chunking strategies for document processing.

Implements semantic-aware chunking that preserves context
and handles regulatory document structure.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.ingestion.loader import LoadedDocument, DocumentChunk
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""

    chunk_size: int = 1000  # Target chunk size in characters
    chunk_overlap: int = 200  # Overlap between chunks
    min_chunk_size: int = 100  # Minimum chunk size
    max_chunk_size: int = 2000  # Maximum chunk size
    preserve_sections: bool = True  # Try to preserve section boundaries
    include_metadata: bool = True  # Include source metadata in chunks


class TextChunker:
    """
    Semantic-aware text chunker for regulatory documents.

    Features:
    - Respects section boundaries
    - Handles tables and lists
    - Maintains context through overlap
    - Preserves regulatory citations
    """

    # Patterns for section detection
    SECTION_PATTERNS = [
        r"^#{1,6}\s+.+$",  # Markdown headings
        r"^\d+\.\s+[A-Z]",  # Numbered sections (1. Introduction)
        r"^[A-Z][A-Z\s]+:?\s*$",  # ALL CAPS headings
        r"^Section\s+\d+",  # Section X
        r"^Part\s+[IVX]+",  # Part I, II, etc.
        r"^Schedule\s+\d+",  # Schedule 1, 2, etc.
        r"^Rule\s+\d+",  # Rule 1, 2, etc.
    ]

    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
        self.logger = get_logger(self.__class__.__name__)
        self._section_regex = re.compile(
            "|".join(self.SECTION_PATTERNS),
            re.MULTILINE
        )

    def chunk_document(self, document: LoadedDocument) -> List[DocumentChunk]:
        """
        Split a document into semantic chunks.

        Args:
            document: Loaded document to chunk

        Returns:
            List of DocumentChunk objects
        """
        self.logger.info(f"Chunking document: {document.metadata.get('file_name', 'unknown')}")

        if self.config.preserve_sections:
            chunks = self._chunk_by_sections(document)
        else:
            chunks = self._chunk_by_size(document.content, document.metadata)

        self.logger.info(f"Created {len(chunks)} chunks")
        return chunks

    def _chunk_by_sections(self, document: LoadedDocument) -> List[DocumentChunk]:
        """
        Chunk document respecting section boundaries.

        First splits by sections, then applies size-based chunking
        to sections that are too large.
        """
        content = document.content
        metadata = document.metadata

        # Find section boundaries
        sections = self._split_into_sections(content)

        chunks = []
        for section_idx, section in enumerate(sections):
            section_text = section["text"]
            section_title = section.get("title", "")

            # If section is within size limits, keep as single chunk
            if len(section_text) <= self.config.max_chunk_size:
                if len(section_text) >= self.config.min_chunk_size:
                    chunk_metadata = {
                        **metadata,
                        "section_title": section_title,
                        "section_index": section_idx,
                        "chunk_index": 0,
                    }
                    chunks.append(DocumentChunk(
                        content=section_text,
                        metadata=chunk_metadata,
                    ))
            else:
                # Split large sections
                sub_chunks = self._chunk_by_size(
                    section_text,
                    {
                        **metadata,
                        "section_title": section_title,
                        "section_index": section_idx,
                    }
                )
                chunks.extend(sub_chunks)

        return chunks

    def _split_into_sections(self, content: str) -> List[Dict[str, Any]]:
        """Split content into sections based on headings."""
        sections = []
        current_section = {"title": "", "text": ""}

        lines = content.split("\n")
        for line in lines:
            # Check if line is a section heading
            if self._section_regex.match(line.strip()):
                # Save current section if it has content
                if current_section["text"].strip():
                    sections.append(current_section)
                # Start new section
                current_section = {"title": line.strip(), "text": line + "\n"}
            else:
                current_section["text"] += line + "\n"

        # Don't forget the last section
        if current_section["text"].strip():
            sections.append(current_section)

        # If no sections found, treat entire content as one section
        if not sections:
            sections = [{"title": "", "text": content}]

        return sections

    def _chunk_by_size(
        self,
        text: str,
        base_metadata: Dict[str, Any],
    ) -> List[DocumentChunk]:
        """
        Chunk text based on size with overlap.

        Uses sentence boundaries where possible for cleaner breaks.
        """
        chunks = []

        # Clean and normalize text
        text = self._normalize_text(text)

        if len(text) <= self.config.chunk_size:
            if len(text) >= self.config.min_chunk_size:
                chunks.append(DocumentChunk(
                    content=text,
                    metadata={**base_metadata, "chunk_index": 0},
                ))
            return chunks

        # Split into sentences for cleaner chunking
        sentences = self._split_into_sentences(text)

        current_chunk = ""
        chunk_index = 0

        for sentence in sentences:
            # If adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) > self.config.chunk_size:
                # Save current chunk if it meets minimum size
                if len(current_chunk) >= self.config.min_chunk_size:
                    chunks.append(DocumentChunk(
                        content=current_chunk.strip(),
                        metadata={**base_metadata, "chunk_index": chunk_index},
                    ))
                    chunk_index += 1

                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = overlap_text + sentence
                else:
                    current_chunk += sentence
            else:
                current_chunk += sentence

        # Don't forget the last chunk
        if current_chunk.strip() and len(current_chunk) >= self.config.min_chunk_size:
            chunks.append(DocumentChunk(
                content=current_chunk.strip(),
                metadata={**base_metadata, "chunk_index": chunk_index},
            ))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - handles common cases
        # For production, consider using spaCy or NLTK

        # Handle common abbreviations to avoid false splits
        text = re.sub(r"(\b(?:Dr|Mr|Mrs|Ms|Prof|Inc|Ltd|etc|e\.g|i\.e))\.", r"\1<PERIOD>", text)

        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # Restore periods in abbreviations
        sentences = [s.replace("<PERIOD>", ".") for s in sentences]

        return sentences

    def _get_overlap_text(self, text: str) -> str:
        """Get the overlap portion from the end of a chunk."""
        if len(text) <= self.config.chunk_overlap:
            return text

        # Try to break at a sentence boundary within overlap region
        overlap_region = text[-self.config.chunk_overlap:]

        # Find last sentence boundary in overlap region
        match = re.search(r"[.!?]\s+", overlap_region)
        if match:
            return overlap_region[match.end():]

        # Fall back to word boundary
        words = overlap_region.split()
        if len(words) > 1:
            return " ".join(words[1:]) + " "

        return overlap_region

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent processing."""
        # Replace multiple whitespace with single space
        text = re.sub(r"\s+", " ", text)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()


# Default chunker instance
text_chunker = TextChunker()


def chunk_document(document: LoadedDocument) -> List[DocumentChunk]:
    """Convenience function for document chunking."""
    return text_chunker.chunk_document(document)
