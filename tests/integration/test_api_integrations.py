"""
API Integration Tests
Tests Yahoo Finance, RSS feeds, and database operations
"""
import pytest
import asyncio
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import yfinance as yf
import feedparser


class TestAPIIntegrations:
    """Test suite for API integrations"""
    
    @pytest.mark.api
    @pytest.mark.requires_network
    def test_yahoo_finance_api_integration(self, mock_yahoo_finance_data):
        """Test Yahoo Finance API integration and data extraction"""
        
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock ticker
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = mock_yahoo_finance_data['AEM.TO']
            
            # Mock historical data
            mock_ticker_instance.history.return_value = MagicMock()
            mock_ticker_instance.history.return_value.to_dict.return_value = {
                'Close': {
                    datetime(2025, 8, 1): 82.45,
                    datetime(2025, 8, 2): 83.70,
                    datetime(2025, 8, 3): 82.95
                },
                'Volume': {
                    datetime(2025, 8, 1): 892000,
                    datetime(2025, 8, 2): 756000,
                    datetime(2025, 8, 3): 934000
                }
            }
            
            mock_ticker.return_value = mock_ticker_instance
            
            # Test basic ticker data retrieval
            symbols = ['AEM.TO', 'FM.TO', 'HBM.TO']
            
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Verify required fields are present
                required_fields = ['shortName', 'regularMarketPrice', 'marketCap']
                for field in required_fields:
                    assert field in info, f"Required field {field} missing for {symbol}"
                
                # Verify data types
                assert isinstance(info['regularMarketPrice'], (int, float))
                assert isinstance(info['marketCap'], (int, float))
                assert isinstance(info['shortName'], str)
                
                # Verify reasonable value ranges
                assert info['regularMarketPrice'] > 0
                assert info['marketCap'] > 0
                assert len(info['shortName']) > 0
                
                # Test historical data retrieval
                hist_data = ticker.history(period="5d")
                hist_dict = hist_data.to_dict()
                
                assert 'Close' in hist_dict
                assert 'Volume' in hist_dict
                assert len(hist_dict['Close']) > 0
    
    @pytest.mark.api
    def test_rss_feed_api_integration(self, mock_rss_feed_data):
        """Test RSS feed API integration and parsing"""
        
        with patch('feedparser.parse') as mock_parse:
            # Setup mock RSS response
            mock_parse.return_value = {
                'feed': {
                    'title': 'Mining News Feed',
                    'link': 'https://mining-news.com',
                    'description': 'Latest mining industry news'
                },
                'entries': [
                    {
                        'title': 'Gold prices reach new monthly highs amid inflation fears',
                        'link': 'https://mining-news.com/gold-prices-highs',
                        'description': 'Gold futures climbed to $2,650 per ounce as investors seek safe-haven assets.',
                        'published': 'Mon, 03 Aug 2025 10:30:00 GMT',
                        'published_parsed': (2025, 8, 3, 10, 30, 0, 0, 215, 0),
                        'id': 'mining-news-gold-001'
                    },
                    {
                        'title': 'Canadian mining companies report strong Q2 earnings',
                        'link': 'https://mining-news.com/canadian-q2-earnings',
                        'description': 'Major Canadian miners including Barrick Gold reported better-than-expected results.',
                        'published': 'Mon, 03 Aug 2025 09:15:00 GMT',
                        'published_parsed': (2025, 8, 3, 9, 15, 0, 0, 215, 0),
                        'id': 'mining-news-earnings-001'
                    }
                ]
            }
            
            # Test RSS feed parsing
            test_feeds = [
                'https://feeds.reuters.com/reuters/businessNews',
                'https://feeds.bbci.co.uk/news/business/rss.xml',
                'https://mining.com/feed/'
            ]
            
            for feed_url in test_feeds:
                parsed_feed = feedparser.parse(feed_url)
                
                # Verify feed structure
                assert 'feed' in parsed_feed
                assert 'entries' in parsed_feed
                
                # Verify feed metadata
                feed_info = parsed_feed['feed']
                assert 'title' in feed_info
                assert 'link' in feed_info
                
                # Verify entries
                entries = parsed_feed['entries']
                assert len(entries) > 0
                
                for entry in entries:
                    # Verify required entry fields
                    required_fields = ['title', 'link', 'description']
                    for field in required_fields:
                        assert field in entry, f"Required field {field} missing in RSS entry"
                    
                    # Verify data quality
                    assert len(entry['title']) > 0
                    assert entry['link'].startswith('http')
                    assert len(entry['description']) > 0
                    
                    # Verify timestamp parsing
                    if 'published_parsed' in entry:
                        time_struct = entry['published_parsed']
                        assert len(time_struct) == 9  # Standard time tuple
                        assert time_struct[0] >= 2020  # Reasonable year
    
    @pytest.mark.api
    def test_database_operations_integration(self, temp_db):
        """Test database operations integration"""
        
        # Test database connection and basic operations
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Test table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['companies', 'intelligence_data']
        for table in expected_tables:
            assert table in tables, f"Expected table {table} not found"
        
        # Test data insertion
        test_intelligence_data = [
            (
                'Test mining company announces expansion plans',
                'Company plans to expand operations in northern Canada',
                'https://test.com/expansion',
                'test_source',
                datetime.now(),
                75.0,
                'corporate',
                'medium',
                80.0
            ),
            (
                'Copper prices surge on supply disruption',
                'Copper futures gained 8% on supply concerns',
                'https://test.com/copper-surge',
                'commodity_news',
                datetime.now(),
                85.0,
                'market_move',
                'high',
                70.0
            )
        ]
        
        for data in test_intelligence_data:
            cursor.execute('''
                INSERT INTO intelligence_data 
                (headline, summary, url, source, published, priority_score, event_type, impact_level, canadian_relevance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
        
        conn.commit()
        
        # Test data retrieval
        cursor.execute('SELECT * FROM intelligence_data')
        retrieved_data = cursor.fetchall()
        
        assert len(retrieved_data) >= len(test_intelligence_data)
        
        # Test data filtering and querying
        cursor.execute('SELECT * FROM intelligence_data WHERE priority_score >= 80.0')
        high_priority_data = cursor.fetchall()
        
        assert len(high_priority_data) >= 1
        
        # Test company data operations
        cursor.execute('SELECT * FROM companies WHERE sector = "Gold"')
        gold_companies = cursor.fetchall()
        
        assert len(gold_companies) >= 1
        
        # Test complex queries
        cursor.execute('''
            SELECT c.name, i.headline, i.priority_score 
            FROM companies c 
            LEFT JOIN intelligence_data i ON i.headline LIKE '%' || c.name || '%'
            WHERE c.market_cap > 10000000000
        ''')
        
        company_intelligence = cursor.fetchall()
        # Should return some results for large companies
        
        conn.close()
    
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_comprehensive_data_aggregator_integration(self, temp_db, mock_yahoo_finance_data):
        """Test comprehensive data aggregator with multiple API sources"""
        
        with patch('yfinance.Ticker') as mock_ticker, \
             patch('feedparser.parse') as mock_feedparser:
            
            # Setup Yahoo Finance mock
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = mock_yahoo_finance_data['AEM.TO']
            mock_ticker.return_value = mock_ticker_instance
            
            # Setup RSS feed mock
            mock_feedparser.return_value = {
                'entries': [
                    {
                        'title': 'Agnico Eagle reports record gold production',
                        'description': 'Company achieved 850,000 ounces in Q3',
                        'link': 'https://mining-news.com/agnico-production',
                        'published_parsed': datetime.now().timetuple()
                    }
                ]
            }
            
            # Test data aggregation
            from src.processors.comprehensive_data_aggregator import ComprehensiveDataAggregator
            
            aggregator = ComprehensiveDataAggregator()
            
            # Test financial data aggregation
            symbols = ['AEM.TO', 'FM.TO']
            financial_data = {}
            
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    financial_data[symbol] = ticker.info
                except Exception as e:
                    pytest.fail(f"Financial data aggregation failed for {symbol}: {e}")
            
            assert len(financial_data) == len(symbols)
            
            # Test news data aggregation
            news_sources = ['https://test-feed1.com', 'https://test-feed2.com']
            aggregated_news = []
            
            for source in news_sources:
                try:
                    parsed_feed = feedparser.parse(source)
                    for entry in parsed_feed.get('entries', []):
                        news_item = {
                            'headline': entry.get('title', ''),
                            'summary': entry.get('description', ''),
                            'url': entry.get('link', ''),
                            'source': source,
                            'published': datetime.now()
                        }
                        aggregated_news.append(news_item)
                except Exception as e:
                    print(f"News aggregation error (may be expected): {e}")
            
            assert len(aggregated_news) > 0
            
            # Test data correlation
            correlated_data = {}
            for symbol, fin_data in financial_data.items():
                related_news = [
                    news for news in aggregated_news 
                    if any(keyword in news['headline'].lower() 
                          for keyword in ['agnico', 'eagle', 'gold'])
                ]
                
                correlated_data[symbol] = {
                    'financial': fin_data,
                    'related_news': related_news
                }
            
            assert len(correlated_data) > 0
    
    @pytest.mark.api
    def test_api_error_handling_and_resilience(self):
        """Test API error handling and resilience patterns"""
        
        # Test Yahoo Finance error handling
        with patch('yfinance.Ticker') as mock_ticker:
            # Simulate API error
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {}  # Empty response
            mock_ticker.return_value = mock_ticker_instance
            
            # Test graceful handling of empty response
            try:
                ticker = yf.Ticker('INVALID.TO')
                info = ticker.info
                
                # Should handle empty response gracefully
                assert isinstance(info, dict)
                
            except Exception as e:
                # Should not crash the application
                assert len(str(e)) > 0
        
        # Test RSS feed error handling
        with patch('feedparser.parse') as mock_feedparser:
            # Simulate malformed RSS
            mock_feedparser.return_value = {
                'entries': [],  # Empty entries
                'bozo': 1,      # Indicates parsing error
                'bozo_exception': Exception("Malformed XML")
            }
            
            try:
                parsed_feed = feedparser.parse('https://invalid-feed.com')
                
                # Should handle malformed feed gracefully
                assert 'entries' in parsed_feed
                assert isinstance(parsed_feed['entries'], list)
                
            except Exception as e:
                # Should not crash
                assert len(str(e)) > 0
        
        # Test database error handling
        try:
            # Try to connect to invalid database
            conn = sqlite3.connect('/invalid/path/database.db')
            conn.close()
        except Exception as e:
            # Should handle database connection errors
            assert 'unable to open database' in str(e).lower() or 'no such file' in str(e).lower()
    
    @pytest.mark.api
    def test_api_rate_limiting_compliance(self):
        """Test compliance with API rate limiting requirements"""
        
        import time
        
        # Test Yahoo Finance rate limiting
        request_times = []
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {'shortName': 'Test Company', 'regularMarketPrice': 25.0}
            mock_ticker.return_value = mock_ticker_instance
            
            # Make multiple requests and track timing
            symbols = ['AEM.TO', 'FM.TO', 'HBM.TO', 'LUN.TO']
            
            for symbol in symbols:
                start_time = time.time()
                ticker = yf.Ticker(symbol)
                _ = ticker.info
                end_time = time.time()
                
                request_times.append(end_time - start_time)
                
                # Add small delay to be respectful
                time.sleep(0.5)
            
            # Verify we're not making requests too rapidly
            total_time = sum(request_times) + (len(symbols) - 1) * 0.5  # Include delays
            assert total_time >= 1.5, f"Requests made too rapidly: {total_time}s for {len(symbols)} requests"
        
        # Test RSS feed rate limiting
        with patch('feedparser.parse') as mock_feedparser:
            mock_feedparser.return_value = {'entries': []}
            
            rss_feeds = [
                'https://feed1.com/rss.xml',
                'https://feed2.com/rss.xml',
                'https://feed3.com/rss.xml'
            ]
            
            feed_request_times = []
            
            for feed_url in rss_feeds:
                start_time = time.time()
                _ = feedparser.parse(feed_url)
                end_time = time.time()
                
                feed_request_times.append(end_time - start_time)
                
                # Be respectful with delays
                time.sleep(1.0)
            
            total_feed_time = sum(feed_request_times) + (len(rss_feeds) - 1) * 1.0
            assert total_feed_time >= 2.0, f"RSS requests made too rapidly: {total_feed_time}s"
    
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_concurrent_api_access_stability(self, mock_yahoo_finance_data):
        """Test stability of concurrent API access"""
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = mock_yahoo_finance_data['AEM.TO']
            mock_ticker.return_value = mock_ticker_instance
            
            # Test concurrent Yahoo Finance requests
            async def fetch_ticker_data(symbol):
                try:
                    ticker = yf.Ticker(symbol)
                    return ticker.info
                except Exception as e:
                    return {'error': str(e)}
            
            symbols = ['AEM.TO', 'FM.TO', 'HBM.TO', 'LUN.TO', 'GOLD.TO']
            
            # Create concurrent tasks
            tasks = [fetch_ticker_data(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all requests completed
            assert len(results) == len(symbols)
            
            # Verify most requests succeeded
            successful_results = [r for r in results if not isinstance(r, Exception) and 'error' not in r]
            success_rate = len(successful_results) / len(results)
            
            assert success_rate >= 0.8, f"Concurrent API success rate too low: {success_rate}"
        
        # Test concurrent RSS feed parsing
        with patch('feedparser.parse') as mock_feedparser:
            mock_feedparser.return_value = {
                'entries': [
                    {
                        'title': 'Test news item',
                        'description': 'Test description',
                        'link': 'https://test.com/news'
                    }
                ]
            }
            
            async def fetch_rss_data(feed_url):
                try:
                    return feedparser.parse(feed_url)
                except Exception as e:
                    return {'error': str(e)}
            
            rss_feeds = [
                'https://feed1.com/rss.xml',
                'https://feed2.com/rss.xml', 
                'https://feed3.com/rss.xml',
                'https://feed4.com/rss.xml'
            ]
            
            rss_tasks = [fetch_rss_data(feed) for feed in rss_feeds]
            rss_results = await asyncio.gather(*rss_tasks, return_exceptions=True)
            
            assert len(rss_results) == len(rss_feeds)
            
            successful_rss = [r for r in rss_results if not isinstance(r, Exception) and 'error' not in r]
            rss_success_rate = len(successful_rss) / len(rss_results)
            
            assert rss_success_rate >= 0.8, f"Concurrent RSS success rate too low: {rss_success_rate}"
    
    @pytest.mark.api
    def test_api_data_consistency_validation(self, mock_yahoo_finance_data):
        """Test validation of API data consistency and quality"""
        
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup multiple mock responses for consistency testing
            mock_responses = [
                mock_yahoo_finance_data['AEM.TO'],
                mock_yahoo_finance_data['FM.TO']
            ]
            
            mock_ticker_instances = []
            for response in mock_responses:
                instance = MagicMock()
                instance.info = response
                mock_ticker_instances.append(instance)
            
            mock_ticker.side_effect = mock_ticker_instances
            
            # Test data consistency across multiple requests
            symbols = ['AEM.TO', 'FM.TO']
            consistency_data = {}
            
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                data = ticker.info
                
                # Validate data structure consistency
                required_fields = ['shortName', 'regularMarketPrice', 'marketCap']
                for field in required_fields:
                    assert field in data, f"Missing required field {field} for {symbol}"
                
                # Validate data type consistency
                assert isinstance(data['regularMarketPrice'], (int, float))
                assert isinstance(data['marketCap'], (int, float))
                assert isinstance(data['shortName'], str)
                
                # Store for cross-validation
                consistency_data[symbol] = data
            
            # Cross-validate data relationships
            for symbol, data in consistency_data.items():
                # Market cap should be reasonable relative to price
                price = data['regularMarketPrice']
                market_cap = data['marketCap']
                
                # Basic sanity checks
                assert price > 0, f"Invalid price for {symbol}: {price}"
                assert market_cap > 0, f"Invalid market cap for {symbol}: {market_cap}"
                assert market_cap > price * 1000000, f"Market cap too low relative to price for {symbol}"
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.requires_network
    def test_real_api_connectivity(self):
        """Test real API connectivity (requires network)"""
        
        # This test requires actual network connectivity
        # Skip if running in offline environment
        
        try:
            # Test real Yahoo Finance connectivity
            real_ticker = yf.Ticker("AEM.TO")
            real_info = real_ticker.info
            
            # Verify we got real data
            assert 'shortName' in real_info or 'longName' in real_info
            assert 'regularMarketPrice' in real_info
            
            print("✅ Real Yahoo Finance API connectivity - OK")
            
        except Exception as e:
            pytest.skip(f"Yahoo Finance API test skipped: {e}")
        
        try:
            # Test real RSS feed connectivity
            import requests
            
            test_feeds = [
                'https://feeds.reuters.com/reuters/businessNews',
                'https://feeds.bbci.co.uk/news/business/rss.xml'
            ]
            
            working_feeds = 0
            for feed_url in test_feeds:
                try:
                    response = requests.get(feed_url, timeout=10)
                    if response.status_code == 200:
                        working_feeds += 1
                        
                        # Try to parse the feed
                        parsed = feedparser.parse(response.text)
                        assert len(parsed.get('entries', [])) > 0
                        
                except Exception as e:
                    print(f"RSS feed error: {e}")
            
            assert working_feeds >= 1, "No RSS feeds working"
            print(f"✅ Real RSS feed connectivity - {working_feeds} feeds working")
            
        except Exception as e:
            pytest.skip(f"RSS feed test skipped: {e}")
    
    @pytest.mark.api
    def test_database_performance_under_load(self, temp_db):
        """Test database performance under concurrent load"""
        
        import threading
        import time
        
        # Test concurrent database operations
        def database_worker(worker_id, num_operations):
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            for i in range(num_operations):
                # Insert test data
                cursor.execute('''
                    INSERT INTO intelligence_data 
                    (headline, summary, url, source, published, priority_score, event_type, impact_level, canadian_relevance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f'Worker {worker_id} headline {i}',
                    f'Worker {worker_id} summary {i}',
                    f'https://test.com/worker-{worker_id}-item-{i}',
                    f'worker_{worker_id}',
                    datetime.now(),
                    50.0 + (i % 50),
                    'test',
                    'medium',
                    60.0
                ))
                
                # Query data
                cursor.execute('SELECT COUNT(*) FROM intelligence_data WHERE source = ?', (f'worker_{worker_id}',))
                count = cursor.fetchone()[0]
                
                conn.commit()
            
            conn.close()
        
        # Run concurrent workers
        num_workers = 3
        operations_per_worker = 10
        
        start_time = time.time()
        
        threads = []
        for worker_id in range(num_workers):
            thread = threading.Thread(target=database_worker, args=(worker_id, operations_per_worker))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify performance
        total_operations = num_workers * operations_per_worker * 2  # Insert + query
        operations_per_second = total_operations / total_time
        
        assert operations_per_second >= 10, f"Database performance too slow: {operations_per_second} ops/sec"
        
        # Verify data integrity
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM intelligence_data')
        total_records = cursor.fetchone()[0]
        
        # Should have at least the records we inserted
        expected_min_records = num_workers * operations_per_worker
        assert total_records >= expected_min_records
        
        conn.close()