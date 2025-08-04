#!/usr/bin/env python3
"""
Simple Junior Mining Network Scraper
Direct scraping without complex dependencies
"""

import asyncio
import json
import re
import time
from datetime import datetime
from itertools import zip_longest
from pathlib import Path
from typing import Iterable, Set

import aiohttp
from bs4 import BeautifulSoup

COMPANY_PATTERNS = [
    r"([A-Z][A-Za-z\s&]+(?:Mining|Resources|Gold|Silver|Copper|Exploration|Corp|Inc|Ltd)\.?)",
    r"([A-Z][A-Za-z\s&]{3,30})\s+\([A-Z]{2,5}\)",
]

SYMBOL_PATTERNS = [
    r"\b([A-Z]{2,5}(?:\.[A-Z]{1,2})?)\b",
    r"\(([A-Z]{2,5}(?:\.[A-Z]{1,2})?)\)",
]

COMPANY_REGEXES = [re.compile(p) for p in COMPANY_PATTERNS]
SYMBOL_REGEXES = [re.compile(p) for p in SYMBOL_PATTERNS]


def _extract_matches(patterns: Iterable[re.Pattern], text: str) -> Set[str]:
    """Return unique matches for each compiled regex in *patterns*."""

    matches: Set[str] = set()
    for pattern in patterns:
        matches.update(pattern.findall(text))
    return matches


