#!/usr/bin/env python3
"""
Master Intelligence Compiler
Aggregates insights from all specialized analyzers to create unified intelligence reports

Capabilities:
- Cross-domain correlation analysis (prices, economics, companies, news)
- Market opportunity identification 
- Risk assessment and early warning systems
- Investment thesis generation
- Comprehensive market intelligence reports
- Real-time decision support insights
"""

import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import statistics

# Import specialized scrapers
from ..scrapers.specialized.metal_prices_scraper import MetalPricesScraper
from ..scrapers.specialized.economic_data_scraper import EconomicDataScraper  
from ..scrapers.specialized.mining_companies_scraper import MiningCompaniesScraper
from ..scrapers.specialized.mining_news_scraper import SpecializedMiningNewsScraper

# Import analyzers
from ..analyzers.price_analyzer import PriceAnalyzer


class MasterIntelligenceCompiler:
    """Compiles insights from all specialized modules into unified intelligence"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.reports_dir = Path("data/intelligence_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize specialized components
        self.price_scraper = MetalPricesScraper()
        self.economic_scraper = EconomicDataScraper()
        self.companies_scraper = MiningCompaniesScraper()
        self.news_scraper = SpecializedMiningNewsScraper()
        
        # Initialize analyzers
        self.price_analyzer = PriceAnalyzer()
        
        # Intelligence compilation parameters
        self.correlation_threshold = 0.6  # Strong correlation threshold
        self.alert_severity_weights = {
            'critical': 3,
            'warning': 2,
            'info': 1
        }
        
        # Market themes and narratives
        self.market_themes = {
            'inflation_hedge': ['gold', 'silver', 'copper'],
            'industrial_demand': ['copper', 'aluminum', 'zinc', 'nickel'],
            'green_energy': ['lithium', 'cobalt', 'nickel', 'copper'],
            'safe_haven': ['gold', 'silver'],
            'economic_growth': ['copper', 'iron_ore', 'aluminum']
        }
    
    async def generate_comprehensive_intelligence_report(self) -> Dict[str, Any]:
        """Generate a comprehensive mining intelligence report"""
        
        print("🧠 Generating comprehensive mining intelligence report...")
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'report_type': 'comprehensive_intelligence',
            'executive_summary': {},
            'market_overview': {},
            'cross_domain_analysis': {},
            'investment_opportunities': {},
            'risk_assessments': {},
            'strategic_insights': {},
            'actionable_recommendations': {},
            'data_quality_assessment': {},
            'appendix': {}
        }
        
        try:
            # Step 1: Collect fresh data from all domains
            print("📊 Collecting data from all domains...")
            raw_data = await self._collect_all_domain_data()
            
            # Step 2: Perform individual domain analysis
            print("🔍 Analyzing individual domains...")
            domain_analyses = await self._analyze_all_domains(raw_data)
            
            # Step 3: Cross-domain correlation analysis
            print("🔗 Performing cross-domain correlation analysis...")
            cross_correlations = await self._analyze_cross_domain_correlations(domain_analyses)
            
            # Step 4: Market opportunity identification
            print("💡 Identifying market opportunities...")
            opportunities = await self._identify_market_opportunities(domain_analyses, cross_correlations)
            
            # Step 5: Risk assessment
            print("⚠️ Performing comprehensive risk assessment...")
            risk_assessment = await self._perform_risk_assessment(domain_analyses, cross_correlations)
            
            # Step 6: Generate strategic insights
            print("🎯 Generating strategic insights...")
            strategic_insights = await self._generate_strategic_insights(domain_analyses, opportunities, risk_assessment)
            
            # Step 7: Create actionable recommendations
            print("📋 Creating actionable recommendations...")
            recommendations = await self._create_actionable_recommendations(strategic_insights, opportunities, risk_assessment)
            
            # Compile final report
            report.update({
                'executive_summary': self._create_executive_summary(domain_analyses, opportunities, risk_assessment),
                'market_overview': self._create_market_overview(domain_analyses),
                'cross_domain_analysis': cross_correlations,
                'investment_opportunities': opportunities,
                'risk_assessments': risk_assessment,
                'strategic_insights': strategic_insights,
                'actionable_recommendations': recommendations,
                'data_quality_assessment': self._assess_data_quality(raw_data),
                'appendix': {
                    'raw_data_summary': self._summarize_raw_data(raw_data),
                    'methodology': self._document_methodology(),
                    'data_sources': self._list_data_sources()
                }
            })
            
        except Exception as e:
            print(f"❌ Error generating intelligence report: {str(e)}")
            report['error'] = str(e)
            report['partial_data'] = True
        
        # Save comprehensive report
        await self._save_intelligence_report(report)
        
        return report
    
    async def _collect_all_domain_data(self) -> Dict[str, Any]:
        """Collect fresh data from all specialized scrapers"""
        
        raw_data = {
            'collection_timestamp': datetime.now().isoformat(),
            'metal_prices': {},
            'economic_indicators': {},
            'company_data': {},
            'news_data': {},
            'collection_errors': []
        }
        
        # Collect metal prices data
        try:
            print("  💰 Collecting metal prices...")
            prices_data = await self.price_scraper.scrape_all_metal_prices()
            raw_data['metal_prices'] = prices_data
        except Exception as e:
            error_msg = f"Metal prices collection failed: {str(e)}"
            print(f"    ❌ {error_msg}")
            raw_data['collection_errors'].append(error_msg)
        
        # Collect economic data
        try:
            print("  📊 Collecting economic indicators...")
            economic_data = await self.economic_scraper.scrape_all_economic_data()
            raw_data['economic_indicators'] = economic_data
        except Exception as e:
            error_msg = f"Economic data collection failed: {str(e)}"
            print(f"    ❌ {error_msg}")
            raw_data['collection_errors'].append(error_msg)
        
        # Collect company data (limited sample for performance)
        try:
            print("  🏢 Collecting company data...")
            company_data = await self.companies_scraper.scrape_all_companies_data()
            raw_data['company_data'] = company_data
        except Exception as e:
            error_msg = f"Company data collection failed: {str(e)}"
            print(f"    ❌ {error_msg}")
            raw_data['collection_errors'].append(error_msg)
        
        # Collect news data  
        try:
            print("  📰 Collecting mining news...")
            news_data = await self.news_scraper.scrape_all_mining_news()
            raw_data['news_data'] = news_data
        except Exception as e:
            error_msg = f"News data collection failed: {str(e)}"
            print(f"    ❌ {error_msg}")
            raw_data['collection_errors'].append(error_msg)
        
        return raw_data
    
    async def _analyze_all_domains(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on each domain's data"""
        
        domain_analyses = {
            'analysis_timestamp': datetime.now().isoformat(),
            'price_analysis': {},
            'economic_analysis': {},
            'company_analysis': {},
            'news_analysis': {}
        }
        
        # Analyze price data
        if raw_data.get('metal_prices') and not raw_data['metal_prices'].get('errors'):
            try:
                print("  📈 Analyzing price trends...")
                price_analysis = await self.price_analyzer.analyze_all_prices(30)
                domain_analyses['price_analysis'] = price_analysis
            except Exception as e:
                print(f"    ❌ Price analysis failed: {str(e)}")
        
        # Analyze economic data (simplified analysis for now)
        if raw_data.get('economic_indicators'):
            try:
                print("  📊 Analyzing economic indicators...")
                economic_analysis = self._analyze_economic_indicators(raw_data['economic_indicators'])
                domain_analyses['economic_analysis'] = economic_analysis
            except Exception as e:
                print(f"    ❌ Economic analysis failed: {str(e)}")
        
        # Analyze company data
        if raw_data.get('company_data'):
            try:
                print("  🏢 Analyzing company metrics...")
                company_analysis = self._analyze_company_metrics(raw_data['company_data'])
                domain_analyses['company_analysis'] = company_analysis
            except Exception as e:
                print(f"    ❌ Company analysis failed: {str(e)}")
        
        # Analyze news sentiment
        if raw_data.get('news_data'):
            try:
                print("  📰 Analyzing news sentiment...")
                news_analysis = self._analyze_news_sentiment(raw_data['news_data'])
                domain_analyses['news_analysis'] = news_analysis
            except Exception as e:
                print(f"    ❌ News analysis failed: {str(e)}")
        
        return domain_analyses
    
    def _analyze_economic_indicators(self, economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze economic indicators for mining sector impact"""
        
        analysis = {
            'mining_sector_outlook': 'neutral',
            'key_indicators': {},
            'sector_impacts': {},
            'economic_themes': []
        }
        
        # Extract key indicators
        indicators_found = 0
        positive_indicators = 0
        negative_indicators = 0
        
        for source_name, source_data in economic_data.get('canadian_indicators', {}).items():
            if isinstance(source_data, dict) and 'indicators' in source_data:
                for endpoint, endpoint_data in source_data['indicators'].items():
                    indicators = endpoint_data.get('data', {}).get('indicators', {})
                    for indicator_name, indicator_data in indicators.items():
                        indicators_found += 1
                        value = indicator_data.get('value', 0)
                        
                        # Simple scoring based on indicator type
                        if 'gdp' in indicator_name and value > 0:
                            positive_indicators += 1
                        elif 'unemployment' in indicator_name and value > 7:  # High unemployment
                            negative_indicators += 1
                        elif 'inflation' in indicator_name and value > 4:  # High inflation
                            negative_indicators += 1
                        elif 'mining_production' in indicator_name and value > 0:
                            positive_indicators += 1
        
        # Determine overall outlook
        if positive_indicators > negative_indicators * 1.5:
            analysis['mining_sector_outlook'] = 'positive'
        elif negative_indicators > positive_indicators * 1.5:
            analysis['mining_sector_outlook'] = 'negative'
        
        analysis['key_indicators'] = {
            'total_indicators': indicators_found,
            'positive_signals': positive_indicators,
            'negative_signals': negative_indicators
        }
        
        return analysis
    
    def _analyze_company_metrics(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze company performance metrics"""
        
        analysis = {
            'sector_performance': 'neutral',
            'company_standings': {},
            'performance_trends': {},
            'valuation_metrics': {}
        }
        
        companies_with_data = 0
        total_price_change = 0
        
        for ticker, company_info in company_data.get('companies_data', {}).items():
            stock_data = company_info.get('stock_data', {})
            if stock_data.get('price'):
                companies_with_data += 1
                change = stock_data.get('change', 0)
                if isinstance(change, (int, float)):
                    total_price_change += change
        
        if companies_with_data > 0:
            avg_change = total_price_change / companies_with_data
            if avg_change > 0.5:
                analysis['sector_performance'] = 'positive'
            elif avg_change < -0.5:
                analysis['sector_performance'] = 'negative'
        
        analysis['performance_trends'] = {
            'companies_analyzed': companies_with_data,
            'average_price_change': total_price_change / companies_with_data if companies_with_data > 0 else 0
        }
        
        return analysis
    
    def _analyze_news_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze news sentiment and market impact"""
        
        analysis = {
            'overall_sentiment': 'neutral',
            'sentiment_distribution': {},
            'key_themes': [],
            'market_moving_news': [],
            'sector_sentiment': {}
        }
        
        sentiment_data = news_data.get('sentiment_analysis', {})
        if sentiment_data:
            analysis['sentiment_distribution'] = {
                'positive': sentiment_data.get('positive', 0),
                'negative': sentiment_data.get('negative', 0),
                'neutral': sentiment_data.get('neutral', 0)
            }
            
            total_articles = sum(analysis['sentiment_distribution'].values())
            if total_articles > 0:
                positive_ratio = sentiment_data.get('positive', 0) / total_articles
                negative_ratio = sentiment_data.get('negative', 0) / total_articles
                
                if positive_ratio > 0.4:
                    analysis['overall_sentiment'] = 'positive'
                elif negative_ratio > 0.4:
                    analysis['overall_sentiment'] = 'negative'
        
        # Analyze categorized news
        categorized_news = news_data.get('categorized_news', {})
        breaking_news = categorized_news.get('breaking_news', [])
        if breaking_news:
            analysis['market_moving_news'] = [
                {
                    'title': article.get('title', ''),
                    'sentiment': article.get('preliminary_sentiment', 'neutral'),
                    'relevance': article.get('mining_relevance_score', 0)
                }
                for article in breaking_news[:5]  # Top 5 breaking news
            ]
        
        return analysis
    
    async def _analyze_cross_domain_correlations(self, domain_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlations between different data domains"""
        
        correlations = {
            'analysis_timestamp': datetime.now().isoformat(),
            'price_economic_correlation': {},
            'price_news_correlation': {},
            'economic_company_correlation': {},
            'news_company_correlation': {},
            'cross_domain_insights': []
        }
        
        # Price-Economic correlation
        price_sentiment = domain_analyses.get('price_analysis', {}).get('market_overview', {}).get('market_sentiment', 'neutral')
        economic_outlook = domain_analyses.get('economic_analysis', {}).get('mining_sector_outlook', 'neutral')
        
        if price_sentiment == economic_outlook and price_sentiment != 'neutral':
            correlations['price_economic_correlation'] = {
                'correlation_strength': 'strong',
                'alignment': 'positive',
                'insight': f"Price trends and economic outlook both {price_sentiment}"
            }
            correlations['cross_domain_insights'].append(
                f"Strong alignment between price trends ({price_sentiment}) and economic outlook ({economic_outlook})"
            )
        
        # Price-News correlation
        news_sentiment = domain_analyses.get('news_analysis', {}).get('overall_sentiment', 'neutral') 
        if price_sentiment == news_sentiment and price_sentiment != 'neutral':
            correlations['price_news_correlation'] = {
                'correlation_strength': 'strong',
                'alignment': 'positive',
                'insight': f"Price trends align with news sentiment ({news_sentiment})"
            }
            correlations['cross_domain_insights'].append(
                f"News sentiment ({news_sentiment}) supports price trend direction ({price_sentiment})"
            )
        
        return correlations
    
    async def _identify_market_opportunities(self, domain_analyses: Dict[str, Any], 
                                           cross_correlations: Dict[str, Any]) -> Dict[str, Any]:
        """Identify market opportunities based on cross-domain analysis"""
        
        opportunities = {
            'identification_timestamp': datetime.now().isoformat(),
            'high_conviction_opportunities': [],
            'medium_conviction_opportunities': [],
            'contrarian_opportunities': [],
            'thematic_opportunities': {},
            'timing_considerations': {}
        }
        
        # High conviction: All domains align positively
        price_analysis = domain_analyses.get('price_analysis', {})
        economic_analysis = domain_analyses.get('economic_analysis', {})
        news_analysis = domain_analyses.get('news_analysis', {})
        
        # Check for strong alignment across domains
        price_sentiment = price_analysis.get('market_overview', {}).get('market_sentiment', 'neutral')
        economic_outlook = economic_analysis.get('mining_sector_outlook', 'neutral')
        news_sentiment = news_analysis.get('overall_sentiment', 'neutral')
        
        if price_sentiment == 'bullish' and economic_outlook == 'positive' and news_sentiment == 'positive':
            # Find best performing metals
            best_performers = price_analysis.get('market_overview', {}).get('best_performers', [])
            for performer in best_performers[:3]:
                opportunities['high_conviction_opportunities'].append({
                    'asset': performer['metal'],
                    'conviction_level': 'high',
                    'rationale': 'Strong alignment across price trends, economic indicators, and news sentiment',
                    'supporting_factors': [
                        f"Price momentum: +{performer.get('change_percent', 0):.1f}%",
                        'Positive economic outlook for mining sector',
                        'Bullish news sentiment'
                    ],
                    'risk_level': 'moderate'
                })
        
        # Contrarian opportunities: Negative sentiment but strong fundamentals
        if news_sentiment == 'negative' and economic_outlook == 'positive':
            worst_performers = price_analysis.get('market_overview', {}).get('worst_performers', [])
            for performer in worst_performers[-2:]:  # Bottom 2 performers
                opportunities['contrarian_opportunities'].append({
                    'asset': performer['metal'],
                    'conviction_level': 'medium',
                    'rationale': 'Negative sentiment creating potential value opportunity despite positive fundamentals',
                    'supporting_factors': [
                        'Positive economic fundamentals',
                        'Oversold due to negative sentiment',
                        'Potential for sentiment reversal'
                    ],
                    'risk_level': 'high'
                })
        
        # Thematic opportunities
        for theme, metals in self.market_themes.items():
            theme_score = 0
            theme_metals = []
            
            # Check if metals in theme are performing well
            best_performers = price_analysis.get('market_overview', {}).get('best_performers', [])
            for performer in best_performers:
                if performer['metal'] in metals:
                    theme_score += 1
                    theme_metals.append(performer['metal'])
            
            if theme_score >= 2:  # At least 2 metals in theme performing well
                opportunities['thematic_opportunities'][theme] = {
                    'strength': 'strong' if theme_score >= 3 else 'moderate',
                    'participating_metals': theme_metals,
                    'rationale': f'{theme.replace("_", " ").title()} theme showing strength'
                }
        
        return opportunities
    
    async def _perform_risk_assessment(self, domain_analyses: Dict[str, Any], 
                                     cross_correlations: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk assessment"""
        
        risk_assessment = {
            'assessment_timestamp': datetime.now().isoformat(),
            'overall_risk_level': 'moderate',
            'risk_categories': {},
            'early_warning_signals': [],
            'risk_mitigation_strategies': [],
            'portfolio_risk_metrics': {}
        }
        
        # Market risk assessment
        price_analysis = domain_analyses.get('price_analysis', {})
        volatility_leaders = price_analysis.get('market_overview', {}).get('volatility_leaders', [])
        
        if volatility_leaders:
            high_vol_count = sum(1 for metal in volatility_leaders if metal.get('volatility', 0) > 0.05)
            risk_assessment['risk_categories']['market_volatility'] = {
                'level': 'high' if high_vol_count >= 2 else 'moderate',
                'description': f'{high_vol_count} metals showing high volatility',
                'impact': 'Increased portfolio risk and potential for large losses'
            }
        
        # Economic risk assessment
        economic_analysis = domain_analyses.get('economic_analysis', {})
        negative_signals = economic_analysis.get('key_indicators', {}).get('negative_signals', 0)
        
        if negative_signals > 2:
            risk_assessment['early_warning_signals'].append({
                'signal': 'Economic headwinds',
                'severity': 'warning',
                'description': f'{negative_signals} negative economic indicators detected',
                'recommendation': 'Monitor economic data closely, consider defensive positioning'
            })
        
        # News-based risk signals
        news_analysis = domain_analyses.get('news_analysis', {})
        if news_analysis.get('overall_sentiment') == 'negative':
            market_moving_news = news_analysis.get('market_moving_news', [])
            negative_news = [news for news in market_moving_news if news.get('sentiment') == 'negative']
            
            if len(negative_news) >= 2:
                risk_assessment['early_warning_signals'].append({
                    'signal': 'Negative news sentiment',
                    'severity': 'info',
                    'description': f'{len(negative_news)} negative market-moving news items',
                    'recommendation': 'Monitor news flow for sentiment changes'
                })
        
        # Overall risk level determination
        warning_signals = len([signal for signal in risk_assessment['early_warning_signals'] 
                              if signal['severity'] in ['critical', 'warning']])
        
        if warning_signals >= 2:
            risk_assessment['overall_risk_level'] = 'high'
        elif warning_signals == 1:
            risk_assessment['overall_risk_level'] = 'moderate'
        else:
            risk_assessment['overall_risk_level'] = 'low'
        
        return risk_assessment
    
    async def _generate_strategic_insights(self, domain_analyses: Dict[str, Any], 
                                         opportunities: Dict[str, Any], 
                                         risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic insights for decision making"""
        
        insights = {
            'generation_timestamp': datetime.now().isoformat(),
            'market_regime_analysis': {},
            'sector_rotation_signals': {},
            'investment_themes': {},
            'strategic_positioning': {},
            'macro_micro_synthesis': {}
        }
        
        # Market regime analysis
        price_sentiment = domain_analyses.get('price_analysis', {}).get('market_overview', {}).get('market_sentiment', 'neutral')
        economic_outlook = domain_analyses.get('economic_analysis', {}).get('mining_sector_outlook', 'neutral')
        overall_risk = risk_assessment.get('overall_risk_level', 'moderate')
        
        if price_sentiment == 'bullish' and economic_outlook == 'positive' and overall_risk == 'low':
            regime = 'risk_on'
        elif price_sentiment == 'bearish' and economic_outlook == 'negative' and overall_risk == 'high':
            regime = 'risk_off'
        else:
            regime = 'transitional'
        
        insights['market_regime_analysis'] = {
            'current_regime': regime,
            'regime_strength': 'strong' if price_sentiment == economic_outlook else 'weak',
            'implications': self._get_regime_implications(regime)
        }
        
        # Investment themes strength
        thematic_opportunities = opportunities.get('thematic_opportunities', {})
        strong_themes = [theme for theme, data in thematic_opportunities.items() 
                        if data.get('strength') == 'strong']
        
        insights['investment_themes'] = {
            'dominant_themes': strong_themes,
            'theme_rotation_signals': self._analyze_theme_rotation(thematic_opportunities),
            'emerging_themes': self._identify_emerging_themes(domain_analyses)
        }
        
        return insights
    
    def _get_regime_implications(self, regime: str) -> List[str]:
        """Get implications for different market regimes"""
        
        implications = {
            'risk_on': [
                'Favor growth-oriented mining investments',
                'Industrial metals likely to outperform',
                'Higher risk tolerance appropriate',
                'Focus on operational leverage plays'
            ],
            'risk_off': [
                'Favor defensive precious metals',
                'Reduce exposure to volatile base metals',
                'Focus on established producers',
                'Maintain higher cash positions'
            ],
            'transitional': [
                'Maintain balanced exposure',
                'Monitor regime change signals closely',
                'Prepare for increased volatility',
                'Focus on quality assets'
            ]
        }
        
        return implications.get(regime, [])
    
    def _analyze_theme_rotation(self, thematic_opportunities: Dict[str, Any]) -> Dict[str, str]:
        """Analyze potential theme rotation signals"""
        
        rotation_signals = {}
        
        # Check for momentum in different themes
        for theme, data in thematic_opportunities.items():
            strength = data.get('strength', 'weak')
            if strength == 'strong':
                rotation_signals[theme] = 'momentum_building'
            elif strength == 'moderate':
                rotation_signals[theme] = 'early_stage'
        
        return rotation_signals
    
    def _identify_emerging_themes(self, domain_analyses: Dict[str, Any]) -> List[str]:
        """Identify emerging investment themes"""
        
        emerging_themes = []
        
        # Check news for emerging themes
        news_analysis = domain_analyses.get('news_analysis', {})
        market_moving_news = news_analysis.get('market_moving_news', [])
        
        # Simple keyword-based theme detection
        green_energy_keywords = ['lithium', 'cobalt', 'battery', 'electric', 'renewable']
        infrastructure_keywords = ['infrastructure', 'construction', 'development']
        
        green_mentions = sum(1 for news in market_moving_news 
                           if any(keyword in news.get('title', '').lower() 
                                 for keyword in green_energy_keywords))
        
        if green_mentions >= 2:
            emerging_themes.append('green_energy_transition')
        
        return emerging_themes
    
    async def _create_actionable_recommendations(self, strategic_insights: Dict[str, Any],
                                               opportunities: Dict[str, Any], 
                                               risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create specific actionable recommendations"""
        
        recommendations = {
            'generation_timestamp': datetime.now().isoformat(),
            'immediate_actions': [],
            'short_term_strategy': [],
            'medium_term_positioning': [],
            'risk_management': [],
            'monitoring_priorities': []
        }
        
        # Immediate actions based on high conviction opportunities
        high_conviction = opportunities.get('high_conviction_opportunities', [])
        for opportunity in high_conviction:
            recommendations['immediate_actions'].append({
                'action': f"Consider increasing exposure to {opportunity['asset']}",
                'rationale': opportunity['rationale'],
                'priority': 'high',
                'time_horizon': '1-2 weeks'
            })
        
        # Risk management recommendations
        overall_risk = risk_assessment.get('overall_risk_level', 'moderate')
        early_warnings = risk_assessment.get('early_warning_signals', [])
        
        if overall_risk == 'high' or len(early_warnings) >= 2:
            recommendations['risk_management'].extend([
                {
                    'action': 'Reduce position sizes in volatile assets',
                    'rationale': f'Overall risk level: {overall_risk}',
                    'priority': 'high'
                },
                {
                    'action': 'Increase cash reserves',
                    'rationale': 'Prepare for potential market stress',
                    'priority': 'medium'
                }
            ])
        
        # Strategic positioning based on market regime
        regime = strategic_insights.get('market_regime_analysis', {}).get('current_regime', 'transitional')
        regime_implications = strategic_insights.get('market_regime_analysis', {}).get('implications', [])
        
        for implication in regime_implications[:2]:  # Top 2 implications
            recommendations['medium_term_positioning'].append({
                'strategy': implication,
                'regime_context': regime,
                'time_horizon': '1-3 months'
            })
        
        # Monitoring priorities
        recommendations['monitoring_priorities'] = [
            'Track price momentum changes in key metals',
            'Monitor economic indicator releases',
            'Watch for news sentiment shifts',
            'Observe correlation breakdowns between assets'
        ]
        
        return recommendations
    
    def _create_executive_summary(self, domain_analyses: Dict[str, Any], 
                                 opportunities: Dict[str, Any], 
                                 risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary of key findings"""
        
        summary = {
            'report_date': datetime.now().strftime("%Y-%m-%d"),
            'market_outlook': 'neutral',
            'key_findings': [],
            'top_opportunities': [],
            'main_risks': [],
            'overall_assessment': {}
        }
        
        # Determine overall market outlook
        price_sentiment = domain_analyses.get('price_analysis', {}).get('market_overview', {}).get('market_sentiment', 'neutral')
        economic_outlook = domain_analyses.get('economic_analysis', {}).get('mining_sector_outlook', 'neutral')
        
        if price_sentiment == 'bullish' and economic_outlook == 'positive':
            summary['market_outlook'] = 'positive'
        elif price_sentiment == 'bearish' and economic_outlook == 'negative':
            summary['market_outlook'] = 'negative'
        
        # Key findings
        if domain_analyses.get('price_analysis', {}).get('summary', {}).get('metals_analyzed', 0) > 0:
            metals_count = domain_analyses['price_analysis']['summary']['metals_analyzed']
            summary['key_findings'].append(f"Analyzed {metals_count} metals with comprehensive price data")
        
        # Top opportunities
        high_conviction = opportunities.get('high_conviction_opportunities', [])
        for opp in high_conviction[:3]:  # Top 3
            summary['top_opportunities'].append({
                'asset': opp['asset'],
                'conviction': opp['conviction_level'],
                'key_driver': opp['rationale']
            })
        
        # Main risks
        early_warnings = risk_assessment.get('early_warning_signals', [])
        for warning in early_warnings[:3]:  # Top 3
            summary['main_risks'].append({
                'risk': warning['signal'],
                'severity': warning['severity'],
                'description': warning['description']
            })
        
        return summary
    
    def _create_market_overview(self, domain_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive market overview"""
        
        overview = {
            'price_action_summary': {},
            'economic_environment': {},
            'corporate_performance': {},
            'news_sentiment_analysis': {},
            'cross_asset_dynamics': {}
        }
        
        # Price action summary
        price_analysis = domain_analyses.get('price_analysis', {})
        if price_analysis:
            market_overview = price_analysis.get('market_overview', {})
            overview['price_action_summary'] = {
                'market_sentiment': market_overview.get('market_sentiment', 'neutral'),
                'best_performers': market_overview.get('best_performers', [])[:3],
                'worst_performers': market_overview.get('worst_performers', [])[-3:],
                'volatility_leaders': market_overview.get('volatility_leaders', [])[:3]
            }
        
        # Economic environment
        economic_analysis = domain_analyses.get('economic_analysis', {})
        if economic_analysis:
            overview['economic_environment'] = {
                'mining_sector_outlook': economic_analysis.get('mining_sector_outlook', 'neutral'),
                'key_indicators': economic_analysis.get('key_indicators', {}),
                'economic_themes': economic_analysis.get('economic_themes', [])
            }
        
        return overview
    
    def _assess_data_quality(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality and completeness of collected data"""
        
        assessment = {
            'overall_quality': 'good',
            'data_completeness': {},
            'collection_success_rates': {},
            'data_freshness': {},
            'quality_score': 0
        }
        
        total_domains = 4  # metal_prices, economic_indicators, company_data, news_data
        successful_domains = 0
        
        for domain in ['metal_prices', 'economic_indicators', 'company_data', 'news_data']:
            domain_data = raw_data.get(domain, {})
            if domain_data and not domain_data.get('errors'):
                successful_domains += 1
                assessment['data_completeness'][domain] = 'complete'
            else:
                assessment['data_completeness'][domain] = 'partial' if domain_data else 'missing'
        
        # Calculate quality score
        completeness_score = (successful_domains / total_domains) * 100
        assessment['quality_score'] = completeness_score
        
        if completeness_score >= 75:
            assessment['overall_quality'] = 'good'
        elif completeness_score >= 50:
            assessment['overall_quality'] = 'fair'
        else:
            assessment['overall_quality'] = 'poor'
        
        return assessment
    
    def _summarize_raw_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize raw data collection results"""
        
        summary = {
            'collection_timestamp': raw_data.get('collection_timestamp'),
            'domains_collected': [],
            'total_errors': len(raw_data.get('collection_errors', [])),
            'data_points_summary': {}
        }
        
        for domain, data in raw_data.items():
            if domain != 'collection_errors' and domain != 'collection_timestamp' and data:
                summary['domains_collected'].append(domain)
                
                # Count data points where possible
                if domain == 'metal_prices':
                    metals_count = 0
                    for category in ['precious_metals', 'base_metals', 'energy_commodities']:
                        metals_count += len(data.get(category, {}))
                    summary['data_points_summary'][domain] = f"{metals_count} metals"
                
                elif domain == 'news_data':
                    articles_count = data.get('duplicate_detection', {}).get('unique_articles', 0)
                    summary['data_points_summary'][domain] = f"{articles_count} unique articles"
                
                elif domain == 'company_data':
                    companies_count = len(data.get('companies_data', {}))
                    summary['data_points_summary'][domain] = f"{companies_count} companies"
        
        return summary
    
    def _document_methodology(self) -> Dict[str, Any]:
        """Document the analysis methodology"""
        
        return {
            'data_collection': 'Real-time scraping from multiple specialized sources',
            'analysis_approach': 'Cross-domain correlation and pattern recognition',
            'risk_assessment': 'Multi-factorial analysis with early warning signals',
            'opportunity_identification': 'Consensus-based scoring with conviction levels',
            'limitations': [
                'Analysis based on publicly available data only',
                'Historical patterns may not predict future performance',
                'Model assumptions may not hold in all market conditions'
            ]
        }
    
    def _list_data_sources(self) -> Dict[str, List[str]]:
        """List all data sources used"""
        
        return {
            'metal_prices': [
                'Trading Economics', 'Yahoo Finance', 'Kitco', 'London Metal Exchange'
            ],
            'economic_indicators': [
                'Trading Economics Canada', 'Bank of Canada', 'Statistics Canada', 
                'Federal Reserve Economic Data', 'OECD'
            ],
            'company_data': [
                'TSX Company Profiles', 'Yahoo Finance', 'Company Websites'
            ],
            'news_sources': [
                'Northern Miner', 'Mining.com', 'Reuters', 'S&P Global', 
                'Mining Weekly', 'Kitco News'
            ]
        }
    
    async def _save_intelligence_report(self, report: Dict[str, Any]):
        """Save the comprehensive intelligence report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to daily reports
        daily_file = self.reports_dir / "daily" / f"intelligence_report_{timestamp}.json"
        daily_file.parent.mkdir(exist_ok=True)
        
        with open(daily_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Comprehensive intelligence report saved to: {daily_file}")
    
    async def cleanup(self):
        """Cleanup all scraper resources"""
        await self.price_scraper.cleanup()
        await self.economic_scraper.cleanup()
        await self.companies_scraper.cleanup()
        await self.news_scraper.cleanup()


# Convenience function
async def generate_mining_intelligence_report() -> Dict[str, Any]:
    """Convenience function to generate comprehensive mining intelligence report"""
    compiler = MasterIntelligenceCompiler()
    try:
        return await compiler.generate_comprehensive_intelligence_report()
    finally:
        await compiler.cleanup()


# Example usage
if __name__ == "__main__":
    async def main():
        print("🧠 Master Intelligence Compiler - Comprehensive Mining Intelligence")
        print("=" * 80)
        
        compiler = MasterIntelligenceCompiler()
        
        try:
            # Generate comprehensive intelligence report
            print("\n🚀 Generating comprehensive mining intelligence report...")
            report = await compiler.generate_comprehensive_intelligence_report()
            
            print(f"\n📊 INTELLIGENCE REPORT SUMMARY:")
            print(f"   Report Type: {report.get('report_type', 'unknown')}")
            print(f"   Market Outlook: {report.get('executive_summary', {}).get('market_outlook', 'neutral').title()}")
            print(f"   Data Quality: {report.get('data_quality_assessment', {}).get('overall_quality', 'unknown').title()}")
            
            # Show key findings
            key_findings = report.get('executive_summary', {}).get('key_findings', [])
            if key_findings:
                print(f"\n🔍 KEY FINDINGS:")
                for finding in key_findings[:3]:
                    print(f"   • {finding}")
            
            # Show top opportunities
            top_opportunities = report.get('executive_summary', {}).get('top_opportunities', [])
            if top_opportunities:
                print(f"\n💡 TOP OPPORTUNITIES:")
                for opp in top_opportunities:
                    print(f"   • {opp['asset'].title()}: {opp['key_driver']}")
            
            # Show main risks
            main_risks = report.get('executive_summary', {}).get('main_risks', [])
            if main_risks:
                print(f"\n⚠️ MAIN RISKS:")
                for risk in main_risks:
                    print(f"   • {risk['risk']}: {risk['description']}")
            
            print(f"\n✅ Comprehensive intelligence report generated successfully!")
            
        finally:
            await compiler.cleanup()
    
    asyncio.run(main())