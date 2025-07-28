#!/usr/bin/env python3
"""
Тест фильтрации по дате для IEEE Spectrum Scraper
Test script for date filtering functionality
"""

import sys
import os
from datetime import date, timedelta

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_date_parsing():
    """Тест парсинга дат"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        # Тестовые даты
        test_cases = [
            ("22 Jul 2025", date(2025, 7, 22)),
            ("July 22, 2025", date(2025, 7, 22)),
            ("2025-07-22", date(2025, 7, 22)),
            ("22/07/2025", date(2025, 7, 22)),
            ("Today", scraper.today),
            ("Yesterday", scraper.today - timedelta(days=1)),
            ("2 hours ago", scraper.today),
            ("1 day ago", scraper.today),
            ("", None),
            ("Invalid date", None),
        ]
        
        print("🧪 Тестирование парсинга дат")
        print("=" * 50)
        
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
        
        print("\n" + "=" * 50)
        print(f"📊 Результаты: {passed}/{total} тестов прошли")
        
        if passed == total:
            print("🎉 Все тесты парсинга дат прошли успешно!")
        else:
            print("⚠️  Некоторые тесты не прошли")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_recent_days_filtering():
    """Тест фильтрации за последние 2 дня"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        # Создаем тестовые статьи
        test_articles = [
            {
                'title': 'Today Article 1',
                'date': 'Today',
                'parsed_date': scraper.today,
                'topic': 'AI'
            },
            {
                'title': 'Yesterday Article',
                'date': 'Yesterday',
                'parsed_date': scraper.today - timedelta(days=1),
                'topic': 'AI'
            },
            {
                'title': 'Old Article',
                'date': '20 Jul 2025',
                'parsed_date': date(2025, 7, 20),
                'topic': 'Robotics'
            },
            {
                'title': 'Today Article 2',
                'date': '2 hours ago',
                'parsed_date': scraper.today,
                'topic': 'Robotics'
            }
        ]
        
        print("\n🔍 Тест фильтрации за последние 2 дня:")
        print(f"Сегодняшняя дата: {scraper.today}")
        
        recent_articles = []
        for article in test_articles:
            if scraper.is_article_from_recent_days(article['parsed_date']):
                recent_articles.append(article)
                print(f"   ✅ Недавняя: {article['title']} ({article['date']})")
            else:
                print(f"   ❌ Старая: {article['title']} ({article['date']})")
        
        print(f"\n📊 Найдено статей за последние 2 дня: {len(recent_articles)}")
        
        expected_recent = 3  # "Today Article 1", "Today Article 2" и "Yesterday Article"
        if len(recent_articles) == expected_recent:
            print("✅ Фильтрация работает корректно!")
            return True
        else:
            print(f"❌ Ожидалось {expected_recent} статей, найдено {len(recent_articles)}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка тестирования фильтрации: {e}")
        return False

def test_scraper_initialization():
    """Тест инициализации скрапера с фильтрацией по дате"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        print("\n🔍 Тест инициализации скрапера:")
        print(f"   Сегодняшняя дата: {scraper.today}")
        print(f"   AI URL: {scraper.ai_url}")
        print(f"   Robotics URL: {scraper.robotics_url}")
        
        # Проверяем, что дата установлена корректно
        if scraper.today == date.today():
            print("   ✅ Дата установлена корректно")
            return True
        else:
            print("   ❌ Ошибка установки даты")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование фильтрации по дате IEEE Spectrum Scraper")
    print("=" * 70)
    
    tests = [
        ("Инициализация скрапера", test_scraper_initialization),
        ("Парсинг дат", test_date_parsing),
        ("Фильтрация за последние 2 дня", test_recent_days_filtering),
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
        print("✅ Фильтрация по дате работает корректно")
        print("✅ Скрапер будет обрабатывать статьи за последние 2 дня")
    else:
        print("⚠️  Некоторые тесты не прошли")
        print("❌ Проверьте функциональность фильтрации по дате")
    
    print("\n📝 Следующие шаги:")
    print("1. Запустите: python run_ieee_scraper.py")
    print("2. Проверьте логи в ieee_scraper.log")
    print("3. Убедитесь, что обрабатываются статьи за последние 2 дня")

if __name__ == "__main__":
    main() 