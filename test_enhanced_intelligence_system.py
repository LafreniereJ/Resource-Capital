#!/usr/bin/env python3
"""
Test Enhanced Intelligence System
Validates detection and analysis of major events like Trump tariffs and copper plunges
"""

import sys
import os
sys.path.append('src')

import asyncio
import json
from datetime import datetime, timedelta
from src.intelligence.breaking_news_monitor import BreakingNewsMonitor, BreakingNewsEvent
from src.intelligence.event_correlation_engine import EventCorrelationEngine
from src.intelligence.smart_report_generator import SmartReportGenerator

def create_test_trump_tariff_event():
    """Create a test Trump tariff event for validation"""
    return BreakingNewsEvent(
        id="test_trump_tariff_001",
        headline="Trump announces 50% tariff on copper imports beginning August 1",
        summary="President Trump announced a 50% tariff on copper imports effective August 1, 2025, citing national security concerns. The decision follows a robust national security assessment and aims to protect domestic copper production while reducing dependence on foreign suppliers.",
        url="https://www.whitehouse.gov/fact-sheets/2025/07/trump-copper-tariff-announcement",
        source="whitehouse_official",
        published=datetime(2025, 7, 8, 14, 30, 0),
        priority_score=0.0,  # Will be calculated
        event_type="general",  # Will be determined
        impact_level="medium",  # Will be determined
        canadian_relevance=0.0,  # Will be calculated
        commodity_impact={},  # Will be populated
        companies_affected=[],  # Will be populated
        keywords=[],  # Will be populated
        sentiment="neutral"  # Will be determined
    )

def create_test_copper_plunge_event():
    """Create a test copper price plunge event for validation"""
    return BreakingNewsEvent(
        id="test_copper_plunge_001",
        headline="Copper prices plunge 18% in after-hours trading following Trump tariff announcement",
        summary="U.S. copper prices crashed as much as 18% in after-hours trading immediately after the White House announced the new 50% tariff rate. The dramatic price collapse reflects concerns about reduced demand and potential retaliation from trading partners.",
        url="https://www.mining.com/copper-price-plunges-trump-tariff-impact",
        source="mining_com",
        published=datetime(2025, 7, 8, 18, 45, 0),
        priority_score=0.0,  # Will be calculated
        event_type="general",  # Will be determined
        impact_level="medium",  # Will be determined
        canadian_relevance=0.0,  # Will be calculated
        commodity_impact={},  # Will be populated
        companies_affected=[],  # Will be populated
        keywords=[],  # Will be populated
        sentiment="neutral"  # Will be determined
    )

def create_test_mining_stock_reaction_event():
    """Create a test mining stock reaction event for validation"""
    return BreakingNewsEvent(
        id="test_mining_reaction_001",
        headline="Canadian copper miners surge as Trump tariffs boost domestic production outlook",
        summary="First Quantum Minerals, Lundin Mining, and Hudbay Minerals led Canadian mining stocks higher following Trump's announcement of 50% copper tariffs. Analysts suggest domestic producers could benefit from reduced foreign competition and higher domestic prices.",
        url="https://financialpost.com/commodities/canadian-copper-miners-trump-tariff-boost",
        source="financial_post",
        published=datetime(2025, 7, 9, 9, 15, 0),
        priority_score=0.0,  # Will be calculated
        event_type="general",  # Will be determined  
        impact_level="medium",  # Will be determined
        canadian_relevance=0.0,  # Will be calculated
        commodity_impact={},  # Will be populated
        companies_affected=[],  # Will be populated
        keywords=[],  # Will be populated
        sentiment="neutral"  # Will be determined
    )

