"""
Pytest configuration and shared fixtures for testing
"""
import pytest
import asyncio
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
        
    # Create basic tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create companies table
    cursor.execute('''
        CREATE TABLE companies (
            id INTEGER PRIMARY KEY,
            symbol TEXT UNIQUE,
            name TEXT,
            market_cap REAL,
            exchange TEXT,
            sector TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create intelligence_data table
    cursor.execute('''
        CREATE TABLE intelligence_data (
            id INTEGER PRIMARY KEY,
            headline TEXT,
            summary TEXT,
            url TEXT,
            source TEXT,
            published TIMESTAMP,
            priority_score REAL,
            event_type TEXT,
            impact_level TEXT,
            canadian_relevance REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert test companies
    test_companies = [
        ('AEM.TO', 'Agnico Eagle Mines Limited', 25000000000, 'TSX', 'Gold'),
        ('FM.TO', 'First Quantum Minerals Ltd.', 8500000000, 'TSX', 'Copper'),
        ('HBM.TO', 'Hudbay Minerals Inc.', 2100000000, 'TSX', 'Copper'),
        ('LUN.TO', 'Lundin Mining Corporation', 7800000000, 'TSX', 'Copper'),
        ('GOLD.TO', 'Barrick Gold Corporation', 35000000000, 'TSX', 'Gold')
    ]
    
    cursor.executemany(
        'INSERT INTO companies (symbol, name, market_cap, exchange, sector) VALUES (?, ?, ?, ?, ?)',
        test_companies
    )
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_news_events():
    """Sample news events for testing"""
    base_time = datetime.now()
    
    return [
        {
            'id': 'test_event_1',
            'headline': 'Agnico Eagle reports strong Q3 results with 15% production increase',
            'summary': 'Agnico Eagle Mines Limited reported quarterly gold production of 812,000 ounces, up 15% from the previous quarter, driven by strong performance at Fosterville and Canadian Malartic mines.',
            'url': 'https://test.com/agnico-q3-results',
            'source': 'mining_com',
            'published': base_time - timedelta(hours=2),
            'priority_score': 75.0,
            'event_type': 'corporate',
            'impact_level': 'medium',
            'canadian_relevance': 85.0
        },
        {
            'id': 'test_event_2',
            'headline': 'Copper prices surge 8% on China demand outlook optimism',
            'summary': 'Copper futures climbed to three-month highs as traders bet on stronger demand from China following positive manufacturing data and infrastructure spending commitments.',
            'url': 'https://test.com/copper-surge',
            'source': 'reuters',
            'published': base_time - timedelta(hours=1),
            'priority_score': 90.0,
            'event_type': 'market_move',
            'impact_level': 'high',
            'canadian_relevance': 70.0
        },
        {
            'id': 'test_event_3',
            'headline': 'First Quantum announces new copper discovery in Zambia',
            'summary': 'First Quantum Minerals has discovered significant copper mineralization at its Sentinel mine extension project in Zambia, with initial drilling results showing high-grade copper intercepts.',
            'url': 'https://test.com/fqm-discovery',
            'source': 'northern_miner',
            'published': base_time - timedelta(minutes=30),
            'priority_score': 80.0,
            'event_type': 'operational',
            'impact_level': 'high',
            'canadian_relevance': 75.0
        }
    ]


@pytest.fixture
def mock_rss_feed_data():
    """Mock RSS feed data for testing scrapers"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Mining News</title>
        <link>https://test-mining-news.com</link>
        <description>Latest mining industry news</description>
        <item>
            <title>Gold prices reach new monthly highs amid inflation fears</title>
            <link>https://test-mining-news.com/gold-prices-highs</link>
            <description>Gold futures climbed to $2,650 per ounce as investors seek safe-haven assets amid rising inflation concerns and geopolitical tensions.</description>
            <pubDate>Mon, 03 Aug 2025 10:30:00 GMT</pubDate>
            <guid>test-gold-price-001</guid>
        </item>
        <item>
            <title>Canadian mining companies report strong Q2 earnings</title>
            <link>https://test-mining-news.com/canadian-q2-earnings</link>
            <description>Major Canadian mining companies including Barrick Gold and Shopify reported better-than-expected quarterly results driven by higher commodity prices.</description>
            <pubDate>Mon, 03 Aug 2025 09:15:00 GMT</pubDate>
            <guid>test-earnings-001</guid>
        </item>
    </channel>
</rss>'''


@pytest.fixture
def mock_yahoo_finance_data():
    """Mock Yahoo Finance data for testing"""
    return {
        'AEM.TO': {
            'shortName': 'Agnico Eagle Mines Limited',
            'regularMarketPrice': 82.45,
            'regularMarketChange': 1.25,
            'regularMarketChangePercent': 1.54,
            'marketCap': 25000000000,
            'fiftyTwoWeekHigh': 89.32,
            'fiftyTwoWeekLow': 68.12,
            'volume': 892000,
            'averageVolume': 1200000
        },
        'FM.TO': {
            'shortName': 'First Quantum Minerals Ltd.',
            'regularMarketPrice': 21.87,
            'regularMarketChange': 0.89,
            'regularMarketChangePercent': 4.25,
            'marketCap': 8500000000,
            'fiftyTwoWeekHigh': 28.45,
            'fiftyTwoWeekLow': 15.23,
            'volume': 2150000,
            'averageVolume': 1800000
        }
    }


@pytest.fixture
def test_config():
    """Test configuration settings"""
    return {
        'database_path': ':memory:',
        'scraping_delay': 0.1,  # Faster for testing
        'max_retries': 2,
        'timeout': 5,
        'rate_limit_requests_per_minute': 120,
        'priority_threshold_high': 70.0,
        'priority_threshold_critical': 85.0,
        'canadian_relevance_threshold': 50.0
    }


# Async test timeout is configured in pytest.ini


# Test data constants
TEST_COMPANIES = [
    'AEM.TO', 'FM.TO', 'HBM.TO', 'LUN.TO', 'GOLD.TO', 
    'ABX.TO', 'NEM', 'TECK.B.TO', 'CCO.TO', 'SU.TO'
]

TEST_COMMODITIES = [
    'gold', 'copper', 'silver', 'uranium', 'lithium', 
    'nickel', 'zinc', 'platinum', 'palladium', 'iron'
]

TEST_RSS_SOURCES = [
    'https://feeds.reuters.com/reuters/businessNews',
    'https://feeds.bbci.co.uk/news/business/rss.xml',
    'https://rss.cnn.com/rss/money_latest.rss'
]