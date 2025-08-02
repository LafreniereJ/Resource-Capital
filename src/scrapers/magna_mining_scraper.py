#!/usr/bin/env python3
"""
Magna Mining Website Scraper
Scrapes comprehensive information from magnamining.com using Crawl4AI
"""

import asyncio
import json
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import os

class MagnaMiningScaper:
    def __init__(self):
        self.base_url = "https://magnamining.com"
        self.data = {}
        
    async def scrape_page(self, crawler, url, page_name):
        """Scrape a specific page and extract relevant information"""
        print(f"Scraping {page_name}: {url}")
        
        try:
            result = await crawler.arun(
                url=url,
                word_count_threshold=10
            )
            
            return {
                'url': url,
                'title': getattr(result, 'title', ''),
                'content': result.markdown,
                'links': getattr(result, 'links', {}),
                'images': getattr(result, 'images', []),
                'metadata': getattr(result, 'metadata', {})
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    async def discover_pages(self, crawler):
        """Discover important pages on the website"""
        print("Discovering pages...")
        
        result = await crawler.arun(
            url=self.base_url,
            word_count_threshold=5
        )
        
        # Extract main navigation links
        important_pages = {
            'home': self.base_url,
        }
        
        # Common mining company page patterns
        common_pages = [
            '/about', '/about-us', '/company',
            '/projects', '/properties', '/operations',
            '/investors', '/investor-relations',
            '/news', '/press-releases', '/media',
            '/management', '/team', '/leadership',
            '/financials', '/reports',
            '/contact', '/contact-us',
            '/sustainability', '/esg',
            '/technical-reports', '/resources'
        ]
        
        links = getattr(result, 'links', {})
        if isinstance(links, dict):
            links = links.get('internal', []) + links.get('external', [])
        
        for link in links:
            href = link.get('href', '').lower()
            text = link.get('text', '').lower()
            
            # Check for important page patterns
            for page_type in common_pages:
                if page_type in href or page_type.replace('-', ' ') in text:
                    page_name = page_type.strip('/')
                    if page_name not in important_pages:
                        full_url = href if href.startswith('http') else f"{self.base_url.rstrip('/')}{href}"
                        important_pages[page_name] = full_url
        
        return important_pages

    async def scrape_all(self):
        """Main scraping function"""
        print("Starting Magna Mining website scraping...")
        
        async with AsyncWebCrawler(
            headless=True
        ) as crawler:
            
            # Discover important pages
            pages = await self.discover_pages(crawler)
            print(f"Found {len(pages)} important pages to scrape")
            
            # Scrape each page
            for page_name, url in pages.items():
                page_data = await self.scrape_page(crawler, url, page_name)
                if page_data:
                    self.data[page_name] = page_data
                
                # Add delay to be respectful
                await asyncio.sleep(2)
        
        return self.data

    def save_data(self, filename=None):
        """Save scraped data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"magna_mining_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")
        return filename

    def generate_summary(self):
        """Generate a summary of scraped data"""
        summary = {
            'scrape_timestamp': datetime.now().isoformat(),
            'total_pages_scraped': len(self.data),
            'pages_scraped': list(self.data.keys()),
            'total_content_size': sum(len(str(page_data)) for page_data in self.data.values())
        }
        
        return summary

async def main():
    """Main execution function"""
    scraper = MagnaMiningScaper()
    
    try:
        # Scrape the website
        data = await scraper.scrape_all()
        
        # Save the data
        filename = scraper.save_data()
        
        # Generate and display summary
        summary = scraper.generate_summary()
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        print(f"Pages scraped: {summary['total_pages_scraped']}")
        print(f"Pages: {', '.join(summary['pages_scraped'])}")
        print(f"Content size: {summary['total_content_size']:,} characters")
        print(f"Data saved to: {filename}")
        
        # Save summary
        summary_file = filename.replace('.json', '_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Summary saved to: {summary_file}")
        
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    # Check if crawl4ai is installed
    try:
        import crawl4ai
        print("Crawl4AI found, starting scraper...")
    except ImportError:
        print("Error: crawl4ai not found. Please install it with:")
        print("pip install crawl4ai")
        print("crawl4ai-setup")
        exit(1)
    
    # Run the scraper
    success = asyncio.run(main())
    
    if success:
        print("\nScraping completed successfully!")
    else:
        print("\nScraping failed. Check the error messages above.")