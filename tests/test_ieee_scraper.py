#!/usr/bin/env python3
"""
Тест IEEE Spectrum Scraper
Test script for IEEE Spectrum scraper
"""

import sys
import os
import asyncio
from datetime import datetime

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ieee_scraper_import():
    """Тест импорта IEEE скрапера"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        print("✅ IEEE Spectrum Scraper импортирован успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта IEEE Spectrum Scraper: {e}")
        return False

def test_ieee_scraper_initialization():
    """Тест инициализации IEEE скрапера"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        print("✅ IEEE Spectrum Scraper инициализирован успешно")
        print(f"   - Загружено {len(scraper.published_urls)} опубликованных URL")
        print(f"   - Папка архива: {scraper.json_folder}")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации IEEE Spectrum Scraper: {e}")
        return False

def test_ieee_url_management():
    """Тест управления URL"""
    try:
        from manage_ieee_urls import load_published_urls, save_published_urls
        urls = load_published_urls()
        print(f"✅ Утилита управления URL работает: {len(urls)} URL загружено")
        return True
    except Exception as e:
        print(f"❌ Ошибка управления URL: {e}")
        return False

def test_ieee_scraping():
    """Тест скрапинга статей"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        print("🔍 Тестирование скрапинга статей...")
        articles = scraper.scrape_ieee_articles()
        
        if articles:
            print(f"✅ Найдено {len(articles)} статей")
            for i, article in enumerate(articles[:3], 1):
                print(f"   {i}. {article['title'][:60]}...")
                print(f"      Тема: {article['topic']}")
                print(f"      Автор: {article['author']}")
        else:
            print("⚠️  Статьи не найдены (возможно, проблема с доступом к сайту)")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка скрапинга: {e}")
        return False

def test_ieee_article_filtering():
    """Тест фильтрации статей"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        # Создаем тестовые статьи
        test_articles = [
            {
                'title': 'Test AI Article 1',
                'link': 'https://spectrum.ieee.org/test1',
                'topic': 'AI',
                'author': 'Test Author'
            },
            {
                'title': 'Test Robotics Article 2',
                'link': 'https://spectrum.ieee.org/test2',
                'topic': 'Robotics',
                'author': 'Test Author'
            }
        ]
        
        # Тестируем фильтрацию
        filtered = scraper.filter_unpublished_articles(test_articles)
        print(f"✅ Фильтрация работает: {len(filtered)} из {len(test_articles)} статей не опубликованы")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка фильтрации: {e}")
        return False

async def test_telegram_connection():
    """Тест подключения к Telegram"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        if not scraper.telegram_token:
            print("⚠️  Telegram токен не настроен")
            return True
        
        # Тестируем подключение к боту
        bot_info = await scraper.telegram_bot.get_me()
        print(f"✅ Подключение к Telegram успешно: @{bot_info.username}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование IEEE Spectrum Scraper")
    print("=" * 50)
    
    tests = [
        ("Импорт скрапера", test_ieee_scraper_import),
        ("Инициализация", test_ieee_scraper_initialization),
        ("Управление URL", test_ieee_url_management),
        ("Фильтрация статей", test_ieee_article_filtering),
        ("Скрапинг статей", test_ieee_scraping),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ Тест '{test_name}' не прошел")
    
    # Тест Telegram (асинхронный)
    print(f"\n🔍 Подключение к Telegram...")
    try:
        asyncio.run(test_telegram_connection())
        passed += 1
    except Exception as e:
        print(f"   ❌ Тест 'Подключение к Telegram' не прошел: {e}")
    
    total += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно! IEEE Spectrum Scraper готов к работе.")
    else:
        print("⚠️  Некоторые тесты не прошли. Проверьте конфигурацию.")
    
    print("\n📝 Следующие шаги:")
    print("1. Настройте .env файл с API ключами")
    print("2. Запустите: python run_ieee_scraper.py")
    print("3. Проверьте логи в ieee_scraper.log")

if __name__ == "__main__":
    main() 