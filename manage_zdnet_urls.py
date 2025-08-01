#!/usr/bin/env python3
"""
ZDNet URL Manager
Управление опубликованными URL для ZDNet скраппера
"""

import json
import os
import sys
from datetime import datetime

def load_published_urls():
    """Загрузка списка опубликованных URL"""
    filename = 'zdnet_published_urls.json'
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('published_urls', [])
        else:
            print(f"File {filename} not found")
            return []
    except Exception as e:
        print(f"Error loading URLs: {e}")
        return []

def save_published_urls(urls):
    """Сохранение списка опубликованных URL"""
    filename = 'zdnet_published_urls.json'
    try:
        data = {'published_urls': urls}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(urls)} URLs to {filename}")
    except Exception as e:
        print(f"Error saving URLs: {e}")

def show_urls():
    """Показать все опубликованные URL"""
    urls = load_published_urls()
    if not urls:
        print("No published URLs found")
        return
    
    print(f"Found {len(urls)} published URLs:")
    print("-" * 50)
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")

def add_url(url):
    """Добавить URL в список опубликованных"""
    urls = load_published_urls()
    if url not in urls:
        urls.append(url)
        save_published_urls(urls)
        print(f"Added URL: {url}")
    else:
        print(f"URL already exists: {url}")

def remove_url(url_or_index):
    """Удалить URL из списка опубликованных"""
    urls = load_published_urls()
    
    try:
        # Пробуем как индекс
        index = int(url_or_index) - 1
        if 0 <= index < len(urls):
            removed_url = urls.pop(index)
            save_published_urls(urls)
            print(f"Removed URL: {removed_url}")
        else:
            print("Invalid index")
    except ValueError:
        # Пробуем как URL
        if url_or_index in urls:
            urls.remove(url_or_index)
            save_published_urls(urls)
            print(f"Removed URL: {url_or_index}")
        else:
            print(f"URL not found: {url_or_index}")

def clear_urls():
    """Очистить все опубликованные URL"""
    confirm = input("Are you sure you want to clear all published URLs? (y/N): ")
    if confirm.lower() == 'y':
        save_published_urls([])
        print("All published URLs cleared")
    else:
        print("Operation cancelled")

def search_urls(query):
    """Поиск URL по ключевому слову"""
    urls = load_published_urls()
    matching_urls = [url for url in urls if query.lower() in url.lower()]
    
    if matching_urls:
        print(f"Found {len(matching_urls)} matching URLs:")
        print("-" * 50)
        for i, url in enumerate(matching_urls, 1):
            print(f"{i}. {url}")
    else:
        print(f"No URLs found matching '{query}'")

def show_stats():
    """Показать статистику"""
    urls = load_published_urls()
    print(f"Total published URLs: {len(urls)}")
    
    if urls:
        # Анализ доменов
        domains = {}
        for url in urls:
            try:
                domain = url.split('/')[2]  # Получаем домен
                domains[domain] = domains.get(domain, 0) + 1
            except:
                pass
        
        print("\nURLs by domain:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain}: {count}")

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("ZDNet URL Manager")
        print("Usage:")
        print("  python manage_zdnet_urls.py show")
        print("  python manage_zdnet_urls.py add <url>")
        print("  python manage_zdnet_urls.py remove <url_or_index>")
        print("  python manage_zdnet_urls.py clear")
        print("  python manage_zdnet_urls.py search <query>")
        print("  python manage_zdnet_urls.py stats")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'show':
        show_urls()
    elif command == 'add' and len(sys.argv) > 2:
        add_url(sys.argv[2])
    elif command == 'remove' and len(sys.argv) > 2:
        remove_url(sys.argv[2])
    elif command == 'clear':
        clear_urls()
    elif command == 'search' and len(sys.argv) > 2:
        search_urls(sys.argv[2])
    elif command == 'stats':
        show_stats()
    else:
        print("Invalid command or missing arguments")

if __name__ == "__main__":
    main() 