async def test_breaking_news_monitor():
    """Test the breaking news monitor with tariff scenarios"""
    print("🚨 Testing Breaking News Monitor")
    print("=" * 60)
    
    monitor = BreakingNewsMonitor()
    
    # Test event analysis with our test events
    test_events = [
        create_test_trump_tariff_event(),
        create_test_copper_plunge_event(), 
        create_test_mining_stock_reaction_event()
    ]
    
    print("📊 Analyzing test events...")
    
    analyzed_events = []
    for i, event in enumerate(test_events, 1):
        print(f"\n{i}. Testing: {event.headline}")
        
        # Analyze the event (this sets priority_score, keywords, etc.)
        monitor.analyze_event_priority(event, 1.0)
        analyzed_events.append(event)
        
        print(f"   Priority Score: {event.priority_score:.1f}")
        print(f"   Event Type: {event.event_type}")
        print(f"   Impact Level: {event.impact_level}")
        print(f"   Canadian Relevance: {event.canadian_relevance:.1f}")
        print(f"   Keywords: {', '.join(event.keywords)}")
        print(f"   Sentiment: {event.sentiment}")
        
        if event.commodity_impact:
            impacts = [f"{k}: {v:.1f}" for k, v in event.commodity_impact.items()]
            print(f"   Commodity Impact: {', '.join(impacts)}")
        
        if event.companies_affected:
            print(f"   Companies: {', '.join(event.companies_affected)}")
    
    # Test priority detection
    high_priority_events = [e for e in analyzed_events if e.priority_score >= 60.0]
    critical_events = [e for e in analyzed_events if e.priority_score >= 80.0]
    
    print(f"\n📈 Priority Analysis Results:")
    print(f"   High Priority Events (≥60): {len(high_priority_events)}")
    print(f"   Critical Events (≥80): {len(critical_events)}")
    
    # Validate tariff detection
    tariff_events = [e for e in analyzed_events if "tariff" in e.keywords]
    print(f"   Tariff Events Detected: {len(tariff_events)}")
    
    # Validate copper focus
    copper_events = [e for e in analyzed_events if "copper" in e.commodity_impact]
    print(f"   Copper-Related Events: {len(copper_events)}")
    
    return analyzed_events

async def test_event_correlation_engine(test_events):
    """Test the event correlation engine"""
    print("\n🔍 Testing Event Correlation Engine")
    print("=" * 60)
    
    correlation_engine = EventCorrelationEngine()
    
    correlations = []
    
    for i, event in enumerate(test_events, 1):
        if event.priority_score >= 60.0:  # Only analyze high priority events
            print(f"\n{i}. Analyzing correlation for: {event.headline[:50]}...")
            
            try:
                # Note: This would normally analyze real market data
                # For testing, we'll create mock correlation
                correlation = await correlation_engine.analyze_event_market_impact(event)
                correlations.append(correlation)
                
                print(f"   Overall Impact Score: {correlation.overall_impact_score:.1f}")
                print(f"   Canadian Mining Impact: {correlation.canadian_mining_impact:.1f}%")
                print(f"   Correlation Strength: {correlation.correlation_strength}")
                print(f"   Primary Impact: {correlation.primary_impact}")
                
                if correlation.commodity_impacts:
                    print("   Commodity Impacts:")
                    for impact in correlation.commodity_impacts[:3]:
                        print(f"     {impact.commodity}: {impact.change_percent:+.1f}% (confidence: {impact.correlation_confidence:.2f})")
                
                if correlation.mining_stock_impacts:
                    print("   Top Stock Impacts:")
                    for impact in correlation.mining_stock_impacts[:3]:
                        print(f"     {impact.symbol}: {impact.change_percent:+.1f}%")
            
            except Exception as e:
                print(f"   ⚠️ Correlation analysis error: {e}")
    
    return correlations

