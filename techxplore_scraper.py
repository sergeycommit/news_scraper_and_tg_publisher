#!/usr/bin/env python3
"""
Techxplore Scraper and Telegram Publisher
"""

import os
import logging
import requests
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram_publisher import TelegramPublisher
from published_urls_manager import get_urls_manager
from urllib.parse import urljoin
import json
import re
import asyncio
import feedparser
import time
from email.utils import parsedate_to_datetime

# Suppress urllib3 LibreSSL warning if present
try:
    import warnings
    import urllib3 as _urllib3
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
except Exception:
    pass

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('techxplore_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TechxploreScraper:
    def __init__(self):
        load_dotenv()
        
        # OpenRouter/AI Configuration
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.ai_model = os.getenv('AI_MODEL', 'google/gemini-pro')
        
        # Telegram Configuration
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_channel = os.getenv('TELEGRAM_CHANNEL_ID')
        
        # Techxplore RSS URL
        self.rss_url = 'https://techxplore.com/rss-feed/robotics-news/'
        
        # Date filtering (articles not older than SCRAPING_DAYS)
        self.today = date.today()
        scraping_days = int(os.getenv('SCRAPING_DAYS', '2'))
        self.yesterday = self.today - timedelta(days=scraping_days)
        logger.info(f"Techxplore date filter: last {scraping_days} days (from {self.yesterday} to {self.today})")
        
        # JSON archive folder
        self.json_folder = 'techxplore_articles_archive'
        self.create_json_folder()
        
        # Менеджер для отслеживания опубликованных URL
        self.urls_manager = get_urls_manager()
        self.source_name = 'techxplore'
        
        # Initialize TelegramPublisher
        self.telegram_publisher = TelegramPublisher(
            telegram_token=self.telegram_token,
            telegram_channel=self.telegram_channel,
            openai_api_key=self.openrouter_api_key,
            ai_model=self.ai_model
        )
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # HTTP session with retries
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            self.session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.8,
                status_forcelist=[429, 403, 422, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
            self.session.headers.update(self.headers)
        except Exception:
            # Fallback to plain requests if retry setup fails
            self.session = requests
        
        logger.info("Techxplore Scraper initialized successfully")

    def create_json_folder(self):
        if not os.path.exists(self.json_folder):
            os.makedirs(self.json_folder)

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
            logging.info(f"Added and saved URL to published list: {url}")
        return success

    def is_url_published(self, url):
        """Проверка, был ли URL уже опубликован"""
        return self.urls_manager.is_url_published(self.source_name, url)

    def parse_article_date_value(self, value):
        """Парсинг различных форматов даты из RSS: struct_time или строка."""
        try:
            if not value:
                return None
            # feedparser обычно отдает struct_time
            if isinstance(value, time.struct_time):
                return datetime.fromtimestamp(time.mktime(value)).date()
            # некоторые поля могут быть строкой RFC822/ISO
            if isinstance(value, str):
                try:
                    dt = parsedate_to_datetime(value)
                    if dt:
                        return dt.date()
                except Exception:
                    pass
            return None
        except Exception as e:
            logger.error(f"Error parsing date value: {e}")
            return None

    def get_entry_date(self, entry):
        """Достает дату из разных возможных полей RSS и приводит к date."""
        candidates = [
            getattr(entry, 'published_parsed', None),
            getattr(entry, 'updated_parsed', None),
            getattr(entry, 'created_parsed', None),
            getattr(entry, 'expired_parsed', None),
            getattr(entry, 'issued_parsed', None),
            getattr(entry, 'date_parsed', None),
            getattr(entry, 'published', None),
            getattr(entry, 'updated', None),
            getattr(entry, 'created', None),
        ]
        for value in candidates:
            d = self.parse_article_date_value(value)
            if d:
                return d
        return None

    def scrape_articles_from_rss(self):
        logger.info(f"Scraping articles from RSS feed: {self.rss_url}")
        # Try parsing with explicit headers (some feeds require a UA/Referer)
        try:
            feed = feedparser.parse(self.rss_url, request_headers={
                'User-Agent': self.headers.get('User-Agent', ''),
                'Accept': 'application/rss+xml, application/xml;q=0.9, */*;q=0.8',
                'Accept-Language': self.headers.get('Accept-Language', 'en-US,en;q=0.9'),
                'Referer': 'https://techxplore.com/'
            })
        except Exception as e:
            logger.warning(f"feedparser parse with headers failed: {e}")
            feed = feedparser.parse(self.rss_url)

        total_entries = len(getattr(feed, 'entries', []))
        logger.info(f"RSS entries fetched: {total_entries}")

        # If empty, try manual HTTP GET with headers then parse content
        if total_entries == 0:
            try:
                logger.info("RSS empty, trying manual HTTP fetch via session...")
                resp = self.session.get(self.rss_url, headers={
                    **self.headers,
                    'Accept': 'application/rss+xml, application/xml;q=0.9, */*;q=0.8',
                    'Referer': 'https://techxplore.com/'
                }, timeout=25)
                resp.raise_for_status()
                feed = feedparser.parse(resp.content)
                total_entries = len(getattr(feed, 'entries', []))
                logger.info(f"Manual fetch RSS entries: {total_entries}")
            except Exception as e:
                logger.error(f"Manual RSS fetch failed: {e}")

        articles = []
        skipped_no_date = 0
        skipped_old = 0
        debug_preview = 0
        for entry in feed.entries:
            article_date = self.get_entry_date(entry)
            if not article_date:
                skipped_no_date += 1
                continue
            if article_date < self.yesterday:
                skipped_old += 1
                continue
            title = getattr(entry, 'title', '').strip()
            url = getattr(entry, 'link', '').strip()
            description = getattr(entry, 'summary', '') or getattr(entry, 'description', '') or ''
            articles.append({
                'title': title,
                'url': url,
                'date': article_date,
                'description': description,
                'topic': None
            })
            if debug_preview < 5:
                logger.info(f"Accepted entry: '{title[:80]}' | date={article_date} | url={url}")
                debug_preview += 1
        logger.info(f"Found {len(articles)} recent articles from RSS (skipped: no_date={skipped_no_date}, old={skipped_old})")
        return articles

    def scrape_article_content_and_media(self, article_url):
        try:
            # Some sites like TechXplore require a referer to avoid 422/403
            headers = dict(self.headers)
            headers['Referer'] = 'https://techxplore.com/'
            response = self.session.get(article_url, headers=headers, timeout=25)
            # If we get a 422/403, try once with a slightly different UA
            if response.status_code in (403, 422):
                alt_headers = dict(headers)
                alt_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
                time.sleep(1.0)
                response = self.session.get(article_url, headers=alt_headers, timeout=25)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract content using multiple fallback selectors
            selectors = [
                '.article-main',
                'div#article-body',
                'article .text',
                'article .article-content',
                'div[itemprop="articleBody"]',
                'div.article-content'
            ]
            content = ""
            for selector in selectors:
                el = soup.select_one(selector)
                if el and el.get_text(strip=True):
                    content = el.get_text(separator='\n', strip=True)
                    break

            # Extract media URL (prefer og:image)
            media_element = soup.select_one('meta[property="og:image"]')
            media_url = media_element['content'] if media_element and media_element.has_attr('content') else None
            
            return {'content': content, 'media_url': media_url}
        except Exception as e:
            logger.error(f"Error scraping article content: {e}")
            return {'content': "", 'media_url': None}

    def save_article_data(self, article, post_content, media_url=None):
        filename = f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.json_folder, filename)
        data = {
            'title': article['title'],
            'url': article['url'],
            'date': article['date'].isoformat(),
            'post_content': post_content,
            'media_url': media_url,
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved article data to {filepath}")

    async def run_daily_scraping(self):
        logger.info("🚀 Starting Techxplore daily scraping...")
        articles = self.scrape_articles_from_rss()
        
        if not articles:
            logger.info("No new articles to publish.")
            return None
            
        # Sort articles by date, newest first
        articles.sort(key=lambda x: x['date'], reverse=True)
        
        for article in articles:
            if not self.is_url_published(article['url']):
                logger.info(f"Processing new article: {article['title']}")
                
                article_data = self.scrape_article_content_and_media(article['url'])
                if not article_data['content'] or len(article_data['content']) < 100:
                    logger.warning("Article content too short or missing, skipping.")
                    continue

                result = await self.telegram_publisher.create_and_publish_post(
                    title=article['title'],
                    content=article_data['content'],
                    article_url=article['url'],
                    topic=article['topic'],
                    media_url=article_data.get('media_url')
                )
                
                if result['success']:
                    self.add_published_url(article['url'])
                    self.save_article_data(article, result['post_content'], result.get('media_url'))
                    logger.info("✅ Article published successfully!")
                    return article
                else:
                    logger.error(f"❌ Failed to publish article: {result.get('error')}")
                    return None
        
        logger.info("No new unpublished articles found.")
        return None

async def main():
    scraper = TechxploreScraper()
    await scraper.run_daily_scraping()

if __name__ == "__main__":
    asyncio.run(main())
