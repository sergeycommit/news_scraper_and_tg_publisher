#!/usr/bin/env python3
"""
Менеджер для работы с единым файлом published_urls.json
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

class PublishedURLsManager:
    """Класс для управления опубликованными URL в едином файле"""
    
    def __init__(self, file_path='published_urls.json'):
        self.file_path = file_path
        self.data = self.load_data()
    
    def load_data(self):
        """Загрузка данных из файла"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded published URLs from {self.file_path}")
                    return data
            else:
                logger.info(f"Published URLs file not found: {self.file_path}, creating new one")
                return self._create_empty_structure()
        except Exception as e:
            logger.error(f"Error loading published URLs: {e}")
            return self._create_empty_structure()
    
    def _create_empty_structure(self):
        """Создание пустой структуры данных"""
        return {
            "robotreport": [],
            "theverge": [],
            "wired": [],
            "techxplore": [],
            "sciencedaily": [],
            "zdnet": [],
            "arstechnica": []
        }
    
    def save_data(self):
        """Сохранение данных в файл"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved published URLs to {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving published URLs: {e}")
            return False
    
    def add_url(self, source, url):
        """Добавление URL для конкретного источника"""
        if source not in self.data:
            logger.warning(f"Unknown source: {source}, creating new entry")
            self.data[source] = []
        
        if url not in self.data[source]:
            self.data[source].append(url)
            logger.info(f"Added URL to {source}: {url}")
            return True
        else:
            logger.info(f"URL already exists in {source}: {url}")
            return False
    
    def is_url_published(self, source, url):
        """Проверка, был ли URL уже опубликован для конкретного источника"""
        if source not in self.data:
            return False
        return url in self.data[source]
    
    def get_published_urls(self, source):
        """Получение списка опубликованных URL для конкретного источника"""
        return self.data.get(source, [])
    
    def get_all_urls(self):
        """Получение всех опубликованных URL"""
        all_urls = []
        for source, urls in self.data.items():
            all_urls.extend(urls)
        return all_urls
    
    def get_stats(self):
        """Получение статистики по источникам"""
        stats = {}
        for source, urls in self.data.items():
            stats[source] = len(urls)
        return stats
    
    def migrate_from_old_files(self):
        """Миграция данных из старых отдельных файлов"""
        old_files = {
            'robotreport': 'robotreport_published_urls.json',
            'theverge': 'theverge_published_urls.json',
            'wired': 'wired_published_urls.json',
            'techxplore': 'techxplore_published_urls.json',
            'sciencedaily': 'sciencedaily_published_urls.json',
            'zdnet': 'zdnet_published_urls.json',
            'arstechnica': 'arstechnica_published_urls.json'
        }
        
        migrated = 0
        for source, old_file in old_files.items():
            if os.path.exists(old_file):
                try:
                    with open(old_file, 'r', encoding='utf-8') as f:
                        old_data = json.load(f)
                        urls = old_data.get('published_urls', [])
                        if urls:
                            self.data[source] = urls
                            migrated += len(urls)
                            logger.info(f"Migrated {len(urls)} URLs from {old_file}")
                except Exception as e:
                    logger.error(f"Error migrating {old_file}: {e}")
        
        if migrated > 0:
            self.save_data()
            logger.info(f"Total migrated URLs: {migrated}")
        
        return migrated

# Глобальный экземпляр менеджера
urls_manager = PublishedURLsManager()

def get_urls_manager():
    """Получение глобального экземпляра менеджера"""
    return urls_manager
