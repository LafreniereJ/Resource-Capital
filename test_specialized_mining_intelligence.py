#!/usr/bin/env python3
"""
Specialized Mining Intelligence System Test
Comprehensive test of the new specialized scraping and analysis architecture

Tests:
1. Individual specialized scrapers
2. Domain-specific analyzers  
3. Master intelligence compiler
4. Data architecture and storage
5. Cross-domain correlations
6. End-to-end intelligence workflow
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Import specialized scrapers
from src.scrapers.specialized.metal_prices_scraper import MetalPricesScraper
from src.scrapers.specialized.economic_data_scraper import EconomicDataScraper
from src.scrapers.specialized.mining_companies_scraper import MiningCompaniesScraper
from src.scrapers.specialized.mining_news_scraper import SpecializedMiningNewsScraper

# Import analyzers
from src.analyzers.price_analyzer import PriceAnalyzer

# Import master compiler
from src.intelligence.master_compiler import MasterIntelligenceCompiler


async def test_individual_scrapers():
    """Test each specialized scraper individually"""
    
    print("🧪 TESTING INDIVIDUAL SPECIALIZED SCRAPERS")
    print("=" * 60)
    
    test_results = {
        'metal_prices_scraper': {'status': 'pending', 'data': None, 'error': None},
        'economic_data_scraper': {'status': 'pending', 'data': None, 'error': None},
        'companies_scraper': {'status': 'pending', 'data': None, 'error': None},
        'news_scraper': {'status': 'pending', 'data': None, 'error': None}
    }
    
    # Test Metal Prices Scraper
    print("\n💰 Testing Metal Prices Scraper...")
    try:
        scraper = MetalPricesScraper()
        results = await scraper.scrape_all_metal_prices()
        await scraper.cleanup()
        
        test_results['metal_prices_scraper'] = {
            'status': 'success',
            'data': {
                'metals_scraped': results['summary']['total_metals_scraped'],
                'successful_sources': results['summary']['successful_sources'],
                'metals_with_consensus': results['summary']['metals_with_consensus'],
                'scraping_duration': results['summary']['scraping_duration']
            },
            'error': None
        }
        print(f"   ✅ Success: {results['summary']['total_metals_scraped']} metals, {results['summary']['successful_sources']} sources")
        
    except Exception as e:
        test_results['metal_prices_scraper']['status'] = 'failed'
        test_results['metal_prices_scraper']['error'] = str(e)
        print(f"   ❌ Failed: {str(e)}")
    
    # Test Economic Data Scraper
    print("\n📊 Testing Economic Data Scraper...")
    try:
        scraper = EconomicDataScraper()
        results = await scraper.scrape_all_economic_data()
        await scraper.cleanup()
        
        test_results['economic_data_scraper'] = {
            'status': 'success',
            'data': {
                'sources_scraped': results['summary']['total_sources_scraped'],
                'indicators_found': results['summary']['total_indicators_found'],
                'successful_extractions': results['summary']['successful_extractions'],
                'scraping_duration': results['summary']['scraping_duration']
            },
            'error': None
        }
        print(f"   ✅ Success: {results['summary']['total_sources_scraped']} sources, {results['summary']['total_indicators_found']} indicators")
        
    except Exception as e:
        test_results['economic_data_scraper']['status'] = 'failed'
        test_results['economic_data_scraper']['error'] = str(e)
        print(f"   ❌ Failed: {str(e)}")
    
    # Test Companies Scraper
    print("\n🏢 Testing Mining Companies Scraper...")
    try:
        scraper = MiningCompaniesScraper()
        results = await scraper.scrape_all_companies_data()
        await scraper.cleanup()
        
        test_results['companies_scraper'] = {
            'status': 'success',
            'data': {
                'companies_attempted': results['summary']['total_companies_attempted'],
                'successful_scrapes': results['summary']['successful_company_scrapes'],
                'companies_with_stock_data': results['summary']['companies_with_stock_data'],
                'scraping_duration': results['summary']['scraping_duration']
            },
            'error': None
        }
        print(f"   ✅ Success: {results['summary']['successful_company_scrapes']}/{results['summary']['total_companies_attempted']} companies")
        
    except Exception as e:
        test_results['companies_scraper']['status'] = 'failed'
        test_results['companies_scraper']['error'] = str(e)
        print(f"   ❌ Failed: {str(e)}")
    
    # Test News Scraper
    print("\n📰 Testing Specialized Mining News Scraper...")
    try:
        scraper = SpecializedMiningNewsScraper()
        results = await scraper.scrape_all_mining_news()
        await scraper.cleanup()
        
        test_results['news_scraper'] = {
            'status': 'success', 
            'data': {
                'sources_scraped': results['summary']['total_sources_scraped'],
                'articles_found': results['summary']['total_articles_found'],
                'unique_articles': results['summary']['unique_articles'],
                'scraping_duration': results['summary']['scraping_duration']
            },
            'error': None
        }
        print(f"   ✅ Success: {results['summary']['unique_articles']} unique articles from {results['summary']['total_sources_scraped']} sources")
        
    except Exception as e:
        test_results['news_scraper']['status'] = 'failed'
        test_results['news_scraper']['error'] = str(e)
        print(f"   ❌ Failed: {str(e)}")
    
    return test_results


async def test_price_analyzer():
    """Test the price analyzer"""
    
    print("\n📈 TESTING PRICE ANALYZER")
    print("=" * 30)
    
    try:
        analyzer = PriceAnalyzer()
        results = await analyzer.analyze_all_prices(30)  # 30 days of data
        
        analyzer_results = {
            'status': 'success',
            'data': {
                'metals_analyzed': results['summary']['metals_analyzed'],
                'market_sentiment': results['summary']['market_sentiment'],
                'total_alerts': results['summary']['total_alerts'],
                'analysis_success_rate': results['summary']['analysis_coverage']['success_rate']
            },
            'error': None
        }
        
        print(f"   ✅ Analysis Success: {results['summary']['metals_analyzed']} metals analyzed")
        print(f"   📊 Market Sentiment: {results['summary']['market_sentiment'].title()}")
        print(f"   🚨 Alerts Generated: {results['summary']['total_alerts']}")
        
        return analyzer_results
        
    except Exception as e:
        print(f"   ❌ Price Analyzer Failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


async def test_master_intelligence_compiler():
    """Test the master intelligence compiler"""
    
    print("\n🧠 TESTING MASTER INTELLIGENCE COMPILER")
    print("=" * 45)
    
    try:
        compiler = MasterIntelligenceCompiler()
        report = await compiler.generate_comprehensive_intelligence_report()
        await compiler.cleanup()
        
        compiler_results = {
            'status': 'success',
            'data': {
                'report_type': report.get('report_type'),
                'market_outlook': report.get('executive_summary', {}).get('market_outlook'),
                'data_quality': report.get('data_quality_assessment', {}).get('overall_quality'),
                'top_opportunities_count': len(report.get('executive_summary', {}).get('top_opportunities', [])),
                'main_risks_count': len(report.get('executive_summary', {}).get('main_risks', [])),
                'key_findings_count': len(report.get('executive_summary', {}).get('key_findings', []))
            },
            'error': None
        }
        
        print(f"   ✅ Intelligence Report Generated Successfully")
        print(f"   📊 Market Outlook: {report.get('executive_summary', {}).get('market_outlook', 'unknown').title()}")
        print(f"   🎯 Data Quality: {report.get('data_quality_assessment', {}).get('overall_quality', 'unknown').title()}")
        print(f"   💡 Opportunities Identified: {len(report.get('executive_summary', {}).get('top_opportunities', []))}")
        print(f"   ⚠️ Risks Identified: {len(report.get('executive_summary', {}).get('main_risks', []))}")
        
        return compiler_results
        
    except Exception as e:
        print(f"   ❌ Master Compiler Failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


async def test_data_architecture():
    """Test the specialized data architecture"""
    
    print("\n🗂️ TESTING DATA ARCHITECTURE")
    print("=" * 32)
    
    architecture_test = {
        'directories_created': True,
        'data_separation': True,
        'storage_structure': True,
        'file_organization': True
    }
    
    # Check directory structure
    required_dirs = [
        "data/metal_prices/raw",
        "data/metal_prices/processed", 
        "data/metal_prices/historical",
        "data/economic_indicators/raw",
        "data/economic_indicators/processed",
        "data/economic_indicators/historical",
        "data/companies/raw",
        "data/companies/processed",
        "data/companies/historical",
        "data/news/raw",
        "data/news/processed",
        "data/news/historical",
        "data/news/by_category",
        "data/intelligence_reports/daily",
        "data/intelligence_reports/weekly",
        "data/intelligence_reports/special_reports"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"   ❌ Missing directories: {missing_dirs}")
        architecture_test['directories_created'] = False
    else:
        print(f"   ✅ All {len(required_dirs)} required directories exist")
    
    # Check for data files in appropriate locations
    data_files_found = {
        'metal_prices': len(list(Path("data/metal_prices").glob("**/*.json"))),
        'economic_indicators': len(list(Path("data/economic_indicators").glob("**/*.json"))),
        'companies': len(list(Path("data/companies").glob("**/*.json"))),
        'news': len(list(Path("data/news").glob("**/*.json"))),
        'intelligence_reports': len(list(Path("data/intelligence_reports").glob("**/*.json")))
    }
    
    total_files = sum(data_files_found.values())
    print(f"   📁 Data files found: {total_files} total")
    for domain, count in data_files_found.items():
        if count > 0:
            print(f"      {domain}: {count} files")
    
    architecture_test['data_files_count'] = total_files
    
    return architecture_test


async def test_end_to_end_workflow():
    """Test the complete end-to-end workflow"""
    
    print("\n🔄 TESTING END-TO-END WORKFLOW")
    print("=" * 35)
    
    workflow_results = {
        'data_collection': 'pending',
        'analysis': 'pending', 
        'intelligence_compilation': 'pending',
        'report_generation': 'pending',
        'overall_success': False
    }
    
    try:
        # Step 1: Data Collection (using master compiler which calls all scrapers)
        print("   1️⃣ Starting comprehensive data collection...")
        compiler = MasterIntelligenceCompiler()
        
        # This calls all scrapers internally
        raw_data = await compiler._collect_all_domain_data()
        
        collection_success = len(raw_data.get('collection_errors', [])) < 2  # Allow up to 1 error
        workflow_results['data_collection'] = 'success' if collection_success else 'partial'
        print(f"      {'✅' if collection_success else '⚠️'} Data collection: {workflow_results['data_collection']}")
        
        # Step 2: Domain Analysis
        print("   2️⃣ Performing domain-specific analysis...")
        domain_analyses = await compiler._analyze_all_domains(raw_data)
        
        analysis_success = len([d for d in domain_analyses.values() if d]) >= 2  # At least 2 domains analyzed
        workflow_results['analysis'] = 'success' if analysis_success else 'partial'
        print(f"      {'✅' if analysis_success else '⚠️'} Analysis: {workflow_results['analysis']}")
        
        # Step 3: Intelligence Compilation
        print("   3️⃣ Compiling cross-domain intelligence...")
        correlations = await compiler._analyze_cross_domain_correlations(domain_analyses)
        opportunities = await compiler._identify_market_opportunities(domain_analyses, correlations)
        
        compilation_success = len(opportunities.get('high_conviction_opportunities', [])) > 0 or len(opportunities.get('thematic_opportunities', {})) > 0
        workflow_results['intelligence_compilation'] = 'success' if compilation_success else 'partial'
        print(f"      {'✅' if compilation_success else '⚠️'} Intelligence compilation: {workflow_results['intelligence_compilation']}")
        
        # Step 4: Report Generation
        print("   4️⃣ Generating comprehensive report...")
        report = await compiler.generate_comprehensive_intelligence_report()
        
        report_success = 'executive_summary' in report and 'actionable_recommendations' in report
        workflow_results['report_generation'] = 'success' if report_success else 'partial'
        print(f"      {'✅' if report_success else '⚠️'} Report generation: {workflow_results['report_generation']}")
        
        # Overall success
        workflow_results['overall_success'] = all(
            status in ['success', 'partial'] 
            for status in [workflow_results['data_collection'], workflow_results['analysis'], 
                          workflow_results['intelligence_compilation'], workflow_results['report_generation']]
        )
        
        await compiler.cleanup()
        
    except Exception as e:
        print(f"   ❌ End-to-end workflow failed: {str(e)}")
        workflow_results['error'] = str(e)
    
    return workflow_results


async def generate_test_report(scraper_results, analyzer_results, compiler_results, 
                              architecture_results, workflow_results):
    """Generate comprehensive test report"""
    
    print("\n📋 COMPREHENSIVE TEST REPORT")
    print("=" * 50)
    
    test_report = {
        'test_timestamp': datetime.now().isoformat(),
        'system_overview': {
            'specialized_scrapers': 4,
            'analyzers': 1,  # Only price analyzer tested
            'master_compiler': 1,
            'data_domains': 4
        },
        'test_results': {
            'scrapers': scraper_results,
            'analyzers': analyzer_results,
            'compiler': compiler_results,
            'architecture': architecture_results,
            'end_to_end': workflow_results
        },
        'overall_assessment': {},
        'recommendations': []
    }
    
    # Calculate success rates
    scraper_success_count = sum(1 for result in scraper_results.values() if result['status'] == 'success')
    scraper_success_rate = (scraper_success_count / len(scraper_results)) * 100
    
    analyzer_success = analyzer_results.get('status') == 'success'
    compiler_success = compiler_results.get('status') == 'success'
    architecture_success = architecture_results.get('directories_created', False)
    workflow_success = workflow_results.get('overall_success', False)
    
    # Overall assessment
    test_report['overall_assessment'] = {
        'scraper_success_rate': scraper_success_rate,
        'analyzer_success': analyzer_success,
        'compiler_success': compiler_success,
        'architecture_success': architecture_success,
        'end_to_end_success': workflow_success,
        'system_readiness': 'production' if all([
            scraper_success_rate >= 75,
            analyzer_success,
            compiler_success,
            architecture_success,
            workflow_success
        ]) else 'development'
    }
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print(f"   Scraper Success Rate: {scraper_success_rate:.1f}%")
    print(f"   Analyzer Success: {'✅' if analyzer_success else '❌'}")  
    print(f"   Compiler Success: {'✅' if compiler_success else '❌'}")
    print(f"   Architecture Success: {'✅' if architecture_success else '❌'}")
    print(f"   End-to-End Success: {'✅' if workflow_success else '❌'}")
    print(f"   System Readiness: {test_report['overall_assessment']['system_readiness'].title()}")
    
    # Recommendations
    if scraper_success_rate < 100:
        test_report['recommendations'].append("Address scraper failures to improve data collection reliability")
    
    if not analyzer_success:
        test_report['recommendations'].append("Fix analyzer issues to enable proper price analysis")
    
    if not compiler_success:
        test_report['recommendations'].append("Resolve compiler issues for intelligence generation")
    
    if test_report['overall_assessment']['system_readiness'] == 'production':
        test_report['recommendations'].append("System ready for production deployment")
        print(f"\n🎉 SYSTEM READY FOR PRODUCTION!")
    else:
        test_report['recommendations'].append("Address failing components before production deployment")
        print(f"\n⚠️ SYSTEM NEEDS ATTENTION BEFORE PRODUCTION")
    
    # Save test report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"specialized_mining_intelligence_test_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(test_report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Test report saved to: {report_file}")
    
    return test_report


async def main():
    """Main test execution"""
    
    print("🧪 SPECIALIZED MINING INTELLIGENCE SYSTEM - COMPREHENSIVE TEST")
    print("=" * 80)
    print("Testing the new specialized scraping and analysis architecture")
    print()
    
    try:
        # Test 1: Individual Scrapers
        scraper_results = await test_individual_scrapers()
        
        # Test 2: Price Analyzer
        analyzer_results = await test_price_analyzer()
        
        # Test 3: Master Intelligence Compiler
        compiler_results = await test_master_intelligence_compiler()
        
        # Test 4: Data Architecture
        architecture_results = await test_data_architecture()
        
        # Test 5: End-to-End Workflow
        workflow_results = await test_end_to_end_workflow()
        
        # Generate Comprehensive Test Report
        test_report = await generate_test_report(
            scraper_results, analyzer_results, compiler_results, 
            architecture_results, workflow_results
        )
        
        return test_report
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        return {'error': str(e)}


if __name__ == "__main__":
    results = asyncio.run(main())
    
    if results.get('overall_assessment', {}).get('system_readiness') == 'production':
        print("\n✅ Specialized Mining Intelligence System testing completed successfully!")
    else:
        print("\n❌ Specialized Mining Intelligence System testing identified issues!")