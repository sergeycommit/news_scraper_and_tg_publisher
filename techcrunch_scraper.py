#!/usr/bin/env python3
"""
TechCrunch Auto Scraper and Telegram Publisher
Автоматический скрапер статей с TechCrunch с публикацией в Telegram
"""

import os
import logging
import requests
import feedparser
from datetime import datetime
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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TechCrunchScraper:
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
        
        # RSS URL
        self.rss_url = os.getenv('TECHCRUNCH_RSS_URL', 'https://techcrunch.com/feed/')
        
        # Создаем папку для JSON файлов
        self.json_folder = 'articles_archive'
        self.create_json_folder()
        
        # Файл для отслеживания опубликованных URL
        self.published_urls_file = 'published_urls.json'
        self.published_urls = self.load_published_urls()
        
        # Инициализация клиентов
        self.openai_client = OpenAI(
            api_key=self.openrouter_api_key,
            base_url=self.openrouter_base_url
        )
        self.telegram_bot = Bot(token=self.telegram_token)
        
        # Headers для запросов
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info("TechCrunch Scraper initialized successfully")
        logger.info(f"Loaded {len(self.published_urls)} previously published URLs")
    
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
            # Если не удалось создать папку, используем текущую директорию
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
    
    def filter_unpublished_articles(self, articles):
        """Фильтрация статей, исключая уже опубликованные"""
        unpublished_articles = []
        skipped_count = 0
        
        for article in articles:
            if not self.is_url_published(article['link']):
                unpublished_articles.append(article)
            else:
                skipped_count += 1
                logger.info(f"Skipping already published article: {article['title']}")
        
        logger.info(f"Filtered articles: {len(unpublished_articles)} unpublished, {skipped_count} already published")
        return unpublished_articles
    
    def scrape_rss_feed(self):
        """Скрапинг RSS ленты TechCrunch"""
        try:
            logger.info(f"Scraping RSS feed from: {self.rss_url}")
            response = requests.get(self.rss_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            articles = []
            
            for entry in feed.entries[:20]:  # Берем первые 20 статей
                article = {
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', ''),
                    'author': entry.get('author', 'Unknown')
                }
                articles.append(article)
            
            logger.info(f"Successfully scraped {len(articles)} articles from RSS feed")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping RSS feed: {e}")
            return []
    
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
                articles_text += f"   Краткое описание: {article['summary'][:200]}...\n\n"
            
            prompt = f"""
            Ты эксперт по технологиям и контенту. Из следующего списка статей с TechCrunch выбери ОДНУ самую интересную и виральную статью для публикации в Telegram канале о технологиях.

            Критерии выбора:
            - Актуальность и новизна
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
    
    def scrape_article_content_and_image(self, article_url):
        """Скрапинг полного содержимого статьи и главного изображения"""
        try:
            logger.info(f"Scraping article content and image from: {article_url}")
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
                # Если не нашли по селекторам, берем весь body
                content = soup.get_text(separator=' ', strip=True)
            
            # Очищаем контент
            content = ' '.join(content.split())
            
            # Ищем главное изображение статьи
            image_url = self.extract_main_image(soup, article_url)
            
            logger.info(f"Successfully scraped article content ({len(content)} characters)")
            if image_url:
                logger.info(f"Found main image: {image_url}")
            else:
                logger.info("No main image found")
            
            return content, image_url
            
        except Exception as e:
            logger.error(f"Error scraping article content and image: {e}")
            return "", None
    
    def extract_main_image(self, soup, article_url):
        """Извлечение главного изображения статьи"""
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
                        # Берем первое изображение с достаточным размером
                        for img in elements:
                            src = img.get('src')
                            if src:
                                # Проверяем размеры изображения
                                width = img.get('width')
                                height = img.get('height')
                                
                                # Если размеры не указаны, берем изображение
                                if not width or not height:
                                    image_url = src
                                    break
                                
                                # Проверяем минимальные размеры (200x200)
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
    
    def download_image(self, image_url):
        """Скачивание изображения во временный файл"""
        try:
            if not image_url:
                return None
                
            logger.info(f"Downloading image: {image_url}")
            
            response = requests.get(image_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Проверяем, что это изображение
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not point to an image: {content_type}")
                return None
            
            # Определяем расширение файла
            ext = self.get_image_extension(content_type, image_url)
            
            # Создаем временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_file.write(response.content)
            temp_file.close()
            
            logger.info(f"Image downloaded to: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None
    
    def get_image_extension(self, content_type, url):
        """Определение расширения файла изображения"""
        # По content-type
        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'
        elif 'webp' in content_type:
            return '.webp'
        
        # По URL
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        if path.endswith('.jpg') or path.endswith('.jpeg'):
            return '.jpg'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.gif'):
            return '.gif'
        elif path.endswith('.webp'):
            return '.webp'
        
        # По умолчанию
        return '.jpg'
    
    def create_viral_post(self, article_title, article_content, article_url):
        """Создание вирального поста для Telegram с помощью AI"""
        try:
            prompt = f"""
            Создай для Telegram канала на основе этой статьи виральный пост длинной до 900 символов. Используй разметку, отступы и эмоджи. Вопрос в конце поста не нужен.

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

    async def publish_to_telegram(self, post_content, image_path=None):
        """Публикация поста в Telegram канал с изображением"""
        try:
            logger.info(f"Publishing post to Telegram channel: {self.telegram_channel}")
            
            # Конвертируем Markdown в HTML
            html_content = self.convert_markdown_to_html(post_content)
            
            if image_path and os.path.exists(image_path):
                # Публикуем пост с изображением
                logger.info(f"Publishing post with image: {image_path}")
                
                with open(image_path, 'rb') as photo:
                    await self.telegram_bot.send_photo(
                        chat_id=self.telegram_channel,
                        photo=photo,
                        caption=html_content,
                        parse_mode='HTML'
                    )
                
                # Удаляем временный файл изображения
                try:
                    os.unlink(image_path)
                    logger.info("Temporary image file deleted")
                except Exception as e:
                    logger.warning(f"Could not delete temporary image file: {e}")
                    
            else:
                # Публикуем пост без изображения
                logger.info("Publishing post without image")
                
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
            logger.error(f"Error publishing to Telegram: {e}")
            # Удаляем временный файл изображения в случае ошибки
            if image_path and os.path.exists(image_path):
                try:
                    os.unlink(image_path)
                except:
                    pass
            return False
    
    def save_article_data(self, article, post_content, image_url=None):
        """Сохранение данных о статье для архива"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"article_{timestamp}.json"
            
            data = {
                'timestamp': timestamp,
                'article': article,
                'post_content': post_content,
                'image_url': image_url,
                'published': True
            }
            
            with open(os.path.join(self.json_folder, filename), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Article data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving article data: {e}")
    
    async def run_daily_scraping(self):
        """Основной метод для запуска ежедневного скраппинга"""
        logger.info("Starting daily TechCrunch scraping process")
        
        image_path = None
        
        try:
            # 1. Скрапинг RSS ленты
            articles = self.scrape_rss_feed()
            if not articles:
                logger.error("No articles found in RSS feed")
                return False
            
            # 2. Фильтрация уже опубликованных статей
            unpublished_articles = self.filter_unpublished_articles(articles)
            if not unpublished_articles:
                logger.warning("All articles have already been published")
                return False
            
            # 3. Выбор лучшей статьи с помощью AI
            best_article = self.select_best_article(unpublished_articles)
            if not best_article:
                logger.error("No suitable article selected")
                return False
            
            # 4. Скрапинг содержимого статьи и изображения
            article_content, image_url = self.scrape_article_content_and_image(best_article['link'])
            if not article_content:
                logger.error("Failed to scrape article content")
                return False
            
            # 5. Скачивание изображения
            if image_url:
                image_path = self.download_image(image_url)
                if not image_path:
                    logger.warning("Failed to download image, will publish without it")
            
            # 6. Создание вирального поста с помощью AI
            post_content = self.create_viral_post(
                best_article['title'],
                article_content,
                best_article['link']
            )
            if not post_content:
                logger.error("Failed to create viral post")
                return False
            
            # 7. Публикация в Telegram с изображением
            success = await self.publish_to_telegram(post_content, image_path)
            if not success:
                logger.error("Failed to publish to Telegram")
                return False
            
            # 8. Добавление URL в список опубликованных
            self.add_published_url(best_article['link'])
            
            # 9. Сохранение данных
            self.save_article_data(best_article, post_content, image_url)
            
            logger.info("Daily scraping process completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in daily scraping process: {e}")
            # Удаляем временный файл изображения в случае ошибки
            if image_path and os.path.exists(image_path):
                try:
                    os.unlink(image_path)
                except:
                    pass
            return False

async def main():
    """Главная функция"""
    scraper = TechCrunchScraper()
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