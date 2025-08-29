#!/usr/bin/env python3
"""
Запуск Ars Technica Scraper
"""

import asyncio
from arstechnica_scraper import ArsTechnicaScraper

async def main():
    """Основная функция запуска"""
    scraper = ArsTechnicaScraper()
    result = await scraper.run_daily_scraping()
    
    if result:
        print(f"✅ Published article: {result['title']}")
        print(f"📰 URL: {result['url']}")
        print(f"📅 Date: {result['date']}")
        print(f"🏷️ Topic: {result['topic']}")
    else:
        print("ℹ️ No new articles to publish")

if __name__ == "__main__":
    asyncio.run(main())
