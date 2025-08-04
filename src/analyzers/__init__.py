"""
Mining Intelligence Analyzers
Specialized analysis modules for mining industry data

Each analyzer processes data from its corresponding scraper:
- PriceAnalyzer: Analyzes metal and commodity price trends
- EconomicAnalyzer: Analyzes economic indicators affecting mining
- CompanyAnalyzer: Analyzes company performance and financials
- NewsAnalyzer: Analyzes news sentiment and market impact
"""

from .price_analyzer import PriceAnalyzer

__all__ = [
    'PriceAnalyzer'
]

__version__ = "1.0.0"
__author__ = "Mining Intelligence System"
__description__ = "Specialized analyzers for comprehensive mining intelligence"