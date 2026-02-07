"""
Hybrid retriever combining vector search with keyword matching.

Provides intelligent document retrieval for RAG applications.
"""

from dataclasses import dataclass
from typing import Any

from src.ingestion.embedder import EmbeddingGenerator, embedding_generator
from src.retrieval.vectorstore import VectorStoreManager, vector_store
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """A single retrieval result with relevance information."""

    content: str
    metadata: dict[str, Any]
    score: float
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
            "source": self.source,
        }


class HybridRetriever:
    """
    Hybrid retriever combining semantic search with optional keyword boosting.

    Features:
    - Vector similarity search
    - Metadata filtering
    - Query expansion for regulatory terms
    - Result deduplication
    """

    # Common regulatory term expansions
    TERM_EXPANSIONS = {
        "mdl": ["medical device licence", "device licence", "licence application"],
        "mdel": ["medical device establishment licence", "establishment licence"],
        "samd": ["software as medical device", "software medical device", "digital health"],
        "qms": ["quality management system", "iso 13485", "quality system"],
        "ivd": ["in-vitro diagnostic", "in vitro diagnostic", "diagnostic device"],
        "udi": ["unique device identification", "device identifier"],
        "imdrf": ["international medical device regulators forum"],
        "mdsap": ["medical device single audit program"],
    }

    def __init__(
        self,
        vector_store_manager: VectorStoreManager | None = None,
        embedder: EmbeddingGenerator | None = None,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ):
        self.vector_store = vector_store_manager or vector_store
        self.embedder = embedder or embedding_generator
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.logger = get_logger(self.__class__.__name__)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filter_category: str | None = None,
        filter_source: str | None = None,
        expand_query: bool = True,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Search query
            top_k: Number of results (overrides default)
            filter_category: Filter by document category
            filter_source: Filter by source file
            expand_query: Whether to expand regulatory terms

        Returns:
            List of RetrievalResult objects
        """
        k = top_k or self.top_k
        self.logger.info(f"Retrieving documents for: {query[:100]}...")

        # Optionally expand query with regulatory terms
        if expand_query:
            query = self._expand_query(query)

        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)

        # Build metadata filter
        metadata_filter = {}
        if filter_category:
            metadata_filter["category"] = filter_category
        if filter_source:
            metadata_filter["source"] = filter_source

        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=k * 2,  # Get extra for filtering
            filter_metadata=metadata_filter if metadata_filter else None,
        )

        # Convert to RetrievalResult and filter by score
        retrieval_results = []
        seen_content = set()

        for result in results:
            # Skip low-scoring results
            if result["score"] < self.score_threshold:
                continue

            # Skip duplicates (based on content hash)
            content_hash = hash(result["content"][:200])
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)

            retrieval_results.append(
                RetrievalResult(
                    content=result["content"],
                    metadata=result["metadata"],
                    score=result["score"],
                    source=result["metadata"].get("source", "unknown"),
                )
            )

            if len(retrieval_results) >= k:
                break

        self.logger.info(f"Retrieved {len(retrieval_results)} relevant documents")
        return retrieval_results

    def retrieve_with_context(
        self,
        query: str,
        context_window: int = 1,
        **kwargs: Any,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents with surrounding context chunks.

        Args:
            query: Search query
            context_window: Number of adjacent chunks to include
            **kwargs: Additional arguments passed to retrieve()

        Returns:
            List of RetrievalResult with expanded context
        """
        # Get initial results
        results = self.retrieve(query, **kwargs)

        if context_window <= 0:
            return results

        # For each result, try to find adjacent chunks
        expanded_results = []
        for result in results:
            # Get source and chunk index from metadata
            source = result.metadata.get("source", "")
            chunk_index = result.metadata.get("chunk_index", 0)

            # Try to retrieve adjacent chunks
            adjacent_chunks = []
            for offset in range(-context_window, context_window + 1):
                if offset == 0:
                    continue
                target_index = chunk_index + offset
                if target_index < 0:
                    continue

                # Search for adjacent chunk
                adjacent = self._find_adjacent_chunk(source, target_index)
                if adjacent:
                    adjacent_chunks.append(adjacent)

            # Combine content if we found adjacent chunks
            if adjacent_chunks:
                combined_content = self._combine_chunks(result, adjacent_chunks)
                result = RetrievalResult(
                    content=combined_content,
                    metadata=result.metadata,
                    score=result.score,
                    source=result.source,
                )

            expanded_results.append(result)

        return expanded_results

    def _expand_query(self, query: str) -> str:
        """Expand query with regulatory term synonyms."""
        query_lower = query.lower()
        expansions = []

        for term, synonyms in self.TERM_EXPANSIONS.items():
            if term in query_lower:
                expansions.extend(synonyms)

        if expansions:
            return f"{query} {' '.join(expansions[:3])}"
        return query

    def _find_adjacent_chunk(
        self,
        source: str,
        chunk_index: int,
    ) -> RetrievalResult | None:
        """Find a specific chunk by source and index."""
        try:
            # This is a simplified implementation
            # In production, you'd want a more efficient lookup
            results = self.vector_store.search(
                query_embedding=[0.0] * self.embedder.dimensions,  # Dummy embedding
                n_results=1000,  # Get all from source
                filter_metadata={"source": source},
            )

            for result in results:
                if result["metadata"].get("chunk_index") == chunk_index:
                    return RetrievalResult(
                        content=result["content"],
                        metadata=result["metadata"],
                        score=result["score"],
                        source=source,
                    )
        except Exception as e:
            self.logger.debug(f"Could not find adjacent chunk: {e}")

        return None

    def _combine_chunks(
        self,
        main_chunk: RetrievalResult,
        adjacent: list[RetrievalResult],
    ) -> str:
        """Combine main chunk with adjacent chunks."""
        # Sort by chunk index
        all_chunks = [main_chunk] + adjacent
        all_chunks.sort(key=lambda x: x.metadata.get("chunk_index", 0))

        # Combine content
        contents = [chunk.content for chunk in all_chunks]
        return "\n\n---\n\n".join(contents)


# Default retriever instance
hybrid_retriever = HybridRetriever()


def retrieve(query: str, **kwargs: Any) -> list[RetrievalResult]:
    """Convenience function for document retrieval."""
    return hybrid_retriever.retrieve(query, **kwargs)