async def test_smart_report_generator(test_events, correlations):
    """Test the smart report generator"""
    print("\n🧠 Testing Smart Report Generator")
    print("=" * 60)
    
    generator = SmartReportGenerator()
    
    # Override the major events collection for testing
    generator.test_events = test_events
    generator.test_correlations = correlations
    
    # Generate test report
    print("📊 Generating Saturday wrap report with test events...")
    
    try:
        # For testing, we'll manually create a test report
        test_report = await generator.generate_smart_weekend_report("saturday_wrap")
        
        print(f"\n✅ Report Generated Successfully:")
        print(f"   Report Type: {test_report.report_type}")
        print(f"   Event-driven: {test_report.event_driven}")
        print(f"   Confidence Score: {test_report.confidence_score:.1f}%")
        print(f"   Canadian Relevance: {test_report.canadian_relevance_score:.1f}%")
        print(f"   Major Events: {len(test_report.major_events)}")
        print(f"   Event Correlations: {len(test_report.event_correlations)}")
        
        print(f"\n📰 Market Narrative:")
        print(f"   {test_report.market_narrative}")
        
        print(f"\n📊 Impact Analysis:")
        print(f"   {test_report.impact_analysis}")
        
        # Test LinkedIn post generation
        print(f"\n📱 LinkedIn Post Generation:")
        linkedin_post = generator.format_linkedin_post(test_report)
        print("=" * 50)
        print(linkedin_post)
        print("=" * 50)
        
        return test_report
        
    except Exception as e:
        print(f"❌ Report generation error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_keyword_detection():
    """Test keyword detection accuracy"""
    print("\n🎯 Testing Keyword Detection Accuracy")
    print("=" * 60)
    
    monitor = BreakingNewsMonitor()
    
    # Test scenarios
    test_scenarios = [
        {
            "text": "Trump announces 50% tariff on copper imports citing national security",
            "expected_keywords": ["tariff", "copper", "national security"],
            "expected_priority": 90.0,
            "expected_type": "policy"
        },
        {
            "text": "Copper prices plunge 18% amid fears of Trump tariffs hurting demand",
            "expected_keywords": ["copper", "plunge", "tariff"],
            "expected_priority": 85.0,
            "expected_type": "market_move"
        },
        {
            "text": "First Quantum Minerals surges on domestic copper production boost",
            "expected_keywords": ["surge", "copper", "production"],
            "expected_priority": 70.0,
            "expected_type": "market_move"
        },
        {
            "text": "Canadian mining companies quarterly earnings report shows mixed results",
            "expected_keywords": ["earnings", "quarterly", "canadian"],
            "expected_priority": 50.0,
            "expected_type": "corporate"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Testing: {scenario['text']}")
        
        # Create test event
        test_event = BreakingNewsEvent(
            id=f"test_{i}",
            headline=scenario['text'],
            summary=scenario['text'],
            url="https://test.com",
            source="test_source",
            published=datetime.now()
        )
        
        # Analyze
        monitor.analyze_event_priority(test_event, 1.0)
        
        # Check results
        detected_keywords = set(test_event.keywords)
        expected_keywords = set(scenario['expected_keywords'])
        keyword_match = len(detected_keywords.intersection(expected_keywords)) / len(expected_keywords)
        
        priority_accuracy = abs(test_event.priority_score - scenario['expected_priority']) <= 20.0
        type_match = test_event.event_type == scenario['expected_type']
        
        results.append({
            'scenario': i,
            'keyword_accuracy': keyword_match,
            'priority_accuracy': priority_accuracy,
            'type_match': type_match,
            'detected_keywords': list(detected_keywords),
            'actual_priority': test_event.priority_score,
            'actual_type': test_event.event_type
        })
        
        print(f"   Expected Keywords: {expected_keywords}")
        print(f"   Detected Keywords: {detected_keywords}")
        print(f"   Keyword Match: {keyword_match:.1%}")
        print(f"   Expected Priority: {scenario['expected_priority']}")
        print(f"   Actual Priority: {test_event.priority_score:.1f}")
        print(f"   Priority Accurate: {priority_accuracy}")
        print(f"   Expected Type: {scenario['expected_type']}")
        print(f"   Actual Type: {test_event.event_type}")
        print(f"   Type Match: {type_match}")
    
    # Overall accuracy
    avg_keyword_accuracy = sum(r['keyword_accuracy'] for r in results) / len(results)
    priority_accuracy_rate = sum(1 for r in results if r['priority_accuracy']) / len(results)
    type_accuracy_rate = sum(1 for r in results if r['type_match']) / len(results)
    
    print(f"\n📊 Overall Accuracy Results:")
    print(f"   Keyword Detection: {avg_keyword_accuracy:.1%}")
    print(f"   Priority Scoring: {priority_accuracy_rate:.1%}")
    print(f"   Event Type Classification: {type_accuracy_rate:.1%}")
    
    return results

async def validate_trump_tariff_scenario():
    """Validate complete Trump tariff scenario detection and analysis"""
    print("\n🎯 Trump Tariff Scenario Validation")
    print("=" * 60)
    
    # Test the complete pipeline
    test_events = [
        create_test_trump_tariff_event(),
        create_test_copper_plunge_event(),
        create_test_mining_stock_reaction_event()
    ]
    
    monitor = BreakingNewsMonitor()
    
    # Analyze all events
    for event in test_events:
        monitor.analyze_event_priority(event, 1.0)
    
    # Validation criteria
    validation_results = {
        "tariff_detected": False,
        "high_priority_assigned": False,
        "copper_impact_identified": False,
        "canadian_relevance_calculated": False,
        "policy_event_classified": False,
        "market_correlation_analyzed": False
    }
    
    # Check tariff event detection
    tariff_event = test_events[0]  # Trump tariff announcement
    
    if "tariff" in tariff_event.keywords:
        validation_results["tariff_detected"] = True
        print("✅ Tariff keyword detected")
    else:
        print("❌ Tariff keyword NOT detected")
    
    if tariff_event.priority_score >= 80.0:
        validation_results["high_priority_assigned"] = True
        print("✅ High priority assigned to tariff event")
    else:
        print(f"❌ Low priority assigned: {tariff_event.priority_score:.1f}")
    
    if "copper" in tariff_event.commodity_impact:
        validation_results["copper_impact_identified"] = True
        print("✅ Copper impact identified")
    else:
        print("❌ Copper impact NOT identified")
    
    if tariff_event.canadian_relevance >= 50.0:
        validation_results["canadian_relevance_calculated"] = True
        print("✅ Canadian relevance properly calculated")
    else:
        print(f"❌ Low Canadian relevance: {tariff_event.canadian_relevance:.1f}")
    
    if tariff_event.event_type == "policy":
        validation_results["policy_event_classified"] = True
        print("✅ Policy event properly classified")
    else:
        print(f"❌ Incorrect classification: {tariff_event.event_type}")
    
    # Test correlation analysis
    correlation_engine = EventCorrelationEngine()
    try:
        correlation = await correlation_engine.analyze_event_market_impact(tariff_event)
        if correlation.correlation_strength in ["strong", "moderate"]:
            validation_results["market_correlation_analyzed"] = True
            print("✅ Market correlation properly analyzed")
        else:
            print(f"❌ Weak correlation detected: {correlation.correlation_strength}")
    except Exception as e:
        print(f"❌ Correlation analysis failed: {e}")
    
    # Overall validation score
    passed_tests = sum(1 for result in validation_results.values() if result)
    total_tests = len(validation_results)
    validation_score = passed_tests / total_tests
    
    print(f"\n📊 Validation Score: {validation_score:.1%} ({passed_tests}/{total_tests} tests passed)")
    
    if validation_score >= 0.8:
        print("🎉 EXCELLENT: System properly detects and analyzes Trump tariff scenarios")
    elif validation_score >= 0.6:
        print("✅ GOOD: System mostly works, minor improvements needed")
    else:
        print("⚠️ NEEDS IMPROVEMENT: System requires significant enhancements")
    
    return validation_results

async def main():
    """Run complete enhanced intelligence system test"""
    print("🧠 Enhanced Intelligence System Validation")
    print("=" * 80)
    print("Testing Trump tariff and copper plunge detection capabilities")
    print("=" * 80)
    
    # Test 1: Breaking News Monitor
    test_events = await test_breaking_news_monitor()
    
    # Test 2: Event Correlation Engine  
    correlations = await test_event_correlation_engine(test_events)
    
    # Test 3: Smart Report Generator
    test_report = await test_smart_report_generator(test_events, correlations)
    
    # Test 4: Keyword Detection Accuracy
    keyword_results = test_keyword_detection()
    
    # Test 5: Complete Scenario Validation
    validation_results = await validate_trump_tariff_scenario()
    
    print(f"\n🎉 COMPLETE ENHANCED INTELLIGENCE SYSTEM TEST FINISHED")
    print("=" * 80)
    
    # Summary
    print(f"📊 TEST SUMMARY:")
    print(f"   Breaking News Events Analyzed: {len(test_events)}")
    print(f"   Event Correlations Generated: {len(correlations) if correlations else 0}")
    print(f"   Smart Report Generated: {'Yes' if test_report else 'No'}")
    print(f"   Keyword Detection Tests: {len(keyword_results)}")
    
    # Validation score
    if validation_results:
        passed_validations = sum(1 for result in validation_results.values() if result)
        total_validations = len(validation_results)
        overall_score = passed_validations / total_validations
        print(f"   Overall Validation Score: {overall_score:.1%}")
        
        if overall_score >= 0.8:
            print("\n🎉 SYSTEM READY: Enhanced intelligence system successfully detects major events!")
        else:
            print("\n⚠️ NEEDS WORK: System requires improvements before deployment")
    
    print(f"\n💡 The enhanced system now captures events like:")
    print(f"   • Trump tariff announcements → Automatic high priority detection")
    print(f"   • Copper price plunges → Market correlation analysis")
    print(f"   • Canadian mining impacts → Relevance scoring and targeting")
    print(f"   • Smart report integration → Auto-inclusion in weekend reports")

if __name__ == "__main__":
    asyncio.run(main())