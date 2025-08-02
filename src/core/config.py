#!/usr/bin/env python3
"""
Configuration file for Enhanced Mining Data Extractor
"""

import os
from typing import Dict, Any

class Config:
    """Configuration settings for the mining data extraction system"""
    
    # API Keys (set these as environment variables or update directly)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")
    
    # Database settings
    DATABASE_PATH = "mining_companies.db"
    
    # Crawling settings
    CRAWL_DELAY = 2  # seconds between requests
    REQUEST_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    
    # Content extraction settings
    MIN_WORD_COUNT = 100
    MAX_CONTENT_SIZE = 1000000  # 1MB
    
    # LLM settings
    DEFAULT_LLM_PROVIDER = "openai/gpt-4o-mini"  # Cost-effective model
    ALTERNATIVE_LLM_PROVIDER = "anthropic/claude-3-haiku"  # Backup option
    
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
    def get_llm_config(cls) -> Dict[str, Any]:
        """Get LLM configuration based on available API keys"""
        
        if cls.OPENAI_API_KEY and cls.OPENAI_API_KEY != "your-openai-api-key-here":
            return {
                "provider": cls.DEFAULT_LLM_PROVIDER,
                "api_token": cls.OPENAI_API_KEY
            }
        elif cls.ANTHROPIC_API_KEY and cls.ANTHROPIC_API_KEY != "your-anthropic-api-key-here":
            return {
                "provider": cls.ALTERNATIVE_LLM_PROVIDER,
                "api_token": cls.ANTHROPIC_API_KEY
            }
        else:
            # Fallback to local model (requires ollama)
            return {
                "provider": "ollama/llama3.2",
                "api_token": "no-token-needed"
            }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        
        issues = []
        
        # Check API keys
        llm_config = cls.get_llm_config()
        if "ollama" not in llm_config["provider"] and llm_config["api_token"] == "no-token-needed":
            issues.append("No valid API key found for OpenAI or Anthropic")
        
        # Check database path
        if not cls.DATABASE_PATH:
            issues.append("Database path not specified")
        
        # Check numeric settings
        if cls.CRAWL_DELAY < 1:
            issues.append("Crawl delay should be at least 1 second")
        
        if cls.REQUEST_TIMEOUT < 10:
            issues.append("Request timeout should be at least 10 seconds")
        
        if issues:
            print("Configuration issues found:")
            for issue in issues:
                print(f"  • {issue}")
            return False
        
        return True
    
    @classmethod
    def setup_instructions(cls) -> str:
        """Return setup instructions for users"""
        
        instructions = """
SETUP INSTRUCTIONS:
==================

1. API Keys (choose one):
   Option A - OpenAI:
     export OPENAI_API_KEY="your-openai-api-key"
   
   Option B - Anthropic:
     export ANTHROPIC_API_KEY="your-anthropic-api-key"
   
   Option C - Local Ollama (free but requires setup):
     Install ollama: https://ollama.ai/
     Run: ollama pull llama3.2

2. Install required packages:
   pip install openai anthropic

3. Update config.py if needed:
   - Adjust crawl delays for your use case
   - Modify content weights and keywords
   - Set custom relevance thresholds

4. Test the configuration:
   python config.py
"""
        return instructions

def main():
    """Test configuration and display setup instructions"""
    
    print("Mining Data Extractor Configuration")
    print("=" * 40)
    
    # Validate configuration
    if Config.validate_config():
        print("✓ Configuration is valid")
        
        # Show LLM configuration
        llm_config = Config.get_llm_config()
        print(f"✓ LLM Provider: {llm_config['provider']}")
        
        if "ollama" in llm_config['provider']:
            print("  Note: Using local Ollama model (free but requires ollama installation)")
        elif "openai" in llm_config['provider']:
            print("  Note: Using OpenAI API (paid service)")
        elif "anthropic" in llm_config['provider']:
            print("  Note: Using Anthropic API (paid service)")
        
        print(f"✓ Database: {Config.DATABASE_PATH}")
        print(f"✓ Crawl delay: {Config.CRAWL_DELAY}s")
        print(f"✓ High relevance threshold: {Config.HIGH_RELEVANCE_THRESHOLD}")
        
    else:
        print("✗ Configuration issues found")
        print(Config.setup_instructions())

if __name__ == "__main__":
    main()