"""
Vector store management for document embeddings.

Supports:
- ChromaDB (local development)
- Pinecone (production)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from configs.settings import settings
from src.ingestion.loader import DocumentChunk
from src.utils.logging import get_logger

logger = get_logger(__name__)


class VectorStoreManager:
    """
    Manages vector storage and retrieval using ChromaDB.

    Features:
    - Persistent storage
    - Metadata filtering
    - Batch operations
    - Collection management
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name or settings.chroma_collection_name
        self.logger = get_logger(self.__class__.__name__)

        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )

        self.logger.info(
            f"Initialized vector store: {self.collection_name} "
            f"({self.collection.count()} documents)"
        )

    def add_documents(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        """
        Add document chunks with embeddings to the store.

        Args:
            chunks: List of document chunks
            embeddings: Corresponding embeddings

        Returns:
            Number of documents added
        """
        if not chunks or not embeddings:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")

        self.logger.info(f"Adding {len(chunks)} documents to vector store")

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Generate unique ID
            doc_id = f"{chunk.metadata.get('file_name', 'doc')}_{chunk.id}_{i}"
            ids.append(doc_id)
            documents.append(chunk.content)

            # Prepare metadata (ChromaDB requires flat structure)
            flat_metadata = self._flatten_metadata(chunk.metadata)
            metadatas.append(flat_metadata)

        # Add to collection in batches
        batch_size = 100
        added_count = 0

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_docs = documents[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]

            try:
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                )
                added_count += len(batch_ids)
            except Exception as e:
                self.logger.error(f"Error adding batch: {e}")

        self.logger.info(f"Added {added_count} documents")
        return added_count

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of search results with content, metadata, and scores
        """
        self.logger.debug(f"Searching for {n_results} similar documents")

        # Build where clause for filtering
        where = None
        if filter_metadata:
            where = filter_metadata

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []

        # Format results
        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                result = {
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    "score": 1 - results["distances"][0][i] if results["distances"] else 1.0,
                }
                formatted_results.append(result)

        return formatted_results

    def delete_by_source(self, source_path: str) -> int:
        """
        Delete all documents from a specific source file.

        Args:
            source_path: Path to source file

        Returns:
            Number of documents deleted
        """
        try:
            # Get IDs of documents from this source
            results = self.collection.get(
                where={"source": source_path},
                include=[],
            )

            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                self.logger.info(f"Deleted {len(results['ids'])} documents from {source_path}")
                return len(results["ids"])

        except Exception as e:
            self.logger.error(f"Delete error: {e}")

        return 0

    def clear(self) -> None:
        """Clear all documents from the collection."""
        self.logger.warning("Clearing entire vector store")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        count = self.collection.count()

        # Get unique sources
        try:
            all_metadata = self.collection.get(include=["metadatas"])
            sources = set()
            categories = {}

            for meta in all_metadata.get("metadatas", []):
                if meta:
                    sources.add(meta.get("source", "unknown"))
                    cat = meta.get("category", "other")
                    categories[cat] = categories.get(cat, 0) + 1

        except Exception:
            sources = set()
            categories = {}

        return {
            "total_documents": count,
            "unique_sources": len(sources),
            "categories": categories,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
        }

    def _flatten_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested metadata for ChromaDB compatibility."""
        flat = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                flat[key] = value
            elif isinstance(value, list):
                flat[key] = str(value)  # Convert lists to strings
            elif value is None:
                flat[key] = ""
            else:
                flat[key] = str(value)
        return flat


# Lazy singleton pattern to avoid circular imports
_vector_store: Optional["VectorStoreManager"] = None


def get_vector_store() -> "VectorStoreManager":
    """Get or create the default vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store


# For backwards compatibility - lazy property
class _VectorStoreProxy:
    """Proxy that lazily initializes the vector store."""
    def __getattr__(self, name):
        return getattr(get_vector_store(), name)


vector_store = _VectorStoreProxy()
