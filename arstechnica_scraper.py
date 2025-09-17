#!/usr/bin/env python3
"""
Ars Technica Scraper and Telegram Publisher
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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arstechnica_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ArsTechnicaScraper:
    def __init__(self):
        load_dotenv()
        
        # OpenRouter/AI Configuration
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.ai_model = os.getenv('AI_MODEL', 'google/gemini-pro')
        
        # Telegram Configuration
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_channel = os.getenv('TELEGRAM_CHANNEL_ID')
        
        # Ars Technica RSS URL
        self.rss_url = 'https://arstechnica.com/ai/feed/'
        
        # Date filtering (articles no older than 2 days)
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=2)
        
        # JSON archive folder
        self.json_folder = 'arstechnica_articles_archive'
        self.create_json_folder()
        
        # Менеджер для отслеживания опубликованных URL
        self.urls_manager = get_urls_manager()
        self.source_name = 'arstechnica'
        
        # Initialize TelegramPublisher
        self.telegram_publisher = TelegramPublisher(
            telegram_token=self.telegram_token,
            telegram_channel=self.telegram_channel,
            openai_api_key=self.openrouter_api_key,
            ai_model=self.ai_model
        )
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        logger.info("Ars Technica Scraper initialized successfully")

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

    def parse_article_date(self, published_time):
        try:
            return datetime.fromtimestamp(time.mktime(published_time)).date()
        except Exception as e:
            logger.error(f"Error parsing date: {e}")
            return None

    def scrape_articles_from_rss(self):
        logger.info(f"Scraping articles from RSS feed: {self.rss_url}")
        feed = feedparser.parse(self.rss_url)
        articles = []
        for entry in feed.entries:
            article_date = self.parse_article_date(entry.published_parsed)
            if article_date and article_date >= self.yesterday:
                articles.append({
                    'title': entry.title,
                    'url': entry.link,
                    'date': article_date,
                    'description': entry.summary,
                    'topic': 'AI'
                })
        logger.info(f"Found {len(articles)} recent articles from RSS feed")
        return articles

    def scrape_article_content_and_media(self, article_url):
        try:
            response = requests.get(article_url, headers=self.headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content for Ars Technica
            content_element = soup.select_one('div.article-content')
            if not content_element:
                content_element = soup.select_one('div[itemprop="articleBody"]')

            content = ""
            if content_element:
                # Remove unwanted elements like figures, scripts, etc.
                for figure in content_element.find_all('figure'):
                    figure.decompose()
                content = content_element.get_text(separator='\n', strip=True)

            # Extract media URL
            media_element = soup.select_one('meta[property="og:image"]')
            media_url = media_element['content'] if media_element else None
            
            return {'content': content, 'media_url': media_url}
        except Exception as e:
            logger.error(f"Error scraping article content: {e}")
            return {'content': "", 'media_url': None}

    def save_article_data(self, article, post_content, media_url=None):
        filename = f"arstechnica_article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
        logger.info("🚀 Starting Ars Technica daily scraping...")
        articles = self.scrape_articles_from_rss()
        
        if not articles:
            logger.info("No new articles to publish.")
            return None
            
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
                    # Do not return here, try the next article
        
        logger.info("No new unpublished articles found.")
        return None

async def main():
    scraper = ArsTechnicaScraper()
    await scraper.run_daily_scraping()

if __name__ == "__main__":
    asyncio.run(main())
