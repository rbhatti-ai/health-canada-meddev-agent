"""
End-to-end document ingestion pipeline.

Orchestrates the full ingestion workflow:
1. Load documents
2. Chunk text
3. Generate embeddings
4. Store in vector database
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.ingestion.chunker import ChunkingConfig, TextChunker
from src.ingestion.embedder import EmbeddingGenerator
from src.ingestion.loader import DocumentLoader, LoadedDocument
from src.utils.logging import get_logger

if TYPE_CHECKING:
    from src.retrieval.vectorstore import VectorStoreManager

logger = get_logger(__name__)


@dataclass
class IngestionStats:
    """Statistics from an ingestion run."""

    documents_processed: int = 0
    documents_failed: int = 0
    chunks_created: int = 0
    embeddings_generated: int = 0
    documents_stored: int = 0
    errors: list[str] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents_processed": self.documents_processed,
            "documents_failed": self.documents_failed,
            "chunks_created": self.chunks_created,
            "embeddings_generated": self.embeddings_generated,
            "documents_stored": self.documents_stored,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
        }


class IngestionPipeline:
    """
    Complete document ingestion pipeline.

    Handles the full workflow from raw documents to searchable vectors.
    """

    def __init__(
        self,
        loader: DocumentLoader | None = None,
        chunker: TextChunker | None = None,
        embedder: EmbeddingGenerator | None = None,
        vector_store: "VectorStoreManager | None" = None,
        chunking_config: ChunkingConfig | None = None,
    ):
        # Lazy import to avoid circular dependency
        from src.retrieval.vectorstore import VectorStoreManager

        self.loader = loader or DocumentLoader()
        self.chunker = chunker or TextChunker(chunking_config)
        self.embedder = embedder or EmbeddingGenerator()
        self.vector_store = vector_store or VectorStoreManager()
        self.logger = get_logger(self.__class__.__name__)

    def ingest_file(self, file_path: Path) -> IngestionStats:
        """
        Ingest a single file.

        Args:
            file_path: Path to document file

        Returns:
            IngestionStats for this file
        """
        stats = IngestionStats(start_time=datetime.now())
        file_path = Path(file_path)

        self.logger.info(f"Ingesting file: {file_path}")

        try:
            # Load document
            document = self.loader.load_file(file_path)
            if not document:
                stats.documents_failed += 1
                stats.errors.append(f"Failed to load: {file_path}")
                return stats

            stats.documents_processed += 1

            # Process single document
            self._process_document(document, stats)

        except Exception as e:
            self.logger.error(f"Error ingesting {file_path}: {e}")
            stats.documents_failed += 1
            stats.errors.append(f"{file_path}: {str(e)}")

        stats.end_time = datetime.now()
        return stats

    def ingest_path(
        self,
        path: Path,
        recursive: bool = True,
    ) -> IngestionStats:
        """
        Ingest all documents from a path (file or directory).

        Args:
            path: Path to file or directory
            recursive: Whether to process subdirectories

        Returns:
            Aggregated IngestionStats
        """
        stats = IngestionStats(start_time=datetime.now())
        path = Path(path)

        self.logger.info(f"Starting ingestion from: {path}")

        if path.is_file():
            # Single file
            file_stats = self.ingest_file(path)
            stats = self._merge_stats(stats, file_stats)
        elif path.is_dir():
            # Directory - process all files
            for document in self.loader.load_directory(path, recursive):
                try:
                    self._process_document(document, stats)
                    stats.documents_processed += 1
                except Exception as e:
                    self.logger.error(f"Error processing {document.source_path}: {e}")
                    stats.documents_failed += 1
                    stats.errors.append(f"{document.source_path}: {str(e)}")
        else:
            stats.errors.append(f"Path not found: {path}")

        stats.end_time = datetime.now()

        self.logger.info(
            f"Ingestion complete: {stats.documents_processed} documents, "
            f"{stats.chunks_created} chunks in {stats.duration_seconds:.1f}s"
        )

        return stats

    def ingest_documents(
        self,
        documents: list[LoadedDocument],
    ) -> IngestionStats:
        """
        Ingest pre-loaded documents.

        Args:
            documents: List of LoadedDocument objects

        Returns:
            IngestionStats
        """
        stats = IngestionStats(start_time=datetime.now())

        for document in documents:
            try:
                self._process_document(document, stats)
                stats.documents_processed += 1
            except Exception as e:
                self.logger.error(f"Error processing {document.source_path}: {e}")
                stats.documents_failed += 1
                stats.errors.append(f"{document.source_path}: {str(e)}")

        stats.end_time = datetime.now()
        return stats

    def _process_document(
        self,
        document: LoadedDocument,
        stats: IngestionStats,
    ) -> None:
        """Process a single loaded document through the pipeline."""
        self.logger.debug(f"Processing: {document.metadata.get('file_name', 'unknown')}")

        # Chunk the document
        chunks = self.chunker.chunk_document(document)
        stats.chunks_created += len(chunks)

        if not chunks:
            self.logger.warning(f"No chunks created from {document.source_path}")
            return

        # Generate embeddings
        chunk_embeddings = self.embedder.embed_chunks(chunks)
        stats.embeddings_generated += len(chunk_embeddings)

        # Separate chunks and embeddings
        chunks_only = [ce[0] for ce in chunk_embeddings]
        embeddings_only = [ce[1] for ce in chunk_embeddings]

        # Store in vector database
        stored = self.vector_store.add_documents(chunks_only, embeddings_only)
        stats.documents_stored += stored

    def _merge_stats(
        self,
        base: IngestionStats,
        addition: IngestionStats,
    ) -> IngestionStats:
        """Merge two stats objects."""
        base.documents_processed += addition.documents_processed
        base.documents_failed += addition.documents_failed
        base.chunks_created += addition.chunks_created
        base.embeddings_generated += addition.embeddings_generated
        base.documents_stored += addition.documents_stored
        base.errors.extend(addition.errors)
        return base

    def reindex_all(self, source_path: Path, recursive: bool = True) -> IngestionStats:
        """
        Clear and rebuild the entire index from source documents.

        Args:
            source_path: Path to source documents
            recursive: Whether to process subdirectories

        Returns:
            IngestionStats
        """
        self.logger.warning("Reindexing: Clearing existing vector store")
        self.vector_store.clear()
        return self.ingest_path(source_path, recursive)


# Lazy singleton pattern to avoid circular import
_ingestion_pipeline: "IngestionPipeline | None" = None


def get_ingestion_pipeline() -> "IngestionPipeline":
    """Get or create the default pipeline instance."""
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        _ingestion_pipeline = IngestionPipeline()
    return _ingestion_pipeline


def ingest_path(path: Path, recursive: bool = True) -> dict[str, Any]:
    """Convenience function for path ingestion."""
    stats = get_ingestion_pipeline().ingest_path(path, recursive)
    return stats.to_dict()


def ingest_file(file_path: Path) -> dict[str, Any]:
    """Convenience function for file ingestion."""
    stats = get_ingestion_pipeline().ingest_file(file_path)
    return stats.to_dict()
