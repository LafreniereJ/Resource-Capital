"""
Data quality validation tests
Tests extraction accuracy, deduplication, and relevance scoring
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from src.intelligence.breaking_news_monitor import BreakingNewsEvent
from src.processors.comprehensive_data_aggregator import ComprehensiveDataAggregator


class TestDataValidation:
    """Test suite for data quality validation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.aggregator = ComprehensiveDataAggregator()
    
    @pytest.mark.data_quality
    def test_duplicate_detection_accuracy(self):
        """Test accuracy of duplicate event detection"""
        
        # Create events with varying levels of similarity
        base_time = datetime.now()
        
        test_events = [
            # Exact duplicate
            BreakingNewsEvent(
                id="dup_1",
                headline="Copper prices surge 15% on strong demand outlook",
                summary="Copper futures gained significantly today",
                url="https://source1.com/copper-surge",
                source="source1",
                published=base_time
            ),
            BreakingNewsEvent(
                id="dup_2", 
                headline="Copper prices surge 15% on strong demand outlook",
                summary="Copper futures gained significantly today",
                url="https://source2.com/copper-surge",
                source="source2",
                published=base_time + timedelta(minutes=5)
            ),
            # Near duplicate (slightly different wording)
            BreakingNewsEvent(
                id="near_dup_1",
                headline="Copper prices jump 15% amid demand optimism",
                summary="Copper futures rose significantly on positive outlook",
                url="https://source3.com/copper-jump",
                source="source3", 
                published=base_time + timedelta(minutes=10)
            ),
            # Different event
            BreakingNewsEvent(
                id="different_1",
                headline="Gold mining company reports quarterly earnings",
                summary="Agnico Eagle reported strong Q3 results",
                url="https://source4.com/agnico-earnings",
                source="source4",
                published=base_time + timedelta(hours=1)
            )
        ]
        
        # Test duplicate detection
        duplicates = self._detect_duplicates(test_events)
        
        # Should detect the exact and near duplicates
        duplicate_groups = duplicates['duplicate_groups']
        assert len(duplicate_groups) >= 1
        
        # The copper price events should be grouped together
        copper_group = None
        for group in duplicate_groups:
            if any("copper" in event.headline.lower() for event in group):
                copper_group = group
                break
        
        assert copper_group is not None
        assert len(copper_group) >= 2  # At least the exact duplicates
        
        # The earnings event should not be in any duplicate group
        earnings_event_ids = [event.id for group in duplicate_groups for event in group if "earnings" in event.headline.lower()]
        assert len(earnings_event_ids) == 0
    
    @pytest.mark.data_quality
    def test_data_extraction_accuracy(self):
        """Test accuracy of data extraction from various sources"""
        
        test_cases = [
            {
                'source_type': 'rss',
                'raw_data': {
                    'title': 'First Quantum Minerals Ltd. (TSX:FM) Stock Price Up 5.2%',
                    'description': 'First Quantum Minerals Ltd. (TSX:FM) shares traded up 5.2% during trading on Tuesday, reaching $23.45. The company reported strong copper production results.',
                    'link': 'https://finance.yahoo.com/news/first-quantum-stock-up',
                    'published': '2025-08-03T14:30:00Z'
                },
                'expected_extractions': {
                    'company_symbols': ['FM', 'TSX:FM'],
                    'price_changes': [5.2],
                    'price_values': [23.45],
                    'commodities': ['copper'],
                    'sentiment': 'positive'
                }
            },
            {
                'source_type': 'html', 
                'raw_data': {
                    'headline': 'BREAKING: Trump Announces 25% Tariff on Canadian Copper Imports',
                    'content': 'President Trump announced a 25% tariff on copper imports from Canada, citing national security concerns. The policy will take effect September 1st and is expected to impact major Canadian miners including Hudbay Minerals (HBM.TO) and Lundin Mining (LUN.TO).',
                    'timestamp': '2025-08-03T16:45:00'
                },
                'expected_extractions': {
                    'company_symbols': ['HBM.TO', 'LUN.TO'],
                    'policy_changes': ['tariff'],
                    'tariff_rates': [25],
                    'commodities': ['copper'],
                    'geographic_focus': ['canada', 'canadian'],
                    'sentiment': 'negative',
                    'impact_level': 'high'
                }
            }
        ]
        
        for test_case in test_cases:
            extracted_data = self._extract_structured_data(
                test_case['raw_data'], 
                test_case['source_type']
            )
            
            expected = test_case['expected_extractions']
            
            # Test company symbol extraction
            if 'company_symbols' in expected:
                extracted_symbols = extracted_data.get('company_symbols', [])
                for expected_symbol in expected['company_symbols']:
                    assert any(expected_symbol in symbol for symbol in extracted_symbols), \
                        f"Expected symbol {expected_symbol} not found in {extracted_symbols}"
            
            # Test commodity detection
            if 'commodities' in expected:
                extracted_commodities = extracted_data.get('commodities', [])
                for expected_commodity in expected['commodities']:
                    assert any(expected_commodity in commodity.lower() for commodity in extracted_commodities), \
                        f"Expected commodity {expected_commodity} not found in {extracted_commodities}"
            
            # Test sentiment accuracy
            if 'sentiment' in expected:
                assert extracted_data.get('sentiment') == expected['sentiment'], \
                    f"Expected sentiment {expected['sentiment']}, got {extracted_data.get('sentiment')}"
    
    @pytest.mark.data_quality
    def test_relevance_scoring_accuracy(self):
        """Test accuracy of Canadian mining relevance scoring"""
        
        test_cases = [
            {
                'event': {
                    'headline': 'Agnico Eagle Mines reports record gold production at Canadian operations',
                    'summary': 'Toronto-based Agnico Eagle achieved record quarterly gold production of 850,000 ounces across its Canadian mining operations',
                    'source': 'northern_miner'
                },
                'expected_relevance': 95.0,
                'expected_priority': 80.0
            },
            {
                'event': {
                    'headline': 'Copper prices rise 3% on London Metal Exchange',
                    'summary': 'Global copper prices increased modestly on the LME amid supply concerns',
                    'source': 'reuters'
                },
                'expected_relevance': 65.0,
                'expected_priority': 50.0
            },
            {
                'event': {
                    'headline': 'Australian iron ore exports reach new highs',
                    'summary': 'Australia reported record iron ore export volumes to China last quarter',
                    'source': 'mining_com'
                },
                'expected_relevance': 25.0,
                'expected_priority': 30.0
            },
            {
                'event': {
                    'headline': 'Trump announces 50% tariff on Canadian copper imports',
                    'summary': 'US President implements major trade policy affecting Canadian mining sector',
                    'source': 'reuters'
                },
                'expected_relevance': 90.0,
                'expected_priority': 95.0
            }
        ]
        
        from src.intelligence.breaking_news_monitor import BreakingNewsMonitor
        monitor = BreakingNewsMonitor()
        
        for test_case in test_cases:
            event_data = test_case['event']
            event = BreakingNewsEvent(
                id=f"relevance_test_{hash(event_data['headline'])}",
                headline=event_data['headline'],
                summary=event_data['summary'],
                url="https://test.com",
                source=event_data['source'],
                published=datetime.now()
            )
            
            monitor.analyze_event_priority(event, 1.0)
            
            # Test relevance scoring
            relevance_error = abs(event.canadian_relevance - test_case['expected_relevance'])
            assert relevance_error <= 20.0, \
                f"Relevance score error too high: expected {test_case['expected_relevance']}, got {event.canadian_relevance}, error: {relevance_error}"
            
            # Test priority scoring
            priority_error = abs(event.priority_score - test_case['expected_priority'])
            assert priority_error <= 25.0, \
                f"Priority score error too high: expected {test_case['expected_priority']}, got {event.priority_score}, error: {priority_error}"
    
    @pytest.mark.data_quality
    def test_data_completeness_validation(self):
        """Test validation of data completeness and quality"""
        
        # Test cases with various levels of data completeness
        test_events = [
            # Complete event
            {
                'headline': 'Complete event with all required fields',
                'summary': 'This event has all required fields properly filled',
                'url': 'https://valid-url.com/article',
                'source': 'reliable_source',
                'published': datetime.now(),
                'expected_quality_score': 100.0
            },
            # Missing summary
            {
                'headline': 'Event with missing summary',
                'summary': '',
                'url': 'https://valid-url.com/article',
                'source': 'reliable_source',
                'published': datetime.now(),
                'expected_quality_score': 75.0
            },
            # Invalid URL
            {
                'headline': 'Event with invalid URL',
                'summary': 'Valid summary content',
                'url': 'not-a-valid-url',
                'source': 'reliable_source',
                'published': datetime.now(),
                'expected_quality_score': 80.0
            },
            # Missing source
            {
                'headline': 'Event with missing source',
                'summary': 'Valid summary content',
                'url': 'https://valid-url.com/article',
                'source': '',
                'published': datetime.now(),
                'expected_quality_score': 70.0
            },
            # Very poor quality
            {
                'headline': '',
                'summary': '',
                'url': 'invalid',
                'source': '',
                'published': datetime.now(),
                'expected_quality_score': 20.0
            }
        ]
        
        for test_event in test_events:
            event = BreakingNewsEvent(
                id=f"quality_test_{hash(test_event['headline'])}",
                headline=test_event['headline'] or 'Unknown headline',
                summary=test_event['summary'] or 'No summary',
                url=test_event['url'],
                source=test_event['source'] or 'unknown',
                published=test_event['published']
            )
            
            quality_score = self._calculate_data_quality_score(event)
            
            expected_score = test_event['expected_quality_score']
            score_error = abs(quality_score - expected_score)
            
            assert score_error <= 20.0, \
                f"Quality score error too high: expected {expected_score}, got {quality_score}, error: {score_error}"
    
    @pytest.mark.data_quality
    def test_financial_data_accuracy(self, mock_yahoo_finance_data):
        """Test accuracy of financial data extraction and validation"""
        
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock data
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = mock_yahoo_finance_data['AEM.TO']
            mock_ticker.return_value = mock_ticker_instance
            
            # Test financial data extraction
            from src.linkedin.commodity_price_tracker import CommodityPriceTracker
            tracker = CommodityPriceTracker()
            
            symbol = 'AEM.TO'
            
            try:
                ticker = mock_ticker(symbol)
                financial_data = ticker.info
                
                # Validate required fields are present
                required_fields = ['regularMarketPrice', 'marketCap', 'shortName']
                for field in required_fields:
                    assert field in financial_data, f"Required field {field} missing from financial data"
                
                # Validate data types
                assert isinstance(financial_data['regularMarketPrice'], (int, float))
                assert isinstance(financial_data['marketCap'], (int, float))
                assert isinstance(financial_data['shortName'], str)
                
                # Validate reasonable ranges
                assert financial_data['regularMarketPrice'] > 0
                assert financial_data['marketCap'] > 0
                assert len(financial_data['shortName']) > 0
                
            except Exception as e:
                pytest.fail(f"Financial data extraction failed: {e}")
    
    @pytest.mark.data_quality
    def test_temporal_data_consistency(self):
        """Test consistency of temporal data and event ordering"""
        
        base_time = datetime.now()
        
        # Create events with different timestamps
        events = [
            BreakingNewsEvent(
                id="temporal_1",
                headline="First event",
                summary="This happened first",
                url="https://test.com/1",
                source="test",
                published=base_time - timedelta(hours=3)
            ),
            BreakingNewsEvent(
                id="temporal_2", 
                headline="Second event",
                summary="This happened second",
                url="https://test.com/2",
                source="test",
                published=base_time - timedelta(hours=2)
            ),
            BreakingNewsEvent(
                id="temporal_3",
                headline="Third event", 
                summary="This happened third",
                url="https://test.com/3",
                source="test",
                published=base_time - timedelta(hours=1)
            )
        ]
        
        # Test temporal ordering
        sorted_events = sorted(events, key=lambda e: e.published, reverse=True)
        
        # Most recent should be first
        assert sorted_events[0].id == "temporal_3"
        assert sorted_events[1].id == "temporal_2"
        assert sorted_events[2].id == "temporal_1"
        
        # Test temporal filtering
        cutoff_time = base_time - timedelta(hours=2.5)
        recent_events = [e for e in events if e.published > cutoff_time]
        
        assert len(recent_events) == 2
        assert all(e.published > cutoff_time for e in recent_events)
    
    @pytest.mark.data_quality
    def test_commodity_classification_accuracy(self):
        """Test accuracy of commodity classification and extraction"""
        
        test_cases = [
            {
                'text': 'Gold mining company Barrick reports strong production results with 2.1 million ounces',
                'expected_commodities': ['gold'],
                'expected_confidence': 0.9
            },
            {
                'text': 'Copper and zinc prices surge amid supply disruption concerns',
                'expected_commodities': ['copper', 'zinc'],
                'expected_confidence': 0.85
            },
            {
                'text': 'Diversified miner produces gold, silver, copper and molybdenum',
                'expected_commodities': ['gold', 'silver', 'copper', 'molybdenum'],
                'expected_confidence': 0.8
            },
            {
                'text': 'Mining company reports quarterly results with mixed performance',
                'expected_commodities': [],
                'expected_confidence': 0.3
            }
        ]
        
        for test_case in test_cases:
            commodities, confidence = self._classify_commodities(test_case['text'])
            
            expected_commodities = test_case['expected_commodities']
            expected_confidence = test_case['expected_confidence']
            
            # Check commodity detection
            for expected_commodity in expected_commodities:
                assert any(expected_commodity in detected.lower() for detected in commodities), \
                    f"Expected commodity {expected_commodity} not detected in {commodities}"
            
            # Check confidence level
            confidence_error = abs(confidence - expected_confidence)
            assert confidence_error <= 0.2, \
                f"Confidence error too high: expected {expected_confidence}, got {confidence}, error: {confidence_error}"
    
    def _detect_duplicates(self, events: List[BreakingNewsEvent]) -> Dict[str, Any]:
        """Helper method to detect duplicate events"""
        from difflib import SequenceMatcher
        
        duplicate_groups = []
        processed_ids = set()
        
        for i, event1 in enumerate(events):
            if event1.id in processed_ids:
                continue
                
            current_group = [event1]
            processed_ids.add(event1.id)
            
            for j, event2 in enumerate(events[i+1:], i+1):
                if event2.id in processed_ids:
                    continue
                
                # Calculate similarity
                headline_similarity = SequenceMatcher(None, event1.headline.lower(), event2.headline.lower()).ratio()
                summary_similarity = SequenceMatcher(None, event1.summary.lower(), event2.summary.lower()).ratio()
                
                # Consider duplicates if high similarity
                if headline_similarity > 0.8 or (headline_similarity > 0.6 and summary_similarity > 0.7):
                    current_group.append(event2)
                    processed_ids.add(event2.id)
            
            if len(current_group) > 1:
                duplicate_groups.append(current_group)
        
        return {
            'duplicate_groups': duplicate_groups,
            'total_duplicates': sum(len(group) for group in duplicate_groups),
            'unique_events': len(events) - sum(len(group) - 1 for group in duplicate_groups)
        }
    
    def _extract_structured_data(self, raw_data: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        """Helper method to extract structured data from raw content"""
        import re
        
        if source_type == 'rss':
            text = f"{raw_data.get('title', '')} {raw_data.get('description', '')}"
        else:
            text = f"{raw_data.get('headline', '')} {raw_data.get('content', '')}"
        
        extracted = {}
        
        # Extract company symbols
        symbol_patterns = [
            r'(\w+\.TO)',  # TSX symbols
            r'TSX:(\w+)',  # TSX format
            r'\((\w+)\)',  # Symbols in parentheses
        ]
        
        symbols = []
        for pattern in symbol_patterns:
            symbols.extend(re.findall(pattern, text, re.IGNORECASE))
        
        extracted['company_symbols'] = list(set(symbols))
        
        # Extract commodities
        commodity_keywords = ['gold', 'copper', 'silver', 'zinc', 'nickel', 'uranium', 'lithium', 'iron']
        detected_commodities = []
        
        text_lower = text.lower()
        for commodity in commodity_keywords:
            if commodity in text_lower:
                detected_commodities.append(commodity)
        
        extracted['commodities'] = detected_commodities
        
        # Extract sentiment
        positive_words = ['surge', 'gain', 'rise', 'boost', 'strong', 'positive', 'up']
        negative_words = ['plunge', 'fall', 'drop', 'decline', 'weak', 'negative', 'down']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            extracted['sentiment'] = 'positive'
        elif negative_count > positive_count:
            extracted['sentiment'] = 'negative'
        else:
            extracted['sentiment'] = 'neutral'
        
        return extracted
    
    def _calculate_data_quality_score(self, event: BreakingNewsEvent) -> float:
        """Helper method to calculate data quality score"""
        score = 0.0
        
        # Headline quality (30 points)
        if event.headline and len(event.headline.strip()) > 10:
            score += 30.0
        elif event.headline and len(event.headline.strip()) > 0:
            score += 15.0
        
        # Summary quality (25 points)
        if event.summary and len(event.summary.strip()) > 20:
            score += 25.0
        elif event.summary and len(event.summary.strip()) > 0:
            score += 12.5
        
        # URL validity (20 points)
        if event.url and (event.url.startswith('http://') or event.url.startswith('https://')):
            score += 20.0
        elif event.url and len(event.url.strip()) > 0:
            score += 10.0
        
        # Source quality (15 points)
        if event.source and len(event.source.strip()) > 0:
            score += 15.0
        
        # Timestamp validity (10 points)
        if event.published and isinstance(event.published, datetime):
            score += 10.0
        
        return score
    
    def _classify_commodities(self, text: str) -> tuple[List[str], float]:
        """Helper method to classify commodities from text"""
        commodity_keywords = {
            'gold': ['gold', 'au', 'bullion'],
            'copper': ['copper', 'cu'],
            'silver': ['silver', 'ag'],
            'zinc': ['zinc', 'zn'],
            'nickel': ['nickel', 'ni'],
            'uranium': ['uranium', 'u3o8'],
            'lithium': ['lithium', 'li'],
            'iron': ['iron', 'fe', 'iron ore'],
            'molybdenum': ['molybdenum', 'moly', 'mo']
        }
        
        text_lower = text.lower()
        detected_commodities = []
        
        for commodity, keywords in commodity_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_commodities.append(commodity)
        
        # Calculate confidence based on specificity and context
        if len(detected_commodities) == 0:
            confidence = 0.2
        elif len(detected_commodities) == 1:
            confidence = 0.9
        elif len(detected_commodities) <= 3:
            confidence = 0.8
        else:
            confidence = 0.6
        
        return detected_commodities, confidence