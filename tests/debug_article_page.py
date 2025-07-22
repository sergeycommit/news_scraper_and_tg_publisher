#!/usr/bin/env python3
"""
Debug script для анализа структуры страницы статьи IEEE Spectrum
"""

import requests
from bs4 import BeautifulSoup
import re

def find_article_url():
    """Поиск URL статьи на странице robotics"""
    print("🔍 Поиск URL статьи на странице robotics...")
    
    url = "https://spectrum.ieee.org/topic/robotics"
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
            # Берем первую статью
            first_article = articles[0]
            
            # Ищем заголовок для отладки
            title_elem = first_article.find('h2') or first_article.find('h3')
            if title_elem:
                title = title_elem.get_text(strip=True)
                print(f"📝 Заголовок первой статьи: {title}")
            
            # Анализируем структуру статьи
            print(f"\n🏗️ Структура статьи:")
            for i, child in enumerate(first_article.children):
                if hasattr(child, 'name') and child.name:
                    print(f"   {i}: <{child.name}> {child.get('class', '')}")
                    if child.name == 'a':
                        href = child.get('href')
                        text = child.get_text(strip=True)
                        print(f"      href='{href}' text='{text}'")
            
            # Ищем все ссылки в статье
            links = first_article.find_all('a')
            print(f"\n🔗 Найдено ссылок в статье: {len(links)}")
            
            for i, link in enumerate(links):
                href = link.get('href')
                text = link.get_text(strip=True)
                print(f"   Ссылка {i+1}: {href} - '{text}'")
                
                # Ищем ссылку на статью (не на topic, не на type)
                if href and not any(exclude in href for exclude in ['/topic/', '/type/', 'spectrum.ieee.org/topic/', 'spectrum.ieee.org/type/']):
                    if href.startswith('/'):
                        article_url = f"https://spectrum.ieee.org{href}"
                    elif href.startswith('http'):
                        article_url = href
                    else:
                        continue
                    
                    print(f"🔗 Найдена ссылка на статью: {article_url}")
                    return article_url
            
            # Если не нашли подходящую ссылку, попробуем найти по заголовку
            print(f"\n🔍 Поиск по заголовку...")
            if title:
                # Ищем ссылку, которая содержит текст заголовка
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    if text and any(word in text.lower() for word in ['deepmind', 'robots', 'tennis']):
                        if href.startswith('/'):
                            article_url = f"https://spectrum.ieee.org{href}"
                        elif href.startswith('http'):
                            article_url = href
                        else:
                            continue
                        
                        print(f"🔗 Найдена ссылка по заголовку: {article_url}")
                        return article_url
        
        return None
        
    except Exception as e:
        print(f"❌ Ошибка поиска статьи: {e}")
        return None

def analyze_article_page(url):
    """Анализ структуры страницы статьи IEEE Spectrum"""
    print(f"🔍 Анализ страницы статьи: {url}")
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
        
        # Ищем элементы picture
        pictures = soup.find_all('picture')
        print(f"📸 Найдено элементов picture: {len(pictures)}")
        
        for i, picture in enumerate(pictures):
            print(f"\n🔍 Picture {i+1}:")
            
            # Ищем source элементы
            sources = picture.find_all('source')
            print(f"   📹 Sources: {len(sources)}")
            
            for j, source in enumerate(sources):
                srcset = source.get('srcset')
                src = source.get('src')
                media = source.get('media')
                type_attr = source.get('type')
                
                print(f"     Source {j+1}:")
                print(f"       srcset: {srcset}")
                print(f"       src: {src}")
                print(f"       media: {media}")
                print(f"       type: {type_attr}")
            
            # Ищем img элемент
            img = picture.find('img')
            if img:
                src = img.get('src')
                alt = img.get('alt')
                width = img.get('width')
                height = img.get('height')
                
                print(f"   🖼️ Img:")
                print(f"     src: {src}")
                print(f"     alt: {alt}")
                print(f"     width: {width}")
                print(f"     height: {height}")
        
        # Ищем все img элементы
        images = soup.find_all('img')
        print(f"\n🖼️ Всего изображений: {len(images)}")
        
        # Ищем GIF файлы
        gif_images = []
        for img in images:
            src = img.get('src', '')
            if '.gif' in src.lower():
                gif_images.append(img)
        
        print(f"🎬 Найдено GIF изображений: {len(gif_images)}")
        
        for i, gif in enumerate(gif_images):
            src = gif.get('src')
            alt = gif.get('alt')
            print(f"   GIF {i+1}: {src}")
            print(f"     alt: {alt}")
        
        # Ищем в meta тегах
        meta_images = []
        for meta in soup.find_all('meta'):
            property_attr = meta.get('property', '')
            name_attr = meta.get('name', '')
            content = meta.get('content', '')
            
            if any(prop in property_attr.lower() for prop in ['image', 'og:image', 'twitter:image']):
                meta_images.append((property_attr, content))
        
        print(f"\n📋 Meta изображения: {len(meta_images)}")
        for prop, content in meta_images:
            print(f"   {prop}: {content}")
        
        # Ищем в JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        print(f"\n📄 JSON-LD скриптов: {len(scripts)}")
        
        for i, script in enumerate(scripts):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and 'image' in data:
                    print(f"   JSON-LD {i+1} image: {data['image']}")
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        return False

def main():
    """Главная функция"""
    print("🔍 Анализ структуры страниц статей IEEE Spectrum")
    print("=" * 70)
    
    # Сначала найдем URL статьи
    article_url = find_article_url()
    
    if article_url:
        print(f"\n{'='*20} Анализ статьи {'='*20}")
        analyze_article_page(article_url)
    else:
        print("❌ Не удалось найти URL статьи")

if __name__ == "__main__":
    main() 