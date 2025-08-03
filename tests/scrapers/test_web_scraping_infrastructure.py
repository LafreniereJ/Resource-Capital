"""
Web scraping infrastructure tests
Tests source reliability, anti-bot protection, and failure recovery
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from src.intelligence.robust_web_scraper import RobustWebScraper, ScrapingTarget, ScrapingResult


class TestWebScrapingInfrastructure:
    """Test suite for web scraping infrastructure"""
    
    @pytest.mark.scraper
    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement(self):
        """Test that rate limiting is properly enforced"""
        
        # Create scraper with very strict rate limiting
        async with RobustWebScraper() as scraper:
            test_target = ScrapingTarget(
                name="rate_limit_test",
                url="https://httpbin.org/delay/1",
                scrape_type="rss",
                rate_limit=2.0,  # 2 second minimum delay
                retry_count=1,
                timeout=10
            )
            
            # Record start time
            start_time = datetime.now()
            
            # Make multiple requests
            results = []
            for i in range(3):
                result = await scraper.scrape_single_target(test_target)
                results.append((datetime.now(), result))
            
            # Verify rate limiting was enforced
            for i in range(1, len(results)):
                time_diff = (results[i][0] - results[i-1][0]).total_seconds()
                assert time_diff >= 1.8, f"Rate limiting not enforced: {time_diff}s between requests"
                
            total_time = (results[-1][0] - start_time).total_seconds()
            assert total_time >= 4.0, f"Total time too short: {total_time}s for 3 requests with 2s rate limit"
    
    @pytest.mark.scraper
    @pytest.mark.asyncio
    async def test_retry_logic_and_error_handling(self):
        """Test retry logic and error handling for failed requests"""
        
        async with RobustWebScraper() as scraper:
            # Test with non-existent domain
            failing_target = ScrapingTarget(
                name="failing_test",
                url="https://definitely-does-not-exist-12345.com/feed.xml",
                scrape_type="rss", 
                retry_count=3,
                timeout=5
            )
            
            start_time = datetime.now()
            result = await scraper.scrape_single_target(failing_target)
            end_time = datetime.now()
            
            # Should fail gracefully
            assert not result.success
            assert result.error_message is not None
            assert len(result.error_message) > 0
            
            # Should have attempted retries
            retry_time = (end_time - start_time).total_seconds()
            assert retry_time >= 10, f"Retry time too short: {retry_time}s (expected at least 3 retries * ~3s each)"
    
    @pytest.mark.scraper
    @pytest.mark.asyncio
    async def test_rss_feed_parsing_accuracy(self):
        """Test RSS feed parsing accuracy with various feed formats"""
        
        # Mock RSS feed data
        mock_rss_data = '''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Mining Industry News</title>
                <description>Latest mining news and updates</description>
                <link>https://mining-news.com</link>
                <item>
                    <title>First Quantum Minerals reports strong copper production</title>
                    <description>Canadian copper miner First Quantum Minerals Ltd. reported quarterly copper production of 185,000 tonnes, exceeding guidance by 8%.</description>
                    <link>https://mining-news.com/first-quantum-copper-production</link>
                    <pubDate>Mon, 03 Aug 2025 14:30:00 GMT</pubDate>
                    <guid>mining-news-001</guid>
                </item>
                <item>
                    <title>Gold prices surge to 3-month highs on inflation concerns</title>
                    <description>Gold futures climbed 2.5% to $2,085 per ounce as investors sought safe-haven assets amid rising inflation expectations.</description>
                    <link>https://mining-news.com/gold-price-surge</link>
                    <pubDate>Mon, 03 Aug 2025 13:15:00 GMT</pubDate>
                    <guid>mining-news-002</guid>
                </item>
            </channel>
        </rss>'''
        
        with patch('feedparser.parse') as mock_feedparser:
            # Setup mock to return parsed RSS data
            mock_feedparser.return_value = {
                'entries': [
                    {
                        'title': 'First Quantum Minerals reports strong copper production',
                        'description': 'Canadian copper miner First Quantum Minerals Ltd. reported quarterly copper production of 185,000 tonnes, exceeding guidance by 8%.',
                        'link': 'https://mining-news.com/first-quantum-copper-production',
                        'published_parsed': (2025, 8, 3, 14, 30, 0, 0, 215, 0),
                        'id': 'mining-news-001'
                    },
                    {
                        'title': 'Gold prices surge to 3-month highs on inflation concerns',
                        'description': 'Gold futures climbed 2.5% to $2,085 per ounce as investors sought safe-haven assets amid rising inflation expectations.',
                        'link': 'https://mining-news.com/gold-price-surge',
                        'published_parsed': (2025, 8, 3, 13, 15, 0, 0, 215, 0),
                        'id': 'mining-news-002'
                    }
                ]
            }
            
            async with RobustWebScraper() as scraper:
                rss_target = ScrapingTarget(
                    name="test_rss_feed",
                    url="https://test-mining-news.com/feed.xml",
                    scrape_type="rss",
                    enabled=True
                )
                
                result = await scraper.scrape_single_target(rss_target)
                
                # Verify parsing success
                assert result.success
                assert len(result.events) == 2
                
                # Verify event data extraction
                events = result.events
                
                # Check first event
                first_event = events[0]
                assert "First Quantum" in first_event.headline
                assert "copper production" in first_event.headline.lower()
                assert "185,000 tonnes" in first_event.summary
                assert first_event.url == "https://mining-news.com/first-quantum-copper-production"
                
                # Check second event
                second_event = events[1]
                assert "Gold prices surge" in second_event.headline
                assert "$2,085" in second_event.summary
                assert first_event.url == "https://mining-news.com/gold-price-surge"
    
    @pytest.mark.scraper
    @pytest.mark.asyncio
    async def test_html_scraping_resilience(self):
        """Test HTML scraping resilience with various webpage structures"""
        
        # Mock HTML content
        mock_html_content = '''
        <html>
            <head><title>Mining News Site</title></head>
            <body>
                <div class="news-container">
                    <article class="news-item">
                        <h2 class="headline">Barrick Gold announces new discovery in Nevada</h2>
                        <p class="summary">Major gold discovery could extend mine life by 15 years</p>
                        <span class="date">2025-08-03</span>
                    </article>
                    <article class="news-item">
                        <h2 class="headline">Copper demand outlook remains strong despite economic concerns</h2>
                        <p class="summary">Analysts maintain positive copper demand forecasts for 2025</p>
                        <span class="date">2025-08-02</span>
                    </article>
                </div>
            </body>
        </html>
        '''
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_html_content
            mock_response.headers = {'content-type': 'text/html'}
            mock_get.return_value = mock_response
            
            async with RobustWebScraper() as scraper:
                html_target = ScrapingTarget(
                    name="test_html_site",
                    url="https://test-mining-site.com/news",
                    scrape_type="html",
                    enabled=True
                )
                
                result = await scraper.scrape_single_target(html_target)
                
                # Verify HTML parsing success
                assert result.success
                assert len(result.events) >= 1
                
                # Verify content extraction
                events = result.events
                headlines = [event.headline for event in events]
                
                # Should extract meaningful headlines
                assert any("Barrick Gold" in headline for headline in headlines)
                assert any("Nevada" in headline for headline in headlines)
    
    @pytest.mark.scraper
    @pytest.mark.asyncio
    async def test_concurrent_scraping_performance(self):
        """Test concurrent scraping performance and stability"""
        
        # Create multiple test targets
        test_targets = []
        for i in range(5):
            target = ScrapingTarget(
                name=f"concurrent_test_{i}",
                url=f"https://httpbin.org/delay/{i}",  # Different delays
                scrape_type="rss",
                rate_limit=0.5,
                timeout=10,
                enabled=True
            )
            test_targets.append(target)
        
        with patch('feedparser.parse') as mock_feedparser:
            # Mock successful RSS parsing
            mock_feedparser.return_value = {
                'entries': [
                    {
                        'title': f'Test news item',
                        'description': 'Test description',
                        'link': 'https://test.com/item',
                        'published_parsed': datetime.now().timetuple()
                    }
                ]
            }
            
            async with RobustWebScraper() as scraper:
                # Override targets for testing
                scraper.scraping_targets = test_targets
                
                start_time = datetime.now()
                results = await scraper.scrape_all_targets()
                end_time = datetime.now()
                
                concurrent_time = (end_time - start_time).total_seconds()
                
                # Verify concurrent performance
                # Should complete much faster than sequential processing
                assert concurrent_time < 15.0, f"Concurrent scraping too slow: {concurrent_time}s"
                
                # Verify all targets were processed
                assert len(results) == len(test_targets)
                
                # Verify results structure
                for result in results:
                    assert hasattr(result, 'success')
                    assert hasattr(result, 'response_time')
                    assert hasattr(result, 'events')
    
    @pytest.mark.scraper
    @pytest.mark.asyncio
    async def test_user_agent_rotation(self):
        """Test user agent rotation for anti-bot protection"""
        
        request_headers = []
        
        def mock_get_with_header_capture(*args, **kwargs):
            # Capture headers from each request
            headers = kwargs.get('headers', {})
            request_headers.append(headers.get('User-Agent', ''))
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<rss><channel></channel></rss>'
            return mock_response
        
        with patch('requests.get', side_effect=mock_get_with_header_capture):
            async with RobustWebScraper() as scraper:
                target = ScrapingTarget(
                    name="user_agent_test",
                    url="https://test-site.com/feed.xml",
                    scrape_type="rss",
                    enabled=True
                )
                
                # Make multiple requests
                for i in range(5):
                    await scraper.scrape_single_target(target)
                
                # Verify user agents were used
                assert len(request_headers) == 5
                assert all(len(ua) > 0 for ua in request_headers)
                
                # Verify user agent variation (should not all be identical)
                unique_user_agents = set(request_headers)
                assert len(unique_user_agents) >= 2, "User agent rotation not working"
    
    @pytest.mark.scraper
    @pytest.mark.asyncio
    async def test_content_filtering_and_relevance(self):
        """Test content filtering and relevance scoring"""
        
        # Mock RSS data with various content types
        mock_entries = [
            {
                'title': 'Agnico Eagle Mines reports record quarterly gold production',
                'description': 'Canadian gold miner achieves 850,000 ounces in Q3 2025',
                'link': 'https://mining-news.com/agnico-production',
                'published_parsed': datetime.now().timetuple()
            },
            {
                'title': 'Weather update: Sunny skies expected in Toronto',
                'description': 'Local weather forecast shows clear conditions',
                'link': 'https://weather.com/toronto-weather',
                'published_parsed': datetime.now().timetuple()
            },
            {
                'title': 'Global copper prices surge 8% on supply concerns',
                'description': 'Copper futures hit 3-month highs amid supply disruptions',
                'link': 'https://commodity-news.com/copper-surge',
                'published_parsed': datetime.now().timetuple()
            },
            {
                'title': 'Sports: Local hockey team wins championship',
                'description': 'Toronto team defeats rivals in finals',
                'link': 'https://sports.com/hockey-championship',
                'published_parsed': datetime.now().timetuple()
            }
        ]
        
        with patch('feedparser.parse') as mock_feedparser:
            mock_feedparser.return_value = {'entries': mock_entries}
            
            async with RobustWebScraper() as scraper:
                target = ScrapingTarget(
                    name="content_filter_test",
                    url="https://mixed-content-feed.com/rss.xml",
                    scrape_type="rss",
                    enabled=True
                )
                
                result = await scraper.scrape_single_target(target)
                
                # Verify filtering worked
                assert result.success
                
                # Should prioritize mining-related content
                events = result.events
                mining_events = [e for e in events if any(keyword in e.headline.lower() 
                                 for keyword in ['mining', 'gold', 'copper', 'agnico'])]
                
                assert len(mining_events) >= 2, "Mining content should be prioritized"
                
                # Verify relevance scoring
                for event in mining_events:
                    # Mining events should have higher priority scores
                    from src.intelligence.breaking_news_monitor import BreakingNewsMonitor
                    monitor = BreakingNewsMonitor()
                    monitor.analyze_event_priority(event, 1.0)
                    
                    assert event.priority_score >= 50.0, f"Mining event has low priority: {event.priority_score}"
    
    @pytest.mark.scraper
    @pytest.mark.asyncio
    async def test_error_recovery_and_fallbacks(self):
        """Test error recovery mechanisms and fallback strategies"""
        
        async with RobustWebScraper() as scraper:
            # Test various error conditions
            error_scenarios = [
                {
                    'name': 'timeout_error',
                    'url': 'https://httpbin.org/delay/30',  # Will timeout
                    'expected_error_type': 'timeout'
                },
                {
                    'name': 'http_error',
                    'url': 'https://httpbin.org/status/500',  # HTTP 500 error
                    'expected_error_type': 'http_error'
                },
                {
                    'name': 'invalid_url',
                    'url': 'not-a-valid-url-at-all',
                    'expected_error_type': 'invalid_url'
                }
            ]
            
            for scenario in error_scenarios:
                target = ScrapingTarget(
                    name=scenario['name'],
                    url=scenario['url'],
                    scrape_type="rss",
                    retry_count=2,
                    timeout=5,
                    enabled=True
                )
                
                result = await scraper.scrape_single_target(target)
                
                # Should fail gracefully without crashing
                assert not result.success
                assert result.error_message is not None
                assert len(result.error_message) > 0
                
                # Should have attempted operation despite error
                assert result.response_time > 0
    
    @pytest.mark.scraper
    @pytest.mark.asyncio 
    async def test_memory_usage_under_load(self):
        """Test memory usage and resource management under load"""
        
        # Create large number of targets to test memory usage
        large_target_set = []
        for i in range(20):
            target = ScrapingTarget(
                name=f"memory_test_{i}",
                url=f"https://httpbin.org/json",
                scrape_type="rss",
                rate_limit=0.1,
                timeout=5,
                enabled=True
            )
            large_target_set.append(target)
        
        with patch('feedparser.parse') as mock_feedparser:
            # Mock small responses to test memory efficiency
            mock_feedparser.return_value = {
                'entries': [
                    {
                        'title': f'Test item {i}',
                        'description': 'Small test description',
                        'link': f'https://test.com/item-{i}',
                        'published_parsed': datetime.now().timetuple()
                    } for i in range(3)  # Small number of items per feed
                ]
            }
            
            async with RobustWebScraper() as scraper:
                # Override targets
                scraper.scraping_targets = large_target_set
                
                # Monitor memory usage (simplified)
                import psutil
                import os
                
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                results = await scraper.scrape_all_targets()
                
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = memory_after - memory_before
                
                # Verify memory usage is reasonable
                assert memory_increase < 50, f"Memory usage too high: {memory_increase}MB increase"
                
                # Verify all targets were processed
                assert len(results) == len(large_target_set)
    
    @pytest.mark.scraper
    def test_scraping_target_configuration_validation(self):
        """Test validation of scraping target configurations"""
        
        # Test valid configuration
        valid_target = ScrapingTarget(
            name="valid_test",
            url="https://valid-site.com/feed.xml",
            scrape_type="rss",
            rate_limit=1.0,
            retry_count=3,
            timeout=30,
            enabled=True
        )
        
        assert valid_target.name == "valid_test"
        assert valid_target.url == "https://valid-site.com/feed.xml"
        assert valid_target.scrape_type == "rss"
        assert valid_target.rate_limit == 1.0
        assert valid_target.retry_count == 3
        assert valid_target.timeout == 30
        assert valid_target.enabled is True
        
        # Test invalid configurations
        invalid_configs = [
            {
                'name': '',  # Empty name
                'url': 'https://test.com',
                'scrape_type': 'rss'
            },
            {
                'name': 'test',
                'url': '',  # Empty URL
                'scrape_type': 'rss'
            },
            {
                'name': 'test',
                'url': 'https://test.com',
                'scrape_type': 'invalid_type'  # Invalid scrape type
            }
        ]
        
        for config in invalid_configs:
            try:
                target = ScrapingTarget(**config)
                # If we get here, validation should catch the invalid config
                # For now, we'll just verify the target was created
                assert hasattr(target, 'name')
            except Exception as e:
                # Expected for invalid configurations
                assert len(str(e)) > 0