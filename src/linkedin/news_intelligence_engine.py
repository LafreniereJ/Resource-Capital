#!/usr/bin/env python3
"""
News Intelligence Engine
Processes RSS feeds and news sources for mining industry intelligence
"""

import sys
import os
sys.path.append('../')

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import re
import time
from urllib.parse import urlparse

from ..core.config import Config

@dataclass
class NewsItem:
    """News article data structure"""
    headline: str
    summary: str
    url: str
    source: str
    published: str
    priority: str = "medium"  # critical, high, medium, low
    category: str = "general"  # M&A, earnings, operational, regulatory, etc.
    companies: List[str] = None
    relevance_score: float = 0.0
    sentiment: str = "neutral"  # positive, negative, neutral
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.companies is None:
            self.companies = []
        if self.keywords is None:
            self.keywords = []
        
        # Auto-categorize if not set
        if self.category == "general":
            self.category = self._auto_categorize()
        
        # Calculate relevance score if not set
        if self.relevance_score == 0.0:
            self.relevance_score = self._calculate_relevance()
    
    def _auto_categorize(self) -> str:
        """Auto-categorize news based on headline and summary"""
        text = f"{self.headline} {self.summary}".lower()
        
        # M&A keywords
        if any(word in text for word in ["acquisition", "merger", "takeover", "bought", "acquired", "deal"]):
            return "M&A"
        
        # Earnings keywords
        if any(word in text for word in ["earnings", "quarterly", "revenue", "profit", "loss", "results"]):
            return "earnings"
        
        # Operational keywords
        if any(word in text for word in ["production", "mining", "exploration", "drilling", "discovery"]):
            return "operational"
        
        # Regulatory/Environmental
        if any(word in text for word in ["permit", "approval", "regulatory", "environmental", "government"]):
            return "regulatory"
        
        # Corporate changes
        if any(word in text for word in ["ceo", "management", "appointment", "resign", "board"]):
            return "corporate"
        
        return "general"
    
    def _calculate_relevance(self) -> float:
        """Calculate relevance score based on content"""
        score = 0.0
        text = f"{self.headline} {self.summary}".lower()
        
        # High-value keywords
        high_value_keywords = ["gold", "copper", "silver", "mining", "production", "acquisition", "merger"]
        score += sum(5 for keyword in high_value_keywords if keyword in text)
        
        # Canadian relevance
        canadian_keywords = ["canada", "canadian", "ontario", "quebec", "british columbia", "tsx", "tsxv"]
        score += sum(3 for keyword in canadian_keywords if keyword in text)
        
        # Company mentions (bonus for known companies)
        if self.companies:
            score += len(self.companies) * 2
        
        # Category bonuses
        category_bonus = {
            "M&A": 10,
            "earnings": 8,
            "operational": 6,
            "regulatory": 4,
            "corporate": 3
        }
        score += category_bonus.get(self.category, 1)
        
        return min(score, 100.0)  # Cap at 100

@dataclass
class NewsAnalysis:
    """Daily news analysis summary"""
    date: str
    total_articles: int
    critical_news: List[NewsItem]
    high_priority_news: List[NewsItem]
    ma_activity: List[NewsItem]
    earnings_updates: List[NewsItem]
    operational_news: List[NewsItem]
    sentiment_summary: Dict[str, int]
    top_companies_mentioned: List[Tuple[str, int]]
    trending_keywords: List[Tuple[str, int]]

