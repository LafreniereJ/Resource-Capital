#!/usr/bin/env python3
"""
Scraper Configuration Manager
Loads and validates scraper target configurations
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScraperTarget:
    """Individual scraper target configuration"""

    name: str
    base_url: str
    priority: str
    enabled: bool
    target_pages: List[Dict[str, Any]]
    keywords: Dict[str, List[str]]
    rate_limit: float
    headers: Optional[Dict[str, str]] = None
    api_endpoints: Optional[List[Dict[str, Any]]] = None
    scraper_strategy: Optional[Dict[str, Any]] = None


@dataclass
class GlobalSettings:
    """Global scraper settings"""

    rate_limit_delay: float
    max_retries: int
    timeout_seconds: int
    user_agent: str
    respect_robots_txt: bool
    enable_logging: bool
    primary_scraper: str = "crawl4ai"
    fallback_scrapers: List[str] = None
    min_content_length: int = 100

    def __post_init__(self):
        if self.fallback_scrapers is None:
            self.fallback_scrapers = ["requests", "playwright", "selenium"]


class ScraperConfigManager:
    """Manages scraper configuration loading and validation"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config",
                "scraper_targets.json",
            )
        self.config_path = config_path
        self.config = None
        self.global_settings = None
        self.targets = {}

    def load_config(self) -> bool:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            # Validate basic structure
            if not self._validate_config():
                logger.error("Configuration validation failed")
                return False

            # Load global settings
            self.global_settings = GlobalSettings(**self.config["global_settings"])

            # Load targets by category
            self._load_targets()

            logger.info(
                f"Loaded {len(self.targets)} scraper targets from {self.config_path}"
            )
            return True

        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False

    def _validate_config(self) -> bool:
        """Validate configuration structure"""
        required_sections = [
            "global_settings",
            "categories",
            "websites",
            "extraction_rules",
        ]

        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required section: {section}")
                return False

        # Validate global settings
        required_global = [
            "rate_limit_delay",
            "max_retries",
            "timeout_seconds",
            "user_agent",
        ]
        for setting in required_global:
            if setting not in self.config["global_settings"]:
                logger.error(f"Missing global setting: {setting}")
                return False

        return True

    def _load_targets(self):
        """Load all scraper targets from configuration"""
        websites = self.config["websites"]

        for category, sites in websites.items():
            for site_config in sites:
                try:
                    target = ScraperTarget(
                        name=site_config["name"],
                        base_url=site_config["base_url"],
                        priority=site_config["priority"],
                        enabled=site_config.get("enabled", True),
                        target_pages=site_config.get("target_pages", []),
                        keywords=site_config.get("keywords", {}),
                        rate_limit=site_config.get(
                            "rate_limit", self.global_settings.rate_limit_delay
                        ),
                        headers=site_config.get("headers"),
                        api_endpoints=site_config.get("api_endpoints"),
                        scraper_strategy=site_config.get("scraper_strategy"),
                    )

                    self.targets[site_config["name"]] = target

                except KeyError as e:
                    logger.warning(
                        f"Invalid target configuration for {site_config.get('name', 'unknown')}: missing {e}"
                    )
                    continue

    def get_enabled_targets(
        self, category: str = None, priority: str = None
    ) -> List[ScraperTarget]:
        """Get enabled targets, optionally filtered by category or priority"""
        targets = [target for target in self.targets.values() if target.enabled]

        if priority:
            targets = [target for target in targets if target.priority == priority]

        if category:
            # Filter by category based on the configuration
            category_sites = []
            if category in self.config["websites"]:
                site_names = [
                    site["name"] for site in self.config["websites"][category]
                ]
                targets = [target for target in targets if target.name in site_names]

        return targets

    def get_target_by_name(self, name: str) -> Optional[ScraperTarget]:
        """Get specific target by name"""
        return self.targets.get(name)

    def get_keywords(self, keyword_type: str = None) -> List[str]:
        """Get extraction keywords by type"""
        extraction_rules = self.config.get("extraction_rules", {})

        if keyword_type:
            return extraction_rules.get(keyword_type, [])

        # Return all keywords combined without duplicates
        return list(
            {
                kw
                for kws in extraction_rules.values()
                if isinstance(kws, list)
                for kw in kws
            }
        )

    def get_blacklist(self) -> Dict[str, List[str]]:
        """Get blacklist configuration"""
        return self.config.get("blacklist", {})

    def get_content_filters(self) -> Dict[str, Any]:
        """Get content filtering rules"""
        return self.config.get("content_filters", {})

    def is_url_blacklisted(self, url: str) -> bool:
        """Check if URL is blacklisted"""
        blacklist = self.get_blacklist()

        # Check domains
        for domain in blacklist.get("domains", []):
            if domain in url.lower():
                return True

        # Check file extensions
        for ext in blacklist.get("file_extensions", []):
            if url.lower().endswith(ext):
                return True

        return False

    def calculate_relevance_score(self, content: str) -> int:
        """Calculate content relevance score based on keywords"""
        content_lower = content.lower()
        score = 0

        filters = self.get_content_filters()
        scoring = filters.get("relevance_scoring", {})

        # Score based on keyword categories
        for category, weight in scoring.items():
            if category == "min_score_threshold":
                continue

            keywords = self.get_keywords(category)
            for keyword in keywords:
                score += content_lower.count(keyword.lower()) * weight

        return min(score, 100)  # Cap at 100

    def passes_quality_filters(
        self, content: str, metadata: Dict[str, Any] = None
    ) -> bool:
        """Check if content passes quality filters"""
        filters = self.get_content_filters()
        quality = filters.get("quality_filters", {})

        # Word count check
        word_count = len(content.split())
        min_words = quality.get("min_word_count", 0)
        max_words = quality.get("max_word_count", float("inf"))

        if word_count < min_words or word_count > max_words:
            return False

        # Relevance score check
        relevance_threshold = filters.get("relevance_scoring", {}).get(
            "min_score_threshold", 0
        )
        if self.calculate_relevance_score(content) < relevance_threshold:
            return False

        # Date requirement check
        if quality.get("require_date", False):
            if not metadata or not metadata.get("date"):
                return False

        return True

    def get_output_settings(self) -> Dict[str, Any]:
        """Get output configuration"""
        return self.config.get("output_settings", {})

    def get_monitoring_settings(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.config.get("monitoring", {})

    def validate_target_health(self, target_name: str, success_rate: float) -> bool:
        """Check if target meets health thresholds"""
        monitoring = self.get_monitoring_settings()
        threshold = monitoring.get("success_rate_threshold", 0.75)
        return success_rate >= threshold

    def get_rate_limit(self, target_name: str) -> float:
        """Get rate limit for specific target"""
        target = self.get_target_by_name(target_name)
        if target:
            return target.rate_limit
        return self.global_settings.rate_limit_delay

    def get_scraper_strategy(self, target_name: str) -> Dict[str, Any]:
        """Get scraper strategy for specific target"""
        target = self.get_target_by_name(target_name)

        if target and target.scraper_strategy:
            return target.scraper_strategy

        # Return default strategy
        return {
            "primary": self.global_settings.primary_scraper,
            "fallbacks": self.global_settings.fallback_scrapers,
            "js_heavy": False,
            "requires_cookies": False,
        }

    def get_optimal_scraper_order(self, target_name: str, url: str = None) -> List[str]:
        """Get optimal scraper order for a target"""
        strategy = self.get_scraper_strategy(target_name)

        # Check for RSS feeds first
        if url and (url.endswith((".rss", ".xml")) or "/feed/" in url):
            if strategy.get("rss_available"):
                return ["feedparser"] + [
                    s for s in strategy["fallbacks"] if s != "feedparser"
                ]

        # Check for JavaScript-heavy sites
        if strategy.get("js_heavy"):
            return ["playwright", "crawl4ai"] + [
                s for s in strategy["fallbacks"] if s not in ["playwright", "crawl4ai"]
            ]

        # Default order
        scrapers = [strategy["primary"]] + strategy["fallbacks"]

        # Remove duplicates while preserving order
        seen = set()
        return [s for s in scrapers if not (s in seen or seen.add(s))]

    def reload_config(self) -> bool:
        """Reload configuration from file"""
        logger.info("Reloading scraper configuration")
        return self.load_config()

    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of loaded configuration"""
        if not self.config:
            return {}

        return {
            "version": self.config.get("version"),
            "last_updated": self.config.get("last_updated"),
            "total_targets": len(self.targets),
            "enabled_targets": len(self.get_enabled_targets()),
            "categories": list(self.config.get("categories", {}).keys()),
            "config_file": self.config_path,
        }


# Convenience function for quick access
def load_scraper_config(config_path: str = None) -> Optional[ScraperConfigManager]:
    """Load and return scraper configuration manager"""
    manager = ScraperConfigManager(config_path)
    if manager.load_config():
        return manager
    return None


# Example usage
if __name__ == "__main__":
    # Test the configuration manager
    config_manager = load_scraper_config()

    if config_manager:
        print("Configuration loaded successfully!")

        # Show summary
        summary = config_manager.get_config_summary()
        print(f"Summary: {summary}")

        # Show enabled targets
        targets = config_manager.get_enabled_targets()
        print(f"Enabled targets: {[t.name for t in targets]}")

        # Show keywords
        mining_keywords = config_manager.get_keywords("mining_keywords")
        print(f"Mining keywords: {mining_keywords[:10]}...")  # First 10

    else:
        print("Failed to load configuration!")
