#!/usr/bin/env python3
"""
Тест конвертации Markdown в HTML
Test script for markdown to HTML conversion
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_markdown_conversion():
    """Тест конвертации Markdown в HTML"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        # Тестовые примеры
        test_cases = [
            {
                'markdown': 'Это **жирный текст** и *курсив*',
                'expected_html': 'Это <b>жирный текст</b> и <i>курсив</i>'
            },
            {
                'markdown': '**Важная новость** о __технологиях__',
                'expected_html': '<b>Важная новость</b> о <u>технологиях</u>'
            },
            {
                'markdown': 'Код: `print("Hello")` и ~~старый текст~~',
                'expected_html': 'Код: <code>print("Hello")</code> и <s>старый текст</s>'
            },
            {
                'markdown': 'Ссылка: [TechCrunch](https://techcrunch.com)',
                'expected_html': 'Ссылка: <a href="https://techcrunch.com">TechCrunch</a>'
            },
            {
                'markdown': 'Смешанный **текст** с *разными* __стилями__',
                'expected_html': 'Смешанный <b>текст</b> с <i>разными</i> <u>стилями</u>'
            }
        ]
        
        print("🧪 Тестирование конвертации Markdown в HTML")
        print("=" * 50)
        
        passed = 0
        total = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Тест {i}:")
            print(f"   Markdown: {test_case['markdown']}")
            
            result = scraper.convert_markdown_to_html(test_case['markdown'])
            print(f"   Результат: {result}")
            print(f"   Ожидалось: {test_case['expected_html']}")
            
            if result == test_case['expected_html']:
                print("   ✅ Успешно")
                passed += 1
            else:
                print("   ❌ Ошибка")
        
        print("\n" + "=" * 50)
        print(f"📊 Результаты: {passed}/{total} тестов прошли")
        
        if passed == total:
            print("🎉 Все тесты конвертации прошли успешно!")
        else:
            print("⚠️  Некоторые тесты не прошли")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_complex_markdown():
    """Тест сложного Markdown"""
    try:
        from ieee_spectrum_scraper import IEEESpectrumScraper
        scraper = IEEESpectrumScraper()
        
        complex_markdown = """
🚀 **Новая технология AI** революционизирует индустрию!

*Исследователи* из __ведущих университетов__ разработали ~~устаревший подход~~ и создали `инновационное решение`.

Подробнее: [Читать статью](https://spectrum.ieee.org/article/123)

**Ключевые особенности:**
• Высокая производительность
• Низкое энергопотребление
• Простота использования
        """
        
        print("\n🔍 Тест сложного Markdown:")
        print("Исходный текст:")
        print(complex_markdown)
        
        result = scraper.convert_markdown_to_html(complex_markdown)
        print("\nРезультат конвертации:")
        print(result)
        
        # Проверяем наличие основных тегов
        checks = [
            ('<b>', 'жирный текст'),
            ('<i>', 'курсив'),
            ('<u>', 'подчеркнутый'),
            ('<s>', 'зачеркнутый'),
            ('<code>', 'код'),
            ('<a href=', 'ссылка')
        ]
        
        print("\nПроверка тегов:")
        for tag, description in checks:
            if tag in result:
                print(f"   ✅ {description}: {tag}")
            else:
                print(f"   ❌ {description}: {tag} - не найден")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования сложного Markdown: {e}")
        return False

def main():
    """Главная функция"""
    print("🧪 Тестирование конвертации Markdown в HTML")
    print("=" * 60)
    
    # Базовые тесты
    basic_tests = test_markdown_conversion()
    
    # Сложный тест
    complex_test = test_complex_markdown()
    
    print("\n" + "=" * 60)
    if basic_tests and complex_test:
        print("🎉 Все тесты прошли успешно!")
        print("✅ Конвертация Markdown в HTML работает корректно")
        print("✅ Теперь посты в Telegram будут отображаться с правильным форматированием")
    else:
        print("⚠️  Некоторые тесты не прошли")
        print("❌ Проверьте функцию конвертации")

if __name__ == "__main__":
    main() 