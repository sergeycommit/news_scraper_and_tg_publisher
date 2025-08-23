#!/usr/bin/env python3
"""
Wired Robots Scraper and Telegram Publisher
Автоматический скраппер статей с Wired robots раздела с публикацией в Telegram
"""

import os
import logging
import requests
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram_publisher import TelegramPublisher
from urllib.parse import urljoin, urlparse
import json
import time
import sys
import re
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wired_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WiredRobotsScraper:
    def __init__(self):
        load_dotenv()
        
        # Конфигурация OpenRouter
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.ai_model = os.getenv('AI_MODEL', 'google/gemini-pro')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.7'))
        self.prompt = os.getenv('PROMPT')
        self.system_prompt = os.getenv('SYSTEM_PROMPT')
        
        # Конфигурация Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_channel = os.getenv('TELEGRAM_CHANNEL_ID')
        
        # Wired URLs
        self.base_url = 'https://www.wired.com'
        self.robots_url = 'https://www.wired.com/tag/robots/'
        
        # Даты для фильтрации (статьи не старше 2 дней)
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=2)
        
        # Создаем папку для JSON файлов
        self.json_folder = 'wired_articles_archive'
        self.create_json_folder()
        
        # Файл для отслеживания опубликованных URL
        self.published_urls_file = 'wired_published_urls.json'
        self.published_urls = self.load_published_urls()
        
        # Инициализация TelegramPublisher
        self.telegram_publisher = TelegramPublisher(
            telegram_token=self.telegram_token,
            telegram_channel=self.telegram_channel,
            openai_api_key=self.openrouter_api_key,
            ai_model=self.ai_model
        )
        
        # Заголовки для запросов
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        logger.info("Wired Robots Scraper initialized successfully")
        logger.info(f"Loaded {len(self.published_urls)} previously published URLs")
        logger.info(f"Filtering articles for today and yesterday: {self.yesterday} to {self.today}")
    
    def create_json_folder(self):
        """Создание папки для JSON файлов"""
        try:
            if not os.path.exists(self.json_folder):
                os.makedirs(self.json_folder)
                logger.info(f"Created JSON folder: {self.json_folder}")
            else:
                logger.info(f"JSON folder already exists: {self.json_folder}")
        except Exception as e:
            logger.error(f"Error creating JSON folder: {e}")
            self.json_folder = '.'
    
    def load_published_urls(self):
        """Загрузка списка уже опубликованных URL"""
        try:
            if os.path.exists(self.published_urls_file):
                with open(self.published_urls_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('published_urls', [])
            else:
                logger.info(f"Published URLs file not found: {self.published_urls_file}")
                return []
        except Exception as e:
            logger.error(f"Error loading published URLs: {e}")
            return []
    
    def save_published_urls(self):
        """Сохранение списка опубликованных URL"""
        try:
            data = {'published_urls': self.published_urls}
            with open(self.published_urls_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.published_urls)} published URLs")
        except Exception as e:
            logger.error(f"Error saving published URLs: {e}")
    
    def add_published_url(self, url):
        """Добавление URL в список опубликованных"""
        if url not in self.published_urls:
            self.published_urls.append(url)
            self.save_published_urls()
    
    def is_url_published(self, url):
        """Проверка, был ли URL уже опубликован"""
        return url in self.published_urls

    def parse_article_date(self, date_text):
        """Парсинг даты статьи из текста Wired"""
        try:
            # Убираем лишние пробелы и символы
            date_text = date_text.strip()
            
            # Паттерны для различных форматов дат на Wired
            patterns = [
                r'(\d{1,2})\s+(hour|hours|minute|minutes|day|days)\s+ago',
                r'(\w+)\s+(\d{1,2})',  # Aug 21
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_text, re.IGNORECASE)
                if match:
                    if 'ago' in date_text.lower():
                        # Обработка относительных дат (X hours ago, X minutes ago)
                        amount = int(match.group(1))
                        unit = match.group(2).lower()
                        
                        if unit in ['hour', 'hours']:
                            return self.today - timedelta(hours=amount)
                        elif unit in ['minute', 'minutes']:
                            return self.today
                        elif unit in ['day', 'days']:
                            return self.today - timedelta(days=amount)
                    
                    elif len(match.groups()) == 2:
                        # Формат Aug 21
                        month_name = match.group(1)
                        day = int(match.group(2))
                        year = self.today.year
                        
                        # Словарь для месяцев
                        months = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        
                        month = months.get(month_name.lower()[:3], 1)
                        
                        # Проверяем, не прошлогодняя ли это статья
                        article_date = date(year, month, day)
                        if article_date > self.today:
                            article_date = date(year - 1, month, day)
                        
                        return article_date
            
            # Если не удалось распарсить, возвращаем None
            logger.warning(f"Could not parse date: {date_text}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_text}': {e}")
            return None
    
    def extract_date_from_url(self, url):
        """Извлечение даты из URL статьи Wired"""
        try:
            # Паттерны для поиска дат в URL Wired
            patterns = [
                r'/(\d{4})/(\d{1,2})/(\d{1,2})/',  # /2025/08/05/
                r'(\d{4})-(\d{1,2})-(\d{1,2})',    # 2025-08-05
                r'(\d{1,2})-(\d{1,2})-(\d{4})',    # 08-05-2025
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        if len(groups[0]) == 4:  # YYYY-MM-DD или YYYY/MM/DD
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # MM-DD-YYYY
                            month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                        
                        # Проверяем валидность даты
                        try:
                            return date(year, month, day)
                        except ValueError:
                            logger.warning(f"Invalid date in URL: {year}-{month}-{day}")
                            continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting date from URL: {e}")
            return None
    
    def is_article_from_recent_days(self, article_date):
        """Проверка, что статья не старше 2 дней от текущей даты"""
        # Для Wired скрапера не фильтруем по дате - публикуем любую новость
        return True
    
    def scrape_wired_articles(self):
        """Основной метод скрапинга статей с Wired robots раздела"""
        logger.info("Starting Wired robots articles scraping...")
        logger.info("No date filtering - will publish any unpublished article")
        
        try:
            logger.info(f"Scraping robots articles from: {self.robots_url}")
            articles = self.scrape_robots_page(self.robots_url)
            logger.info(f"Found {len(articles)} articles in robots section")
            return articles
        except Exception as e:
            logger.error(f"Error scraping robots articles: {e}")
            return []
    
    def scrape_robots_page(self, url):
        """Скрапинг статей с robots страницы Wired"""
        articles = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем статьи на странице Wired robots
            # Wired использует ссылки с /story/ для статей
            article_links = soup.find_all('a', href=re.compile(r'/story/'))
            
            logger.info(f"Found {len(article_links)} story links on Wired robots page")
            
            # Фильтруем только robots статьи
            robots_articles = []
            for link in article_links:
                try:
                    # Получаем родительский элемент для извлечения информации
                    parent_element = link.parent
                    if not parent_element:
                        parent_element = link
                    
                    logger.info(f"Processing story link: {link['href']}")
                    article_info = self.extract_article_info_from_link(link, parent_element)
                    if article_info:
                        robots_articles.append(article_info)
                        logger.info(f"Added robots article: {article_info['title'][:50]}...")
                    else:
                        logger.info(f"Article info extraction failed for link: {link['href']}")
                except Exception as e:
                    logger.warning(f"Error extracting article info from link: {e}")
                    continue
            
            logger.info(f"Robots articles after filtering: {len(robots_articles)}")
            return robots_articles
            
        except Exception as e:
            logger.error(f"Error scraping robots page {url}: {e}")
            return []

    def extract_article_info(self, element):
        """Извлечение информации о статье из элемента Wired"""
        try:
            # Поиск ссылки на статью
            link_element = element.find('a', href=True)
            if not link_element:
                return None
            
            article_url = link_element['href']
            if not article_url.startswith('http'):
                article_url = urljoin(self.base_url, article_url)
            
            # Проверяем, что это ссылка на статью Wired
            if not article_url.startswith('https://www.wired.com/'):
                return None
            
            # Поскольку мы скрапим с robots страницы (https://www.wired.com/tag/robots/),
            # ВСЕ найденные статьи автоматически считаются robots статьями
            is_robots_article = True
            
            # Проверяем, что это валидная статья Wired
            if not article_url.startswith('https://www.wired.com/'):
                logger.info(f"Article excluded (not from Wired): {article_url}")
                return None
            
            # Поиск заголовка
            title_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if not title_element:
                # Ищем заголовок в специальных классах Wired
                title_element = element.find(class_=re.compile(r'title|headline|entry-title|c-entry-title|SummaryItemHed'))
                if not title_element:
                    title_element = link_element
            
            title = title_element.get_text(strip=True) if title_element else "No title"
            
            # Очищаем заголовок от лишних символов
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Проверяем минимальную длину заголовка
            if len(title) < 10:
                return None
            
            # Поиск даты - ищем в элементе
            date_text = ""
            
            # 1. Поиск по стандартным селекторам Wired
            date_element = element.find(['time', 'span', 'div'], 
                                     class_=re.compile(r'date|time|published|updated|SummaryItemPublishDate'))
            if date_element:
                date_text = date_element.get_text(strip=True)
            
            # 2. Поиск по атрибутам
            if not date_text:
                date_element = element.find(['time', 'span', 'div'], 
                                         attrs={'datetime': True})
                if date_element:
                    date_text = date_element.get('datetime', '')
            
            # 3. Поиск по тексту с датами
            if not date_text:
                all_text = element.get_text()
                date_patterns = [
                    r'\b\d{1,2}\s+(hour|hours|minute|minutes|day|days)\s+ago\b',
                    r'\b\w+\s+\d{1,2}\b',  # Aug 21
                    r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                    r'\b\d{4}-\d{1,2}-\d{1,2}\b'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, all_text, re.IGNORECASE)
                    if match:
                        date_text = match.group(0)
                        break
            
            # Поиск описания
            desc_element = element.find(['p', 'div'], 
                                     class_=re.compile(r'description|excerpt|summary|content|SummaryItemDek'))
            description = desc_element.get_text(strip=True) if desc_element else ""
            
            # Парсинг даты
            article_date = self.parse_article_date(date_text)
            
            # Дополнительная проверка даты из URL
            url_date = self.extract_date_from_url(article_url)
            if url_date:
                article_date = url_date
                logger.info(f"Using date from URL: {article_date} for article: {title[:50]}...")
            
            # Для Wired скрапера не исключаем статьи без даты
            # Если есть дата из URL, используем её
            if url_date:
                article_date = url_date
            elif article_date is None:
                # Если нет даты, устанавливаем сегодняшнюю дату
                article_date = self.today
                logger.info(f"No date found, using today's date: {article_date} for article: {title[:50]}...")
            
            # Проверка, что статья из последних дней (всегда True для Wired)
            if not self.is_article_from_recent_days(article_date):
                logger.info(f"Article filtered out (too old): {title[:50]}... (date: {article_date}, cutoff: {self.yesterday})")
                return None
            
            logger.info(f"Found recent article: {title[:50]}... -> {article_url} (date: {article_date})")
            logger.info(f"Article passed date filter successfully")
            
            return {
                'title': title,
                'url': article_url,
                'date': article_date,
                'description': description,
                'topic': 'Robots'
            }
            
        except Exception as e:
            logger.warning(f"Error extracting article info: {e}")
            return None
    
    def extract_article_info_from_link(self, link, parent_element):
        """Извлечение информации о статье из ссылки Wired"""
        try:
            # Получаем URL статьи
            article_url = link['href']
            if not article_url.startswith('http'):
                article_url = urljoin(self.base_url, article_url)
            
            # Проверяем, что это ссылка на статью Wired
            if not article_url.startswith('https://www.wired.com/'):
                return None
            
            # Поиск заголовка
            title = link.get_text(strip=True)
            if not title:
                # Ищем заголовок в родительском элементе
                title_element = parent_element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_element:
                    title = title_element.get_text(strip=True)
                else:
                    # Ищем заголовок в специальных классах Wired
                    title_element = parent_element.find(class_=re.compile(r'title|headline|entry-title|c-entry-title|SummaryItemHed'))
                    if title_element:
                        title = title_element.get_text(strip=True)
            
            # Очищаем заголовок от лишних символов
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Проверяем минимальную длину заголовка
            if len(title) < 10:
                logger.info(f"Title too short: '{title}'")
                return None
            
            # Поиск даты - ищем в родительском элементе
            date_text = ""
            
            # 1. Поиск по стандартным селекторам Wired
            date_element = parent_element.find(['time', 'span', 'div'], 
                                         class_=re.compile(r'date|time|published|updated|SummaryItemPublishDate'))
            if date_element:
                date_text = date_element.get_text(strip=True)
            
            # 2. Поиск по атрибутам
            if not date_text:
                date_element = parent_element.find(['time', 'span', 'div'], 
                                             attrs={'datetime': True})
                if date_element:
                    date_text = date_element.get('datetime', '')
            
            # 3. Поиск по тексту с датами
            if not date_text:
                all_text = parent_element.get_text()
                date_patterns = [
                    r'\b\d{1,2}\s+(hour|hours|minute|minutes|day|days)\s+ago\b',
                    r'\b\w+\s+\d{1,2}\b',  # Aug 21
                    r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                    r'\b\d{4}-\d{1,2}-\d{1,2}\b'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, all_text, re.IGNORECASE)
                    if match:
                        date_text = match.group(0)
                        break
            
            # Поиск описания
            desc_element = parent_element.find(['p', 'div'], 
                                         class_=re.compile(r'description|excerpt|summary|content|SummaryItemDek'))
            description = desc_element.get_text(strip=True) if desc_element else ""
            
            # Парсинг даты
            article_date = self.parse_article_date(date_text)
            
            # Дополнительная проверка даты из URL
            url_date = self.extract_date_from_url(article_url)
            if url_date:
                article_date = url_date
                logger.info(f"Using date from URL: {article_date} for article: {title[:50]}...")
            
            # Для Wired скрапера не исключаем статьи без даты
            # Если есть дата из URL, используем её
            if url_date:
                article_date = url_date
            elif article_date is None:
                # Если нет даты, устанавливаем сегодняшнюю дату
                article_date = self.today
                logger.info(f"No date found, using today's date: {article_date} for article: {title[:50]}...")
            
            # Проверка, что статья из последних дней (всегда True для Wired)
            if not self.is_article_from_recent_days(article_date):
                logger.info(f"Article filtered out (too old): {title[:50]}... (date: {article_date}, cutoff: {self.yesterday})")
                return None
            
            logger.info(f"Found recent article: {title[:50]}... -> {article_url} (date: {article_date})")
            logger.info(f"Article passed date filter successfully")
            
            return {
                'title': title,
                'url': article_url,
                'date': article_date,
                'description': description,
                'topic': 'Robots'
            }
            
        except Exception as e:
            logger.warning(f"Error extracting article info from link: {e}")
            return None
    
    def filter_unpublished_articles(self, articles):
        """Фильтрация неопубликованных статей"""
        unpublished = []
        for article in articles:
            if not self.is_url_published(article['url']):
                unpublished.append(article)
            else:
                logger.info(f"Article already published: {article['title']}")
        
        logger.info(f"Found {len(unpublished)} unpublished articles")
        return unpublished
    
    def select_best_article(self, articles):
        """Выбор лучшей статьи для публикации"""
        if not articles:
            return None
        
        # Фильтруем статьи, исключаем служебные страницы
        valid_articles = []
        for article in articles:
            url = article.get('url', '')
            title = article.get('title', '').lower()
            
            # Поскольку все статьи уже из robots раздела, просто проверяем валидность
            # Исключаем служебные страницы и не-статьи
            if not any(exclude in title for exclude in ['see all', 'topic', 'category', 'more', 'follow']):
                valid_articles.append(article)
        
        if not valid_articles:
            # Если нет валидных статей, берем первую
            return articles[0] if articles else None
        
        # Сортируем по дате (новые сначала)
        sorted_articles = sorted(valid_articles, key=lambda x: x['date'], reverse=True)
        
        # Предпочитаем статьи с описанием
        articles_with_desc = [a for a in sorted_articles if a.get('description', '').strip()]
        
        if articles_with_desc:
            return articles_with_desc[0]
        else:
            return sorted_articles[0]

    def scrape_article_content_and_media(self, article_url):
        """Скрапинг содержимого статьи и медиа Wired"""
        try:
            response = requests.get(article_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлечение основного контента Wired
            content_selectors = [
                '.ArticleBodyContent',  # Основной контент Wired
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content-body',
                'article',
                'main'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    logger.info(f"Found content using selector: {selector}")
                    break
            
            if not content_element:
                # Альтернативный поиск по классам
                content_element = soup.find('div', class_=re.compile(r'content|body|text|entry|ArticleBody'))
                if content_element:
                    logger.info("Found content using alternative search")
            
            content = ""
            if content_element:
                # Удаляем ненужные элементы
                for unwanted in content_element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                    unwanted.decompose()
                
                # Извлекаем текст
                content = content_element.get_text(separator='\n', strip=True)
                logger.info(f"Extracted content length: {len(content)} characters")
            
            # Извлечение изображения
            media_url = self.extract_article_image(soup, article_url)
            
            return {
                'content': content,
                'media_url': media_url
            }
            
        except Exception as e:
            logger.error(f"Error extracting article content and media: {e}")
            return {'content': "", 'media_url': None}
    
    def extract_article_image(self, soup, article_url):
        """Извлечение изображения статьи Wired"""
        try:
            # Приоритетные селекторы для изображений Wired
            image_selectors = [
                'meta[property="og:image"]',  # Open Graph изображение
                'meta[name="twitter:image"]',  # Twitter изображение
                '.ArticleBodyContent img',     # Изображения в контенте статьи
                '.article-hero img',           # Hero изображение статьи
                '.entry-hero img',             # Hero изображение записи
                '.hero-image img',             # Hero изображение
                '.featured-image img',         # Избранное изображение
                '.article-image img',          # Изображение статьи
                '.entry-image img',            # Изображение записи
                '.post-image img',             # Изображение поста
                'img[data-src]',              # Lazy loading изображения
                'img[src*="media.wired.com"]' # CDN изображения Wired
            ]
            
            for selector in image_selectors:
                if selector.startswith('meta'):
                    # Для meta тегов
                    meta_element = soup.select_one(selector)
                    if meta_element and meta_element.get('content'):
                        image_url = meta_element['content']
                        if self.is_valid_image_url(image_url):
                            logger.info(f"Found image using meta selector: {selector}")
                            return self.normalize_image_url(image_url, article_url)
                else:
                    # Для img тегов
                    img_element = soup.select_one(selector)
                    if img_element:
                        image_url = img_element.get('src') or img_element.get('data-src')
                        if image_url and self.is_valid_image_url(image_url):
                            logger.info(f"Found image using selector: {selector}")
                            return self.normalize_image_url(image_url, article_url)
            
            # Альтернативный поиск по атрибутам
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and self.is_valid_image_url(src):
                    # Проверяем размеры изображения
                    width = img.get('width') or img.get('data-width')
                    height = img.get('height') or img.get('data-height')
                    
                    if width and height:
                        try:
                            w, h = int(width), int(height)
                            if w >= 300 and h >= 200:  # Минимальные размеры для качественного изображения
                                logger.info(f"Found image with good dimensions: {w}x{h}")
                                return self.normalize_image_url(src, article_url)
                        except (ValueError, TypeError):
                            pass
                    
                    # Если нет размеров, берем первое подходящее изображение
                    logger.info("Found image without dimensions")
                    return self.normalize_image_url(src, article_url)
            
            logger.warning("No suitable image found")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting article image: {e}")
            return None
    
    def is_valid_image_url(self, url):
        """Проверка валидности URL изображения"""
        if not url:
            return False
        
        # Исключаем служебные изображения
        invalid_patterns = [
            'logo', 'icon', 'avatar', 'placeholder', 'blank',
            'spacer', 'pixel', 'tracking', 'analytics',
            'social', 'share', 'button', 'banner'
        ]
        
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in invalid_patterns):
            return False
        
        # Проверяем расширения изображений
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        if not any(ext in url_lower for ext in valid_extensions):
            return False
        
        return True
    
    def normalize_image_url(self, image_url, article_url):
        """Нормализация URL изображения"""
        if not image_url:
            return None
        
        # Если URL относительный, делаем абсолютным
        if image_url.startswith('//'):
            return 'https:' + image_url
        elif image_url.startswith('/'):
            # Извлекаем домен из URL статьи
            from urllib.parse import urlparse
            parsed = urlparse(article_url)
            return f"{parsed.scheme}://{parsed.netloc}{image_url}"
        elif not image_url.startswith('http'):
            # Относительный URL
            from urllib.parse import urljoin
            return urljoin(article_url, image_url)
        
        return image_url

    def save_article_data(self, article, post_content, media_url=None):
        """Сохранение данных статьи в JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"wired_article_{timestamp}.json"
            filepath = os.path.join(self.json_folder, filename)
            
            data = {
                'title': article['title'],
                'url': article['url'],
                'date': article['date'].isoformat(),
                'topic': article['topic'],
                'description': article.get('description', ''),
                'post_content': post_content,
                'media_url': media_url,
                'published_at': datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved article data: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving article data: {e}")
    
    async def run_daily_scraping(self):
        """Основной метод запуска ежедневного скрапинга"""
        try:
            logger.info("🚀 Starting Wired robots daily scraping...")
            
            # Скрапим статьи
            articles = self.scrape_wired_articles()
            
            if not articles:
                logger.warning("No articles found")
                return None
            
            # Берем только первую (последнюю) статью
            latest_article = articles[0]
            logger.info(f"Latest article: {latest_article['title']}")
            logger.info(f"Article URL: {latest_article['url']}")
            
            # Проверяем, была ли уже опубликована эта статья
            if self.is_url_published(latest_article['url']):
                logger.info("Latest article already published. Exiting.")
                return None
            
            # Статья новая, публикуем её
            best_article = latest_article
            
            # Проверяем наличие заголовка
            if not best_article.get('title') or len(best_article['title'].strip()) < 10:
                logger.warning("Article title too short or missing")
                return None
            
            # Скрапим содержимое статьи и медиа
            article_data = self.scrape_article_content_and_media(best_article['url'])
            
            if not article_data['content']:
                logger.warning("No content extracted from article")
                return None
            
            # Проверяем минимальную длину контента
            if len(article_data['content'].strip()) < 100:
                logger.warning("Article content too short")
                return None
            
            logger.info(f"Extracted content length: {len(article_data['content'])} characters")
            if article_data['media_url']:
                logger.info(f"Found media URL: {article_data['media_url']}")

            # Создаем пост и публикуем через TelegramPublisher
            logger.info(f"Creating and publishing post with URL: {best_article['url']}")
            result = await self.telegram_publisher.create_and_publish_post(
                title=best_article['title'],
                content=article_data['content'],
                article_url=best_article['url'],
                topic=best_article['topic'],
                media_url=article_data.get('media_url')
            )
            
            if result['success']:
                # Сохраняем данные и добавляем URL в опубликованные
                self.add_published_url(best_article['url'])
                self.save_article_data(best_article, result['post_content'], result.get('media_url'))
                logger.info("✅ Article published successfully!")
                return best_article
            else:
                logger.error(f"❌ Failed to publish article: {result.get('error', 'Unknown error')}")
                return None
            
        except Exception as e:
            logger.error(f"Error in daily scraping: {e}")
            return None

async def main():
    """Основная функция"""
    scraper = WiredRobotsScraper()
    result = await scraper.run_daily_scraping()
    if result:
        print(f"Published article: {result['title']}")
    else:
        print("No new articles to publish")

def run_with_proper_cleanup():
    """Запуск с правильной очисткой ресурсов"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Wired robots scraper finished")

if __name__ == "__main__":
    run_with_proper_cleanup()
