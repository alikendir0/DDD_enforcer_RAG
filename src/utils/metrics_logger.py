"""Centralized metrics collection and aggregation utilities."""
from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Any, List

from src.models.conversation import QueryMetrics, IndexingMetrics
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MetricsLogger:
    """In-memory metrics logger with simple aggregation per session.

    This is intentionally lightweight and can be extended later to persist
    metrics or export them to external monitoring systems.
    """

    def __init__(self) -> None:
        self._queries: Dict[str, List[QueryMetrics]] = {}
        self._global_total_tokens: int = 0

    def log_query(self, session_id: str, metrics: QueryMetrics) -> None:
        """Record metrics for a single query in a session."""
        self._queries.setdefault(session_id, []).append(metrics)
        # Update global aggregate token count
        try:
            self._global_total_tokens += max(0, int(metrics.total_tokens))
        except Exception:
            # Be defensive; never let metrics logging break the main flow
            pass
        logger.info(
            "Query metrics | session=%s | data=%s",
            session_id,
            asdict(metrics),
        )

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Compute simple aggregates for a session.

        Returns empty aggregates if the session is unknown.
        """
        items = self._queries.get(session_id, [])
        if not items:
            return {
                "total_queries": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "avg_total_time_ms": 0.0,
            }

        total_queries = len(items)
        total_tokens = sum(m.total_tokens for m in items)
        total_cost = sum(m.cost_usd for m in items)
        avg_total_time = sum(m.total_time_ms for m in items) / total_queries

        return {
            "total_queries": total_queries,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "avg_total_time_ms": avg_total_time,
        }

    def get_global_total_tokens(self) -> int:
        """Return total tokens used across all sessions in this process."""
        return self._global_total_tokens


# Global singleton for simplicity in this app
metrics_logger = MetricsLogger()
