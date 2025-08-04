"""
Unified Web Scraping System
Intelligent, self-learning scrapers for mining industry intelligence

Main Components:
- UnifiedScraper: Core scraping engine with crawl4ai as primary
- ScraperFactory: Central orchestrator for all scraping operations  
- MiningNewsScraper: Specialized for mining industry news
- FinancialDataScraper: Specialized for financial and market data
- ScraperIntelligence: Learning system that optimizes scraper selection

Usage:
    from src.scrapers import scrape_all_mining_sources, scrape_mining_news
    
    # Scrape all sources
    results = await scrape_all_mining_sources()
    
    # Scrape specific category
    news = await scrape_mining_news()
"""

# Main factory functions - primary interface
from .scraper_factory import (
    scrape_all_mining_sources,
    scrape_mining_news, 
    scrape_financial_data,
    get_intelligence_report,
    ScraperFactory
)

# Specialized scrapers
from .mining_news_scraper import MiningNewsScraper
from .financial_data_scraper import FinancialDataScraper

# Core components
from .unified_scraper import UnifiedScraper, ScrapingStrategy, ScrapingResult
from .scraper_intelligence import ScraperIntelligence

# Configuration
from ..utils.scraper_config import load_scraper_config

__all__ = [
    # Main interface functions
    'scrape_all_mining_sources',
    'scrape_mining_news',
    'scrape_financial_data', 
    'get_intelligence_report',
    
    # Classes for advanced usage
    'ScraperFactory',
    'UnifiedScraper',
    'MiningNewsScraper',
    'FinancialDataScraper',
    'ScraperIntelligence',
    
    # Data structures
    'ScrapingStrategy',
    'ScrapingResult',
    
    # Configuration
    'load_scraper_config'
]

# Version and metadata
__version__ = "1.0.0"
__author__ = "Mining Intelligence System"
__description__ = "Intelligent web scraping system with self-learning capabilities"