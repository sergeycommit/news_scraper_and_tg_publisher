#!/usr/bin/env python3
"""
Debug script для анализа структуры страницы IEEE Spectrum
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def analyze_ieee_page(url, topic):
    """Анализ структуры страницы IEEE Spectrum"""
    print(f"🔍 Анализ страницы: {url}")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Ищем статьи
        articles = soup.find_all('article')
        print(f"📰 Найдено статей: {len(articles)}")
        
        if articles:
            # Анализируем первую статью
            first_article = articles[0]
            print(f"\n🔍 Анализ первой статьи:")
            
            # Ищем заголовок
            title_selectors = ['h1', 'h2', 'h3', '.title', '.headline', '[data-testid="title"]']
            title = None
            for selector in title_selectors:
                title_elem = first_article.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    print(f"   📝 Заголовок ({selector}): {title[:100]}...")
                    break
            
            # Ищем ссылку
            link_elem = first_article.find('a')
            if link_elem and link_elem.get('href'):
                link = link_elem.get('href')
                print(f"   🔗 Ссылка: {link}")
            
            # Анализируем скрипты в статье
            scripts = first_article.find_all('script')
            print(f"\n📜 Найдено скриптов: {len(scripts)}")
            
            for i, script in enumerate(scripts):
                script_content = script.string
                if script_content:
                    print(f"\n🔍 Скрипт {i+1}:")
                    print(f"   Класс: {script.get('class', '')}")
                    print(f"   Длина: {len(script_content)} символов")
                    
                    # Ищем JSON данные
                    if 'window.__INITIAL_STATE__' in script_content:
                        print(f"   ✅ Найден INITIAL_STATE")
                        # Извлекаем JSON
                        json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_content, re.DOTALL)
                        if json_match:
                            try:
                                data = json.loads(json_match.group(1))
                                print(f"   📊 JSON данные найдены")
                                # Ищем дату в JSON
                                if 'article' in data:
                                    article_data = data['article']
                                    if 'publishedDate' in article_data:
                                        print(f"   📅 Дата в JSON: {article_data['publishedDate']}")
                                    if 'date' in article_data:
                                        print(f"   📅 Дата в JSON: {article_data['date']}")
                            except json.JSONDecodeError:
                                print(f"   ❌ Ошибка парсинга JSON")
                    
                    # Ищем другие паттерны с датами
                    date_patterns = [
                        r'"publishedDate"\s*:\s*"([^"]+)"',
                        r'"date"\s*:\s*"([^"]+)"',
                        r'"timestamp"\s*:\s*"([^"]+)"',
                        r'"createdAt"\s*:\s*"([^"]+)"',
                        r'"updatedAt"\s*:\s*"([^"]+)"'
                    ]
                    
                    for pattern in date_patterns:
                        matches = re.findall(pattern, script_content)
                        if matches:
                            print(f"   📅 Найдены даты ({pattern}): {matches[:3]}")
            
            # Ищем дату в обычных элементах
            print(f"\n📅 Поиск даты в HTML элементах:")
            
            # Расширенные селекторы для дат
            date_selectors = [
                'time', '.date', '.time', '[data-testid="date"]',
                '.article-date', '.post-date', '.published-date',
                '.meta-date', '.timestamp', '.publish-date',
                '.byline', '.author-info', '.meta',
                '[class*="date"]', '[class*="time"]', '[class*="published"]'
            ]
            
            for selector in date_selectors:
                date_elements = first_article.select(selector)
                if date_elements:
                    for elem in date_elements:
                        text = elem.get_text(strip=True)
                        datetime_attr = elem.get('datetime')
                        if text or datetime_attr:
                            print(f"   ✅ Найдена дата ({selector}): text='{text}' datetime='{datetime_attr}'")
            
            # Ищем в тексте статьи
            article_text = first_article.get_text()
            date_patterns = [
                r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',
                r'\d{4}-\d{1,2}-\d{1,2}',
                r'\d{1,2}/\d{1,2}/\d{4}',
                r'(Today|Yesterday)',
                r'\d+\s+(hour|day|minute)s?\s+ago'
            ]
            
            found_dates = []
            for pattern in date_patterns:
                matches = re.findall(pattern, article_text, re.IGNORECASE)
                if matches:
                    found_dates.extend(matches)
            
            if found_dates:
                print(f"   ✅ Найдены даты в тексте: {found_dates[:3]}")
            else:
                print(f"   ❌ Даты не найдены в тексте")
            
            # Анализируем все атрибуты элементов
            print(f"\n🔍 Анализ всех элементов с датами:")
            for elem in first_article.find_all():
                for attr_name, attr_value in elem.attrs.items():
                    if isinstance(attr_value, str) and any(char.isdigit() for char in attr_value):
                        if any(date_word in attr_value.lower() for date_word in ['date', 'time', 'published', 'created']):
                            print(f"   {elem.name}.{attr_name}='{attr_value}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        return False

def main():
    """Главная функция"""
    print("🔍 Анализ структуры IEEE Spectrum")
    print("=" * 60)
    
    urls = [
        ("AI", "https://spectrum.ieee.org/topic/artificial-intelligence"),
        ("Robotics", "https://spectrum.ieee.org/topic/robotics")
    ]
    
    for topic, url in urls:
        print(f"\n{'='*20} {topic} {'='*20}")
        analyze_ieee_page(url, topic)
        print()

if __name__ == "__main__":
    main() 