#!/usr/bin/env python3
"""
ZDNet Auto Scraper and Telegram Publisher
Автоматический скраппер статей с ZDNet с публикацией в Telegram
"""

import os
import logging
import requests
import feedparser
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram_publisher import TelegramPublisher
from urllib.parse import urljoin, urlparse
import json
import time
import sys
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zdnet_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZDNetScraper:
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
        
        # ZDNet URLs
        self.base_url = 'https://www.zdnet.com'
        self.latest_url = 'https://www.zdnet.com/latest/'
        
        # Даты для фильтрации (статьи не старше 2 дней)
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=2)
        
        # Создаем папку для JSON файлов
        self.json_folder = 'zdnet_articles_archive'
        self.create_json_folder()
        
        # Файл для отслеживания опубликованных URL
        self.published_urls_file = 'zdnet_published_urls.json'
        self.published_urls = self.load_published_urls()
        
        # Файл для отслеживания времени последнего запуска
        self.last_run_file = 'zdnet_last_run.txt'
        
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
        
        logger.info("ZDNet Scraper initialized successfully")
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
    
    def check_last_run_time(self):
        """Проверка времени последнего запуска (не чаще чем раз в 6 часов)"""
        try:
            if os.path.exists(self.last_run_file):
                with open(self.last_run_file, 'r') as f:
                    last_run_str = f.read().strip()
                    if last_run_str:
                        from datetime import datetime
                        last_run = datetime.fromisoformat(last_run_str)
                        time_diff = datetime.now() - last_run
                        
                        # Проверяем, прошло ли 6 часов
                        if time_diff.total_seconds() < 6 * 3600:  # 6 часов в секундах
                            hours_remaining = (6 * 3600 - time_diff.total_seconds()) / 3600
                            logger.info(f"Scraper was run recently. Wait {hours_remaining:.1f} hours before next run.")
                            return False
            return True
        except Exception as e:
            logger.warning(f"Error checking last run time: {e}")
            return True
    
    def update_last_run_time(self):
        """Обновление времени последнего запуска"""
        try:
            with open(self.last_run_file, 'w') as f:
                f.write(datetime.now().isoformat())
            logger.info("Updated last run time")
        except Exception as e:
            logger.error(f"Error updating last run time: {e}")
    
    def parse_article_date(self, date_text):
        """Парсинг даты статьи из текста"""
        try:
            # Убираем лишние пробелы и символы
            date_text = date_text.strip()
            
            # Паттерны для различных форматов дат на ZDNet
            patterns = [
                r'(\d{1,2})\s+(hour|hours|minute|minutes|day|days)\s+ago',
                r'(\d{1,2}):(\d{2})\s+(AM|PM)\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})',
                r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',
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
                    
                    elif len(match.groups()) >= 3:
                        # Обработка абсолютных дат
                        try:
                            if ':' in date_text:  # Формат с временем
                                hour = int(match.group(1))
                                minute = int(match.group(2))
                                ampm = match.group(3)
                                month_name = match.group(4)
                                day = int(match.group(5))
                                year = int(match.group(6))
                                
                                # Конвертация 12-часового формата в 24-часовой
                                if ampm.upper() == 'PM' and hour != 12:
                                    hour += 12
                                elif ampm.upper() == 'AM' and hour == 12:
                                    hour = 0
                                
                                # Словарь для месяцев
                                months = {
                                    'january': 1, 'february': 2, 'march': 3, 'april': 4,
                                    'may': 5, 'june': 6, 'july': 7, 'august': 8,
                                    'september': 9, 'october': 10, 'november': 11, 'december': 12
                                }
                                
                                month = months.get(month_name.lower(), 1)
                                return date(year, month, day)
                            
                            elif len(match.groups()) == 3:
                                # Формат MM/DD/YYYY или YYYY-MM-DD
                                if len(match.group(1)) == 4:  # YYYY-MM-DD
                                    year = int(match.group(1))
                                    month = int(match.group(2))
                                    day = int(match.group(3))
                                else:  # MM/DD/YYYY
                                    month = int(match.group(1))
                                    day = int(match.group(2))
                                    year = int(match.group(3))
                                
                                return date(year, month, day)
                        
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Error parsing date components: {e}")
                            continue
            
            # Если не удалось распарсить, возвращаем None
            logger.warning(f"Could not parse date: {date_text}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_text}': {e}")
            return None
    
    def extract_date_from_url(self, url):
        """Извлечение даты из URL статьи"""
        try:
            # Паттерны для поиска дат в URL ZDNet
            patterns = [
                r'/(\d{4})/(\d{1,2})/(\d{1,2})/',  # /2025/08/05/
                r'(\d{4})-(\d{1,2})-(\d{1,2})',    # 2025-08-05
                r'(\d{1,2})-(\d{1,2})-(\d{4})',    # 08-05-2025
                r'(\d{4})/(\d{1,2})/(\d{1,2})',    # 2025/08/05
                r'(\d{1,2})/(\d{1,2})/(\d{4})',    # 08/05/2025
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        if len(groups[0]) == 4:  # YYYY-MM-DD или YYYY/MM/DD
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # MM-DD-YYYY или MM/DD/YYYY
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
    
    def scrape_zdnet_articles(self):
        """Основной метод скрапинга статей с ZDNet"""
        logger.info("Starting ZDNet articles scraping...")
        logger.info(f"Date filter: articles not older than {self.yesterday} (2 days from today)")
        
        all_articles = []
        total_found = 0
        filtered_by_date = 0
        
        # Скрапим статьи с топика /latest
        topic_name = 'Latest'
        
        try:
            logger.info(f"Scraping {topic_name} articles from: {self.latest_url}")
            topic_articles = self.scrape_topic_page(self.latest_url, topic_name)
            all_articles.extend(topic_articles)
            logger.info(f"Found {len(topic_articles)} articles in {topic_name}")
        except Exception as e:
            logger.error(f"Error scraping {topic_name} articles: {e}")
        
        logger.info(f"Total articles found: {len(all_articles)}")
        logger.info(f"Date filtering: showing only articles from {self.yesterday} to {self.today}")
        return all_articles
    
    def scrape_topic_page(self, url, topic):
        """Скрапинг статей с тематической страницы"""
        articles = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем блок с классом c-listingDefault (основной блок со статьями на /latest)
            listing_block = soup.find('div', class_='c-listingDefault')
            
            if listing_block:
                logger.info("Found listing block with class 'c-listingDefault'")
                # Ищем ссылки на статьи внутри этого блока
                article_links = listing_block.find_all('a', href=True)
                logger.info(f"Found {len(article_links)} article links in listing block")
                
                # Обрабатываем каждую ссылку как потенциальную статью
                for link in article_links:
                    try:
                        article_info = self.extract_article_info_from_link(link, topic)
                        if article_info:
                            articles.append(article_info)
                    except Exception as e:
                        logger.warning(f"Error extracting article info from link: {e}")
                        continue
            else:
                logger.info("Listing block not found, searching in entire page")
                # Ищем статьи на странице (fallback)
                article_elements = soup.find_all(['article', 'div'], class_=re.compile(r'article|story|post|item'))
                
                if not article_elements:
                    # Альтернативный поиск по структуре
                    article_elements = soup.find_all('div', class_=re.compile(r'content|listing|feed'))
                
                logger.info(f"Found {len(article_elements)} potential article elements in entire page")
                
                for element in article_elements:
                    try:
                        article_info = self.extract_article_info(element, topic)
                        if article_info:
                            articles.append(article_info)
                    except Exception as e:
                        logger.warning(f"Error extracting article info: {e}")
                        continue
            
            # Если не нашли статьи стандартным способом, попробуем альтернативный
            if not articles:
                articles = self.scrape_alternative_articles(soup, topic)
            
        except Exception as e:
            logger.error(f"Error scraping topic page {url}: {e}")
        
        return articles
    
    def extract_article_info_from_link(self, link_element, topic):
        """Извлечение информации о статье из ссылки (для /latest страницы)"""
        try:
            article_url = link_element['href']
            if not article_url.startswith('http'):
                article_url = urljoin(self.base_url, article_url)
            
            # Проверяем, что это ссылка на статью ZDNet
            if not article_url.startswith('https://www.zdnet.com/'):
                return None
            
            # Исключаем служебные страницы
            if any(exclude in article_url.lower() for exclude in ['/topic/', '/meet-the-team/', '/about/', '/contact/', '/privacy/', '/terms/']):
                return None
            
            # Извлекаем заголовок из текста ссылки
            title = link_element.get_text(strip=True)
            
            # Очищаем заголовок от лишних символов
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Проверяем минимальную длину заголовка
            if len(title) < 10:
                return None
            
            # Исключаем служебные заголовки
            if any(exclude in title.lower() for exclude in ['see all', 'topic', 'category', 'more']):
                return None
            
            # Поиск даты - ищем в родительском элементе
            date_text = ""
            parent = link_element.find_parent()
            
            if parent:
                # 1. Поиск по стандартным селекторам
                date_element = parent.find(['time', 'span', 'div'], 
                                         class_=re.compile(r'date|time|published|updated'))
                if date_element:
                    date_text = date_element.get_text(strip=True)
                
                # 2. Поиск по атрибутам
                if not date_text:
                    date_element = parent.find(['time', 'span', 'div'], 
                                             attrs={'datetime': True})
                    if date_element:
                        date_text = date_element.get('datetime', '')
                
                # 3. Поиск по тексту с датами
                if not date_text:
                    all_text = parent.get_text()
                    date_patterns = [
                        r'\b\d{1,2}\s+(hour|hours|minute|minutes|day|days)\s+ago\b',
                        r'\b\d{1,2}:\d{2}\s+(AM|PM)\s+\w+\s+\d{1,2},?\s+\d{4}\b',
                        r'\b\w+\s+\d{1,2},?\s+\d{4}\b',
                        r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                        r'\b\d{4}-\d{1,2}-\d{1,2}\b'
                    ]
                    
                    for pattern in date_patterns:
                        match = re.search(pattern, all_text, re.IGNORECASE)
                        if match:
                            date_text = match.group(0)
                            break
            
            # Поиск описания в родительском элементе
            description = ""
            if parent:
                desc_element = parent.find(['p', 'div'], 
                                         class_=re.compile(r'description|excerpt|summary|content'))
                description = desc_element.get_text(strip=True) if desc_element else ""
            
            # Парсинг даты
            article_date = self.parse_article_date(date_text)
            
            # Дополнительная проверка даты из URL (если есть паттерн даты в URL)
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
            
            logger.info(f"Found recent article: {title[:50]}... -> {article_url} (date: {article_date})")
            
            return {
                'title': title,
                'url': article_url,
                'date': article_date,
                'description': description,
                'topic': topic
            }
            
        except Exception as e:
            logger.warning(f"Error extracting article info from link: {e}")
            return None

    def extract_article_info(self, element, topic):
        """Извлечение информации о статье из элемента"""
        try:
            # Поиск ссылки на статью
            link_element = element.find('a', href=True)
            if not link_element:
                return None
            
            article_url = link_element['href']
            if not article_url.startswith('http'):
                article_url = urljoin(self.base_url, article_url)
            
            # Проверяем, что это ссылка на статью ZDNet
            if not article_url.startswith('https://www.zdnet.com/'):
                return None
            
            # Поиск заголовка
            title_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if not title_element:
                title_element = link_element
            
            title = title_element.get_text(strip=True) if title_element else "No title"
            
            # Очищаем заголовок от лишних символов
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Проверяем минимальную длину заголовка
            if len(title) < 10:
                return None
            
            # Поиск даты - расширенный поиск
            date_text = ""
            
            # 1. Поиск по стандартным селекторам
            date_element = element.find(['time', 'span', 'div'], 
                                     class_=re.compile(r'date|time|published|updated'))
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
                # Ищем любой текст, содержащий дату
                all_text = element.get_text()
                date_patterns = [
                    r'\b\d{1,2}\s+(hour|hours|minute|minutes|day|days)\s+ago\b',
                    r'\b\d{1,2}:\d{2}\s+(AM|PM)\s+\w+\s+\d{1,2},?\s+\d{4}\b',
                    r'\b\w+\s+\d{1,2},?\s+\d{4}\b',
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
                                     class_=re.compile(r'description|excerpt|summary|content'))
            description = desc_element.get_text(strip=True) if desc_element else ""
            
            # Парсинг даты
            article_date = self.parse_article_date(date_text)
            
            # Дополнительная проверка даты из URL (если есть паттерн даты в URL)
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
            
            logger.info(f"Found recent article: {title[:50]}... -> {article_url} (date: {article_date})")
            
            return {
                'title': title,
                'url': article_url,
                'date': article_date,
                'description': description,
                'topic': topic
            }
            
        except Exception as e:
            logger.warning(f"Error extracting article info: {e}")
            return None
    
    def scrape_alternative_articles(self, soup, topic):
        """Альтернативный метод поиска статей"""
        articles = []
        
        try:
            # Поиск всех ссылок на статьи
            links = soup.find_all('a', href=True)
            
            for link in links:
                try:
                    href = link['href']
                    if not href.startswith('http'):
                        href = urljoin(self.base_url, href)
                    
                    # Проверяем, что это ссылка на статью
                    if '/article/' in href or '/news/' in href or '/story/' in href:
                        title = link.get_text(strip=True)
                        if title and len(title) > 10:  # Минимальная длина заголовка
                            
                            # Извлекаем дату из URL
                            article_date = self.extract_date_from_url(href)
                            if not article_date:
                                logger.info(f"Article excluded (no date in URL): {title[:50]}...")
                                continue  # Пропускаем статьи без даты
                            
                            # Проверяем, что статья из последних дней
                            if self.is_article_from_recent_days(article_date):
                                logger.info(f"Found recent article (alternative): {title[:50]}... (date: {article_date})")
                                articles.append({
                                    'title': title,
                                    'url': href,
                                    'date': article_date,
                                    'description': "",
                                    'topic': topic
                                })
                            else:
                                logger.info(f"Article filtered out (alternative): {title[:50]}... (date: {article_date}, cutoff: {self.yesterday})")
                
                except Exception as e:
                    continue
            
        except Exception as e:
            logger.error(f"Error in alternative article scraping: {e}")
        
        return articles
    
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
            if ('/article/' in url and 
                not url.endswith('/topic/') and 
                not url.endswith('/topic') and
                not 'topic' in title and
                not 'see all' in title):
                valid_articles.append(article)
        
        if not valid_articles:
            # Если нет валидных статей, берем первую с /article/
            for article in articles:
                if '/article/' in article.get('url', ''):
                    return article
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
        """Скрапинг содержимого статьи и медиа"""
        try:
            response = requests.get(article_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлечение основного контента
            content = self.extract_article_content(soup)
            
            # Извлечение медиа
            media_url = self.extract_media(soup, article_url)
            
            return {
                'content': content,
                'media_url': media_url
            }
            
        except Exception as e:
            logger.error(f"Error scraping article content: {e}")
            return {'content': '', 'media_url': None}
    
    def extract_article_content(self, soup):
        """Извлечение основного контента статьи"""
        try:
            # Специфичные селекторы для ZDNet
            content_selectors = [
                '.c-ShortcodeContent',  # Основной контент ZDNet
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content-body',
                '.story-body',
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
                content_element = soup.find('div', class_=re.compile(r'content|body|text|shortcode'))
                if content_element:
                    logger.info("Found content using alternative search")
            
            if content_element:
                # Удаляем ненужные элементы
                for unwanted in content_element.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                    unwanted.decompose()
                
                # Извлекаем текст
                content = content_element.get_text(separator='\n', strip=True)
                logger.info(f"Extracted content length: {len(content)} characters")
                return content
            
            logger.warning("No content found with any selector")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting article content: {e}")
            return ""
    
    def extract_media(self, soup, article_url):
        """Извлечение медиа из статьи"""
        try:
            # Поиск главного изображения
            main_image = self.extract_main_image(soup, article_url)
            if main_image:
                return main_image
            
            # Поиск любого изображения
            images = soup.find_all('img', src=True)
            for img in images:
                src = img['src']
                if not src.startswith('http'):
                    src = urljoin(article_url, src)
                
                # Проверяем, что это не иконка или маленькое изображение
                if self.is_valid_image(src):
                    return src
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting media: {e}")
            return None
    
    def extract_main_image(self, soup, article_url):
        """Извлечение главного изображения статьи"""
        try:
            # Специфичные селекторы для ZDNet
            image_selectors = [
                '.c-ShortcodeContent img',  # Основной контент ZDNet
                '.article-image img',
                '.post-image img',
                '.entry-image img',
                '.featured-image img',
                '.hero-image img',
                '.article-header img',
                '.article-content img',
                '.story-image img',
                '.main-image img',
                '.lead-image img',
                'article .image img',
                '.content img',
                'article img'
            ]
            
            # Собираем все изображения с их размерами
            all_images = []
            
            for selector in image_selectors:
                imgs = soup.select(selector)
                logger.info(f"Found {len(imgs)} images with selector: {selector}")
                
                for img in imgs:
                    src = img.get('src')
                    if not src:
                        continue
                    
                    if not src.startswith('http'):
                        src = urljoin(article_url, src)
                    
                    # Проверяем размеры изображения
                    width = img.get('width', '0')
                    height = img.get('height', '0')
                    
                    # Пытаемся извлечь размеры из URL
                    url_width = url_height = None
                    if 'width=' in src and 'height=' in src:
                        try:
                            width_match = re.search(r'width=(\d+)', src)
                            height_match = re.search(r'height=(\d+)', src)
                            if width_match and height_match:
                                url_width = int(width_match.group(1))
                                url_height = int(height_match.group(1))
                        except:
                            pass
                    
                    # Определяем размеры
                    w = h = 0
                    if width and height:
                        try:
                            w, h = int(width), int(height)
                        except ValueError:
                            pass
                    elif url_width and url_height:
                        w, h = url_width, url_height
                    
                    # Проверяем валидность изображения
                    if self.is_valid_image(src):
                        all_images.append({
                            'src': src,
                            'width': w,
                            'height': h,
                            'area': w * h
                        })
            
            # Сортируем по площади изображения (большие сначала)
            all_images.sort(key=lambda x: x['area'], reverse=True)
            
            # Ищем изображения с минимальным размером 400x300
            for img in all_images:
                if img['width'] >= 400 and img['height'] >= 300:
                    logger.info(f"Found high-quality image: {img['width']}x{img['height']}")
                    return img['src']
            
            # Если нет больших изображений, берем самое большое
            if all_images:
                best_img = all_images[0]
                logger.info(f"Found best available image: {best_img['width']}x{best_img['height']}")
                return best_img['src']
            
            # Если не нашли по селекторам, ищем любое большое изображение
            all_images = soup.find_all('img', src=True)
            logger.info(f"Total images found: {len(all_images)}")
            
            for img in all_images:
                src = img['src']
                if not src.startswith('http'):
                    src = urljoin(article_url, src)
                
                # Проверяем размеры
                width = img.get('width', '0')
                height = img.get('height', '0')
                
                if width and height:
                    try:
                        w, h = int(width), int(height)
                        if w >= 300 and h >= 200:
                            if self.is_valid_image(src):
                                logger.info(f"Found large image with size {w}x{h}: {src}")
                                return src
                    except ValueError:
                        pass
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting main image: {e}")
            return None
    
    def is_valid_image(self, image_url):
        """Проверка валидности изображения"""
        try:
            # Исключаем иконки, аватары и маленькие изображения
            excluded_patterns = [
                r'icon', r'avatar', r'logo', r'thumb', r'small',
                r'16x16', r'32x32', r'48x48', r'64x64', r'80x80',
                r'profile', r'user', r'author', r'headshot',
                r'gravatar', r'placeholder', r'default'
            ]
            
            # Проверяем паттерны исключения
            for pattern in excluded_patterns:
                if re.search(pattern, image_url, re.IGNORECASE):
                    logger.info(f"Excluded image with pattern '{pattern}': {image_url}")
                    return False
            
            # Проверяем, что URL содержит признаки изображения статьи
            article_patterns = [
                r'\.(jpg|jpeg|png|gif|webp)$',
                r'image', r'photo', r'picture', r'img'
            ]
            
            has_article_pattern = any(re.search(pattern, image_url, re.IGNORECASE) 
                                   for pattern in article_patterns)
            
            if has_article_pattern:
                logger.info(f"Valid article image found: {image_url}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return False
    
    # Метод download_media больше не нужен, логика перенесена в TelegramPublisher
    
    # Метод get_media_extension больше не нужен, так как используется TelegramPublisher
    
    def translate_title_to_russian(self, title):
        """Перевод заголовка на русский язык"""
        if not title:
            logger.warning("No title provided for translation")
            return "Без заголовка"
        
        try:
            # Используем TelegramPublisher для перевода
            return self.telegram_publisher.translate_to_russian(title)
        except Exception as e:
            logger.error(f"Error translating title: {e}")
            return title

    # Метод translate_to_russian больше не нужен, логика перенесена в TelegramPublisher
    
    # Метод create_viral_post больше не нужен, логика перенесена в TelegramPublisher
    
    # Метод get_hashtags_for_topic больше не нужен, логика перенесена в TelegramPublisher

    # Метод convert_markdown_to_html больше не нужен, логика перенесена в TelegramPublisher
    
    # Метод publish_to_telegram больше не нужен, логика перенесена в TelegramPublisher
    
    def save_article_data(self, article, post_content, media_url=None):
        """Сохранение данных статьи в JSON"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"zdnet_article_{timestamp}.json"
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
            logger.info("🚀 Starting ZDNet daily scraping...")
            
            # Проверяем, не запускался ли скрапер недавно
            if not self.check_last_run_time():
                logger.info("Scraper was run recently, skipping this run")
                return
            
            # Скрапим статьи
            articles = self.scrape_zdnet_articles()
            
            if not articles:
                logger.warning("No articles found")
                return
            
            # Фильтруем неопубликованные
            unpublished_articles = self.filter_unpublished_articles(articles)
            
            if not unpublished_articles:
                logger.info("No new articles to publish")
                return
            
            # Выбираем лучшую статью
            best_article = self.select_best_article(unpublished_articles)
            
            if not best_article:
                logger.warning("No suitable article selected")
                return
            
            logger.info(f"Selected article: {best_article['title']}")
            logger.info(f"Article URL: {best_article['url']}")
            
            # Проверяем наличие заголовка
            if not best_article.get('title') or len(best_article['title'].strip()) < 10:
                logger.warning("Article title too short or missing")
                return
            
            # Скрапим содержимое статьи
            article_data = self.scrape_article_content_and_media(best_article['url'])
            
            if not article_data['content']:
                logger.warning("No content extracted from article")
                return
            
            # Проверяем минимальную длину контента
            if len(article_data['content'].strip()) < 100:
                logger.warning("Article content too short")
                return
            
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
                # Обновляем время последнего запуска
                self.update_last_run_time()
                logger.info("✅ Article published successfully!")
            else:
                logger.error(f"❌ Failed to publish article: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Error in daily scraping: {e}")

async def main():
    """Основная функция"""
    scraper = ZDNetScraper()
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
        logger.info("ZDNet scraper finished") 