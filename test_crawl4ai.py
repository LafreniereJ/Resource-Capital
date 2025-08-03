import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://www.nbcnews.com/business")
        print(result.markdown[:1000])  # print first 1000 characters of the summary

if __name__ == "__main__":
    asyncio.run(main())

