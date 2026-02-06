"""
Result reranking for improved retrieval quality.

Implements various reranking strategies:
- Cross-encoder reranking
- LLM-based reranking
- Diversity reranking
"""

from typing import List, Optional
from dataclasses import dataclass

from src.retrieval.retriever import RetrievalResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RerankedResult(RetrievalResult):
    """Retrieval result with reranking score."""

    original_score: float = 0.0
    rerank_score: float = 0.0


class Reranker:
    """
    Reranks retrieval results for improved relevance.

    Strategies:
    1. Score normalization
    2. Diversity promotion (reduce redundancy)
    3. Recency boosting (for time-sensitive queries)
    4. Category boosting (prioritize certain document types)
    """

    # Category priority weights (higher = more important)
    CATEGORY_WEIGHTS = {
        "regulation": 1.2,
        "guidance": 1.1,
        "standard": 1.0,
        "form": 0.9,
        "checklist": 0.95,
        "other": 0.8,
    }

    def __init__(
        self,
        diversity_threshold: float = 0.8,
        enable_diversity: bool = True,
        enable_category_boost: bool = True,
    ):
        self.diversity_threshold = diversity_threshold
        self.enable_diversity = enable_diversity
        self.enable_category_boost = enable_category_boost
        self.logger = get_logger(self.__class__.__name__)

    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: Optional[int] = None,
    ) -> List[RerankedResult]:
        """
        Rerank retrieval results.

        Args:
            query: Original query
            results: Initial retrieval results
            top_k: Number of results to return

        Returns:
            Reranked results
        """
        if not results:
            return []

        self.logger.debug(f"Reranking {len(results)} results")

        # Convert to RerankedResult
        reranked = [
            RerankedResult(
                content=r.content,
                metadata=r.metadata,
                score=r.score,
                source=r.source,
                original_score=r.score,
                rerank_score=r.score,
            )
            for r in results
        ]

        # Apply category boosting
        if self.enable_category_boost:
            reranked = self._apply_category_boost(reranked)

        # Apply diversity reranking
        if self.enable_diversity:
            reranked = self._apply_diversity_rerank(reranked)

        # Sort by final rerank score
        reranked.sort(key=lambda x: x.rerank_score, reverse=True)

        # Apply top_k limit
        if top_k:
            reranked = reranked[:top_k]

        return reranked

    def _apply_category_boost(
        self,
        results: List[RerankedResult],
    ) -> List[RerankedResult]:
        """Apply category-based score boosting."""
        for result in results:
            category = result.metadata.get("category", "other")
            weight = self.CATEGORY_WEIGHTS.get(category, 1.0)
            result.rerank_score *= weight

        return results

    def _apply_diversity_rerank(
        self,
        results: List[RerankedResult],
    ) -> List[RerankedResult]:
        """
        Promote diversity by penalizing similar results.

        Uses a simple content overlap heuristic.
        """
        if len(results) <= 1:
            return results

        # Track selected results and their content
        selected = [results[0]]
        candidates = results[1:]

        for candidate in candidates:
            # Check similarity to already selected results
            max_similarity = 0.0
            for selected_result in selected:
                similarity = self._compute_similarity(
                    candidate.content,
                    selected_result.content,
                )
                max_similarity = max(max_similarity, similarity)

            # Penalize if too similar to existing selections
            if max_similarity > self.diversity_threshold:
                candidate.rerank_score *= (1.0 - max_similarity * 0.5)

            selected.append(candidate)

        return selected

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute simple text similarity using word overlap.

        For production, consider using sentence embeddings.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)  # Jaccard similarity


# Default reranker instance
reranker = Reranker()


def rerank(
    query: str,
    results: List[RetrievalResult],
    **kwargs,
) -> List[RerankedResult]:
    """Convenience function for reranking."""
    return reranker.rerank(query, results, **kwargs)
