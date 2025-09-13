#!/usr/bin/env python3
"""
Run script for The Robot Report Scraper
Запуск скрапера The Robot Report для публикации в Telegram
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from robotreport_scraper import RobotReportScraper

async def main():
    """Основная функция запуска скрапера"""
    print("🤖 Starting The Robot Report Scraper...")
    
    try:
        scraper = RobotReportScraper()
        result = await scraper.run_daily_scraping()
        
        if result:
            print(f"✅ Successfully published article: {result['title']}")
            print(f"🔗 Article URL: {result['url']}")
        else:
            print("ℹ️ No new articles to publish")
            
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
