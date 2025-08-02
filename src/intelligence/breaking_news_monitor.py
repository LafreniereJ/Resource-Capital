#!/usr/bin/env python3
"""
Breaking News Monitor
Real-time detection and prioritization of market-moving mining industry news
"""

import asyncio
import aiohttp
import feedparser
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import hashlib

@dataclass
class BreakingNewsEvent:
    """Breaking news event data structure"""
    id: str
    headline: str
    summary: str
    url: str
    source: str
    published: datetime
    priority_score: float = 0.0
    event_type: str = "general"  # policy, market_move, corporate, regulatory
    impact_level: str = "medium"  # critical, high, medium, low
    canadian_relevance: float = 0.0
    commodity_impact: Dict[str, float] = None
    companies_affected: List[str] = None
    keywords: List[str] = None
    sentiment: str = "neutral"
    
    def __post_init__(self):
        if self.commodity_impact is None:
            self.commodity_impact = {}
        if self.companies_affected is None:
            self.companies_affected = []
        if self.keywords is None:
            self.keywords = []
        
        # Generate unique ID if not provided
        if not self.id:
            content_hash = hashlib.md5(f"{self.headline}{self.url}".encode()).hexdigest()
            self.id = f"news_{content_hash[:12]}"

class BreakingNewsMonitor:
    """Real-time breaking news monitoring system"""
    
    def __init__(self, db_path: str = "data/databases/mining_intelligence.db"):
        self.db_path = db_path
        self.setup_database()
        
        # Real-time news sources
        self.news_sources = {
            # Major Financial News
            "bloomberg_mining": {
                "url": "https://www.bloomberg.com/feeds/mining",
                "rss": "https://feeds.bloomberg.com/markets/news.rss",
                "type": "rss",
                "priority_weight": 1.0
            },
            "reuters_commodities": {
                "url": "https://www.reuters.com/business/commodities/",
                "rss": "https://feeds.reuters.com/reuters/businessNews",
                "type": "rss",
                "priority_weight": 1.0
            },
            "financial_post": {
                "url": "https://financialpost.com/commodities",
                "rss": "https://financialpost.com/feed/",
                "type": "rss",
                "priority_weight": 0.9
            },
            "globe_mail": {
                "url": "https://www.theglobeandmail.com/business/",
                "rss": "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
                "type": "rss",
                "priority_weight": 0.8
            },
            
            # Mining-Specific Sources
            "mining_com": {
                "url": "https://www.mining.com",
                "rss": "https://www.mining.com/feed/",
                "type": "rss",
                "priority_weight": 0.9
            },
            "northern_miner": {
                "url": "https://www.northernminer.com",
                "rss": "https://www.northernminer.com/feed/",
                "type": "rss",
                "priority_weight": 0.9
            },
            "kitco_news": {
                "url": "https://www.kitco.com/news/",
                "rss": "https://www.kitco.com/rss/KitcoNews.xml",
                "type": "rss",
                "priority_weight": 0.8
            },
            
            # Government & Policy
            "gov_canada": {
                "url": "https://www.canada.ca/en/services/business/trade.html",
                "type": "web",
                "priority_weight": 1.0
            },
            "whitehouse": {
                "url": "https://www.whitehouse.gov/news/",
                "type": "web", 
                "priority_weight": 1.0
            }
        }
        
        # Priority keywords for breaking news detection
        self.priority_keywords = {
            # Policy & Regulatory (Highest Priority)
            "policy_critical": {
                "keywords": ["tariff", "trade war", "sanctions", "embargo", "ban", "restriction"],
                "score": 100,
                "requires_context": ["mining", "commodity", "metal", "copper", "gold", "silver"]
            },
            "regulatory_critical": {
                "keywords": ["emergency", "national security", "government action", "federal", "policy change"],
                "score": 90,
                "requires_context": ["mining", "commodity", "resource"]
            },
            
            # Market Movements (High Priority)
            "price_critical": {
                "keywords": ["plunge", "surge", "crash", "rally", "spike", "collapse"],
                "score": 85,
                "requires_context": ["copper", "gold", "silver", "platinum", "uranium", "mining"]
            },
            "volatility_high": {
                "keywords": ["volatile", "dramatic", "historic", "record", "unprecedented"],
                "score": 75,
                "requires_context": ["price", "trading", "market"]
            },
            
            # Corporate Events (Medium-High Priority)
            "ma_activity": {
                "keywords": ["acquisition", "merger", "takeover", "buyout", "deal"],
                "score": 70,
                "requires_context": ["mining", "canadian"]
            },
            "earnings_critical": {
                "keywords": ["earnings miss", "guidance cut", "surprise", "beat expectations"],
                "score": 65,
                "requires_context": ["mining", "canadian"]
            },
            
            # Operational (Medium Priority)
            "operational_significant": {
                "keywords": ["production halt", "mine closure", "strike", "accident", "discovery"],
                "score": 60,
                "requires_context": ["mining", "canadian"]
            }
        }
        
        # Canadian mining companies for relevance scoring
        self.canadian_companies = [
            "barrick gold", "agnico eagle", "kinross", "first quantum", "lundin mining",
            "hudbay minerals", "teck resources", "franco nevada", "eldorado gold",
            "centerra gold", "iamgold", "osisko", "yamana", "b2gold", "torex gold",
            "seabridge gold", "alamos gold", "kirkland lake", "detour gold",
            "magna mining", "calibre mining", "endeavour mining", "pretium resources"
        ]
        
        # Commodity mappings for impact assessment
        self.commodity_keywords = {
            "copper": ["copper", "cu", "red metal", "industrial metal"],
            "gold": ["gold", "au", "yellow metal", "precious metal"],
            "silver": ["silver", "ag", "white metal"],
            "platinum": ["platinum", "pt", "pgm"],
            "uranium": ["uranium", "u3o8", "nuclear"],
            "iron_ore": ["iron ore", "iron", "steel"],
            "nickel": ["nickel", "ni"],
            "zinc": ["zinc", "zn"],
            "oil": ["oil", "crude", "petroleum", "wti", "brent"],
            "natural_gas": ["natural gas", "lng", "gas"]
        }
    
    def setup_database(self):
        """Setup database for breaking news storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breaking_news (
                id TEXT PRIMARY KEY,
                headline TEXT NOT NULL,
                summary TEXT,
                url TEXT,
                source TEXT,
                published TIMESTAMP,
                priority_score REAL,
                event_type TEXT,
                impact_level TEXT,
                canadian_relevance REAL,
                commodity_impact TEXT,
                companies_affected TEXT,
                keywords TEXT,
                sentiment TEXT,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Index for efficient querying
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority_score ON breaking_news (priority_score DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_published ON breaking_news (published DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed ON breaking_news (processed)')
        
        conn.commit()
        conn.close()
    
    async def monitor_all_sources(self, hours_back: int = 2) -> List[BreakingNewsEvent]:
        """Monitor all news sources for breaking news"""
        print(f"🚨 Monitoring breaking news from {len(self.news_sources)} sources...")
        
        all_events = []
        tasks = []
        
        async with aiohttp.ClientSession() as session:
            for source_name, source_config in self.news_sources.items():
                if source_config["type"] == "rss":
                    task = self.monitor_rss_source(session, source_name, source_config, hours_back)
                    tasks.append(task)
        
        # Execute all monitoring tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                print(f"⚠️ Monitoring error: {result}")
        
        # Sort by priority score and filter for high-priority events
        breaking_events = [event for event in all_events if event.priority_score >= 50.0]
        breaking_events.sort(key=lambda x: x.priority_score, reverse=True)
        
        print(f"🎯 Found {len(breaking_events)} high-priority events")
        
        # Save to database
        if breaking_events:
            self.save_breaking_news(breaking_events)
        
        return breaking_events
    
    async def monitor_rss_source(self, session: aiohttp.ClientSession, 
                                source_name: str, source_config: Dict,
                                hours_back: int) -> List[BreakingNewsEvent]:
        """Monitor single RSS source for breaking news"""
        events = []
        
        try:
            rss_url = source_config["rss"]
            print(f"📡 Scanning {source_name}...")
            
            async with session.get(rss_url, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    cutoff_time = datetime.now() - timedelta(hours=hours_back)
                    
                    for entry in feed.entries[:20]:  # Limit to recent entries
                        try:
                            # Parse publication date
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                            else:
                                pub_date = datetime.now()
                            
                            # Skip old news
                            if pub_date < cutoff_time:
                                continue
                            
                            # Extract content
                            headline = entry.get('title', '')
                            summary = entry.get('summary', '')
                            url = entry.get('link', '')
                            
                            # Create event and analyze priority
                            event = BreakingNewsEvent(
                                id="",
                                headline=headline,
                                summary=summary,
                                url=url,
                                source=source_name,
                                published=pub_date
                            )
                            
                            # Analyze priority and relevance
                            self.analyze_event_priority(event, source_config["priority_weight"])
                            
                            # Only keep events with decent priority scores
                            if event.priority_score >= 30.0:
                                events.append(event)
                        
                        except Exception as e:
                            print(f"⚠️ Error processing entry from {source_name}: {e}")
                            continue
                
        except Exception as e:
            print(f"❌ Error monitoring {source_name}: {e}")
        
        return events
    
    def analyze_event_priority(self, event: BreakingNewsEvent, source_weight: float):
        """Analyze event priority and set all relevant fields"""
        text = f"{event.headline} {event.summary}".lower()
        
        priority_score = 0.0
        keywords_found = []
        event_types = []
        
        # Check priority keywords
        for category, config in self.priority_keywords.items():
            category_score = 0
            category_keywords = []
            
            # Check for main keywords
            for keyword in config["keywords"]:
                if keyword.lower() in text:
                    category_score += config["score"]
                    category_keywords.append(keyword)
            
            # Check for required context
            if category_score > 0 and "requires_context" in config:
                context_found = any(ctx.lower() in text for ctx in config["requires_context"])
                if context_found:
                    priority_score += category_score
                    keywords_found.extend(category_keywords)
                    event_types.append(category.split('_')[0])
        
        # Canadian relevance scoring
        canadian_score = 0.0
        canadian_keywords = ["canada", "canadian", "tsx", "tsxv", "ontario", "quebec", "british columbia"]
        for keyword in canadian_keywords:
            if keyword in text:
                canadian_score += 10.0
        
        # Company relevance
        companies_mentioned = []
        for company in self.canadian_companies:
            if company.lower() in text:
                canadian_score += 15.0
                companies_mentioned.append(company)
        
        # Commodity impact analysis
        commodity_impacts = {}
        for commodity, terms in self.commodity_keywords.items():
            impact_score = 0.0
            for term in terms:
                if term.lower() in text:
                    impact_score += 5.0
            
            # Boost score for price-related news
            if any(word in text for word in ["price", "cost", "trading", "market"]):
                impact_score *= 1.5
            
            if impact_score > 0:
                commodity_impacts[commodity] = min(impact_score, 50.0)
        
        # Sentiment analysis (basic)
        sentiment = "neutral"
        negative_words = ["plunge", "crash", "decline", "fall", "drop", "loss", "concern", "worry"]
        positive_words = ["surge", "rally", "gain", "rise", "boost", "strong", "positive", "growth"]
        
        neg_count = sum(1 for word in negative_words if word in text)
        pos_count = sum(1 for word in positive_words if word in text)
        
        if neg_count > pos_count:
            sentiment = "negative"
        elif pos_count > neg_count:
            sentiment = "positive"
        
        # Apply source weight
        priority_score *= source_weight
        
        # Determine impact level
        if priority_score >= 80:
            impact_level = "critical"
        elif priority_score >= 60:
            impact_level = "high"
        elif priority_score >= 40:
            impact_level = "medium"
        else:
            impact_level = "low"
        
        # Determine event type
        if "policy" in event_types or "regulatory" in event_types:
            event_type = "policy"
        elif "price" in event_types or "volatility" in event_types:
            event_type = "market_move"
        elif "ma" in event_types or "earnings" in event_types:
            event_type = "corporate"
        else:
            event_type = "general"
        
        # Update event object
        event.priority_score = round(priority_score, 1)
        event.event_type = event_type
        event.impact_level = impact_level
        event.canadian_relevance = round(canadian_score, 1)
        event.commodity_impact = commodity_impacts
        event.companies_affected = companies_mentioned
        event.keywords = keywords_found
        event.sentiment = sentiment
    
    def save_breaking_news(self, events: List[BreakingNewsEvent]):
        """Save breaking news events to database"""
        if not events:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for event in events:
            # Convert complex fields to JSON
            commodity_impact_json = json.dumps(event.commodity_impact)
            companies_json = json.dumps(event.companies_affected)
            keywords_json = json.dumps(event.keywords)
            
            cursor.execute('''
                INSERT OR REPLACE INTO breaking_news 
                (id, headline, summary, url, source, published, priority_score, 
                 event_type, impact_level, canadian_relevance, commodity_impact,
                 companies_affected, keywords, sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.id, event.headline, event.summary, event.url, event.source,
                event.published, event.priority_score, event.event_type,
                event.impact_level, event.canadian_relevance, commodity_impact_json,
                companies_json, keywords_json, event.sentiment
            ))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Saved {len(events)} breaking news events to database")
    
    def get_recent_breaking_news(self, hours_back: int = 24, min_priority: float = 50.0) -> List[BreakingNewsEvent]:
        """Get recent high-priority breaking news"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        cursor.execute('''
            SELECT * FROM breaking_news 
            WHERE published >= ? AND priority_score >= ?
            ORDER BY priority_score DESC, published DESC
        ''', (cutoff_time, min_priority))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            # Parse JSON fields
            commodity_impact = json.loads(row[10]) if row[10] else {}
            companies_affected = json.loads(row[11]) if row[11] else []
            keywords = json.loads(row[12]) if row[12] else []
            
            event = BreakingNewsEvent(
                id=row[0],
                headline=row[1],
                summary=row[2],
                url=row[3],
                source=row[4],
                published=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                priority_score=row[6],
                event_type=row[7],
                impact_level=row[8],
                canadian_relevance=row[9],
                commodity_impact=commodity_impact,
                companies_affected=companies_affected,
                keywords=keywords,
                sentiment=row[13]
            )
            events.append(event)
        
        return events
    
    async def generate_breaking_news_summary(self, hours_back: int = 24) -> Dict:
        """Generate summary of recent breaking news for reports"""
        events = await self.monitor_all_sources(hours_back=hours_back)
        recent_events = self.get_recent_breaking_news(hours_back=hours_back)
        
        # Combine new and stored events
        all_events = {event.id: event for event in events + recent_events}.values()
        all_events = sorted(all_events, key=lambda x: x.priority_score, reverse=True)
        
        summary = {
            "total_events": len(all_events),
            "critical_events": [e for e in all_events if e.impact_level == "critical"],
            "high_priority_events": [e for e in all_events if e.impact_level == "high"],
            "policy_events": [e for e in all_events if e.event_type == "policy"],
            "market_events": [e for e in all_events if e.event_type == "market_move"],
            "corporate_events": [e for e in all_events if e.event_type == "corporate"],
            "canadian_relevant": [e for e in all_events if e.canadian_relevance >= 50.0],
            "commodity_impacts": {},
            "top_events": all_events[:10]
        }
        
        # Aggregate commodity impacts
        for event in all_events:
            for commodity, impact in event.commodity_impact.items():
                if commodity not in summary["commodity_impacts"]:
                    summary["commodity_impacts"][commodity] = []
                summary["commodity_impacts"][commodity].append({
                    "event": event.headline,
                    "impact": impact,
                    "priority": event.priority_score
                })
        
        return summary

async def main():
    """Test the breaking news monitor"""
    print("🚨 Breaking News Monitor Test")
    print("=" * 60)
    
    monitor = BreakingNewsMonitor()
    
    # Monitor for breaking news
    events = await monitor.monitor_all_sources(hours_back=6)
    
    if events:
        print(f"\n✅ Found {len(events)} high-priority events:")
        
        for i, event in enumerate(events[:5], 1):
            print(f"\n{i}. [{event.impact_level.upper()}] {event.headline}")
            print(f"   Source: {event.source}")
            print(f"   Priority: {event.priority_score:.1f}")
            print(f"   Canadian Relevance: {event.canadian_relevance:.1f}")
            print(f"   Type: {event.event_type}")
            print(f"   Keywords: {', '.join(event.keywords[:5])}")
            if event.commodity_impact:
                impacts = [f"{k}: {v:.1f}" for k, v in event.commodity_impact.items()]
                print(f"   Commodity Impact: {', '.join(impacts)}")
            print(f"   URL: {event.url[:80]}...")
    
    else:
        print("ℹ️ No high-priority breaking news found in recent hours")
    
    # Generate summary
    summary = await monitor.generate_breaking_news_summary(hours_back=24)
    
    print(f"\n📊 24-Hour Summary:")
    print(f"📰 Total Events: {summary['total_events']}")
    print(f"🚨 Critical: {len(summary['critical_events'])}")
    print(f"⚡ High Priority: {len(summary['high_priority_events'])}")
    print(f"🇨🇦 Canadian Relevant: {len(summary['canadian_relevant'])}")
    print(f"🏛️ Policy Events: {len(summary['policy_events'])}")
    print(f"📈 Market Events: {len(summary['market_events'])}")

if __name__ == "__main__":
    asyncio.run(main())