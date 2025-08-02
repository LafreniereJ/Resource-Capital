#!/usr/bin/env python3
"""
Configuration file for Enhanced Mining Data Extractor
"""

import os
from typing import Dict, Any

class Config:
    """Configuration settings for the FREE mining data extraction system"""
    
    # V1: 100% FREE - No paid APIs
    USE_FREE_TOOLS_ONLY = True
    
    # Database settings
    DATABASE_PATH = "data/databases/mining_companies.db"
    INTELLIGENCE_DATABASE_PATH = "data/databases/complete_mining_intelligence.db"
    
    # Crawling settings
    CRAWL_DELAY = 2  # seconds between requests (respectful scraping)
    REQUEST_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    
    # Content extraction settings
    MIN_WORD_COUNT = 100
    MAX_CONTENT_SIZE = 1000000  # 1MB
    
    # Free data sources
    FREE_DATA_SOURCES = {
        "yfinance": True,      # Free market data
        "feedparser": True,    # Free RSS feeds
        "beautifulsoup": True, # Free web scraping
        "selenium": True,      # Free browser automation
        "playwright": True     # Free browser automation
    }
    
    # Date range for content relevance
    RELEVANCE_DAYS_BACK = 180  # 6 months
    
    # Scoring thresholds
    HIGH_RELEVANCE_THRESHOLD = 70
    MEDIUM_RELEVANCE_THRESHOLD = 40
    
    # Content categories and weights
    CONTENT_WEIGHTS = {
        "earnings": 30,
        "guidance": 25,
        "operational": 20,
        "corporate": 15,
        "exploration": 10,
        "general": 5
    }
    
    # Financial keywords for relevance scoring
    FINANCIAL_KEYWORDS = [
        "earnings", "revenue", "ebitda", "cash flow", "guidance", 
        "dividend", "acquisition", "merger", "takeover", "ipo",
        "debt", "financing", "capital", "investment", "profit",
        "loss", "quarterly results", "annual results"
    ]
    
    # Operational keywords for mining companies
    OPERATIONAL_KEYWORDS = [
        "production", "mining", "exploration", "drilling", "ore",
        "grade", "recovery", "mill", "processing", "reserves",
        "resources", "deposit", "tonnage", "expansion", "development"
    ]
    
    # News source patterns to prioritize
    PRIORITY_NEWS_SOURCES = [
        "investor-relations", "press-release", "news-release",
        "sec-filing", "sedar", "earnings", "quarterly-report"
    ]
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings for FREE version"""
        
        issues = []
        
        # Check database path
        if not cls.DATABASE_PATH:
            issues.append("Database path not specified")
        
        # Check numeric settings
        if cls.CRAWL_DELAY < 1:
            issues.append("Crawl delay should be at least 1 second")
        
        if cls.REQUEST_TIMEOUT < 10:
            issues.append("Request timeout should be at least 10 seconds")
        
        # Verify we're using only free tools
        if not cls.USE_FREE_TOOLS_ONLY:
            issues.append("V1 must use only free tools")
        
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  • {issue}")
            return False
        
        return True
    
    @classmethod
    def setup_instructions(cls) -> str:
        """Return setup instructions for FREE version"""
        
        instructions = """
FREE MINING INTELLIGENCE SETUP:
===============================

1. Install Python 3.8+ and create virtual environment:
   python -m venv mining_env
   source mining_env/bin/activate  # Linux/Mac
   mining_env\\Scripts\\activate     # Windows

2. Install FREE dependencies:
   pip install -r requirements.txt

3. Install browser drivers (for free web scraping):
   playwright install chromium

4. No API keys required - 100% free!

5. Test the configuration:
   python src/core/config.py

6. Data sources (all FREE):
   ✓ yfinance: Stock market data
   ✓ feedparser: RSS news feeds  
   ✓ BeautifulSoup: Web scraping
   ✓ Selenium: Browser automation
   ✓ Playwright: Modern browser automation
"""
        return instructions

def main():
    """Test FREE configuration and display setup instructions"""
    
    print("🆓 FREE Mining Intelligence System Configuration")
    print("=" * 50)
    
    # Validate configuration
    if Config.validate_config():
        print("✅ Configuration is valid")
        print("✅ 100% FREE - No paid APIs required!")
        
        # Show configuration details
        print(f"✅ Database: {Config.DATABASE_PATH}")
        print(f"✅ Intelligence DB: {Config.INTELLIGENCE_DATABASE_PATH}")
        print(f"✅ Crawl delay: {Config.CRAWL_DELAY}s (respectful scraping)")
        print(f"✅ High relevance threshold: {Config.HIGH_RELEVANCE_THRESHOLD}")
        
        # Show free data sources
        print("\n🔧 Free Data Sources Available:")
        for source, enabled in Config.FREE_DATA_SOURCES.items():
            status = "✅" if enabled else "❌"
            print(f"  {status} {source}")
        
    else:
        print("❌ Configuration issues found")
        print(Config.setup_instructions())

if __name__ == "__main__":
    main()