#!/usr/bin/env python3
"""
Scraper Intelligence System
Learns which scrapers work best for each website over time
Persists learning data and optimizes scraper selection
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ScraperAttempt:
    """Record of a scraper attempt"""
    url: str
    domain: str
    scraper_used: str
    success: bool
    response_time: float
    content_length: int
    error_message: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class DomainStats:
    """Statistics for a domain"""
    domain: str
    total_attempts: int
    successful_attempts: int
    avg_response_time: float
    success_rate: float
    best_scraper: str
    scraper_performance: Dict[str, Dict[str, float]]

class ScraperIntelligence:
    """Intelligent system that learns scraper performance over time"""
    
    def __init__(self, db_path: str = "data/databases/scraper_intelligence.db"):
        self.db_path = db_path
        self.setup_database()
        
        # In-memory cache for quick access
        self.domain_cache = {}
        self.last_cache_update = None
        self.cache_ttl = timedelta(minutes=30)
        
    def setup_database(self):
        """Initialize the intelligence database"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraper_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                domain TEXT NOT NULL,
                scraper_used TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                response_time REAL NOT NULL,
                content_length INTEGER NOT NULL,
                error_message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domain_preferences (
                domain TEXT PRIMARY KEY,
                preferred_scraper TEXT NOT NULL,
                fallback_order TEXT NOT NULL,
                success_rate REAL NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_domain ON scraper_attempts(domain)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON scraper_attempts(timestamp)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Scraper intelligence database initialized at {self.db_path}")
    
    def record_attempt(self, attempt: ScraperAttempt):
        """Record a scraper attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scraper_attempts 
            (url, domain, scraper_used, success, response_time, content_length, error_message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            attempt.url,
            attempt.domain,
            attempt.scraper_used,
            attempt.success,
            attempt.response_time,
            attempt.content_length,
            attempt.error_message,
            attempt.timestamp
        ))
        
        conn.commit()
        conn.close()
        
        # Update cache
        self._update_domain_cache(attempt.domain)
        
        logger.debug(f"Recorded attempt: {attempt.scraper_used} on {attempt.domain} - {'SUCCESS' if attempt.success else 'FAILED'}")
    
    def get_optimal_scraper_order(self, url: str, default_order: List[str] = None) -> List[str]:
        """Get optimal scraper order based on learning"""
        domain = urlparse(url).netloc
        
        # Get domain stats
        stats = self._get_domain_stats(domain)
        
        if not stats or stats.total_attempts < 3:
            # Not enough data, use default order
            if default_order:
                return default_order
            return ['crawl4ai', 'requests', 'playwright', 'selenium']
        
        # Sort scrapers by success rate and response time
        scraper_scores = []
        
        for scraper, perf in stats.scraper_performance.items():
            if perf['attempts'] > 0:
                # Score combines success rate and speed (lower response time is better)
                speed_score = 1 / max(perf['avg_response_time'], 0.1)  # Avoid division by zero
                combined_score = (perf['success_rate'] * 0.7) + (speed_score * 0.3)
                
                scraper_scores.append((scraper, combined_score, perf['success_rate']))
        
        # Sort by combined score (higher is better)
        scraper_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Extract scraper names in optimal order
        optimal_order = [scraper for scraper, _, success_rate in scraper_scores if success_rate > 0]
        
        # Add any missing scrapers from default order
        if default_order:
            for scraper in default_order:
                if scraper not in optimal_order:
                    optimal_order.append(scraper)
        
        logger.info(f"Optimal scraper order for {domain}: {optimal_order}")
        return optimal_order
    
    def get_domain_insights(self, domain: str) -> Optional[DomainStats]:
        """Get detailed insights for a domain"""
        return self._get_domain_stats(domain)
    
    def _get_domain_stats(self, domain: str) -> Optional[DomainStats]:
        """Get cached or computed domain statistics"""
        # Check cache first
        if (domain in self.domain_cache and 
            self.last_cache_update and 
            datetime.now() - self.last_cache_update < self.cache_ttl):
            return self.domain_cache[domain]
        
        # Compute fresh stats
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get overall stats for domain (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        cursor.execute('''
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_attempts,
                AVG(response_time) as avg_response_time
            FROM scraper_attempts 
            WHERE domain = ? AND timestamp > ?
        ''', (domain, thirty_days_ago))
        
        row = cursor.fetchone()
        if not row or row[0] == 0:
            conn.close()
            return None
        
        total_attempts, successful_attempts, avg_response_time = row
        success_rate = (successful_attempts / total_attempts) * 100 if total_attempts > 0 else 0
        
        # Get performance by scraper
        cursor.execute('''
            SELECT 
                scraper_used,
                COUNT(*) as attempts,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                AVG(response_time) as avg_time
            FROM scraper_attempts 
            WHERE domain = ? AND timestamp > ?
            GROUP BY scraper_used
        ''', (domain, thirty_days_ago))
        
        scraper_performance = {}
        best_scraper = None
        best_score = 0
        
        for row in cursor.fetchall():
            scraper, attempts, successes, avg_time = row
            scraper_success_rate = (successes / attempts) * 100 if attempts > 0 else 0
            
            scraper_performance[scraper] = {
                'attempts': attempts,
                'successes': successes,
                'success_rate': scraper_success_rate,
                'avg_response_time': avg_time or 0.0
            }
            
            # Determine best scraper (success rate is most important)
            if scraper_success_rate > best_score:
                best_score = scraper_success_rate
                best_scraper = scraper
        
        conn.close()
        
        stats = DomainStats(
            domain=domain,
            total_attempts=total_attempts,
            successful_attempts=successful_attempts,
            avg_response_time=avg_response_time or 0.0,
            success_rate=success_rate,
            best_scraper=best_scraper or 'crawl4ai',
            scraper_performance=scraper_performance
        )
        
        # Update cache
        self.domain_cache[domain] = stats
        self.last_cache_update = datetime.now()
        
        return stats
    
    def _update_domain_cache(self, domain: str):
        """Update cache for specific domain"""
        self.domain_cache[domain] = self._get_domain_stats(domain)
    
    def get_intelligence_report(self, days: int = 30) -> Dict[str, any]:
        """Generate intelligence report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Overall statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_attempts,
                COUNT(DISTINCT domain) as unique_domains,
                AVG(response_time) as avg_response_time
            FROM scraper_attempts 
            WHERE timestamp > ?
        ''', (cutoff_date,))
        
        overall_stats = cursor.fetchone()
        
        # Scraper performance
        cursor.execute('''
            SELECT 
                scraper_used,
                COUNT(*) as attempts,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                AVG(response_time) as avg_time
            FROM scraper_attempts 
            WHERE timestamp > ?
            GROUP BY scraper_used
            ORDER BY successes DESC
        ''', (cutoff_date,))
        
        scraper_stats = {}
        for row in cursor.fetchall():
            scraper, attempts, successes, avg_time = row
            success_rate = (successes / attempts) * 100 if attempts > 0 else 0
            
            scraper_stats[scraper] = {
                'attempts': attempts,
                'successes': successes,
                'success_rate': round(success_rate, 1),
                'avg_response_time': round(avg_time or 0.0, 2)
            }
        
        # Top performing domains
        cursor.execute('''
            SELECT 
                domain,
                COUNT(*) as attempts,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
            FROM scraper_attempts 
            WHERE timestamp > ?
            GROUP BY domain
            HAVING attempts >= 5
            ORDER BY successes DESC
            LIMIT 10
        ''', (cutoff_date,))
        
        top_domains = []
        for row in cursor.fetchall():
            domain, attempts, successes = row
            success_rate = (successes / attempts) * 100 if attempts > 0 else 0
            top_domains.append({
                'domain': domain,
                'attempts': attempts,
                'successes': successes,
                'success_rate': round(success_rate, 1)
            })
        
        conn.close()
        
        total_attempts, successful_attempts, unique_domains, avg_response_time = overall_stats
        overall_success_rate = (successful_attempts / total_attempts) * 100 if total_attempts > 0 else 0
        
        return {
            'period_days': days,
            'overall': {
                'total_attempts': total_attempts,
                'successful_attempts': successful_attempts,
                'success_rate': round(overall_success_rate, 1),
                'unique_domains': unique_domains,
                'avg_response_time': round(avg_response_time or 0.0, 2)
            },
            'scrapers': scraper_stats,
            'top_domains': top_domains,
            'generated_at': datetime.now().isoformat()
        }
    
    def export_learning_data(self, filepath: str):
        """Export learning data to JSON file"""
        report = self.get_intelligence_report(days=90)  # 3 months of data
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Learning data exported to {filepath}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old learning data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cursor.execute('DELETE FROM scraper_attempts WHERE timestamp < ?', (cutoff_date,))
        deleted_rows = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        # Clear cache to force refresh
        self.domain_cache.clear()
        self.last_cache_update = None
        
        logger.info(f"Cleaned up {deleted_rows} old scraper attempts")
        
        return deleted_rows

# Convenience functions
def record_scraper_attempt(url: str, scraper_used: str, success: bool, 
                          response_time: float, content_length: int, 
                          error_message: str = "", 
                          intelligence: ScraperIntelligence = None) -> None:
    """Convenience function to record a scraper attempt"""
    
    if intelligence is None:
        intelligence = ScraperIntelligence()
    
    domain = urlparse(url).netloc
    
    attempt = ScraperAttempt(
        url=url,
        domain=domain,
        scraper_used=scraper_used,
        success=success,
        response_time=response_time,
        content_length=content_length,
        error_message=error_message
    )
    
    intelligence.record_attempt(attempt)

def get_smart_scraper_order(url: str, default_order: List[str] = None, 
                           intelligence: ScraperIntelligence = None) -> List[str]:
    """Get smart scraper order based on learning"""
    
    if intelligence is None:
        intelligence = ScraperIntelligence()
    
    return intelligence.get_optimal_scraper_order(url, default_order)

# Example usage
if __name__ == "__main__":
    # Test the intelligence system
    intelligence = ScraperIntelligence()
    
    # Simulate some attempts
    test_urls = [
        "https://www.northernminer.com/news/",
        "https://www.mining.com/feed/",
        "https://tradingeconomics.com/commodities"
    ]
    
    for url in test_urls:
        # Simulate crawl4ai working well
        record_scraper_attempt(url, "crawl4ai", True, 1.2, 25000, intelligence=intelligence)
        
        # Simulate requests sometimes failing
        record_scraper_attempt(url, "requests", False, 0.8, 0, "HTTP 403", intelligence=intelligence)
        record_scraper_attempt(url, "requests", True, 0.9, 15000, intelligence=intelligence)
        
        # Show optimal order
        optimal_order = intelligence.get_optimal_scraper_order(url)
        print(f"{url} optimal order: {optimal_order}")
    
    # Generate report
    report = intelligence.get_intelligence_report()
    print(f"\nIntelligence Report:")
    print(f"Overall success rate: {report['overall']['success_rate']}%")
    print(f"Scraper performance: {report['scrapers']}")