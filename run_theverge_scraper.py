#!/usr/bin/env python3
"""
Запуск The Verge AI Scraper
"""

import asyncio
from theverge_scraper import TheVergeAIScraper

async def main():
    """Основная функция запуска"""
    scraper = TheVergeAIScraper()
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
