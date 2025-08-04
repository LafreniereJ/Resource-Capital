#!/usr/bin/env python3
"""
Price Analyzer
Analyzes metal and commodity price data for trends, patterns, and forecasts

Capabilities:
- Price trend analysis (short, medium, long-term)
- Volatility calculations and risk assessment
- Support/resistance level identification
- Correlation analysis between metals
- Price forecasting using statistical models
- Market sentiment indicators from price movements
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import statistics


class PriceAnalyzer:
    """Analyzes metal and commodity price data"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data/metal_prices")
        self.analysis_results_dir = Path("data/metal_prices/processed")
        self.analysis_results_dir.mkdir(parents=True, exist_ok=True)
        
        # Analysis parameters
        self.trend_periods = {
            'short_term': 7,    # 7 days
            'medium_term': 30,  # 30 days  
            'long_term': 90     # 90 days
        }
        
        self.volatility_thresholds = {
            'low': 0.02,      # 2% daily change
            'medium': 0.05,   # 5% daily change
            'high': 0.10      # 10% daily change
        }
        
        # Metal categories for correlation analysis
        self.metal_categories = {
            'precious_metals': ['gold', 'silver', 'platinum', 'palladium'],
            'base_metals': ['copper', 'aluminum', 'zinc', 'nickel', 'lead'],
            'energy_commodities': ['oil', 'natural_gas']
        }
    
    async def analyze_all_prices(self, days_back: int = 90) -> Dict[str, Any]:
        """Perform comprehensive price analysis for all metals"""
        
        print("📊 Starting comprehensive price analysis...")
        
        analysis_results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_period': f"{days_back} days",
            'metal_analyses': {},
            'market_overview': {},
            'correlations': {},
            'portfolio_insights': {},
            'alerts': [],
            'summary': {}
        }
        
        # Load historical price data
        price_data = await self._load_historical_prices(days_back)
        
        if not price_data:
            print("❌ No price data found for analysis")
            return analysis_results
        
        # Analyze each metal individually
        for metal in self._get_available_metals(price_data):
            try:
                print(f"⚡ Analyzing {metal} prices...")
                metal_analysis = await self._analyze_metal_prices(metal, price_data[metal])
                analysis_results['metal_analyses'][metal] = metal_analysis
                
            except Exception as e:
                print(f"❌ Error analyzing {metal}: {str(e)}")
                continue
        
        # Perform cross-metal analysis
        if len(analysis_results['metal_analyses']) > 1:
            print("🔗 Performing correlation analysis...")
            analysis_results['correlations'] = await self._analyze_correlations(price_data)
            
            print("🏆 Generating market overview...")
            analysis_results['market_overview'] = await self._generate_market_overview(analysis_results['metal_analyses'])
            
            print("💼 Creating portfolio insights...")
            analysis_results['portfolio_insights'] = await self._generate_portfolio_insights(analysis_results['metal_analyses'])
            
            print("🚨 Generating alerts...")
            analysis_results['alerts'] = await self._generate_price_alerts(analysis_results['metal_analyses'])
        
        # Generate summary
        analysis_results['summary'] = self._generate_analysis_summary(analysis_results)
        
        # Save analysis results
        await self._save_analysis_results(analysis_results)
        
        return analysis_results
    
    async def _load_historical_prices(self, days_back: int) -> Dict[str, List[Dict[str, Any]]]:
        """Load historical price data from stored files"""
        
        price_data = {}
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Look through monthly directories
        for days in range(days_back):
            date = datetime.now() - timedelta(days=days)
            monthly_dir = self.data_dir / date.strftime("%Y-%m")
            
            if monthly_dir.exists():
                for file_path in monthly_dir.glob("prices_*.json"):
                    try:
                        file_date = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_date < cutoff_date:
                            continue
                            
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Extract price data for each metal
                        for category in ['precious_metals', 'base_metals', 'energy_commodities']:
                            for metal, metal_data in data.get(category, {}).items():
                                if metal not in price_data:
                                    price_data[metal] = []
                                
                                consolidated_price = metal_data.get('consolidated_price')
                                if consolidated_price:
                                    price_data[metal].append({
                                        'date': data.get('scraping_started'),
                                        'price': consolidated_price['average'],
                                        'min_price': consolidated_price['min'],
                                        'max_price': consolidated_price['max'],
                                        'sources_count': consolidated_price['sources_count'],
                                        'price_spread': consolidated_price['price_spread']
                                    })
                    
                    except (json.JSONDecodeError, KeyError, OSError):
                        continue
        
        # Sort price data by date for each metal
        for metal in price_data:
            price_data[metal] = sorted(price_data[metal], key=lambda x: x['date'])
        
        print(f"📊 Loaded price data for {len(price_data)} metals")
        return price_data
    
    def _get_available_metals(self, price_data: Dict[str, List]) -> List[str]:
        """Get list of metals with sufficient data for analysis"""
        
        metals_with_data = []
        for metal, data_points in price_data.items():
            if len(data_points) >= 5:  # Minimum data points for analysis
                metals_with_data.append(metal)
        
        return metals_with_data
    
    async def _analyze_metal_prices(self, metal: str, price_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform comprehensive analysis for a single metal"""
        
        if len(price_points) < 2:
            return {'error': 'Insufficient data for analysis'}
        
        # Extract price series
        prices = [point['price'] for point in price_points]
        dates = [datetime.fromisoformat(point['date']) for point in price_points]
        
        analysis = {
            'metal': metal,
            'data_points': len(price_points),
            'date_range': {
                'start': dates[0].isoformat(),
                'end': dates[-1].isoformat(),
                'days': (dates[-1] - dates[0]).days
            },
            'current_price': prices[-1] if prices else None,
            'price_statistics': self._calculate_price_statistics(prices),
            'trend_analysis': self._analyze_price_trends(prices, dates),
            'volatility_analysis': self._analyze_volatility(prices),
            'support_resistance': self._find_support_resistance_levels(prices),
            'momentum_indicators': self._calculate_momentum_indicators(prices),
            'risk_metrics': self._calculate_risk_metrics(prices),
            'forecast': self._generate_price_forecast(prices, dates)
        }
        
        return analysis
    
    def _calculate_price_statistics(self, prices: List[float]) -> Dict[str, float]:
        """Calculate basic price statistics"""
        
        if not prices:
            return {}
        
        return {
            'mean': statistics.mean(prices),
            'median': statistics.median(prices),
            'std_dev': statistics.stdev(prices) if len(prices) > 1 else 0,
            'min': min(prices),
            'max': max(prices),
            'range': max(prices) - min(prices),
            'coefficient_of_variation': statistics.stdev(prices) / statistics.mean(prices) if len(prices) > 1 and statistics.mean(prices) != 0 else 0
        }
    
    def _analyze_price_trends(self, prices: List[float], dates: List[datetime]) -> Dict[str, Any]:
        """Analyze price trends over different time periods"""
        
        trends = {}
        
        for period_name, days in self.trend_periods.items():
            if len(prices) > days:
                recent_prices = prices[-days:]
                older_prices = prices[-(days*2):-days] if len(prices) > days*2 else prices[:days]
                
                if recent_prices and older_prices:
                    recent_avg = statistics.mean(recent_prices)
                    older_avg = statistics.mean(older_prices)
                    
                    change = recent_avg - older_avg
                    change_percent = (change / older_avg * 100) if older_avg != 0 else 0
                    
                    trends[period_name] = {
                        'change': change,
                        'change_percent': change_percent,
                        'direction': 'bullish' if change > 0 else 'bearish' if change < 0 else 'neutral',
                        'strength': 'strong' if abs(change_percent) > 10 else 'moderate' if abs(change_percent) > 5 else 'weak'
                    }
        
        return trends
    
    def _analyze_volatility(self, prices: List[float]) -> Dict[str, Any]:
        """Analyze price volatility"""
        
        if len(prices) < 2:
            return {}
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                daily_return = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(daily_return)
        
        if not returns:
            return {}
        
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        
        # Classify volatility
        if volatility < self.volatility_thresholds['low']:
            volatility_level = 'low'
        elif volatility < self.volatility_thresholds['medium']:
            volatility_level = 'medium'
        else:
            volatility_level = 'high'
        
        return {
            'daily_volatility': volatility,
            'annualized_volatility': volatility * (252 ** 0.5),  # 252 trading days
            'volatility_level': volatility_level,
            'max_daily_gain': max(returns) if returns else 0,
            'max_daily_loss': min(returns) if returns else 0,
            'positive_days': sum(1 for r in returns if r > 0),
            'negative_days': sum(1 for r in returns if r < 0)
        }
    
    def _find_support_resistance_levels(self, prices: List[float]) -> Dict[str, Any]:
        """Identify support and resistance levels"""
        
        if len(prices) < 10:
            return {}
        
        # Simple support/resistance using local minima/maxima
        support_levels = []
        resistance_levels = []
        
        # Look for local minima (support) and maxima (resistance)
        for i in range(2, len(prices) - 2):
            # Local minimum (support)
            if prices[i] < prices[i-1] and prices[i] < prices[i+1] and prices[i] < prices[i-2] and prices[i] < prices[i+2]:
                support_levels.append(prices[i])
            
            # Local maximum (resistance)  
            if prices[i] > prices[i-1] and prices[i] > prices[i+1] and prices[i] > prices[i-2] and prices[i] > prices[i+2]:
                resistance_levels.append(prices[i])
        
        return {
            'support_levels': sorted(set(support_levels))[-3:] if support_levels else [],  # Top 3 support
            'resistance_levels': sorted(set(resistance_levels), reverse=True)[:3] if resistance_levels else [],  # Top 3 resistance
            'current_position': self._analyze_current_position(prices[-1], support_levels, resistance_levels)
        }
    
    def _analyze_current_position(self, current_price: float, support_levels: List[float], resistance_levels: List[float]) -> str:
        """Analyze current price position relative to support/resistance"""
        
        if not support_levels or not resistance_levels:
            return 'neutral'
        
        nearest_support = max([s for s in support_levels if s < current_price], default=0)
        nearest_resistance = min([r for r in resistance_levels if r > current_price], default=float('inf'))
        
        if nearest_resistance == float('inf'):
            return 'above_resistance'
        elif nearest_support == 0:
            return 'below_support'
        else:
            # Calculate position between support and resistance
            range_size = nearest_resistance - nearest_support
            position = (current_price - nearest_support) / range_size
            
            if position < 0.3:
                return 'near_support'
            elif position > 0.7:
                return 'near_resistance'
            else:
                return 'mid_range'
    
    def _calculate_momentum_indicators(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate momentum indicators"""
        
        if len(prices) < 20:
            return {}
        
        # Simple Moving Averages
        sma_5 = statistics.mean(prices[-5:]) if len(prices) >= 5 else None
        sma_20 = statistics.mean(prices[-20:]) if len(prices) >= 20 else None
        
        # Rate of Change
        roc_10 = ((prices[-1] - prices[-11]) / prices[-11] * 100) if len(prices) >= 11 and prices[-11] != 0 else None
        
        momentum = {
            'sma_5': sma_5,
            'sma_20': sma_20,
            'price_vs_sma_5': ((prices[-1] - sma_5) / sma_5 * 100) if sma_5 and sma_5 != 0 else None,
            'price_vs_sma_20': ((prices[-1] - sma_20) / sma_20 * 100) if sma_20 and sma_20 != 0 else None,
            'sma_crossover': 'bullish' if sma_5 and sma_20 and sma_5 > sma_20 else 'bearish' if sma_5 and sma_20 and sma_5 < sma_20 else 'neutral',
            'rate_of_change_10d': roc_10
        }
        
        return momentum
    
    def _calculate_risk_metrics(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate risk metrics"""
        
        if len(prices) < 2:
            return {}
        
        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if not returns:
            return {}
        
        # Value at Risk (simple 95% confidence)
        sorted_returns = sorted(returns)
        var_95 = sorted_returns[int(len(sorted_returns) * 0.05)] if len(sorted_returns) > 20 else None
        
        # Maximum Drawdown
        peak = prices[0]
        max_drawdown = 0
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'value_at_risk_95': var_95,
            'maximum_drawdown': max_drawdown,
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'downside_deviation': self._calculate_downside_deviation(returns)
        }
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> Optional[float]:
        """Calculate Sharpe ratio"""
        
        if len(returns) < 2:
            return None
        
        mean_return = statistics.mean(returns) * 252  # Annualized
        std_return = statistics.stdev(returns) * (252 ** 0.5)  # Annualized
        
        if std_return == 0:
            return None
        
        return (mean_return - risk_free_rate) / std_return
    
    def _calculate_downside_deviation(self, returns: List[float]) -> Optional[float]:
        """Calculate downside deviation"""
        
        negative_returns = [r for r in returns if r < 0]
        if len(negative_returns) < 2:
            return None
        
        return statistics.stdev(negative_returns)
    
    def _generate_price_forecast(self, prices: List[float], dates: List[datetime]) -> Dict[str, Any]:
        """Generate simple price forecast"""
        
        if len(prices) < 10:
            return {'error': 'Insufficient data for forecasting'}
        
        # Simple linear trend forecast
        recent_prices = prices[-10:]  # Last 10 data points
        trend = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
        
        # Forecast next 7 days
        forecasts = []
        for i in range(1, 8):
            forecast_price = prices[-1] + (trend * i)
            forecasts.append({
                'days_ahead': i,
                'forecast_price': forecast_price,
                'confidence': 'low'  # Simple model has low confidence
            })
        
        return {
            'model_type': 'linear_trend',
            'forecasts': forecasts,
            'trend_direction': 'upward' if trend > 0 else 'downward' if trend < 0 else 'sideways',
            'trend_strength': abs(trend),
            'disclaimer': 'Simple trend-based forecast - not investment advice'
        }
    
    async def _analyze_correlations(self, price_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze correlations between different metals"""
        
        correlations = {
            'metal_pairs': {},
            'category_correlations': {},
            'correlation_summary': {}
        }
        
        # Calculate pairwise correlations
        metals = list(price_data.keys())
        for i, metal1 in enumerate(metals):
            for metal2 in metals[i+1:]:
                correlation = self._calculate_price_correlation(price_data[metal1], price_data[metal2])
                if correlation is not None:
                    pair_name = f"{metal1}_{metal2}"
                    correlations['metal_pairs'][pair_name] = {
                        'correlation': correlation,
                        'strength': self._interpret_correlation_strength(correlation)
                    }
        
        return correlations
    
    def _calculate_price_correlation(self, data1: List[Dict[str, Any]], data2: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate correlation between two price series"""
        
        # Align data by date
        dates1 = {item['date']: item['price'] for item in data1}
        dates2 = {item['date']: item['price'] for item in data2}
        
        common_dates = set(dates1.keys()) & set(dates2.keys())
        if len(common_dates) < 5:
            return None
        
        prices1 = [dates1[date] for date in sorted(common_dates)]
        prices2 = [dates2[date] for date in sorted(common_dates)]
        
        if len(prices1) < 2:
            return None
        
        # Calculate Pearson correlation
        try:
            correlation = np.corrcoef(prices1, prices2)[0, 1]
            return correlation if not np.isnan(correlation) else None
        except:
            return None
    
    def _interpret_correlation_strength(self, correlation: float) -> str:
        """Interpret correlation strength"""
        
        abs_corr = abs(correlation)
        if abs_corr >= 0.8:
            return 'very_strong'
        elif abs_corr >= 0.6:
            return 'strong'
        elif abs_corr >= 0.4:
            return 'moderate'
        elif abs_corr >= 0.2:
            return 'weak'
        else:
            return 'very_weak'
    
    async def _generate_market_overview(self, metal_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall market overview"""
        
        overview = {
            'market_sentiment': 'neutral',
            'trending_metals': {'bullish': [], 'bearish': []},
            'volatility_leaders': [],
            'best_performers': [],
            'worst_performers': []
        }
        
        # Analyze trends
        bullish_count = 0
        bearish_count = 0
        
        performance_data = []
        
        for metal, analysis in metal_analyses.items():
            if 'trend_analysis' in analysis:
                short_term = analysis['trend_analysis'].get('short_term', {})
                direction = short_term.get('direction', 'neutral')
                change_percent = short_term.get('change_percent', 0)
                
                if direction == 'bullish':
                    bullish_count += 1
                    overview['trending_metals']['bullish'].append({
                        'metal': metal,
                        'change_percent': change_percent
                    })
                elif direction == 'bearish':
                    bearish_count += 1
                    overview['trending_metals']['bearish'].append({
                        'metal': metal,
                        'change_percent': change_percent
                    })
                
                performance_data.append({
                    'metal': metal,
                    'change_percent': change_percent,
                    'volatility': analysis.get('volatility_analysis', {}).get('daily_volatility', 0)
                })
        
        # Overall market sentiment
        if bullish_count > bearish_count * 1.5:
            overview['market_sentiment'] = 'bullish'
        elif bearish_count > bullish_count * 1.5:
            overview['market_sentiment'] = 'bearish'
        
        # Sort performance data
        performance_data.sort(key=lambda x: x['change_percent'], reverse=True)
        overview['best_performers'] = performance_data[:3]
        overview['worst_performers'] = performance_data[-3:]
        
        # Volatility leaders
        volatility_sorted = sorted(performance_data, key=lambda x: x['volatility'], reverse=True)
        overview['volatility_leaders'] = volatility_sorted[:3]
        
        return overview
    
    async def _generate_portfolio_insights(self, metal_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate portfolio and investment insights"""
        
        insights = {
            'diversification_opportunities': [],
            'risk_reward_analysis': {},
            'sector_allocation_suggestions': {},
            'investment_themes': []
        }
        
        # Analyze risk-reward profiles
        risk_reward_data = []
        for metal, analysis in metal_analyses.items():
            volatility = analysis.get('volatility_analysis', {}).get('daily_volatility', 0)
            returns = analysis.get('trend_analysis', {}).get('short_term', {}).get('change_percent', 0)
            
            risk_reward_data.append({
                'metal': metal,
                'risk': volatility,
                'return': returns,
                'risk_adjusted_return': returns / volatility if volatility > 0 else 0
            })
        
        # Sort by risk-adjusted returns
        risk_reward_data.sort(key=lambda x: x['risk_adjusted_return'], reverse=True)
        insights['risk_reward_analysis']['best_risk_adjusted'] = risk_reward_data[:3]
        insights['risk_reward_analysis']['highest_risk'] = sorted(risk_reward_data, key=lambda x: x['risk'], reverse=True)[:3]
        
        return insights
    
    async def _generate_price_alerts(self, metal_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate price alerts based on analysis"""
        
        alerts = []
        
        for metal, analysis in metal_analyses.items():
            # High volatility alert
            volatility = analysis.get('volatility_analysis', {})
            if volatility.get('volatility_level') == 'high':
                alerts.append({
                    'type': 'high_volatility',
                    'metal': metal,
                    'severity': 'warning',
                    'message': f"{metal.title()} showing high volatility ({volatility.get('daily_volatility', 0):.1%})",
                    'recommendation': 'Monitor closely, consider position sizing'
                })
            
            # Strong trend alert
            trend = analysis.get('trend_analysis', {}).get('short_term', {})
            if trend.get('strength') == 'strong':
                alerts.append({
                    'type': 'strong_trend',
                    'metal': metal,
                    'severity': 'info',
                    'message': f"{metal.title()} showing strong {trend.get('direction', 'neutral')} trend ({trend.get('change_percent', 0):.1f}%)",
                    'recommendation': f"Consider {'buying' if trend.get('direction') == 'bullish' else 'selling'} opportunities"
                })
            
            # Support/resistance alert
            support_resistance = analysis.get('support_resistance', {})
            position = support_resistance.get('current_position')
            if position in ['near_support', 'near_resistance']:
                alerts.append({
                    'type': 'support_resistance',
                    'metal': metal,
                    'severity': 'info',
                    'message': f"{metal.title()} trading {position.replace('_', ' ')}",
                    'recommendation': f"Watch for {'bounce' if 'support' in position else 'breakout or rejection'}"
                })
        
        return alerts
    
    def _generate_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of price analysis"""
        
        summary = {
            'metals_analyzed': len(analysis_results['metal_analyses']),
            'market_sentiment': analysis_results.get('market_overview', {}).get('market_sentiment', 'neutral'),
            'total_alerts': len(analysis_results['alerts']),
            'alert_breakdown': {},
            'analysis_coverage': {}
        }
        
        # Count alert types
        for alert in analysis_results['alerts']:
            alert_type = alert['type']
            summary['alert_breakdown'][alert_type] = summary['alert_breakdown'].get(alert_type, 0) + 1
        
        # Analysis coverage
        successful_analyses = 0
        for metal, analysis in analysis_results['metal_analyses'].items():
            if 'error' not in analysis:
                successful_analyses += 1
        
        summary['analysis_coverage'] = {
            'successful_analyses': successful_analyses,
            'failed_analyses': len(analysis_results['metal_analyses']) - successful_analyses,
            'success_rate': (successful_analyses / len(analysis_results['metal_analyses']) * 100) if analysis_results['metal_analyses'] else 0
        }
        
        return summary
    
    async def _save_analysis_results(self, analysis_results: Dict[str, Any]):
        """Save price analysis results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comprehensive analysis
        analysis_file = self.analysis_results_dir / f"price_analysis_{timestamp}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Price analysis saved to: {analysis_file}")


# Convenience functions
async def analyze_metal_prices(days_back: int = 90) -> Dict[str, Any]:
    """Convenience function to analyze metal prices"""
    analyzer = PriceAnalyzer()
    return await analyzer.analyze_all_prices(days_back)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("📊 Price Analyzer - Metal Price Intelligence")
        print("=" * 60)
        
        analyzer = PriceAnalyzer()
        
        # Test price analysis
        print("\n🚀 Testing comprehensive price analysis...")
        results = await analyzer.analyze_all_prices(30)  # 30 days
        
        print(f"\n📊 PRICE ANALYSIS SUMMARY:")
        print(f"   Metals Analyzed: {results['summary']['metals_analyzed']}")
        print(f"   Market Sentiment: {results['summary']['market_sentiment'].title()}")
        print(f"   Total Alerts: {results['summary']['total_alerts']}")
        print(f"   Success Rate: {results['summary']['analysis_coverage']['success_rate']:.1f}%")
        
        # Show market overview
        market_overview = results.get('market_overview', {})
        if market_overview:
            print(f"\n🏆 MARKET OVERVIEW:")
            print(f"   Overall Sentiment: {market_overview.get('market_sentiment', 'neutral').title()}")
            
            best_performers = market_overview.get('best_performers', [])
            if best_performers:
                print(f"   Best Performer: {best_performers[0]['metal'].title()} (+{best_performers[0]['change_percent']:.2f}%)")
            
            worst_performers = market_overview.get('worst_performers', [])
            if worst_performers:
                print(f"   Worst Performer: {worst_performers[-1]['metal'].title()} ({worst_performers[-1]['change_percent']:.2f}%)")
        
        # Show alerts
        if results['alerts']:
            print(f"\n🚨 RECENT ALERTS:")
            for alert in results['alerts'][:5]:  # Show first 5 alerts
                print(f"   {alert['type'].replace('_', ' ').title()}: {alert['message']}")
    
    asyncio.run(main())