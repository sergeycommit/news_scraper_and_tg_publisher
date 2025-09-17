#!/usr/bin/env python3
"""
ScienceDaily RSS Scraper and Telegram Publisher
Автоматический скраппер статей с ScienceDaily RSS feed с публикацией в Telegram
"""

import os
import logging
import requests
import feedparser
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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sciencedaily_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScienceDailyScraper:
    def __init__(self):
        load_dotenv()
        
        # Конфигурация OpenRouter
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.ai_model = os.getenv('AI_MODEL', 'google/gemini-pro')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.7'))
        self.prompt = "Создай на основе этой статьи виральный, информативный и полезный пост на русском языке длинной до 4096 символов(включая теги). Используй разметку, отступы и эмоджи. Перепроверь в конце количество символов, получившейся подписи, до 4096(включая хэштеги). Вывести только сам пост."
        self.system_prompt = os.getenv('SYSTEM_PROMPT')
        
        # Конфигурация Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_channel = os.getenv('TELEGRAM_CHANNEL_ID')
        
        # Настройки
        self.rss_url = "https://www.sciencedaily.com/rss/all.xml"
        self.base_url = "https://www.sciencedaily.com"
        self.json_folder = "sciencedaily_articles_archive"
        self.published_urls_file = "sciencedaily_published_urls.json"
        
        # Инициализация TelegramPublisher
        self.telegram_publisher = TelegramPublisher(
            telegram_token=self.telegram_token,
            telegram_channel=self.telegram_channel,
            openai_api_key=self.openrouter_api_key,
            ai_model=self.ai_model
        )
        
        # Создание папки для архива
        self.ensure_json_folder()
        
        # Загрузка опубликованных URL
        self.published_urls = self.load_published_urls()
        
        # Текущая дата
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        
        logger.info("ScienceDaily RSS Scraper initialized successfully")
        published_count = len(self.urls_manager.get_published_urls(self.source_name))
        logger.info(f"Loaded {published_count} previously published URLs")
    
    def ensure_json_folder(self):
        """Создание папки для архива статей"""
        if not os.path.exists(self.json_folder):
            os.makedirs(self.json_folder)
            logger.info(f"Created JSON folder: {self.json_folder}")
        else:
            logger.info(f"JSON folder already exists: {self.json_folder}")
    
    def load_published_urls(self):
        """Загрузка списка опубликованных URL"""
        return self.urls_manager.get_published_urls(self.source_name)
    def save_published_urls(self):
        """Сохранение списка опубликованных URL"""
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
    def scrape_sciencedaily_rss(self):
        """Скрапинг статей с ScienceDaily RSS feed"""
        logger.info("Starting ScienceDaily RSS articles scraping...")
        logger.info("No date filtering - will publish any unpublished article")
        
        try:
            logger.info(f"Scraping RSS feed from: {self.rss_url}")
            
            # Заголовки для RSS запроса
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Сначала скачиваем RSS feed
            response = requests.get(self.rss_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Парсим RSS feed
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.warning("No entries found in RSS feed")
                return []
            
            logger.info(f"Found {len(feed.entries)} entries in RSS feed")
            
            articles = []
            for entry in feed.entries:
                try:
                    article_info = self.extract_article_info_from_rss(entry)
                    if article_info:
                        articles.append(article_info)
                        logger.info(f"Added RSS article: {article_info['title'][:50]}...")
                except Exception as e:
                    logger.warning(f"Error extracting article info from RSS: {e}")
                    continue
            
            logger.info(f"Found {len(articles)} articles from RSS feed")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping RSS feed: {e}")
            return []
    
    def extract_article_info_from_rss(self, entry):
        """Извлечение информации о статье из RSS entry"""
        try:
            # Получаем URL статьи
            article_url = entry.get('link', '')
            if not article_url:
                return None
            
            # Проверяем, что это ссылка на ScienceDaily
            if not article_url.startswith('https://www.sciencedaily.com/'):
                return None
            
            # Получаем заголовок
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            # Получаем описание
            description = entry.get('summary', '').strip()
            
            # Получаем дату публикации
            published_date = entry.get('published_parsed')
            if published_date:
                article_date = datetime(*published_date[:6]).date()
            else:
                article_date = self.today
            
            # Получаем категорию/топик
            category = entry.get('tags', [{}])[0].get('term', 'Science') if entry.get('tags') else 'Science'
            
            logger.info(f"Found RSS article: {title[:50]}... -> {article_url} (date: {article_date})")
            
            return {
                'title': title,
                'url': article_url,
                'date': article_date,
                'description': description,
                'topic': category
            }
            
        except Exception as e:
            logger.warning(f"Error extracting RSS article info: {e}")
            return None
    
    def scrape_article_content_and_media(self, article_url):
        """Скрапинг содержимого статьи и медиафайлов"""
        try:
            logger.info(f"Scraping article content from: {article_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(article_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлекаем содержимое статьи
            content = self.extract_article_content(soup)
            
            # Извлекаем медиафайлы
            media_url = self.extract_media_url(soup, article_url)
            
            logger.info(f"Extracted content length: {len(content)} characters")
            if media_url:
                logger.info(f"Found media URL: {media_url}")
            
            return {
                'content': content,
                'media_url': media_url
            }
            
        except Exception as e:
            logger.error(f"Error scraping article content: {e}")
            return {'content': '', 'media_url': None}
    
    def extract_article_content(self, soup):
        """Извлечение содержимого статьи"""
        try:
            # Ищем основной контент статьи
            content_selectors = [
                '.story-content',
                '.article-content',
                '.story-body',
                '.article-body',
                '.content',
                'article',
                '.story'
            ]
            
            content = ""
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    logger.info(f"Found content using selector: {selector}")
                    
                    # Убираем ненужные элементы
                    for unwanted in content_element.select('script, style, nav, header, footer, .advertisement, .sidebar'):
                        unwanted.decompose()
                    
                    # Извлекаем текст
                    content = content_element.get_text(separator=' ', strip=True)
                    if len(content) > 100:  # Минимальная длина контента
                        break
            
            if not content:
                # Fallback: берем весь текст страницы
                content = soup.get_text(separator=' ', strip=True)
            
            # Очищаем и ограничиваем контент
            content = re.sub(r'\s+', ' ', content).strip()
            if len(content) > 8000:  # Ограничиваем длину
                content = content[:8000] + "..."
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting article content: {e}")
            return ""
    
    def extract_media_url(self, soup, article_url):
        """Извлечение URL медиафайла"""
        try:
            # Исключаем логотипы и служебные изображения
            exclude_patterns = [
                'logo', 'sd-logo', 'banner', 'advertisement', 'sidebar',
                'header', 'footer', 'nav', 'menu', 'icon', 'button'
            ]
            
            # Ищем изображения в статье с приоритетом
            image_selectors = [
                '.story-image img',
                '.article-image img', 
                '.hero-image img',
                '.featured-image img',
                '.main-image img',
                '.story img',
                '.article img',
                '.content img',
                'article img'
            ]
            
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if not src:
                        continue
                    
                    # Преобразуем относительный URL в абсолютный
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    elif not src.startswith('http'):
                        src = urljoin(article_url, src)
                    
                    # Проверяем, что это изображение ScienceDaily и не логотип
                    if ('sciencedaily.com' in src and 
                        any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) and
                        not any(pattern in src.lower() for pattern in exclude_patterns) and
                        'logo' not in src.lower()):
                        
                        # Дополнительная проверка - исключаем изображения с подозрительными названиями
                        img_alt = img.get('alt', '').lower()
                        img_class = ' '.join(img.get('class', [])).lower()
                        
                        if not any(pattern in img_alt for pattern in exclude_patterns) and \
                           not any(pattern in img_class for pattern in exclude_patterns):
                            
                            logger.info(f"Found valid article image: {src}")
                            return src
            
            # Если не нашли изображение, ищем в meta тегах
            meta_image = soup.find('meta', property='og:image')
            if meta_image and meta_image.get('content'):
                src = meta_image['content']
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.base_url, src)
                elif not src.startswith('http'):
                    src = urljoin(article_url, src)
                
                # Проверяем, что meta изображение тоже не логотип
                if not any(pattern in src.lower() for pattern in exclude_patterns):
                    logger.info(f"Found image using meta selector: meta[property='og:image']")
                    return src
            
            # Fallback: ищем любое изображение, но исключаем явные логотипы
            all_images = soup.find_all('img')
            for img in all_images:
                src = img.get('src') or img.get('data-src')
                if not src:
                    continue
                
                # Преобразуем URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.base_url, src)
                elif not src.startswith('http'):
                    src = urljoin(article_url, src)
                
                # Проверяем, что это не логотип и подходящий размер
                if ('sciencedaily.com' in src and 
                    any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) and
                    'logo' not in src.lower() and
                    'sd-logo' not in src.lower() and
                    'banner' not in src.lower()):
                    
                    logger.info(f"Found fallback article image: {src}")
                    return src
            
            logger.warning("No suitable image found")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting media URL: {e}")
            return None
    
    def save_article_data(self, article_info, article_data):
        """Сохранение данных статьи в JSON"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sciencedaily_article_{timestamp}.json"
            filepath = os.path.join(self.json_folder, filename)
            
            data = {
                'article_info': {
                    'title': article_info['title'],
                    'url': article_info['url'],
                    'date': article_info['date'].isoformat() if hasattr(article_info['date'], 'isoformat') else str(article_info['date']),
                    'description': article_info['description'],
                    'topic': article_info['topic']
                },
                'article_data': article_data,
                'scraped_at': datetime.now().isoformat(),
                'scraper_version': '1.0'
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved article data: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving article data: {e}")
    
    async def run_daily_scraping(self):
        """Основной метод запуска ежедневного скрапинга"""
        try:
            logger.info("🚀 Starting ScienceDaily RSS daily scraping...")
            
            # Скрапим статьи из RSS
            articles = self.scrape_sciencedaily_rss()
            
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
                logger.warning("No article content found")
                return None
            
            # Создаем пост и публикуем через TelegramPublisher
            logger.info(f"Creating and publishing post with URL: {best_article['url']}")
            result = await self.telegram_publisher.create_and_publish_post(
                title=best_article['title'],
                content=article_data['content'],
                article_url=best_article['url'],
                topic=best_article['topic'],
                media_url=article_data.get('media_url')
            )
            
            if result and result.get('success'):
                # Сохраняем данные и добавляем URL в опубликованные
                self.add_published_url(best_article['url'])
                self.save_article_data(best_article, article_data)
                
                logger.info("✅ Article published successfully!")
                return {
                    'title': best_article['title'],
                    'url': best_article['url'],
                    'date': best_article['date'],
                    'topic': best_article['topic']
                }
            else:
                logger.error("Failed to publish article")
                return None
                
        except Exception as e:
            logger.error(f"Error in daily scraping: {e}")
            return None

async def run_with_proper_cleanup():
    """Запуск с правильной очисткой ресурсов"""
    scraper = None
    try:
        scraper = ScienceDailyScraper()
        result = await scraper.run_daily_scraping()
        return result
    except Exception as e:
        logger.error(f"Error running scraper: {e}")
        return None
    finally:
        if scraper:
            # Очистка ресурсов
            pass

if __name__ == "__main__":
    asyncio.run(run_with_proper_cleanup())
