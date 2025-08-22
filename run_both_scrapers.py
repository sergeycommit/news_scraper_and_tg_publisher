#!/usr/bin/env python3
"""
Скрипт для запуска обоих скраперов: ZDNet и The Verge AI
"""

import asyncio
import logging
from zdnet_scraper import ZDNetScraper
from theverge_scraper import TheVergeAIScraper

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('both_scrapers.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_zdnet_scraper():
    """Запуск ZDNet скрапера"""
    try:
        logger.info("🚀 Starting ZDNet scraper...")
        scraper = ZDNetScraper()
        await scraper.run_daily_scraping()
        logger.info("✅ ZDNet scraper finished successfully")
        return True
    except Exception as e:
        logger.error(f"❌ ZDNet scraper failed: {e}")
        return False

async def run_theverge_scraper():
    """Запуск The Verge AI скрапера"""
    try:
        logger.info("🚀 Starting The Verge AI scraper...")
        scraper = TheVergeAIScraper()
        await scraper.run_daily_scraping()
        logger.info("✅ The Verge AI scraper finished successfully")
        return True
    except Exception as e:
        logger.error(f"❌ The Verge AI scraper failed: {e}")
        return False

async def run_both_scrapers():
    """Запуск обоих скраперов"""
    logger.info("🎯 Starting both scrapers...")
    
    # Запускаем скраперы параллельно
    zdnet_task = asyncio.create_task(run_zdnet_scraper())
    theverge_task = asyncio.create_task(run_theverge_scraper())
    
    # Ждем завершения обоих
    zdnet_result, theverge_result = await asyncio.gather(
        zdnet_task, 
        theverge_task, 
        return_exceptions=True
    )
    
    # Проверяем результаты
    if isinstance(zdnet_result, Exception):
        logger.error(f"ZDNet scraper failed with exception: {zdnet_result}")
        zdnet_success = False
    else:
        zdnet_success = zdnet_result
    
    if isinstance(theverge_result, Exception):
        logger.error(f"The Verge scraper failed with exception: {theverge_result}")
        theverge_success = False
    else:
        theverge_success = theverge_result
    
    # Итоговый отчет
    logger.info("📊 Final report:")
    logger.info(f"ZDNet scraper: {'✅ SUCCESS' if zdnet_success else '❌ FAILED'}")
    logger.info(f"The Verge AI scraper: {'✅ SUCCESS' if theverge_success else '❌ FAILED'}")
    
    if zdnet_success and theverge_success:
        logger.info("🎉 Both scrapers completed successfully!")
    elif zdnet_success or theverge_success:
        logger.info("⚠️ One scraper completed successfully, one failed")
    else:
        logger.error("💥 Both scrapers failed!")
    
    return zdnet_success and theverge_success

def main():
    """Основная функция"""
    try:
        success = asyncio.run(run_both_scrapers())
        if success:
            print("🎉 All scrapers completed successfully!")
        else:
            print("⚠️ Some scrapers failed. Check logs for details.")
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print("⏹️ Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    main()
