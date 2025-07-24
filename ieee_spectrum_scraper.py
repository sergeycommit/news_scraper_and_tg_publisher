#!/usr/bin/env python3
"""
IEEE Spectrum Auto Scraper and Telegram Publisher
Автоматический скрапер статей с IEEE Spectrum с публикацией в Telegram
"""

import os
import logging
import requests
import feedparser
from datetime import datetime, date
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import asyncio
from telegram import Bot
import json
import time
import tempfile
from urllib.parse import urljoin, urlparse
import sys
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ieee_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IEEESpectrumScraper:
    def __init__(self):
        load_dotenv()
        
        # Конфигурация OpenRouter
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.ai_model = os.getenv('AI_MODEL', 'google/gemini-pro')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.7'))
        
        # Конфигурация Telegram
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_channel = os.getenv('TELEGRAM_CHANNEL_ID')
        
        # IEEE Spectrum URLs
        self.base_url = 'https://spectrum.ieee.org'
        self.ai_url = 'https://spectrum.ieee.org/topic/artificial-intelligence'
        self.robotics_url = 'https://spectrum.ieee.org/topic/robotics'
        
        # Сегодняшняя дата для фильтрации
        self.today = date.today()
        
        # Создаем папку для JSON файлов
        self.json_folder = 'ieee_articles_archive'
        self.create_json_folder()
        
        # Файл для отслеживания опубликованных URL
        self.published_urls_file = 'ieee_published_urls.json'
        self.published_urls = self.load_published_urls()
        
        # Инициализация клиентов
        self.openai_client = OpenAI(
            api_key=self.openrouter_api_key,
            base_url=self.openrouter_base_url
        )
        self.telegram_bot = Bot(token=self.telegram_token)
        
        # Заголовки для запросов
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/gif,*/*',
            'Accept-Encoding': 'identity',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        logger.info("IEEE Spectrum Scraper initialized successfully")
        logger.info(f"Loaded {len(self.published_urls)} previously published URLs")
        logger.info(f"Filtering articles for today's date: {self.today}")
    
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
                    published_urls = set(data.get('published_urls', []))
                    logger.info(f"Loaded {len(published_urls)} published URLs from {self.published_urls_file}")
                    return published_urls
            else:
                logger.info(f"Published URLs file not found, creating new one: {self.published_urls_file}")
                return set()
        except Exception as e:
            logger.error(f"Error loading published URLs: {e}")
            return set()
    
    def save_published_urls(self):
        """Сохранение списка опубликованных URL"""
        try:
            data = {
                'published_urls': list(self.published_urls),
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.published_urls)
            }
            
            with open(self.published_urls_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(self.published_urls)} published URLs to {self.published_urls_file}")
        except Exception as e:
            logger.error(f"Error saving published URLs: {e}")
    
    def add_published_url(self, url):
        """Добавление URL в список опубликованных"""
        self.published_urls.add(url)
        self.save_published_urls()
        logger.info(f"Added URL to published list: {url}")
    
    def is_url_published(self, url):
        """Проверка, был ли URL уже опубликован"""
        return url in self.published_urls
    
    def parse_article_date(self, date_text):
        """Парсинг даты статьи"""
        try:
            if not date_text:
                return None
            
            # Убираем лишние пробелы
            date_text = date_text.strip()
            
            # Различные форматы дат IEEE Spectrum
            date_patterns = [
                # "22 Jul 2025" или "22 Jul 2025 16:30"
                r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',
                # "July 22, 2025" или "July 22, 2025 16:30"
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
                # "2025-07-22" или "2025/07/22"
                r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
                # "22.07.2025" или "22/07/2025"
                r'(\d{1,2})[./](\d{1,2})[./](\d{4})',
                # "Today" или "Yesterday"
                r'(Today|Yesterday)',
                # "2 hours ago", "1 day ago", etc.
                r'(\d+)\s+(hour|day|minute)s?\s+ago',
                # "17h", "2d", "30m" - относительное время IEEE
                r'(\d+)(h|d|m)'
            ]
            
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
                'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
            }
            
            for pattern in date_patterns:
                match = re.search(pattern, date_text, re.IGNORECASE)
                if match:
                    if 'Today' in match.group():
                        return self.today
                    elif 'Yesterday' in match.group():
                        from datetime import timedelta
                        return self.today - timedelta(days=1)
                    elif 'ago' in match.group():
                        # Для "X hours/days ago" считаем как сегодня
                        return self.today
                    elif len(match.groups()) == 2 and match.group(2) in ['h', 'd', 'm']:
                        # Для "17h", "2d", "30m" считаем как сегодня
                        return self.today
                    elif len(match.groups()) == 3:
                        groups = match.groups()
                        if groups[0].isdigit() and groups[1].isdigit() and groups[2].isdigit():
                            # Формат "22 Jul 2025" или "2025-07-22"
                            if len(groups[0]) == 4:  # Год первым
                                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                            else:  # День первым
                                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        else:
                            # Формат "Jul 22 2025" или "July 22, 2025"
                            if groups[0].isdigit():
                                day, month_name, year = int(groups[0]), groups[1], int(groups[2])
                            else:
                                month_name, day, year = groups[0], int(groups[1]), int(groups[2])
                            
                            month = month_map.get(month_name[:3], 1)
                        
                        try:
                            return date(year, month, day)
                        except ValueError:
                            continue
            
            logger.warning(f"Could not parse date: {date_text}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_text}': {e}")
            return None
    
    def is_article_from_today(self, article_date):
        """Проверка, что статья за сегодняшнюю дату"""
        if not article_date:
            return False
        
        return article_date == self.today
    
    def scrape_ieee_articles(self):
        """Скрапинг статей с IEEE Spectrum по тегам AI и Robotics"""
        try:
            articles = []
            
            # Скрапим статьи с AI
            logger.info("Scraping AI articles from IEEE Spectrum")
            ai_articles = self.scrape_topic_page(self.ai_url, "AI")
            articles.extend(ai_articles)
            
            # Скрапим статьи с Robotics
            logger.info("Scraping Robotics articles from IEEE Spectrum")
            robotics_articles = self.scrape_topic_page(self.robotics_url, "Robotics")
            articles.extend(robotics_articles)
            
            # Удаляем дубликаты по URL
            unique_articles = []
            seen_urls = set()
            for article in articles:
                if article['link'] not in seen_urls:
                    unique_articles.append(article)
                    seen_urls.add(article['link'])
            
            logger.info(f"Successfully scraped {len(unique_articles)} unique articles from IEEE Spectrum")
            return unique_articles
            
        except Exception as e:
            logger.error(f"Error scraping IEEE Spectrum articles: {e}")
            return []
    
    def scrape_topic_page(self, url, topic):
        """Скрапинг страницы с определенной темой"""
        try:
            logger.info(f"Scraping {topic} articles from: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            today_articles = 0
            
            # Ищем статьи на странице
            article_selectors = [
                'article',
                '.article-card',
                '.post-card',
                '.content-card',
                '[data-testid="article-card"]'
            ]
            
            for selector in article_selectors:
                elements = soup.select(selector)
                if elements:
                    logger.info(f"Found {len(elements)} articles using selector: {selector}")
                    break
            
            if not elements:
                # Если не нашли по селекторам, ищем по структуре
                elements = soup.find_all(['article', 'div'], class_=re.compile(r'article|post|content'))
            
            for element in elements[:20]:  # Увеличиваем лимит для поиска сегодняшних статей
                try:
                    article = self.extract_article_info(element, topic)
                    if article:
                        # Проверяем, что статья за сегодня
                        if article['parsed_date'] and self.is_article_from_today(article['parsed_date']):
                            articles.append(article)
                            today_articles += 1
                            logger.info(f"Found today's article: {article['title']} ({article['date']})")
                        else:
                            logger.debug(f"Skipping old article: {article['title']} ({article['date']})")
                except Exception as e:
                    logger.warning(f"Error extracting article info: {e}")
                    continue
            
            logger.info(f"Extracted {len(articles)} today's articles from {topic} page (total found: {today_articles})")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping topic page {url}: {e}")
            return []
    
    def extract_article_info(self, element, topic):
        """Извлечение информации о статье из HTML элемента"""
        try:
            # Ищем заголовок
            title_selectors = ['h1', 'h2', 'h3', '.title', '.headline', '[data-testid="title"]']
            title = None
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Ищем ссылку на статью (не на topic/type страницы)
            link_selectors = ['a', '.link', '[data-testid="link"]']
            link = None
            for selector in link_selectors:
                link_elements = element.select(selector)
                for link_elem in link_elements:
                    href = link_elem.get('href')
                    if href:
                        # Исключаем ссылки на topic/type страницы
                        if not any(exclude in href for exclude in ['/topic/', '/type/', 'spectrum.ieee.org/topic/', 'spectrum.ieee.org/type/']):
                            if not href.startswith('http'):
                                link = urljoin(self.base_url, href)
                            else:
                                link = href
                            break
                if link:
                    break
            
            if not link:
                return None
            
            # Ищем описание
            desc_selectors = ['.description', '.summary', '.excerpt', 'p']
            description = ""
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    break
            
            # Ищем автора
            author_selectors = ['.author', '.byline', '[data-testid="author"]']
            author = "Unknown"
            for selector in author_selectors:
                author_elem = element.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            # Ищем дату - обновленные селекторы для IEEE Spectrum
            date_selectors = [
                '.social-date', '.social-date__text',  # Основные селекторы для IEEE
                '[class*="date"]',  # Общий селектор для дат
                'time',
                '.date', '.time', '[data-testid="date"]',
                '.article-date', '.post-date', '.published-date',
                '.meta-date', '.timestamp', '.publish-date',
                '.byline', '.author-info', '.meta'
            ]
            
            date_text = ""
            for selector in date_selectors:
                date_elements = element.select(selector)
                if date_elements:
                    for date_elem in date_elements:
                        text = date_elem.get_text(strip=True)
                        datetime_attr = date_elem.get('datetime')
                        
                        # Приоритет datetime атрибуту
                        if datetime_attr:
                            date_text = datetime_attr
                            break
                        elif text:
                            # Проверяем, что это похоже на дату
                            if any(char.isdigit() for char in text) and len(text) > 2:
                                # Исключаем "X min read" и подобные
                                if not any(word in text.lower() for word in ['min read', 'read', 'ago']):
                                    date_text = text
                                    break
            
            # Если не нашли дату в специальных селекторах, ищем в тексте
            if not date_text:
                # Ищем дату в тексте элемента
                element_text = element.get_text()
                date_patterns = [
                    r'\d+[hdm]',  # 3h, 1h, 2d, 30m - относительное время IEEE
                    r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
                    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}',
                    r'\d{4}-\d{1,2}-\d{1,2}',
                    r'\d{1,2}/\d{1,2}/\d{4}',
                    r'(Today|Yesterday)',
                    r'\d+\s+(hour|day|minute)s?\s+ago'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, element_text, re.IGNORECASE)
                    if match:
                        date_text = match.group()
                        break
            
            # Парсим дату
            article_date = self.parse_article_date(date_text)
            
            article = {
                'title': title,
                'link': link,
                'description': description,
                'author': author,
                'date': date_text,
                'parsed_date': article_date,
                'topic': topic
            }
            
            return article
            
        except Exception as e:
            logger.error(f"Error extracting article info: {e}")
            return None
    
    def filter_unpublished_articles(self, articles):
        """Фильтрация статей, исключая уже опубликованные"""
        unpublished_articles = []
        skipped_count = 0
        
        for article in articles:
            # Статьи уже отфильтрованы по дате в scrape_topic_page
            # Здесь только проверяем, не были ли они уже опубликованы
            if not self.is_url_published(article['link']):
                unpublished_articles.append(article)
            else:
                skipped_count += 1
                logger.info(f"Skipping already published article: {article['title']}")
        
        logger.info(f"Filtered articles: {len(unpublished_articles)} unpublished, {skipped_count} already published")
        return unpublished_articles
    
    def select_best_article(self, articles):
        """Выбор самой интересной статьи с помощью AI"""
        try:
            if not articles:
                logger.warning("No articles to select from")
                return None
            
            # Формируем список статей для AI
            articles_text = ""
            for i, article in enumerate(articles[:10], 1):  # Берем первые 10 статей
                articles_text += f"{i}. {article['title']}\n"
                articles_text += f"   Автор: {article['author']}\n"
                articles_text += f"   Тема: {article['topic']}\n"
                articles_text += f"   Описание: {article['description'][:200]}...\n\n"
            
            prompt = f"""
            Ты эксперт по технологиям и контенту. Из следующего списка статей с IEEE Spectrum (AI и Robotics) выбери ОДНУ самую интересную и виральную статью для публикации в Telegram канале об AI и robotics технологиях.

            Критерии выбора:
            - Потенциал виральности
            - Интерес для широкой аудитории
            - Технологическая значимость

            Статьи:
            {articles_text}

            Ответь ТОЛЬКО номером выбранной статьи (1-10). Если ни одна статья не подходит, ответь "0".
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.ai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=self.temperature
            )
            
            choice = response.choices[0].message.content.strip()
            
            try:
                article_index = int(choice) - 1
                if 0 <= article_index < len(articles):
                    selected_article = articles[article_index]
                    logger.info(f"AI selected article: {selected_article['title']}")
                    return selected_article
                else:
                    logger.warning(f"AI returned invalid index: {choice}")
                    return articles[0] if articles else None
            except ValueError:
                logger.warning(f"AI returned non-numeric response: {choice}")
                return articles[0] if articles else None
                
        except Exception as e:
            logger.error(f"Error selecting best article: {e}")
            return articles[0] if articles else None
    
    def scrape_article_content_and_media(self, article_url):
        """Скрапинг содержимого статьи и извлечение GIF/медиа"""
        try:
            logger.info(f"Scraping article content and media from: {article_url}")
            response = requests.get(article_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()

            # Ищем основной контент статьи
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                'main'
            ]
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(separator=' ', strip=True)
                    break
            if not content:
                content = soup.get_text(separator=' ', strip=True)
            content = ' '.join(content.split())

            # === Новый блок: Поиск GIF ===
            gif_url = None
            # 1. Сначала ищем <picture> с <source srcset=...gif...>
            for picture in soup.find_all('picture'):
                for source in picture.find_all('source'):
                    srcset = source.get('srcset', '')
                    if '.gif' in srcset:
                        # srcset может содержать несколько ссылок через запятую или пробел
                        candidates = [s.strip() for s in re.split('[, ]+', srcset) if '.gif' in s]
                        # Берем самую большую (обычно первая)
                        if candidates:
                            gif_url = candidates[0]
                            logger.info(f"Found GIF in <picture>: {gif_url}")
                            break
                if gif_url:
                    break
            # 2. Если не нашли, ищем <img src=...gif...>
            if not gif_url:
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    if '.gif' in src.lower():
                        gif_url = src
                        logger.info(f"Found GIF in <img>: {gif_url}")
                        break
            # 3. Если не нашли GIF, fallback на обычное изображение (старый код)
            image_url = None
            if not gif_url:
                image_url = self.extract_main_image(soup, article_url)
                if image_url:
                    logger.info(f"Fallback image: {image_url}")
            media_url = gif_url or image_url
            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = urljoin(article_url, media_url)
            return content, media_url
        except Exception as e:
            logger.error(f"Error scraping article content and media: {e}")
            return "", None
    
    def extract_media(self, soup, article_url):
        """Извлечение медиафайлов (изображения или видео)"""
        try:
            # Сначала ищем видео
            video_selectors = [
                'video source',
                'video',
                'iframe[src*="youtube"]',
                'iframe[src*="vimeo"]',
                '.video-player',
                '[data-testid="video"]'
            ]
            
            for selector in video_selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        src = element.get('src')
                        if src:
                            if not src.startswith(('http://', 'https://')):
                                src = urljoin(article_url, src)
                            logger.info(f"Found video: {src}")
                            return src
            
            # Если видео не найдено, ищем изображения
            image_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                'meta[property="og:image:secure_url"]',
                '.article-featured-image img',
                '.post-featured-image img',
                '.entry-featured-image img',
                '.featured-image img',
                'article img',
                '.article-content img',
                '.post-content img',
                '.entry-content img',
                'main img',
                '.hero-image img'
            ]
            
            for selector in image_selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        src = element.get('content') or element.get('src')
                        if src:
                            if not src.startswith(('http://', 'https://')):
                                src = urljoin(article_url, src)
                            logger.info(f"Found image: {src}")
                            return src
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting media: {e}")
            return None
    
    def download_media(self, media_url):
        """Скачивание медиафайла во временный файл"""
        try:
            if not media_url:
                return None
                
            logger.info(f"Downloading media: {media_url}")
            
            response = requests.get(media_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Определяем тип файла
            content_type = response.headers.get('content-type', '')
            url_path = urlparse(media_url).path.lower()
            
            # Определяем расширение файла
            ext = self.get_media_extension(content_type, url_path, media_url)
            
            # Создаем временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_file.write(response.content)
            temp_file.close()
            
            # Проверяем размер файла
            file_size = os.path.getsize(temp_file.name)
            logger.info(f"Media downloaded to: {temp_file.name} (size: {file_size} bytes)")
            
            # Проверяем ограничения Telegram API
            if ext == '.gif' and file_size > 50 * 1024 * 1024:  # 50MB для анимаций
                logger.warning(f"GIF file too large for Telegram ({file_size} bytes > 50MB)")
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                return None
            
            # Если файл слишком маленький, возможно это не изображение
            if file_size < 100:
                logger.warning(f"Media file too small ({file_size} bytes), might not be a valid image")
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                return None
            
            # Если это GIF, валидируем его
            if ext == '.gif':
                try:
                    from PIL import Image
                    with Image.open(temp_file.name) as img:
                        # Проверяем, что это действительно GIF
                        if img.format != 'GIF':
                            logger.warning(f"File has .gif extension but format is {img.format}")
                            
                            # Если это WebP, конвертируем в PNG
                            if img.format == 'WEBP':
                                logger.info("Converting WebP (with .gif extension) to PNG")
                                
                                # Конвертируем в RGB (убираем прозрачность)
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    img = img.convert('RGB')
                                
                                # Создаем новый временный файл с расширением .png
                                png_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                                png_file.close()
                                
                                # Сохраняем как PNG
                                img.save(png_file.name, 'PNG', optimize=True)
                                
                                # Удаляем оригинальный файл
                                try:
                                    os.unlink(temp_file.name)
                                except:
                                    pass
                                
                                logger.info(f"Converted WebP to PNG: {png_file.name}")
                                return png_file.name
                            else:
                                # Для других форматов удаляем файл
                                try:
                                    os.unlink(temp_file.name)
                                except:
                                    pass
                                return None
                        
                        # Проверяем, что это анимированный GIF
                        if hasattr(img, 'n_frames') and img.n_frames > 1:
                            logger.info(f"Valid animated GIF with {img.n_frames} frames")
                        else:
                            logger.warning("GIF file is not animated")
                        
                        # Проверяем размеры (не слишком большие для Telegram)
                        if img.size[0] > 2000 or img.size[1] > 2000:
                            logger.warning(f"GIF dimensions too large: {img.size}")
                        
                except Exception as e:
                    logger.error(f"Error validating GIF: {e}")
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
                    return None
                
                logger.info(f"GIF file downloaded and validated successfully: {temp_file.name}")
                return temp_file.name
            
            # Если это WebP и размер небольшой, попробуем конвертировать в PNG
            if ext == '.webp' and file_size < 50000:  # Меньше 50KB
                try:
                    from PIL import Image
                    import io
                    
                    # Открываем WebP изображение
                    with Image.open(temp_file.name) as img:
                        # Конвертируем в RGB (убираем прозрачность)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Создаем новый временный файл с расширением .png
                        png_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                        png_file.close()
                        
                        # Сохраняем как PNG
                        img.save(png_file.name, 'PNG', optimize=True)
                        
                        # Удаляем оригинальный WebP файл
                        try:
                            os.unlink(temp_file.name)
                        except:
                            pass
                        
                        logger.info(f"Converted WebP to PNG: {png_file.name}")
                        return png_file.name
                        
                except ImportError:
                    logger.warning("PIL not available, cannot convert WebP to PNG")
                except Exception as e:
                    logger.warning(f"Failed to convert WebP to PNG: {e}")
                    # Возвращаем оригинальный файл
                    return temp_file.name
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None
    
    def get_media_extension(self, content_type, url_path, media_url):
        """Определение расширения файла медиа"""
        # Приоритет: проверяем URL на наличие .gif
        if '.gif' in media_url.lower():
            return '.gif'
        
        # По content-type
        if 'video' in content_type:
            if 'mp4' in content_type:
                return '.mp4'
            elif 'webm' in content_type:
                return '.webm'
            elif 'avi' in content_type:
                return '.avi'
            else:
                return '.mp4'
        elif 'image' in content_type:
            if 'jpeg' in content_type or 'jpg' in content_type:
                return '.jpg'
            elif 'png' in content_type:
                return '.png'
            elif 'gif' in content_type:
                return '.gif'
            elif 'webp' in content_type:
                return '.webp'
            else:
                return '.jpg'
        
        # По URL path
        if url_path.endswith('.mp4'):
            return '.mp4'
        elif url_path.endswith('.webm'):
            return '.webm'
        elif url_path.endswith('.avi'):
            return '.avi'
        elif url_path.endswith('.jpg') or url_path.endswith('.jpeg'):
            return '.jpg'
        elif url_path.endswith('.png'):
            return '.png'
        elif url_path.endswith('.gif'):
            return '.gif'
        elif url_path.endswith('.webp'):
            return '.webp'
        
        # По умолчанию
        if 'video' in media_url.lower():
            return '.mp4'
        else:
            return '.jpg'
    
    def create_viral_post(self, article_title, article_content, article_url, topic):
        """Создание вирального поста для Telegram с помощью AI"""
        try:
            prompt = f"""
            Создай на основе этой статьи для Telegram канала об AI и Robotics технологиях виральный пост длинной длинной от 700 до 1024 символов(включая теги), вопрос в конце поста не нужен, количество тегов ограничить 5. Стиль информативный. Используй разметку, отступы и эmоджи. Перепроверь в конце количество символов, получившеся подписи, от 700 до 1024(включая теги). Вывести только сам пост.

            Заголовок статьи: {article_title}
            
            Содержание статьи: {article_content[:2900]}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.ai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Заменяем плейсхолдер ссылки на реальную
            post_content = post_content.replace('[ссылка]', article_url)
            
            logger.info("Successfully created viral post with AI")
            return post_content
            
        except Exception as e:
            logger.error(f"Error creating viral post: {e}")
            return None
    
    def convert_markdown_to_html(self, text):
        """Конвертация Markdown разметки в HTML для Telegram"""
        try:
            # Заменяем Markdown на HTML теги
            import re
            
            # Ссылки: [текст](url) -> <a href="url">текст</a> (делаем первым)
            text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
            
            # Жирный текст: **текст** -> <b>текст</b>
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            
            # Курсив: *текст* -> <i>текст</i>
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
            
            # Подчеркнутый: __текст__ -> <u>текст</u>
            text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
            
            # Зачеркнутый: ~~текст~~ -> <s>текст</s>
            text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)
            
            # Моноширинный: `текст` -> <code>текст</code>
            text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
            
            # Экранируем специальные символы HTML (кроме наших тегов)
            text = text.replace('&', '&amp;')
            
            # Восстанавливаем наши HTML теги
            text = text.replace('&amp;lt;b&amp;gt;', '<b>').replace('&amp;lt;/b&amp;gt;', '</b>')
            text = text.replace('&amp;lt;i&amp;gt;', '<i>').replace('&amp;lt;/i&amp;gt;', '</i>')
            text = text.replace('&amp;lt;u&amp;gt;', '<u>').replace('&amp;lt;/u&amp;gt;', '</u>')
            text = text.replace('&amp;lt;s&amp;gt;', '<s>').replace('&amp;lt;/s&amp;gt;', '</s>')
            text = text.replace('&amp;lt;code&amp;gt;', '<code>').replace('&amp;lt;/code&amp;gt;', '</code>')
            text = text.replace('&amp;lt;a href=&amp;quot;', '<a href="').replace('&amp;lt;/a&amp;gt;', '</a>')
            text = text.replace('&amp;quot;&amp;gt;', '">')
            
            return text
            
        except Exception as e:
            logger.error(f"Error converting markdown to HTML: {e}")
            return text

    async def publish_to_telegram(self, post_content, media_path=None):
        """Публикация поста в Telegram канал с медиафайлом"""
        try:
            logger.info(f"Publishing post to Telegram channel: {self.telegram_channel}")
            
            # Конвертируем Markdown в HTML
            html_content = self.convert_markdown_to_html(post_content)
            
            if media_path and os.path.exists(media_path):
                # Определяем тип медиафайла
                is_gif = media_path.lower().endswith('.gif')
                
                if is_gif:
                    # Для GIF используем sendAnimation
                    logger.info(f"Publishing GIF animation: {media_path}")
                    
                    # Ограничиваем длину подписи для анимаций (1024 символа)
                    if len(html_content) > 1024:
                        html_content = html_content[:1021] + "..."
                        logger.info("Caption truncated for animation (max 1024 characters)")
                    
                    with open(media_path, 'rb') as animation:
                        await self.telegram_bot.send_animation(
                            chat_id=self.telegram_channel,
                            animation=animation,
                            caption=html_content,
                            parse_mode='HTML'
                        )
                else:
                    # Для других изображений используем sendPhoto
                    logger.info(f"Publishing post with image: {media_path}")
                    
                    with open(media_path, 'rb') as photo:
                        await self.telegram_bot.send_photo(
                            chat_id=self.telegram_channel,
                            photo=photo,
                            caption=html_content,
                            parse_mode='HTML'
                        )
                
                # Удаляем временный файл
                try:
                    os.unlink(media_path)
                    logger.info("Temporary media file deleted")
                except Exception as e:
                    logger.warning(f"Could not delete temporary media file: {e}")
                    
            else:
                # Публикуем пост без медиа
                logger.info("Publishing post without media")
                
                # Разбиваем длинный пост на части, если нужно
                if len(html_content) > 4096:
                    parts = [html_content[i:i+4096] for i in range(0, len(html_content), 4096)]
                    for i, part in enumerate(parts):
                        await self.telegram_bot.send_message(
                            chat_id=self.telegram_channel,
                            text=part,
                            parse_mode='HTML',
                            disable_web_page_preview=False
                        )
                        if i < len(parts) - 1:
                            await asyncio.sleep(1)
                else:
                    await self.telegram_bot.send_message(
                        chat_id=self.telegram_channel,
                        text=html_content,
                        parse_mode='HTML',
                        disable_web_page_preview=False
                    )
            
            logger.info("Successfully published post to Telegram")
            return True
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error publishing to Telegram: {error_message}")
            
            # Если ошибка связана с длиной подписи, пересоздаем пост
            if "caption is too long" in error_message.lower():
                logger.warning("Caption too long, recreating post with shorter content...")
                
                # Удаляем временный файл
                if media_path and os.path.exists(media_path):
                    try:
                        os.unlink(media_path)
                    except:
                        pass
                
                # Возвращаем специальный код для пересоздания поста
                return "RECREATE_POST"
            
            # Удаляем временный файл в случае других ошибок
            if media_path and os.path.exists(media_path):
                try:
                    os.unlink(media_path)
                except:
                    pass
            return False
    
    def save_article_data(self, article, post_content, media_url=None):
        """Сохранение данных о статье для архива"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ieee_article_{timestamp}.json"
            
            # Конвертируем date объект в строку для JSON
            article_copy = article.copy()
            if article_copy.get('parsed_date'):
                article_copy['parsed_date'] = article_copy['parsed_date'].isoformat()
            
            data = {
                'timestamp': timestamp,
                'article': article_copy,
                'post_content': post_content,
                'media_url': media_url,
                'published': True
            }
            
            with open(os.path.join(self.json_folder, filename), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Article data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving article data: {e}")
    
    async def run_daily_scraping(self):
        """Основной метод для запуска ежедневного скраппинга"""
        logger.info("Starting daily IEEE Spectrum scraping process")
        
        media_path = None
        
        try:
            # 1. Скрапинг статей с IEEE Spectrum
            articles = self.scrape_ieee_articles()
            if not articles:
                logger.error("No articles found on IEEE Spectrum")
                return False
            
            # 2. Фильтрация уже опубликованных статей
            unpublished_articles = self.filter_unpublished_articles(articles)
            if not unpublished_articles:
                logger.warning("All articles have already been published or are from the past")
                return False
            
            # 3. Выбор лучшей статьи с помощью AI
            best_article = self.select_best_article(unpublished_articles)
            if not best_article:
                logger.error("No suitable article selected")
                return False
            
            # 4. Скрапинг содержимого статьи и медиафайлов
            article_content, media_url = self.scrape_article_content_and_media(best_article['link'])
            if not article_content:
                logger.error("Failed to scrape article content")
                return False
            
            # 5. Скачивание медиафайла
            if media_url:
                media_path = self.download_media(media_url)
                if not media_path:
                    logger.warning("Failed to download media, will publish without it")
            
            # 6. Создание вирального поста с помощью AI
            post_content = self.create_viral_post(
                best_article['title'],
                article_content,
                best_article['link'],
                best_article['topic']
            )
            if not post_content:
                logger.error("Failed to create viral post")
                return False
            
            # 7. Публикация в Telegram с медиафайлом
            max_retry_attempts = 10
            retry_count = 0
            
            while retry_count < max_retry_attempts:
                success = await self.publish_to_telegram(post_content, media_path)
                
                if success == True:
                    break
                elif success == "RECREATE_POST":
                    retry_count += 1
                    logger.info(f"Recreating post (attempt {retry_count}/{max_retry_attempts})")
                    
                    # Создаем новый пост с более коротким лимитом
                    shorter_prompt = f"""
                    Создай на основе этой статьи для Telegram канала об AI и Robotics технологиях очень короткий виральный пост длинной от 700 до 1000 символов(включая теги), вопрос в конце поста не нужен, количество тегов ограничить 3. Стиль поста информативный, полезный. Используй разметку, отступы и эmоджи(красивее когда эмоджи начинают новый абзац). Перепроверь в конце количество символов, получившейся подписи, от 500 до 1000(включая теги). Вывести только сам пост.

                    Заголовок статьи: {best_article['title']}
                    
                    Содержание статьи: {article_content[:1500]}
                    """
                    
                    response = self.openai_client.chat.completions.create(
                        model=self.ai_model,
                        messages=[{"role": "user", "content": shorter_prompt}],
                        max_tokens=self.max_tokens,
                        temperature=self.temperature
                    )
                    
                    post_content = response.choices[0].message.content.strip()
                    post_content = post_content.replace('[ссылка]', best_article['link'])
                    
                    logger.info(f"Recreated post length: {len(post_content)} characters")
                    
                    # Скачиваем медиафайл заново
                    if media_url:
                        media_path = self.download_media(media_url)
                        if not media_path:
                            logger.warning("Failed to download media, will publish without it")
                    
                    continue
                else:
                    logger.error("Failed to publish to Telegram")
                    return False
            
            if retry_count >= max_retry_attempts:
                logger.error(f"Failed to publish after {max_retry_attempts} attempts")
                return False
            
            # 8. Добавление URL в список опубликованных
            self.add_published_url(best_article['link'])
            
            # 9. Сохранение данных
            self.save_article_data(best_article, post_content, media_url)
            
            logger.info("Daily IEEE Spectrum scraping process completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in daily scraping process: {e}")
            # Удаляем временный файл в случае ошибки
            if media_path and os.path.exists(media_path):
                try:
                    os.unlink(media_path)
                except:
                    pass
            return False

    def extract_main_image(self, soup, article_url):
        """Извлечение fallback-изображения статьи (если нет GIF)"""
        try:
            # Список селекторов для поиска главного изображения
            image_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                'meta[property="og:image:secure_url"]',
                '.article-featured-image img',
                '.post-featured-image img',
                '.entry-featured-image img',
                '.featured-image img',
                'article img',
                '.article-content img',
                '.post-content img',
                '.entry-content img',
                'main img'
            ]
            image_url = None
            # Сначала ищем в meta тегах (обычно там лучшее качество)
            for selector in image_selectors[:3]:
                elements = soup.select(selector)
                if elements:
                    image_url = elements[0].get('content') or elements[0].get('src')
                    if image_url:
                        break
            # Если не нашли в meta, ищем в img тегах
            if not image_url:
                for selector in image_selectors[3:]:
                    elements = soup.select(selector)
                    if elements:
                        for img in elements:
                            src = img.get('src')
                            if src:
                                width = img.get('width')
                                height = img.get('height')
                                if not width or not height:
                                    image_url = src
                                    break
                                try:
                                    if int(width) >= 200 and int(height) >= 200:
                                        image_url = src
                                        break
                                except (ValueError, TypeError):
                                    image_url = src
                                    break
            # Преобразуем относительные URL в абсолютные
            if image_url and not image_url.startswith(('http://', 'https://')):
                image_url = urljoin(article_url, image_url)
            return image_url
        except Exception as e:
            logger.error(f"Error extracting main image: {e}")
            return None

async def main():
    """Главная функция"""
    scraper = IEEESpectrumScraper()
    await scraper.run_daily_scraping()

def run_with_proper_cleanup():
    """Запуск с правильной очисткой event loop для Windows"""
    import platform
    
    if platform.system() == 'Windows':
        # Используем SelectEventLoop для Windows чтобы избежать проблем с ProactorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Скрапинг прерван пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        # Очищаем все pending tasks
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except:
            pass

if __name__ == "__main__":
    run_with_proper_cleanup() 