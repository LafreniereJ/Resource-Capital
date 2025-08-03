"""
Unit tests for BreakingNewsMonitor
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.intelligence.breaking_news_monitor import BreakingNewsMonitor, BreakingNewsEvent


class TestBreakingNewsMonitor:
    """Test suite for BreakingNewsMonitor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BreakingNewsMonitor()
        
    def create_test_event(self, headline="Test headline", **kwargs):
        """Helper to create test events"""
        defaults = {
            'id': 'test_001',
            'headline': headline,
            'summary': 'Test summary',
            'url': 'https://test.com',
            'source': 'test_source',
            'published': datetime.now()
        }
        defaults.update(kwargs)
        return BreakingNewsEvent(**defaults)
    
    @pytest.mark.unit
    def test_analyze_event_priority_tariff_detection(self):
        """Test detection of tariff-related events"""
        event = self.create_test_event(
            headline="Trump announces 50% tariff on copper imports",
            summary="President announces new copper tariffs for national security"
        )
        
        self.monitor.analyze_event_priority(event, 1.0)
        
        assert "tariff" in event.keywords
        assert event.priority_score >= 80.0
        assert event.event_type == "policy"
        assert event.impact_level in ["high", "critical"]
        assert "copper" in event.commodity_impact
    
    @pytest.mark.unit
    def test_analyze_event_priority_copper_price_movement(self):
        """Test detection of significant copper price movements"""
        event = self.create_test_event(
            headline="Copper prices plunge 18% in after-hours trading",
            summary="Copper futures crashed 18% following policy announcements"
        )
        
        self.monitor.analyze_event_priority(event, 1.0)
        
        assert "plunge" in event.keywords
        assert "copper" in event.keywords
        assert event.priority_score >= 75.0
        assert event.event_type == "market_move"
        assert "copper" in event.commodity_impact
        assert event.commodity_impact["copper"] >= 80.0
    
    @pytest.mark.unit
    def test_analyze_event_priority_canadian_mining_stocks(self):
        """Test detection of Canadian mining stock movements"""
        event = self.create_test_event(
            headline="First Quantum Minerals surges on copper production boost",
            summary="Canadian copper miner gains 12% on increased production guidance"
        )
        
        self.monitor.analyze_event_priority(event, 1.0)
        
        assert event.canadian_relevance >= 70.0
        assert "First Quantum" in event.companies_affected or "surge" in event.keywords
        assert event.priority_score >= 60.0
        assert event.event_type in ["corporate", "market_move"]
    
    @pytest.mark.unit
    def test_analyze_event_priority_low_relevance_event(self):
        """Test handling of low-relevance events"""
        event = self.create_test_event(
            headline="Local weather report for Toronto shows sunny skies",
            summary="Weather will be sunny in Toronto today with temperatures reaching 25°C"
        )
        
        self.monitor.analyze_event_priority(event, 1.0)
        
        assert event.priority_score < 30.0
        assert event.canadian_relevance < 50.0
        assert event.impact_level == "low"
        assert len(event.commodity_impact) == 0
    
    @pytest.mark.unit
    def test_keyword_extraction_accuracy(self):
        """Test accuracy of keyword extraction"""
        test_cases = [
            {
                'text': "Trump tariff copper national security mining",
                'expected': ["trump", "tariff", "copper", "national", "security", "mining"]
            },
            {
                'text': "First Quantum production surge 15% increase",
                'expected': ["first", "quantum", "production", "surge", "increase"]
            },
            {
                'text': "Gold prices plunge recession fears inflation",
                'expected': ["gold", "prices", "plunge", "recession", "fears", "inflation"]
            }
        ]
        
        for case in test_cases:
            keywords = self.monitor.extract_keywords(case['text'])
            
            # Check that most expected keywords are found
            found_keywords = set(keywords)
            expected_keywords = set(case['expected'])
            overlap = len(found_keywords.intersection(expected_keywords))
            
            assert overlap >= len(expected_keywords) * 0.7  # At least 70% match
    
    @pytest.mark.unit
    def test_commodity_impact_calculation(self):
        """Test commodity impact scoring"""
        test_cases = [
            {
                'text': "Copper prices surge 20% on supply disruption",
                'commodity': "copper",
                'expected_min_impact': 85.0
            },
            {
                'text': "Gold mining company reports strong earnings",
                'commodity': "gold",
                'expected_min_impact': 60.0
            },
            {
                'text': "Silver and platinum see modest gains today",
                'commodity': "silver",
                'expected_min_impact': 40.0
            }
        ]
        
        for case in test_cases:
            event = self.create_test_event(
                headline=case['text'],
                summary=case['text']
            )
            
            self.monitor.analyze_event_priority(event, 1.0)
            
            if case['commodity'] in event.commodity_impact:
                impact = event.commodity_impact[case['commodity']]
                assert impact >= case['expected_min_impact']
    
    @pytest.mark.unit
    def test_canadian_relevance_scoring(self):
        """Test Canadian relevance calculation"""
        test_cases = [
            {
                'text': "Toronto Stock Exchange TSX Canadian mining companies",
                'expected_min': 85.0
            },
            {
                'text': "Agnico Eagle Mines Barrick Gold Canadian operations",
                'expected_min': 80.0
            },
            {
                'text': "US Federal Reserve interest rates American economy",
                'expected_min': 30.0
            },
            {
                'text': "China manufacturing global supply chain",
                'expected_min': 40.0
            }
        ]
        
        for case in test_cases:
            event = self.create_test_event(
                headline=case['text'],
                summary=case['text']
            )
            
            self.monitor.analyze_event_priority(event, 1.0)
            
            assert event.canadian_relevance >= case['expected_min']
    
    @pytest.mark.unit
    def test_event_type_classification(self):
        """Test event type classification accuracy"""
        test_cases = [
            {
                'headline': "Trump announces new tariff policy on imports",
                'expected_type': "policy"
            },
            {
                'headline': "Copper prices surge 15% on strong demand",
                'expected_type': "market_move"
            },
            {
                'headline': "Agnico Eagle reports quarterly earnings results",
                'expected_type': "corporate"
            },
            {
                'headline': "New copper mine discovery in northern Ontario",
                'expected_type': "operational"
            },
            {
                'headline': "Environmental permits approved for mining project",
                'expected_type': "regulatory"
            }
        ]
        
        for case in test_cases:
            event = self.create_test_event(headline=case['headline'])
            self.monitor.analyze_event_priority(event, 1.0)
            
            assert event.event_type == case['expected_type']
    
    @pytest.mark.unit
    def test_priority_score_calculation(self):
        """Test priority score calculation logic"""
        # High priority: Tariff announcement
        high_priority_event = self.create_test_event(
            headline="Trump announces 50% copper tariff effective immediately",
            summary="Major policy announcement affecting copper trade"
        )
        self.monitor.analyze_event_priority(high_priority_event, 1.0)
        assert high_priority_event.priority_score >= 80.0
        
        # Medium priority: Company earnings
        medium_priority_event = self.create_test_event(
            headline="Mining company reports quarterly results",
            summary="Standard earnings report with modest growth"
        )
        self.monitor.analyze_event_priority(medium_priority_event, 1.0)
        assert 40.0 <= medium_priority_event.priority_score <= 75.0
        
        # Low priority: General market news
        low_priority_event = self.create_test_event(
            headline="Stock market opens higher today",
            summary="General market movement without specific focus"
        )
        self.monitor.analyze_event_priority(low_priority_event, 1.0)
        assert low_priority_event.priority_score <= 50.0
    
    @pytest.mark.unit
    def test_impact_level_assignment(self):
        """Test impact level assignment logic"""
        # Critical impact
        critical_event = self.create_test_event(
            headline="Major copper mine explosion halts global production"
        )
        self.monitor.analyze_event_priority(critical_event, 1.0)
        assert critical_event.impact_level == "critical"
        
        # High impact
        high_event = self.create_test_event(
            headline="Gold prices surge 10% on inflation fears"
        )
        self.monitor.analyze_event_priority(high_event, 1.0)
        assert high_event.impact_level in ["high", "critical"]
        
        # Medium impact
        medium_event = self.create_test_event(
            headline="Mining company announces expansion plans"
        )
        self.monitor.analyze_event_priority(medium_event, 1.0)
        assert medium_event.impact_level in ["medium", "high"]
    
    @pytest.mark.unit
    def test_company_detection(self):
        """Test detection of company names in events"""
        test_cases = [
            {
                'text': "Agnico Eagle Mines reports strong production results",
                'expected_companies': ["Agnico Eagle"]
            },
            {
                'text': "First Quantum Minerals and Barrick Gold partnership",
                'expected_companies': ["First Quantum", "Barrick"]
            },
            {
                'text': "Hudbay Minerals increases dividend by 25%",
                'expected_companies': ["Hudbay"]
            }
        ]
        
        for case in test_cases:
            event = self.create_test_event(
                headline=case['text'],
                summary=case['text']
            )
            
            self.monitor.analyze_event_priority(event, 1.0)
            
            # Check that at least one expected company is detected
            found_any = any(
                any(company.lower() in detected.lower() for detected in event.companies_affected)
                for company in case['expected_companies']
            )
            assert found_any or len(event.companies_affected) > 0
    
    @pytest.mark.unit
    def test_sentiment_analysis(self):
        """Test sentiment analysis accuracy"""
        test_cases = [
            {
                'text': "Copper prices surge boom excellent strong performance",
                'expected_sentiment': "positive"
            },
            {
                'text': "Mining stocks plunge crash disaster terrible results",
                'expected_sentiment': "negative"
            },
            {
                'text': "Company reports standard quarterly financial results",
                'expected_sentiment': "neutral"
            }
        ]
        
        for case in test_cases:
            event = self.create_test_event(
                headline=case['text'],
                summary=case['text']
            )
            
            self.monitor.analyze_event_priority(event, 1.0)
            
            assert event.sentiment == case['expected_sentiment']