class NewsIntelligenceEngine:
    """Processes news sources for mining industry intelligence"""
    
    def __init__(self):
        self.config = Config()
        
        # Free RSS feeds for mining news
        self.news_sources = {
            "Mining.com": "https://www.mining.com/feed/",
            "Mining Weekly": "https://www.miningweekly.com/rss/topic/mining",
            "Northern Miner": "https://www.northernminer.com/feed/",
            "Yahoo Finance - Mining": "https://feeds.finance.yahoo.com/rss/2.0/category-mining",
            "MarketWatch - Materials": "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
            "Globe and Mail - Mining": "https://www.theglobeandmail.com/investing/markets/inside-the-market/mining/rss/",
            "Financial Post - Energy": "https://financialpost.com/rss/category/commodities"
        }
        
        # Canadian mining companies for relevance scoring
        self.canadian_companies = self._load_company_names()
        
        # Keywords for categorization and filtering
        self.mining_keywords = {
            "metals": ["gold", "silver", "copper", "zinc", "nickel", "iron", "aluminum", "platinum"],
            "mining_terms": ["mining", "exploration", "production", "drilling", "ore", "deposit", "reserves"],
            "financial": ["earnings", "revenue", "profit", "loss", "dividend", "acquisition", "merger"],
            "operational": ["mill", "processing", "extraction", "development", "expansion", "closure"]
        }
    
    def _load_company_names(self) -> List[str]:
        """Load Canadian mining company names for entity recognition"""
        try:
            import pandas as pd
            
            tsx_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSX Canadian Companies'
            )
            tsxv_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSXV Canadian Companies'
            )
            
            # Extract company names
            companies = []
            for df in [tsx_df, tsxv_df]:
                if 'Name' in df.columns:
                    names = df['Name'].dropna().tolist()
                    companies.extend(names)
            
            # Clean company names (remove common suffixes)
            cleaned_companies = []
            for name in companies:
                cleaned = name.replace(' Corp.', '').replace(' Inc.', '').replace(' Ltd.', '').replace(' Limited', '')
                cleaned_companies.append(cleaned.strip())
            
            return list(set(cleaned_companies))  # Remove duplicates
            
        except Exception as e:
            print(f"Warning: Could not load company names: {e}")
            return []
    
    def fetch_rss_feed(self, source_name: str, feed_url: str, max_age_hours: int = 24) -> List[NewsItem]:
        """Fetch and parse RSS feed"""
        news_items = []
        
        try:
            # Add headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; MiningIntelligenceBot/1.0)'
            }
            
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                print(f"No entries found for {source_name}")
                return news_items
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for entry in feed.entries[:20]:  # Limit to recent articles
                try:
                    # Parse publication date
                    published = entry.get('published', '')
                    pub_date = None
                    
                    if published:
                        try:
                            pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')
                        except:
                            try:
                                pub_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z')
                            except:
                                pub_date = datetime.now()  # Default to now if parsing fails
                    
                    # Skip old articles
                    if pub_date and pub_date.replace(tzinfo=None) < cutoff_time:
                        continue
                    
                    # Extract content
                    headline = entry.get('title', '').strip()
                    summary = entry.get('summary', entry.get('description', '')).strip()
                    url = entry.get('link', '')
                    
                    # Clean HTML from summary
                    if summary:
                        summary = BeautifulSoup(summary, 'html.parser').get_text()
                        summary = ' '.join(summary.split())  # Normalize whitespace
                    
                    # Filter for mining relevance
                    if not self._is_mining_relevant(headline, summary):
                        continue
                    
                    # Detect mentioned companies
                    companies = self._extract_companies(headline + " " + summary)
                    
                    # Create news item
                    news_item = NewsItem(
                        headline=headline,
                        summary=summary[:300],  # Limit summary length
                        url=url,
                        source=source_name,
                        published=published,
                        companies=companies
                    )
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    continue  # Skip problematic entries
            
            print(f"✅ {source_name}: {len(news_items)} relevant articles")
            
        except Exception as e:
            print(f"❌ Error fetching {source_name}: {e}")
        
        return news_items
    
    def _is_mining_relevant(self, headline: str, summary: str) -> bool:
        """Check if article is relevant to mining industry"""
        text = f"{headline} {summary}".lower()
        
        # Must contain mining-related keywords
        mining_keywords = (
            self.mining_keywords["metals"] + 
            self.mining_keywords["mining_terms"] +
            ["commodity", "commodities", "resources", "tsx", "tsxv"]
        )
        
        has_mining_keyword = any(keyword in text for keyword in mining_keywords)
        
        # Additional Canadian relevance
        canadian_terms = ["canada", "canadian", "toronto", "vancouver", "tsx", "tsxv"]
        has_canadian_relevance = any(term in text for term in canadian_terms)
        
        return has_mining_keyword or has_canadian_relevance
    
    def _extract_companies(self, text: str) -> List[str]:
        """Extract Canadian mining company names from text"""
        mentioned_companies = []
        
        text_lower = text.lower()
        
        for company in self.canadian_companies[:100]:  # Check top 100 companies
            company_lower = company.lower()
            
            # Look for exact matches and common variations
            patterns = [
                company_lower,
                company_lower.replace(' ', ''),  # No spaces
                company_lower.split()[0] if ' ' in company_lower else company_lower  # First word only
            ]
            
            for pattern in patterns:
                if len(pattern) > 3 and pattern in text_lower:
                    mentioned_companies.append(company)
                    break
        
        return list(set(mentioned_companies))  # Remove duplicates
    
    def fetch_all_news(self, max_age_hours: int = 24) -> List[NewsItem]:
        """Fetch news from all configured sources"""
        all_news = []
        
        print("📰 Fetching news from all sources...")
        
        for source_name, feed_url in self.news_sources.items():
            news_items = self.fetch_rss_feed(source_name, feed_url, max_age_hours)
            all_news.extend(news_items)
            
            # Rate limiting
            time.sleep(1)
        
        print(f"📊 Total articles collected: {len(all_news)}")
        
        # Remove duplicates based on headline similarity
        unique_news = self._deduplicate_news(all_news)
        print(f"📊 Unique articles after deduplication: {len(unique_news)}")
        
        return unique_news
    
    def _deduplicate_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Remove duplicate news articles"""
        unique_news = []
        seen_headlines = set()
        
        for item in news_items:
            # Create a normalized headline for comparison
            normalized = re.sub(r'[^\w\s]', '', item.headline.lower())
            normalized = ' '.join(normalized.split())
            
            if normalized not in seen_headlines:
                seen_headlines.add(normalized)
                unique_news.append(item)
        
        return unique_news
    
    def prioritize_news(self, news_items: List[NewsItem]) -> NewsAnalysis:
        """Analyze and prioritize news for LinkedIn posting"""
        
        # Sort by relevance score
        news_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Categorize news by priority and type
        critical_news = [item for item in news_items if item.relevance_score >= 80]
        high_priority_news = [item for item in news_items if 60 <= item.relevance_score < 80]
        
        ma_activity = [item for item in news_items if item.category == "M&A"]
        earnings_updates = [item for item in news_items if item.category == "earnings"]
        operational_news = [item for item in news_items if item.category == "operational"]
        
        # Sentiment analysis (simple keyword-based)
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for item in news_items:
            sentiment = self._analyze_sentiment(item.headline + " " + item.summary)
            sentiment_counts[sentiment] += 1
            item.sentiment = sentiment
        
        # Company mention frequency
        company_mentions = {}
        for item in news_items:
            for company in item.companies:
                company_mentions[company] = company_mentions.get(company, 0) + 1
        
        top_companies = sorted(company_mentions.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Trending keywords
        keyword_counts = {}
        for item in news_items:
            text = f"{item.headline} {item.summary}".lower()
            for keyword_list in self.mining_keywords.values():
                for keyword in keyword_list:
                    if keyword in text:
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        trending_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return NewsAnalysis(
            date=datetime.now().strftime("%Y-%m-%d"),
            total_articles=len(news_items),
            critical_news=critical_news[:5],
            high_priority_news=high_priority_news[:10],
            ma_activity=ma_activity[:5],
            earnings_updates=earnings_updates[:5],
            operational_news=operational_news[:5],
            sentiment_summary=sentiment_counts,
            top_companies_mentioned=top_companies,
            trending_keywords=trending_keywords
        )
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis based on keywords"""
        text_lower = text.lower()
        
        positive_keywords = ["growth", "increase", "profit", "success", "expansion", "discovery", "breakthrough"]
        negative_keywords = ["decline", "loss", "drop", "fall", "concern", "risk", "challenge", "closure"]
        
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def format_news_for_linkedin(self, analysis: NewsAnalysis) -> str:
        """Format news analysis for LinkedIn posting"""
        lines = []
        
        # Header
        lines.append(f"📰 Mining News Intelligence - {analysis.date}")
        lines.append(f"Analyzed {analysis.total_articles} articles")
        
        # Critical/breaking news
        if analysis.critical_news:
            lines.append("\n🚨 BREAKING:")
            for item in analysis.critical_news[:2]:
                lines.append(f"• {item.headline[:80]}...")
        
        # M&A activity
        if analysis.ma_activity:
            lines.append("\n💼 M&A ACTIVITY:")
            for item in analysis.ma_activity[:2]:
                lines.append(f"• {item.headline[:80]}...")
        
        # Market sentiment
        total_sentiment = sum(analysis.sentiment_summary.values())
        if total_sentiment > 0:
            positive_pct = (analysis.sentiment_summary["positive"] / total_sentiment) * 100
            lines.append(f"\n📊 Sentiment: {positive_pct:.0f}% positive")
        
        # Top companies
        if analysis.top_companies_mentioned:
            top_3_companies = analysis.top_companies_mentioned[:3]
            companies_str = ", ".join([f"{comp}" for comp, count in top_3_companies])
            lines.append(f"\n🏢 Most Mentioned: {companies_str}")
        
        return "\n".join(lines)
    
    def save_news_analysis(self, analysis: NewsAnalysis) -> str:
        """Save news analysis to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/processed/news_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(asdict(analysis), f, indent=2, default=str)
        
        return filename

def main():
    """Test the news intelligence engine"""
    print("📰 News Intelligence Engine - Mining Industry")
    print("=" * 50)
    
    engine = NewsIntelligenceEngine()
    
    print("🔄 Fetching news from RSS sources...")
    news_items = engine.fetch_all_news(max_age_hours=48)  # 2 days for testing
    
    if not news_items:
        print("❌ No news articles found")
        return
    
    print("🧠 Analyzing news intelligence...")
    analysis = engine.prioritize_news(news_items)
    
    print("\n📊 NEWS ANALYSIS SUMMARY:")
    print(f"• Total Articles: {analysis.total_articles}")
    print(f"• Critical News: {len(analysis.critical_news)}")
    print(f"• M&A Activity: {len(analysis.ma_activity)}")
    print(f"• Earnings Updates: {len(analysis.earnings_updates)}")
    
    # Show top headlines
    if analysis.critical_news:
        print("\n🚨 CRITICAL NEWS:")
        for item in analysis.critical_news[:3]:
            print(f"  • {item.headline}")
            print(f"    Score: {item.relevance_score:.1f} | {item.source}")
    
    if analysis.ma_activity:
        print("\n💼 M&A ACTIVITY:")
        for item in analysis.ma_activity[:2]:
            print(f"  • {item.headline}")
    
    # Show sentiment
    print(f"\n😊 SENTIMENT ANALYSIS:")
    for sentiment, count in analysis.sentiment_summary.items():
        print(f"  • {sentiment.title()}: {count} articles")
    
    # LinkedIn format
    print("\n📱 LINKEDIN FORMAT:")
    print("=" * 40)
    linkedin_text = engine.format_news_for_linkedin(analysis)
    print(linkedin_text)
    print("=" * 40)
    
    # Save results
    filename = engine.save_news_analysis(analysis)
    print(f"\n💾 Analysis saved to: {filename}")

if __name__ == "__main__":
    main()