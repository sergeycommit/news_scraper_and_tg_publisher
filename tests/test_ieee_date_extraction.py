#!/usr/bin/env python3
"""
Тест парсинга дат с IEEE Spectrum
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import date
import sys
import os

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ieee_spectrum_scraper import IEEESpectrumScraper

def test_ieee_date_extraction():
    """Тестирование извлечения дат с IEEE Spectrum"""
    
    scraper = IEEESpectrumScraper()
    
    # URL для тестирования
    test_url = "https://spectrum.ieee.org/thunderforge-ai-wargames-dod"
    
    print(f"🔍 Тестирование парсинга дат с: {test_url}")
    print("=" * 60)
    
    try:
        # Получаем страницу
        response = requests.get(test_url, headers=scraper.headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("📄 Анализ HTML структуры...")
        
        # Ищем все элементы с датами
        date_selectors = [
            '[class*="date"]',
            'time',
            '.date', '.time', '[data-testid="date"]',
            '.article-date', '.post-date', '.published-date',
            '.meta-date', '.timestamp', '.publish-date',
            '.byline', '.author-info', '.meta'
        ]
        
        found_dates = []
        
        for selector in date_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\n✅ Найдены элементы с селектором '{selector}': {len(elements)}")
                
                for i, elem in enumerate(elements[:5]):  # Показываем первые 5
                    text = elem.get_text(strip=True)
                    datetime_attr = elem.get('datetime')
                    
                    print(f"  {i+1}. Текст: '{text}'")
                    if datetime_attr:
                        print(f"     datetime: '{datetime_attr}'")
                    
                    if text and any(char.isdigit() for char in text):
                        found_dates.append({
                            'text': text,
                            'datetime': datetime_attr,
                            'selector': selector
                        })
        
        print(f"\n📅 Найдено потенциальных дат: {len(found_dates)}")
        
        # Тестируем парсинг каждой найденной даты
        print("\n🔧 Тестирование парсинга дат:")
        print("-" * 40)
        
        for i, date_info in enumerate(found_dates):
            print(f"\n{i+1}. Текст: '{date_info['text']}'")
            if date_info['datetime']:
                print(f"   datetime: '{date_info['datetime']}'")
            
            # Парсим дату
            parsed_date = scraper.parse_article_date(date_info['text'])
            if parsed_date:
                print(f"   ✅ Парсинг успешен: {parsed_date}")
                print(f"   📅 Сегодня: {scraper.today}")
                print(f"   🎯 Статья за сегодня: {parsed_date == scraper.today}")
            else:
                print(f"   ❌ Парсинг не удался")
            
            # Также пробуем парсить datetime атрибут
            if date_info['datetime']:
                parsed_datetime = scraper.parse_article_date(date_info['datetime'])
                if parsed_datetime:
                    print(f"   ✅ datetime парсинг: {parsed_datetime}")
                    print(f"   🎯 Статья за сегодня (datetime): {parsed_datetime == scraper.today}")
        
        # Тестируем извлечение информации о статье
        print(f"\n📰 Тестирование извлечения информации о статье:")
        print("-" * 50)
        
        # Ищем основной контейнер статьи
        article_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            'main'
        ]
        
        article_element = None
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                article_element = elements[0]
                print(f"✅ Найден контейнер статьи: {selector}")
                break
        
        if article_element:
            # Извлекаем информацию о статье
            article_info = scraper.extract_article_info(article_element, "AI")
            if article_info:
                print(f"✅ Заголовок: {article_info['title']}")
                print(f"✅ Ссылка: {article_info['link']}")
                print(f"✅ Автор: {article_info['author']}")
                print(f"✅ Дата (текст): {article_info['date']}")
                print(f"✅ Дата (парсинг): {article_info['parsed_date']}")
                print(f"✅ Статья за сегодня: {article_info['parsed_date'] == scraper.today if article_info['parsed_date'] else False}")
            else:
                print("❌ Не удалось извлечь информацию о статье")
        else:
            print("❌ Не найден контейнер статьи")
        
        # Поиск всех статей на странице AI
        print(f"\n🔍 Тестирование поиска статей на странице AI:")
        print("-" * 50)
        
        ai_articles = scraper.scrape_topic_page("https://spectrum.ieee.org/topic/artificial-intelligence", "AI")
        print(f"✅ Найдено статей за сегодня: {len(ai_articles)}")
        
        for i, article in enumerate(ai_articles[:3]):
            print(f"\n{i+1}. {article['title']}")
            print(f"   Дата: {article['date']}")
            print(f"   Парсинг: {article['parsed_date']}")
            print(f"   Ссылка: {article['link']}")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ieee_date_extraction() 