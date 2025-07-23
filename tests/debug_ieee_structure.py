#!/usr/bin/env python3
"""
Детальный анализ HTML структуры IEEE Spectrum
"""

import requests
from bs4 import BeautifulSoup
import sys
import os
import re

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ieee_spectrum_scraper import IEEESpectrumScraper

def debug_ieee_structure():
    """Детальный анализ HTML структуры IEEE Spectrum"""
    
    scraper = IEEESpectrumScraper()
    
    # URL для тестирования
    test_url = "https://spectrum.ieee.org/thunderforge-ai-wargames-dod"
    
    print(f"🔍 Детальный анализ HTML структуры: {test_url}")
    print("=" * 70)
    
    try:
        # Получаем страницу
        response = requests.get(test_url, headers=scraper.headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("📄 Поиск всех элементов с датами...")
        print("-" * 50)
        
        # Ищем все элементы, которые могут содержать даты
        all_elements_with_dates = []
        
        # Ищем по классам, содержащим "date"
        for elem in soup.find_all(class_=lambda x: x and 'date' in x.lower()):
            text = elem.get_text(strip=True)
            if text and any(char.isdigit() for char in text):
                all_elements_with_dates.append({
                    'element': elem,
                    'text': text,
                    'class': elem.get('class'),
                    'tag': elem.name,
                    'datetime': elem.get('datetime')
                })
        
        # Ищем time элементы
        for elem in soup.find_all('time'):
            text = elem.get_text(strip=True)
            if text:
                all_elements_with_dates.append({
                    'element': elem,
                    'text': text,
                    'class': elem.get('class'),
                    'tag': elem.name,
                    'datetime': elem.get('datetime')
                })
        
        # Ищем элементы с относительным временем (3h, 1h, etc.)
        for elem in soup.find_all(text=True):
            if elem.parent and any(char.isdigit() for char in elem) and any(char.isalpha() for char in elem):
                text = elem.strip()
                if re.match(r'\d+[hdm]', text):  # 3h, 1h, 2d, etc.
                    all_elements_with_dates.append({
                        'element': elem.parent,
                        'text': text,
                        'class': elem.parent.get('class'),
                        'tag': elem.parent.name,
                        'datetime': elem.parent.get('datetime')
                    })
        
        print(f"📅 Найдено элементов с датами: {len(all_elements_with_dates)}")
        
        for i, date_info in enumerate(all_elements_with_dates[:10]):  # Показываем первые 10
            print(f"\n{i+1}. Текст: '{date_info['text']}'")
            print(f"   Тег: {date_info['tag']}")
            print(f"   Класс: {date_info['class']}")
            if date_info['datetime']:
                print(f"   datetime: '{date_info['datetime']}'")
            
            # Показываем родительский элемент
            parent = date_info['element'].parent
            if parent:
                print(f"   Родитель: {parent.name} (класс: {parent.get('class')})")
        
        print(f"\n🔍 Поиск статей на странице AI...")
        print("-" * 50)
        
        # Получаем страницу AI
        ai_response = requests.get("https://spectrum.ieee.org/topic/artificial-intelligence", headers=scraper.headers, timeout=30)
        ai_response.raise_for_status()
        ai_soup = BeautifulSoup(ai_response.content, 'html.parser')
        
        # Ищем все article элементы
        articles = ai_soup.find_all('article')
        print(f"📰 Найдено article элементов: {len(articles)}")
        
        # Анализируем первые 3 статьи
        for i, article in enumerate(articles[:3]):
            print(f"\n📄 Статья {i+1}:")
            
            # Ищем заголовок
            title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                print(f"   Заголовок: {title[:60]}...")
            
            # Ищем ссылку
            link_elem = article.find('a')
            if link_elem:
                href = link_elem.get('href')
                if href:
                    if not href.startswith('http'):
                        href = f"https://spectrum.ieee.org{href}"
                    print(f"   Ссылка: {href}")
            
            # Ищем дату в статье
            date_found = False
            for date_info in all_elements_with_dates:
                # Проверяем, находится ли элемент даты внутри этой статьи
                if date_info['element'] in article.descendants:
                    print(f"   Дата: '{date_info['text']}' (найдена в статье)")
                    date_found = True
                    break
            
            if not date_found:
                print(f"   Дата: не найдена")
            
            # Ищем дату в самой статье
            article_dates = []
            for elem in article.find_all(class_=lambda x: x and 'date' in x.lower()):
                text = elem.get_text(strip=True)
                if text and any(char.isdigit() for char in text):
                    article_dates.append(text)
            
            for elem in article.find_all('time'):
                text = elem.get_text(strip=True)
                if text:
                    article_dates.append(text)
            
            if article_dates:
                print(f"   Даты в статье: {article_dates}")
            else:
                print(f"   Даты в статье: не найдены")
        
        # Тестируем извлечение информации о конкретной статье
        print(f"\n🔍 Тестирование извлечения информации о статье Thunderforge...")
        print("-" * 60)
        
        # Ищем статью с заголовком "Thunderforge"
        thunderforge_article = None
        for article in articles:
            title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
            if title_elem and 'Thunderforge' in title_elem.get_text():
                thunderforge_article = article
                break
        
        if thunderforge_article:
            print("✅ Найдена статья Thunderforge")
            
            # Извлекаем информацию
            article_info = scraper.extract_article_info(thunderforge_article, "AI")
            if article_info:
                print(f"✅ Заголовок: {article_info['title']}")
                print(f"✅ Ссылка: {article_info['link']}")
                print(f"✅ Автор: {article_info['author']}")
                print(f"✅ Дата (текст): '{article_info['date']}'")
                print(f"✅ Дата (парсинг): {article_info['parsed_date']}")
                print(f"✅ Статья за сегодня: {article_info['parsed_date'] == scraper.today if article_info['parsed_date'] else False}")
            else:
                print("❌ Не удалось извлечь информацию о статье")
        else:
            print("❌ Статья Thunderforge не найдена в списке статей")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ieee_structure() 