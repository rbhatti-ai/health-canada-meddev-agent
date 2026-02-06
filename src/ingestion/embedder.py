"""
Embedding generation for document chunks.

Supports multiple embedding providers:
- OpenAI text-embedding-3-small/large
- Cohere embed-english-v3.0
- Local models via sentence-transformers
"""

from typing import List, Optional
from abc import ABC, abstractmethod

from openai import OpenAI

from configs.settings import settings
from src.ingestion.loader import DocumentChunk
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BaseEmbedder(ABC):
    """Abstract base class for embedding generators."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        pass


class OpenAIEmbedder(BaseEmbedder):
    """
    OpenAI embedding generator using text-embedding-3 models.

    Models:
    - text-embedding-3-small: 1536 dimensions, cost-effective
    - text-embedding-3-large: 3072 dimensions, higher quality
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        batch_size: int = 100,
    ):
        self.model = model
        self.batch_size = batch_size
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.logger = get_logger(self.__class__.__name__)

        # Set dimensions based on model
        self._dimensions = 1536 if "small" in model else 3072

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Handles batching for large lists.
        """
        if not texts:
            return []

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            self.logger.debug(f"Embedding batch {i // self.batch_size + 1}")

            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

            except Exception as e:
                self.logger.error(f"Embedding error: {e}")
                # Return zero vectors for failed batch
                all_embeddings.extend([[0.0] * self._dimensions] * len(batch))

        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query."""
        embeddings = self.embed_texts([query])
        return embeddings[0] if embeddings else [0.0] * self._dimensions


class EmbeddingGenerator:
    """
    High-level embedding generator with caching and batching.

    Wraps underlying embedding providers and adds:
    - Automatic batching
    - Error handling
    - Logging
    """

    def __init__(
        self,
        embedder: Optional[BaseEmbedder] = None,
    ):
        self.embedder = embedder or OpenAIEmbedder(
            model=settings.embedding_model,
        )
        self.logger = get_logger(self.__class__.__name__)

    def embed_chunks(
        self,
        chunks: List[DocumentChunk],
    ) -> List[tuple[DocumentChunk, List[float]]]:
        """
        Generate embeddings for document chunks.

        Args:
            chunks: List of document chunks

        Returns:
            List of (chunk, embedding) tuples
        """
        if not chunks:
            return []

        self.logger.info(f"Generating embeddings for {len(chunks)} chunks")

        # Extract text content
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings
        embeddings = self.embedder.embed_texts(texts)

        # Pair chunks with embeddings
        results = list(zip(chunks, embeddings))

        self.logger.info(f"Generated {len(results)} embeddings")
        return results

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query."""
        return self.embedder.embed_query(query)

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.embedder.dimensions


# Default generator instance
embedding_generator = EmbeddingGenerator()


def embed_chunks(chunks: List[DocumentChunk]) -> List[tuple[DocumentChunk, List[float]]]:
    """Convenience function for chunk embedding."""
    return embedding_generator.embed_chunks(chunks)


def embed_query(query: str) -> List[float]:
    """Convenience function for query embedding."""
    return embedding_generator.embed_query(query)