class SimpleJuniorMiningScraper:
    """Simple scraper for Junior Mining Network sites"""

    def __init__(self):
        self.output_dir = Path("reports/2025-08-04")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.target_urls = [
            "https://www.juniorminingnetwork.com/",
            "https://www.juniorminingnetwork.com/heat-map.html",
            "https://www.juniorminingnetwork.com/market-data.html",
        ]

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        self.results = {
            "scraping_started": datetime.now().isoformat(),
            "sites_scraped": [],
            "companies_found": [],
            "news_items": [],
            "market_data": {},
            "performance_metrics": {},
            "errors": [],
        }

    async def scrape_all_sites(self):
        """Scrape all Junior Mining Network sites"""

        print("🏗️ Starting Junior Mining Network Scraping")
        print("=" * 60)

        async with aiohttp.ClientSession(
            headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)
        ) as session:

            for i, url in enumerate(self.target_urls, 1):
                print(f"\n🎯 Scraping Site {i}/3: {url}")

                try:
                    start_time = time.time()

                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            duration = time.time() - start_time

                            print(f"   ✅ Successfully fetched ({response.status})")
                            print(f"   📄 Content length: {len(content):,} chars")
                            print(f"   ⏱️ Duration: {duration:.2f}s")

                            # Extract data from content
                            site_data = await self.extract_data(url, content)

                            self.results["sites_scraped"].append(
                                {
                                    "url": url,
                                    "success": True,
                                    "content_length": len(content),
                                    "duration": duration,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )

                            # Merge extracted data
                            self.merge_site_data(site_data)

                        else:
                            error_msg = f"HTTP {response.status}"
                            print(f"   ❌ {error_msg}")
                            self.results["errors"].append(f"{url}: {error_msg}")

                except Exception as e:
                    error_msg = f"Error scraping {url}: {str(e)}"
                    print(f"   💥 {error_msg}")
                    self.results["errors"].append(error_msg)

                # Rate limiting
                await asyncio.sleep(2)

        self.results["scraping_completed"] = datetime.now().isoformat()

        # Generate summary
        await self.generate_summary()

        # Save results
        await self.save_results()

        return self.results

    async def extract_data(self, url, content):
        """Extract meaningful data from scraped content"""

        print(f"   🔍 Extracting data...")

        data = {
            "url": url,
            "companies": [],
            "news_items": [],
            "stock_data": [],
            "market_metrics": {},
        }

        try:
            soup = BeautifulSoup(content, "html.parser")
            text_content = soup.get_text()

            # Extract company names and stock symbols
            companies = self.extract_companies(text_content, soup)
            data["companies"] = companies

            # Extract news headlines
            news = self.extract_news(soup)
            data["news_items"] = news

            # Extract stock/market data
            stock_data = self.extract_stock_data(text_content)
            data["stock_data"] = stock_data

            print(
                f"   📊 Found {len(companies)} companies, {len(news)} news items, {len(stock_data)} stock entries"
            )

        except Exception as e:
            print(f"   ⚠️ Extraction error: {str(e)}")

        return data

    def extract_companies(self, text, soup):
        """Extract mining company information"""

        companies = []

        found_companies = _extract_matches(COMPANY_REGEXES, text)
        found_symbols = _extract_matches(SYMBOL_REGEXES, text)

        company_list = list(found_companies)[:20]
        symbol_list = list(found_symbols)[:20]

        for name, symbol in zip_longest(company_list, symbol_list):
            if name is None:
                companies.append(
                    {
                        "name": f"Company {symbol}",
                        "symbol": symbol,
                        "source": "symbol_only",
                    }
                )
            else:
                companies.append(
                    {"name": name, "symbol": symbol, "source": "text_extraction"}
                )

        return companies[:30]  # Limit total results

    def extract_news(self, soup):
        """Extract news headlines and articles"""

        news_items = []

        # Look for news-related elements
        news_selectors = [
            "h1, h2, h3, h4",  # Headlines
            ".news, .article, .post",  # News containers
            '[class*="headline"], [class*="title"]',  # Title classes
        ]

        found_headlines = set()

        for selector in news_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if (
                        len(text) > 10
                        and len(text) < 200
                        and text not in found_headlines
                    ):
                        # Check for mining relevance
                        relevance = self.calculate_mining_relevance(text)
                        if relevance > 0:
                            news_items.append(
                                {
                                    "headline": text,
                                    "relevance_score": relevance,
                                    "element_type": element.name,
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                            found_headlines.add(text)
            except:
                continue

        # Sort by relevance and return top items
        news_items.sort(key=lambda x: x["relevance_score"], reverse=True)
        return news_items[:15]

    def extract_stock_data(self, text):
        """Extract stock prices and market data"""

        stock_data = []

        # Price patterns
        price_patterns = [
            r"\$(\d{1,4}\.\d{2,4})",
            r"Price:\s*\$?(\d{1,4}\.\d{2,4})",
            r"(\d{1,4}\.\d{2,4})\s*CAD",
        ]

        # Change patterns
        change_patterns = [
            r"([+-]?\d+\.\d{2,4})\s*\([+-]?\d+\.\d{1,2}%\)",
            r"([+-]\d+\.\d{1,2})%",
        ]

        prices = []
        changes = []

        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            prices.extend([float(m) for m in matches if 0.01 <= float(m) <= 9999])

        for pattern in change_patterns:
            matches = re.findall(pattern, text)
            changes.extend(matches)

        # Create stock data entries
        for i, price in enumerate(prices[:20]):
            stock_data.append(
                {
                    "price": price,
                    "change": changes[i] if i < len(changes) else None,
                    "currency": "CAD",  # Assuming CAD for Junior Mining Network
                }
            )

        return stock_data

    def calculate_mining_relevance(self, text):
        """Calculate relevance score for mining content"""

        mining_keywords = [
            "mining",
            "exploration",
            "gold",
            "silver",
            "copper",
            "zinc",
            "nickel",
            "iron ore",
            "coal",
            "production",
            "reserves",
            "resources",
            "drill",
            "assay",
            "feasibility",
            "deposit",
            "ore",
            "mine",
            "junior miner",
            "tsx",
            "tsxv",
            "financing",
            "merger",
            "acquisition",
        ]

        text_lower = text.lower()
        score = 0

        for keyword in mining_keywords:
            count = text_lower.count(keyword)
            if keyword in ["mining", "gold", "exploration", "junior miner"]:
                score += count * 3  # Higher weight
            else:
                score += count

        return score

    def merge_site_data(self, site_data):
        """Merge data from individual site into results"""

        # Merge companies
        for company in site_data["companies"]:
            # Check if company already exists
            existing = None
            for existing_company in self.results["companies_found"]:
                if (
                    company.get("symbol")
                    and company["symbol"] == existing_company.get("symbol")
                ) or (
                    company.get("name")
                    and company["name"] == existing_company.get("name")
                ):
                    existing = existing_company
                    break

            if existing:
                # Update existing company with additional data
                if "sources" not in existing:
                    existing["sources"] = []
                existing["sources"].append(site_data["url"])
            else:
                # Add new company
                company["sources"] = [site_data["url"]]
                self.results["companies_found"].append(company)

        # Merge news items
        self.results["news_items"].extend(site_data["news_items"])

        # Store market data by URL
        if site_data["stock_data"]:
            self.results["market_data"][site_data["url"]] = site_data["stock_data"]

    async def generate_summary(self):
        """Generate performance summary"""

        successful_sites = len(
            [s for s in self.results["sites_scraped"] if s["success"]]
        )
        total_sites = len(self.target_urls)

        # Calculate timing
        start_time = datetime.fromisoformat(self.results["scraping_started"])
        end_time = datetime.fromisoformat(self.results["scraping_completed"])
        total_duration = (end_time - start_time).total_seconds()

        self.results["performance_metrics"] = {
            "sites_attempted": total_sites,
            "sites_successful": successful_sites,
            "success_rate": (successful_sites / total_sites) * 100,
            "total_companies": len(self.results["companies_found"]),
            "total_news_items": len(self.results["news_items"]),
            "total_errors": len(self.results["errors"]),
            "scraping_duration": total_duration,
            "data_quality_score": self.calculate_quality_score(),
        }

    def calculate_quality_score(self):
        """Calculate overall data quality score"""

        score = 0
        metrics = self.results["performance_metrics"]

        # Success rate (40%)
        if "success_rate" in metrics:
            score += (metrics["success_rate"] / 100) * 40

        # Data completeness (40%)
        companies_score = min(len(self.results["companies_found"]) / 10, 1) * 20
        news_score = min(len(self.results["news_items"]) / 5, 1) * 20
        score += companies_score + news_score

        # Error penalty (20%)
        if len(self.results["errors"]) == 0:
            score += 20
        elif len(self.results["errors"]) <= 1:
            score += 10

        return round(score, 1)

    async def save_results(self):
        """Save results to files"""

        # Save main JSON file
        json_file = self.output_dir / "mining_companies_data.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Data saved to: {json_file}")

        # Save summary text file
        summary_file = self.output_dir / "mining_companies_summary.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("JUNIOR MINING NETWORK SCRAPING REPORT\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(
                f"Target Sites: {self.results['performance_metrics']['sites_attempted']}\n"
            )
            f.write(
                f"Successful: {self.results['performance_metrics']['sites_successful']}\n"
            )
            f.write(
                f"Success Rate: {self.results['performance_metrics']['success_rate']:.1f}%\n\n"
            )

            f.write("RESULTS SUMMARY:\n")
            f.write(
                f"- Companies Found: {self.results['performance_metrics']['total_companies']}\n"
            )
            f.write(
                f"- News Items: {self.results['performance_metrics']['total_news_items']}\n"
            )
            f.write(
                f"- Data Quality Score: {self.results['performance_metrics']['data_quality_score']}/100\n"
            )
            f.write(
                f"- Duration: {self.results['performance_metrics']['scraping_duration']:.1f}s\n\n"
            )

            if self.results["companies_found"]:
                f.write("TOP COMPANIES FOUND:\n")
                for i, company in enumerate(self.results["companies_found"][:10], 1):
                    name = company.get("name", "Unknown")
                    symbol = company.get("symbol", "N/A")
                    sources = len(company.get("sources", []))
                    f.write(f"{i:2d}. {name} ({symbol}) - {sources} source(s)\n")
                f.write("\n")

            if self.results["news_items"]:
                f.write("TOP NEWS HEADLINES:\n")
                sorted_news = sorted(
                    self.results["news_items"],
                    key=lambda x: x["relevance_score"],
                    reverse=True,
                )
                for i, news in enumerate(sorted_news[:10], 1):
                    headline = news["headline"][:80]
                    score = news["relevance_score"]
                    f.write(f"{i:2d}. {headline}... (score: {score})\n")
                f.write("\n")

            if self.results["errors"]:
                f.write("ERRORS:\n")
                for error in self.results["errors"]:
                    f.write(f"- {error}\n")

        print(f"📄 Summary saved to: {summary_file}")


async def main():
    """Run the simple Junior Mining Network scraper"""

    print("🏗️ Simple Junior Mining Network Scraper")
    print("Target Sites:")
    print("1. https://www.juniorminingnetwork.com/")
    print("2. https://www.juniorminingnetwork.com/heat-map.html")
    print("3. https://www.juniorminingnetwork.com/market-data.html")
    print("=" * 60)

    scraper = SimpleJuniorMiningScraper()

    try:
        results = await scraper.scrape_all_sites()

        print("\n" + "=" * 60)
        print("🎯 SCRAPING COMPLETE")
        print("=" * 60)

        metrics = results["performance_metrics"]
        print(f"✅ Success Rate: {metrics['success_rate']:.1f}%")
        print(f"🏢 Companies Found: {metrics['total_companies']}")
        print(f"📰 News Items: {metrics['total_news_items']}")
        print(f"🏆 Data Quality: {metrics['data_quality_score']}/100")
        print(f"⏱️ Duration: {metrics['scraping_duration']:.1f}s")

        if results["companies_found"]:
            print(f"\n🏢 TOP COMPANIES:")
            for i, company in enumerate(results["companies_found"][:5], 1):
                name = company.get("name", "Unknown")
                symbol = company.get("symbol", "N/A")
                print(f"   {i}. {name} ({symbol})")

        if results["errors"]:
            print(f"\n⚠️ Errors: {len(results['errors'])}")
            for error in results["errors"][:3]:
                print(f"   • {error}")

        print(f"\n💾 Files created:")
        print(f"   • reports/2025-08-04/mining_companies_data.json")
        print(f"   • reports/2025-08-04/mining_companies_summary.txt")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
