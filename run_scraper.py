#!/usr/bin/env python3
"""
Запуск TechCrunch Scraper
Простой скрипт для запуска основного скрапера
"""

import asyncio
import sys
import os
import platform
from techcrunch_scraper import TechCrunchScraper
from dotenv import load_dotenv

load_dotenv()

async def main():
    """Главная функция запуска"""
    try:
        print("🚀 Запуск TechCrunch Scraper...")
        
        # Проверяем наличие переменных окружения
        required_env_vars = [
            'OPENROUTER_API_KEY',
            'TELEGRAM_BOT_TOKEN', 
            'TELEGRAM_CHANNEL_ID'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
            print("📝 Создайте файл .env на основе config.env.example")
            sys.exit(1)
        
        # Запускаем скрапер
        scraper = TechCrunchScraper()
        success = await scraper.run_daily_scraping()
        
        if success:
            print("✅ Скрапинг завершен успешно!")
        else:
            print("❌ Ошибка при выполнении скрапинга")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Скрапинг прерван пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

def run_with_proper_cleanup():
    """Запуск с правильной очисткой event loop для Windows"""
    if platform.system() == 'Windows':
        # Используем SelectEventLoop для Windows чтобы избежать проблем с ProactorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Скрапинг прерван пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        # Очищаем все pending tasks
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except:
            pass

if __name__ == "__main__":
    run_with_proper_cleanup() 