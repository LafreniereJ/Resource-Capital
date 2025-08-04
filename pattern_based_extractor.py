"""Simple pattern-based extractor used in tests.

This lightweight implementation provides placeholder
structures for financial, operational and news data
extraction. The methods perform minimal processing and
return empty results, allowing tests to import the module
without requiring the full production implementation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Any


@dataclass
class FinancialData:
    """Placeholder container for financial information."""
    items: List[Any] = field(default_factory=list)


@dataclass
class OperationalData:
    """Placeholder container for operational information."""
    items: List[Any] = field(default_factory=list)


@dataclass
class NewsItem:
    """Representation of a news item discovered during scraping."""
    title: str = ""
    category: str = ""
    relevance_score: float = 0.0


class PatternBasedExtractor:
    """Minimal extractor implementing the interface used in tests."""

    def extract_financial_data(self, content: str) -> FinancialData:
        """Return placeholder financial data."""
        return FinancialData()

    def extract_operational_data(self, content: str) -> OperationalData:
        """Return placeholder operational data."""
        return OperationalData()

    def extract_news_items(self, content: str, source: str) -> List[NewsItem]:
        """Return an empty list of news items."""
        return []

    def extract_dates(self, content: str) -> List[str]:
        """Return an empty list of date strings."""
        return []
