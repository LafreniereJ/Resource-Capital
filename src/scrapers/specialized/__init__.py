"""
Specialized Mining Intelligence Scrapers
Focused scraping modules for different data domains

Each scraper is optimized for a specific type of mining-related data:
- MetalPricesScraper: Real-time and historical commodity/metal prices
- EconomicDataScraper: Economic indicators affecting mining sector
- MiningCompaniesScraper: Company-specific data and corporate information
- MiningNewsScraper: Industry news, analysis, and market commentary
"""

from .metal_prices_scraper import MetalPricesScraper
from .economic_data_scraper import EconomicDataScraper
from .mining_companies_scraper import MiningCompaniesScraper
from .mining_news_scraper import SpecializedMiningNewsScraper

__all__ = [
    'MetalPricesScraper',
    'EconomicDataScraper', 
    'MiningCompaniesScraper',
    'SpecializedMiningNewsScraper'
]

__version__ = "1.0.0"
__author__ = "Mining Intelligence System"
__description__ = "Specialized scrapers for comprehensive mining intelligence"