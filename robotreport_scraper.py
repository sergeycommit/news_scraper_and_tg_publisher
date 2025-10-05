    #!/usr/bin/env python3
"""
The Robot Report Scraper and Telegram Publisher
Автоматический скраппер статей с The Robot Report AI/Cognition раздела с публикацией в Telegram
"""

import os
import logging
import requests
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram_publisher import TelegramPublisher
from published_urls_manager import get_urls_manager
from urllib.parse import urljoin, urlparse
import json
import time
import sys
import re
import asyncio
import feedparser
import ssl
import urllib3

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('robotreport_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RobotReportScraper:
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
        
        # The Robot Report URLs
        self.base_url = 'https://www.therobotreport.com'
        self.rss_feed_url = 'https://www.therobotreport.com/category/design-development/ai-cognition/feed/'
        self.ai_cognition_url = 'https://www.therobotreport.com/category/design-development/ai-cognition/'
        
        # Даты для фильтрации (статьи не старше указанного количества дней)
        self.today = date.today()
        scraping_days = int(os.getenv('SCRAPING_DAYS', '2'))  # По умолчанию 2 дня
        self.yesterday = self.today - timedelta(days=scraping_days)
        
        # Создаем папку для JSON файлов
        self.json_folder = 'robotreport_articles_archive'
        self.create_json_folder()
        
        # Менеджер для отслеживания опубликованных URL
        self.urls_manager = get_urls_manager()
        self.source_name = 'robotreport'
        
        # Инициализация TelegramPublisher
        self.telegram_publisher = TelegramPublisher(
            telegram_token=self.telegram_token,
            telegram_channel=self.telegram_channel,
            openai_api_key=self.openrouter_api_key,
            ai_model=self.ai_model
        )
        
        # Заголовки для запросов
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',  # Отключаем сжатие для правильного парсинга
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # Отключаем предупреждения SSL
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        logger.info("The Robot Report Scraper initialized successfully")
        published_count = len(self.urls_manager.get_published_urls(self.source_name))
        logger.info(f"Loaded {published_count} previously published URLs")
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
        """Загрузка списка уже опубликованных URL (для совместимости)"""
        return self.urls_manager.get_published_urls(self.source_name)
    
    def save_published_urls(self):
        """Сохранение списка опубликованных URL (для совместимости)"""
        return self.urls_manager.save_data()
    
    def add_published_url(self, url):
        """Добавление URL в список опубликованных"""
        success = self.urls_manager.add_url(self.source_name, url)
        if success:
            self.urls_manager.save_data()
            logger.info(f"Added and saved URL to published list: {url}")
        return success
    
    def is_url_published(self, url):
        """Проверка, был ли URL уже опубликован"""
        return self.urls_manager.is_url_published(self.source_name, url)

    def parse_rss_feed(self):
        """Парсинг RSS фида The Robot Report"""
        try:
            logger.info(f"Parsing RSS feed: {self.rss_feed_url}")
            
            # Создаем сессию с отключенной проверкой SSL
            session = requests.Session()
            session.verify = False
            
            # Получаем RSS контент через requests
            response = session.get(self.rss_feed_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Парсим RSS контент
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"RSS feed parsing issues: {feed.bozo_exception}")
            
            articles = []
            
            for entry in feed.entries:
                try:
                    # Извлекаем информацию из RSS записи
                    title = entry.get('title', '').strip()
                    link = entry.get('link', '').strip()
                    description = entry.get('description', '').strip()
                    
                    # Парсим дату публикации
                    published_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_date = date(*entry.published_parsed[:3])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_date = date(*entry.updated_parsed[:3])
                    
                    # Если не удалось извлечь дату из RSS, пробуем из URL
                    if not published_date:
                        published_date = self.extract_date_from_url(link)
                    
                    # Проверяем, что статья не старше 2 дней
                    if published_date and not self.is_article_from_recent_days(published_date):
                        logger.info(f"Article filtered out (too old): {title[:50]}... (date: {published_date})")
                        continue
                    
                    # Поскольку мы парсим RSS фид категории AI/Cognition, все статьи автоматически относятся к этой категории
                    # Дополнительная проверка не нужна
                    
                    if title and link and published_date:
                        articles.append({
                            'title': title,
                            'url': link,
                            'date': published_date,
                            'description': description,
                            'topic': 'AI/Cognition'
                        })
                        logger.info(f"Found AI/Cognition article: {title[:50]}... -> {link} (date: {published_date})")
                
                except Exception as e:
                    logger.warning(f"Error processing RSS entry: {e}")
                    continue
            
            logger.info(f"Found {len(articles)} AI/Cognition articles from RSS feed")
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
            return []

    def is_ai_cognition_article(self, url, title, description):
        """Проверка, что статья относится к AI/Cognition категории"""
        try:
            # Ключевые слова для AI/Cognition
            ai_keywords = [
                'ai', 'artificial intelligence', 'machine learning', 'ml', 'neural network',
                'deep learning', 'cognition', 'cognitive', 'intelligence', 'smart',
                'autonomous', 'robotics', 'robot', 'automation', 'algorithm',
                'computer vision', 'nlp', 'natural language', 'chatbot', 'gpt',
                'llm', 'large language model', 'transformer', 'reinforcement learning',
                'data science', 'analytics', 'predictive', 'intelligent system'
            ]
            
            # Объединяем текст для поиска
            search_text = f"{title} {description}".lower()
            
            # Проверяем наличие AI ключевых слов
            for keyword in ai_keywords:
                if keyword in search_text:
                    return True
            
            # Проверяем URL на наличие AI/Cognition категории
            if 'ai-cognition' in url.lower() or 'design-development' in url.lower():
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking AI/Cognition category: {e}")
            return False

    def extract_date_from_url(self, url):
        """Извлечение даты из URL статьи"""
        try:
            # Паттерны для поиска дат в URL The Robot Report
            patterns = [
                r'/(\d{4})/(\d{1,2})/(\d{1,2})/',  # /2025/09/12/
                r'(\d{4})-(\d{1,2})-(\d{1,2})',    # 2025-09-12
                r'(\d{1,2})-(\d{1,2})-(\d{4})',    # 09-12-2025
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
        is_recent = article_date >= self.yesterday
        if not is_recent:
            logger.info(f"Article filtered out - too old: {article_date} (cutoff: {self.yesterday})")
        return is_recent

    def scrape_robotreport_articles(self):
        """Основной метод скрапинга статей с The Robot Report"""
        logger.info("Starting The Robot Report articles scraping...")
        scraping_days = int(os.getenv('SCRAPING_DAYS', '2'))
        logger.info(f"Date filter: articles not older than {self.yesterday} ({scraping_days} days from today)")
        
        # Сначала пробуем RSS фид
        articles = self.parse_rss_feed()
        
        # Если RSS не дал результатов, пробуем скрапинг страницы
        if not articles:
            logger.info("RSS feed didn't return articles, trying page scraping...")
            articles = self.scrape_ai_cognition_page()
        
        logger.info(f"Total articles found: {len(articles)}")
        logger.info(f"Date filtering: showing only articles from {self.yesterday} to {self.today}")
        return articles

    def scrape_ai_cognition_page(self):
        """Скрапинг статей с AI/Cognition страницы The Robot Report"""
        articles = []
        
        try:
            logger.info(f"Scraping AI/Cognition page: {self.ai_cognition_url}")
            
            # Создаем сессию с отключенной проверкой SSL
            session = requests.Session()
            session.verify = False
            
            response = session.get(self.ai_cognition_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем статьи на странице - The Robot Report использует article.type-post.entry
            article_selectors = [
                'article.type-post.entry',
                'article.type-post',
                'article.entry',
                'article',
                '.post',
                '.entry'
            ]
            
            article_elements = []
            for selector in article_selectors:
                elements = soup.select(selector)
                if elements:
                    article_elements.extend(elements)
                    logger.info(f"Found {len(elements)} articles with selector: {selector}")
                    break
            
            if not article_elements:
                # Альтернативный поиск по классам
                article_elements = soup.find_all('article', class_=re.compile(r'type-post|entry'))
                logger.info(f"Found {len(article_elements)} articles with alternative search")
            
            logger.info(f"Total article elements found: {len(article_elements)}")
            
            # Извлекаем информацию о статьях
            for element in article_elements:
                try:
                    article_info = self.extract_article_info(element)
                    if article_info:
                        articles.append(article_info)
                        logger.info(f"Added article: {article_info['title'][:50]}...")
                except Exception as e:
                    logger.warning(f"Error extracting article info: {e}")
                    continue
            
            logger.info(f"Articles after processing: {len(articles)}")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping AI/Cognition page: {e}")
            return []

    def extract_article_info(self, element):
        """Извлечение информации о статье из элемента"""
        try:
            # Поиск ссылки на статью
            link_element = element.find('a', href=True)
            if not link_element:
                return None
            
            article_url = link_element['href']
            if not article_url.startswith('http'):
                article_url = urljoin(self.base_url, article_url)
            
            # Проверяем, что это ссылка на статью The Robot Report
            if not article_url.startswith('https://www.therobotreport.com/'):
                return None
            
            # Поиск заголовка - The Robot Report использует h2.entry-title
            title_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], class_=re.compile(r'entry-title|title'))
            if not title_element:
                title_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if not title_element:
                title_element = element.find(class_=re.compile(r'title|headline|entry-title'))
                if not title_element:
                    title_element = link_element
            
            title = title_element.get_text(strip=True) if title_element else "No title"
            
            # Очищаем заголовок от лишних символов
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Проверяем минимальную длину заголовка
            if len(title) < 10:
                return None
            
            # Поиск описания
            desc_element = element.find(['p', 'div'], 
                                     class_=re.compile(r'description|excerpt|summary|content'))
            description = desc_element.get_text(strip=True) if desc_element else ""
            
            # Поиск даты - The Robot Report использует time.entry-time
            date_text = ""
            date_element = element.find(['time', 'span', 'div'], 
                                     class_=re.compile(r'entry-time|date|time|published|updated'))
            if date_element:
                date_text = date_element.get_text(strip=True)
            
            # Если не нашли дату в специальном элементе, ищем в entry-meta
            if not date_text:
                meta_element = element.find(class_=re.compile(r'entry-meta'))
                if meta_element:
                    time_element = meta_element.find('time')
                    if time_element:
                        date_text = time_element.get_text(strip=True)
            
            # Парсинг даты
            article_date = self.parse_article_date(date_text)
            
            # Дополнительная проверка даты из URL
            url_date = self.extract_date_from_url(article_url)
            if url_date:
                article_date = url_date
                logger.info(f"Using date from URL: {article_date} for article: {title[:50]}...")
            
            # Если не удалось извлечь дату, исключаем статью
            if article_date is None and not url_date:
                logger.info(f"Article excluded (no date found): {title[:50]}...")
                return None
            
            # Если есть дата из URL, используем её
            if url_date:
                article_date = url_date
            elif article_date is None:
                logger.info(f"Article excluded (no valid date): {title[:50]}...")
                return None
            
            # Проверка, что статья из последних дней
            if not self.is_article_from_recent_days(article_date):
                logger.info(f"Article filtered out (too old): {title[:50]}... (date: {article_date}, cutoff: {self.yesterday})")
                return None
            
            # Поскольку мы скрапим с страницы AI/Cognition категории, все статьи автоматически относятся к этой категории
            # Дополнительная проверка не нужна
            
            logger.info(f"Found recent AI/Cognition article: {title[:50]}... -> {article_url} (date: {article_date})")
            
            return {
                'title': title,
                'url': article_url,
                'date': article_date,
                'description': description,
                'topic': 'AI/Cognition'
            }
            
        except Exception as e:
            logger.warning(f"Error extracting article info: {e}")
            return None

    def parse_article_date(self, date_text):
        """Парсинг даты статьи из текста"""
        try:
            if not date_text:
                return None
                
            # Убираем лишние пробелы и символы
            date_text = date_text.strip()
            
            # Паттерны для различных форматов дат
            patterns = [
                r'(\d{1,2})\s+(hour|hours|minute|minutes|day|days)\s+ago',
                r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # September 11, 2025 или Sep 11 2025
                r'(\w+)\s+(\d{1,2})',  # Sep 12
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
                    
                    elif len(match.groups()) == 3:
                        # Формат September 11, 2025 или Sep 11 2025
                        month_name = match.group(1)
                        day = int(match.group(2))
                        year = int(match.group(3))
                        
                        # Словарь для месяцев
                        months = {
                            'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
                            'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
                            'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
                            'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
                            'oct': 10, 'october': 10, 'nov': 11, 'november': 11,
                            'dec': 12, 'december': 12
                        }
                        
                        month = months.get(month_name.lower(), 1)
                        
                        try:
                            return date(year, month, day)
                        except ValueError:
                            logger.warning(f"Invalid date: {year}-{month}-{day}")
                            continue
                    
                    elif len(match.groups()) == 2:
                        # Формат Sep 12
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
        """Скрапинг содержимого статьи и медиа The Robot Report"""
        try:
            # Создаем сессию с отключенной проверкой SSL
            session = requests.Session()
            session.verify = False
            
            response = session.get(article_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Устанавливаем правильную кодировку
            response.encoding = response.apparent_encoding or 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлечение основного контента - The Robot Report использует .entry-content
            content_selectors = [
                '.entry-content',  # Основной контент The Robot Report
                '.post-content',
                '.article-content',
                '.content-body',
                'article .content',
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
                content_element = soup.find('div', class_=re.compile(r'content|body|text|entry'))
                if content_element:
                    logger.info("Found content using alternative search")
            
            # Debug: проверим, что мы нашли
            if content_element:
                logger.info(f"Content element found: {content_element.name} with classes: {content_element.get('class', [])}")
            else:
                logger.warning("No content element found, trying to find any content...")
                # Последняя попытка - ищем любой div с текстом
                content_element = soup.find('div', string=re.compile(r'\w+'))
                if content_element:
                    logger.info("Found content using fallback search")
            
            content = ""
            if content_element:
                # Удаляем ненужные элементы
                for unwanted in content_element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                    unwanted.decompose()
                
                # Извлекаем текст
                content = content_element.get_text(separator='\n', strip=True)
                logger.info(f"Extracted content length: {len(content)} characters")
            
            # Извлечение медиа (видео или изображения)
            media_info = self.extract_article_media(soup, article_url)
            
            return {
                'content': content,
                'media_url': media_info['url'] if media_info else None,
                'media_type': media_info['type'] if media_info else None
            }
            
        except Exception as e:
            logger.error(f"Error extracting article content and media: {e}")
            return {'content': "", 'media_url': None}
    
    def extract_article_media(self, soup, article_url):
        """Извлечение медиа (видео или изображения) статьи The Robot Report"""
        try:
            # Сначала ищем видео
            video_url = self.extract_video_url(soup, article_url)
            if video_url:
                logger.info(f"Found video: {video_url}")
                return {'type': 'video', 'url': video_url}
            
            # Если видео нет, ищем изображение
            image_url = self.extract_image_url(soup, article_url)
            if image_url:
                logger.info(f"Found image: {image_url}")
                return {'type': 'image', 'url': image_url}
            
            logger.warning("No media found")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting article media: {e}")
            return None

    def extract_video_url(self, soup, article_url):
        """Извлечение видео из статьи The Robot Report"""
        try:
            # Приоритетные селекторы для видео
            video_selectors = [
                'meta[property="og:video"]',  # Open Graph видео
                'meta[property="og:video:url"]',  # Open Graph видео URL
                'meta[property="og:video:secure_url"]',  # Open Graph secure видео URL
                'meta[name="twitter:player"]',  # Twitter видео
                'link[itemprop="contentUrl"]',  # schema.org VideoObject contentUrl
                'video[src]',  # HTML5 видео
                'video source[src]',  # HTML5 видео source
                '.fluid-width-video-wrapper video',  # Fluid width видео wrapper (приоритет)
                '.fluid-width-video-wrapper source',  # Fluid width видео source
                '.fluid-width-video-wrapper iframe',  # Fluid width iframe
                '.html5-video-player video',  # HTML5 видео плеер
                '.html5-video-player source',  # HTML5 видео source в плеере
                'iframe[src*="youtube.com/embed"]',  # YouTube встраивание (приоритет)
                'iframe[src*="youtu.be"]',  # YouTube короткие ссылки
                'iframe[src*="youtube"]',  # YouTube встраивание (общий)
                'iframe[src*="vimeo.com"]',  # Vimeo встраивание
                'iframe[data-src*="youtube"], iframe[data-lazy-src*="youtube"]',  # ленивые атрибуты
                '.wp-block-embed__wrapper iframe',  # WP embed wrapper
                '.wp-block-embed__wrapper a',  # WP embed как ссылка
                'iframe[src*="player"]',  # Общие видео плееры
                '.video-container iframe',  # Видео контейнеры
                '.entry-content iframe',  # iframe в контенте
                'iframe[title*="video"]',  # iframe с video в title
                'iframe[title*="demo"]',  # iframe с demo в title
                'a[href*="youtube.com/watch"]',  # Ссылки на YouTube видео
                'a[href*="youtube.com/shorts"]',  # Ссылки на YouTube Shorts
                'a[href*="youtu.be"]',  # Ссылки на YouTube короткие ссылки
                'a[href*="vimeo.com"]'  # Ссылки на Vimeo
            ]
            
            for selector in video_selectors:
                if selector.startswith('meta'):
                    # Для meta тегов
                    meta_element = soup.select_one(selector)
                    if meta_element and meta_element.get('content'):
                        video_url = meta_element['content']
                        if self.is_valid_video_url(video_url):
                            logger.info(f"Found video using meta selector: {selector}")
                            return self.normalize_media_url(video_url, article_url)
                elif 'iframe' in selector:
                    # Для iframe элементов
                    iframe_element = soup.select_one(selector)
                    if iframe_element:
                        # Пытаемся взять src, затем data-src/data-lazy-src, затем srcdoc
                        video_url = iframe_element.get('src') or iframe_element.get('data-src') or iframe_element.get('data-lazy-src')
                        if not video_url:
                            srcdoc = iframe_element.get('srcdoc')
                            if srcdoc:
                                try:
                                    from bs4 import BeautifulSoup as _BS
                                    inner = _BS(srcdoc, 'html.parser')
                                    inner_iframe = inner.find('iframe')
                                    if inner_iframe and (inner_iframe.get('src') or inner_iframe.get('data-src')):
                                        video_url = inner_iframe.get('src') or inner_iframe.get('data-src')
                                    if not video_url:
                                        a_tag = inner.find('a', href=True)
                                        if a_tag:
                                            video_url = a_tag['href']
                                except Exception:
                                    pass
                        if video_url:
                            # Конвертируем YouTube embed ссылки в обычные ссылки на видео
                            if 'youtube.com/embed/' in video_url:
                                video_id = video_url.split('youtube.com/embed/')[1].split('?')[0]
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                                logger.info(f"Converted YouTube embed to watch URL: {video_url}")
                            elif 'youtu.be/' in video_url:
                                video_id = video_url.split('youtu.be/')[1].split('?')[0]
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                                logger.info(f"Converted YouTube short URL to watch URL: {video_url}")
                            elif 'youtube.com/shorts/' in video_url:
                                video_id = video_url.split('youtube.com/shorts/')[1].split('?')[0]
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                                logger.info(f"Converted YouTube shorts to watch URL: {video_url}")
                            
                            if self.is_valid_video_url(video_url):
                                logger.info(f"Found video using iframe selector: {selector}")
                                return self.normalize_media_url(video_url, article_url)
                elif 'video' in selector:
                    # Для video элементов
                    video_element = soup.select_one(selector)
                    if video_element:
                        video_url = video_element.get('src')
                        if not video_url:
                            # Ищем в source элементах
                            source_element = video_element.find('source')
                            if source_element:
                                video_url = source_element.get('src')
                        if video_url and self.is_valid_video_url(video_url):
                            logger.info(f"Found video using video selector: {selector}")
                            return self.normalize_media_url(video_url, article_url)
                elif 'a[href' in selector:
                    # Для ссылок на видео
                    link_element = soup.select_one(selector)
                    if link_element:
                        video_url = link_element.get('href')
                        if video_url and self.is_valid_video_url(video_url):
                            logger.info(f"Found video using link selector: {selector}")
                            return self.normalize_media_url(video_url, article_url)
            
            # Альтернативный поиск по всем iframe (включая ленивые атрибуты и srcdoc)
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src') or iframe.get('data-src') or iframe.get('data-lazy-src')
                if not src and iframe.get('srcdoc'):
                    try:
                        from bs4 import BeautifulSoup as _BS
                        inner = _BS(iframe.get('srcdoc'), 'html.parser')
                        inner_iframe = inner.find('iframe')
                        if inner_iframe and (inner_iframe.get('src') or inner_iframe.get('data-src')):
                            src = inner_iframe.get('src') or inner_iframe.get('data-src')
                        if not src:
                            a_tag = inner.find('a', href=True)
                            if a_tag:
                                src = a_tag['href']
                    except Exception:
                        pass
                if src:
                    # Конвертируем YouTube embed ссылки в обычные ссылки на видео
                    if 'youtube.com/embed/' in src:
                        video_id = src.split('youtube.com/embed/')[1].split('?')[0]
                        src = f"https://www.youtube.com/watch?v={video_id}"
                        logger.info(f"Converted YouTube embed to watch URL: {src}")
                    elif 'youtu.be/' in src:
                        video_id = src.split('youtu.be/')[1].split('?')[0]
                        src = f"https://www.youtube.com/watch?v={video_id}"
                        logger.info(f"Converted YouTube short URL to watch URL: {src}")
                    elif 'youtube.com/shorts/' in src:
                        video_id = src.split('youtube.com/shorts/')[1].split('?')[0]
                        src = f"https://www.youtube.com/watch?v={video_id}"
                        logger.info(f"Converted YouTube shorts to watch URL: {src}")
                    
                    if self.is_valid_video_url(src):
                        logger.info("Found video using iframe search")
                        return self.normalize_media_url(src, article_url)
            
            # Поиск по background-image стилям (YouTube превью)
            import re
            for element in soup.find_all(attrs={'style': True}):
                style = element.get('style', '')
                # Ищем YouTube превью в background-image
                yt_match = re.search(r'ytimg\.com/vi/([a-zA-Z0-9_-]+)', style)
                if yt_match:
                    video_id = yt_match.group(1)
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    logger.info(f"Found video using background-image style: {video_url}")
                    return self.normalize_media_url(video_url, article_url)
            
            # Поиск по всем элементам с data-атрибутами (могут содержать YouTube ID)
            for element in soup.find_all(attrs={'data-video-id': True}):
                video_id = element.get('data-video-id')
                if video_id:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    logger.info(f"Found video using data-video-id: {video_url}")
                    return self.normalize_media_url(video_url, article_url)
            
            # Поиск по всем элементам с YouTube ID в любых атрибутах
            for element in soup.find_all():
                for attr_name, attr_value in element.attrs.items():
                    if isinstance(attr_value, str) and 'WpuD0xHoH9g' in attr_value:
                        # Ищем YouTube ID в атрибуте
                        yt_match = re.search(r'([a-zA-Z0-9_-]{11})', attr_value)
                        if yt_match:
                            video_id = yt_match.group(1)
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                            logger.info(f"Found video using attribute {attr_name}: {video_url}")
                            return self.normalize_media_url(video_url, article_url)
            
            # JSON-LD VideoObject
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    import json as _json
                    data = _json.loads(script.string or "{}")
                    if isinstance(data, dict):
                        graph = data.get('@graph') or [data]
                    elif isinstance(data, list):
                        graph = data
                    else:
                        graph = []
                    for node in graph:
                        if isinstance(node, dict) and node.get('@type') in ('VideoObject', 'VideoObjectPage'):
                            candidate = node.get('contentUrl') or node.get('embedUrl') or node.get('url')
                            if candidate and self.is_valid_video_url(candidate):
                                logger.info("Found video via JSON-LD VideoObject")
                                return self.normalize_media_url(candidate, article_url)
                except Exception:
                    continue

            logger.info("No video found")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting video: {e}")
            return None

    def extract_image_url(self, soup, article_url):
        """Извлечение изображения статьи The Robot Report"""
        try:
            # Приоритетные селекторы для изображений The Robot Report
            image_selectors = [
                'meta[property="og:image"]',  # Open Graph изображение
                'meta[name="twitter:image"]',  # Twitter изображение
                '.entry-content img',         # Изображения в контенте
                '.post-content img',          # Изображения в контенте поста
                '.article-content img',       # Изображения в контенте статьи
                '.entry-image img',           # Изображения записи
                '.post-image img',            # Изображения поста
                'img[data-src]',             # Lazy loading изображения
                'img[src*="therobotreport.com"]', # Изображения с сайта
                'img[src*="wp-content"]'      # WordPress изображения
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
    
    def is_valid_video_url(self, url):
        """Проверка валидности URL видео"""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Исключаем ссылки на каналы и плейлисты
        invalid_patterns = [
            '/channel/', '/user/', '/playlist', '/videos', '/c/',
            '/@', 'youtube.com/channel', 'youtube.com/user'
        ]
        
        if any(pattern in url_lower for pattern in invalid_patterns):
            return False
        
        # Поддерживаемые видео платформы и форматы
        video_patterns = [
            'youtube.com/watch', 'youtu.be/', 'vimeo.com/',
            'dailymotion.com/video', 'player.vimeo.com',
            '.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv'
        ]
        
        return any(pattern in url_lower for pattern in video_patterns)

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
    
    def normalize_media_url(self, media_url, article_url):
        """Нормализация URL медиа (видео или изображения)"""
        if not media_url:
            return None
        
        # Если URL относительный, делаем абсолютным
        if media_url.startswith('//'):
            return 'https:' + media_url
        elif media_url.startswith('/'):
            # Извлекаем домен из URL статьи
            from urllib.parse import urlparse
            parsed = urlparse(article_url)
            return f"{parsed.scheme}://{parsed.netloc}{media_url}"
        elif not media_url.startswith('http'):
            # Относительный URL
            from urllib.parse import urljoin
            return urljoin(article_url, media_url)
        
        return media_url

    def normalize_image_url(self, image_url, article_url):
        """Нормализация URL изображения (для обратной совместимости)"""
        return self.normalize_media_url(image_url, article_url)
    
    def save_article_data(self, article, post_content, media_url=None):
        """Сохранение данных статьи в JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"robotreport_article_{timestamp}.json"
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
            logger.info("🚀 Starting The Robot Report daily scraping...")
            
            # Скрапим статьи
            articles = self.scrape_robotreport_articles()
            
            if not articles:
                logger.warning("No articles found")
                return None
            
            # Фильтруем неопубликованные
            unpublished_articles = self.filter_unpublished_articles(articles)
            
            if not unpublished_articles:
                logger.info("No new articles to publish")
                return None
            
            # Выбираем лучшую статью
            best_article = self.select_best_article(unpublished_articles)
            
            if not best_article:
                logger.warning("No suitable article selected")
                return None
            
            logger.info(f"Selected article: {best_article['title']}")
            logger.info(f"Article URL: {best_article['url']}")
            
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
                media_type = article_data.get('media_type', 'image')
                logger.info(f"Found {media_type}: {article_data['media_url']}")

            # Используем контент без добавления ссылки на видео (видео будет прикреплено к посту)
            content = article_data['content']
            
            # Создаем пост и публикуем через TelegramPublisher
            logger.info(f"Creating and publishing post with URL: {best_article['url']}")
            result = await self.telegram_publisher.create_and_publish_post(
                title=best_article['title'],
                content=content,
                article_url=best_article['url'],
                topic=best_article['topic'],
                media_url=article_data.get('media_url'),
                media_type=article_data.get('media_type', 'image')
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
    scraper = RobotReportScraper()
    await scraper.run_daily_scraping()

def run_with_proper_cleanup():
    """Запуск с правильной очисткой ресурсов"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("The Robot Report scraper finished")

if __name__ == "__main__":
    run_with_proper_cleanup()
