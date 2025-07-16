#!/usr/bin/env python3
"""
Test Image Extraction
Тестовый скрипт для проверки извлечения изображений из статей
"""

import asyncio
import sys
import platform
from techcrunch_scraper import TechCrunchScraper

async def test_image_extraction():
    """Тестирование извлечения изображений"""
    print("🧪 Тестирование извлечения изображений из TechCrunch")
    print("=" * 50)
    
    scraper = TechCrunchScraper()
    
    # Получаем статьи из RSS
    articles = scraper.scrape_rss_feed()
    if not articles:
        print("❌ Не удалось получить статьи из RSS")
        return
    
    print(f"✅ Получено {len(articles)} статей")
    
    # Тестируем первые 3 статьи
    for i, article in enumerate(articles[:3], 1):
        print(f"\n📰 Тестируем статью {i}: {article['title'][:50]}...")
        
        # Извлекаем контент и изображение
        content, image_url = scraper.scrape_article_content_and_image(article['link'])
        
        if image_url:
            print(f"🖼️ Найдено изображение: {image_url}")
            
            # Пробуем скачать
            image_path = scraper.download_image(image_url)
            if image_path:
                print(f"✅ Изображение скачано: {image_path}")
                
                # Удаляем тестовый файл
                import os
                try:
                    os.unlink(image_path)
                    print("🗑️ Тестовый файл удален")
                except:
                    pass
            else:
                print("❌ Не удалось скачать изображение")
        else:
            print("❌ Изображение не найдено")
        
        print("-" * 30)

async def main():
    """Главная функция"""
    try:
        await test_image_extraction()
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def run_with_proper_cleanup():
    """Запуск с правильной очисткой event loop для Windows"""
    if platform.system() == 'Windows':
        # Используем SelectEventLoop для Windows чтобы избежать проблем с ProactorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
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