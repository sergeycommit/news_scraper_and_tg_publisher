#!/usr/bin/env python3
"""
Тест извлечения дат для IEEE Spectrum Scraper
Test script for IEEE Spectrum date extraction
"""

import sys
import os
from datetime import date, timedelta

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ieee_date_extraction():
    """Тест извлечения дат с IEEE Spectrum"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        print("🧪 Тестирование извлечения дат IEEE Spectrum")
        print("=" * 60)
        
        # Тестируем парсинг различных форматов дат IEEE
        test_cases = [
            ("20 Jul 2025", date(2025, 7, 20)),
            ("17h", scraper.today),  # Относительное время
            ("2d", scraper.today),   # Относительное время
            ("30m", scraper.today),  # Относительное время
            ("Today", scraper.today),
            ("Yesterday", scraper.today - timedelta(days=1)),
            ("2 hours ago", scraper.today),
            ("1 day ago", scraper.today),
            ("", None),
            ("Invalid date", None),
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, (date_text, expected) in enumerate(test_cases, 1):
            print(f"\n🔍 Тест {i}:")
            print(f"   Дата: '{date_text}'")
            
            result = scraper.parse_article_date(date_text)
            print(f"   Результат: {result}")
            print(f"   Ожидалось: {expected}")
            
            if result == expected:
                print("   ✅ Успешно")
                passed += 1
            else:
                print("   ❌ Ошибка")
        
        print("\n" + "=" * 60)
        print(f"📊 Результаты: {passed}/{total} тестов прошли")
        
        if passed == total:
            print("🎉 Все тесты парсинга дат прошли успешно!")
        else:
            print("⚠️  Некоторые тесты не прошли")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_actual_scraping():
    """Тест реального скрапинга с IEEE Spectrum"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        print("\n🔍 Тест реального скрапинга IEEE Spectrum:")
        
        # Скрапим статьи
        articles = scraper.scrape_ieee_articles()
        
        print(f"📰 Найдено статей: {len(articles)}")
        
        if articles:
            print("\n📋 Примеры статей:")
            for i, article in enumerate(articles[:3], 1):
                print(f"   {i}. {article['title'][:60]}...")
                print(f"      Дата: '{article['date']}' -> {article['parsed_date']}")
                print(f"      Тема: {article['topic']}")
                print()
            
            # Проверяем, что есть статьи с датами
            articles_with_dates = [a for a in articles if a['parsed_date']]
            print(f"📅 Статей с распарсенными датами: {len(articles_with_dates)}")
            
            if articles_with_dates:
                print("✅ Скрапинг работает корректно!")
                return True
            else:
                print("⚠️  Не удалось распарсить даты")
                return False
        else:
            print("❌ Статьи не найдены")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка скрапинга: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование извлечения дат IEEE Spectrum Scraper")
    print("=" * 70)
    
    tests = [
        ("Парсинг дат IEEE", test_ieee_date_extraction),
        ("Реальный скрапинг", test_actual_scraping),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ Тест '{test_name}' не прошел")
    
    print("\n" + "=" * 70)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
        print("✅ Извлечение дат работает корректно")
        print("✅ Скрапер готов к работе с IEEE Spectrum")
    else:
        print("⚠️  Некоторые тесты не прошли")
        print("❌ Проверьте функциональность извлечения дат")
    
    print("\n📝 Следующие шаги:")
    print("1. Запустите: python run_ieee_scraper.py")
    print("2. Проверьте логи в ieee_scraper.log")
    print("3. Убедитесь, что даты извлекаются корректно")

if __name__ == "__main__":
    main() 