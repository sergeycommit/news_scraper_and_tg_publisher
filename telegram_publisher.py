#!/usr/bin/env python3
"""
Модуль для публикации постов в Telegram
Включает функции составления постов и отправки
"""

import os
import logging
import asyncio
import tempfile
from datetime import datetime
from urllib.parse import urljoin
import requests
from openai import OpenAI
from telegram import Bot
from telegram.error import TelegramError
import re

# Настройка логирования
logger = logging.getLogger(__name__)

class TelegramPublisher:
    """Класс для публикации постов в Telegram"""
    
    def __init__(self, telegram_token, telegram_channel, openai_api_key, ai_model="openai/gpt-4o-mini"):
        """
        Инициализация издателя
        
        Args:
            telegram_token (str): Токен Telegram бота
            telegram_channel (str): ID канала для публикации
            openai_api_key (str): API ключ OpenAI/OpenRouter
            ai_model (str): Модель AI для генерации постов
        """
        self.telegram_token = telegram_token
        self.telegram_channel = telegram_channel
        self.ai_model = ai_model
        
        # Инициализация клиентов
        self.telegram_bot = Bot(token=telegram_token)
        self.openai_client = OpenAI(
            api_key=openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Настройки AI
        self.max_tokens = 1000
        
        # Загрузка промптов из переменных окружения
        self.custom_prompt = os.getenv('PROMPT', '')
        self.custom_system_prompt = os.getenv('SYSTEM_PROMPT', '')
        
        logger.info("TelegramPublisher initialized successfully")
    
    async def create_and_publish_post(self, title, content, article_url, topic=None, media_url=None):
        """
        Основной метод: создает пост из исходного текста и публикует с изображением
        
        Args:
            title (str): Заголовок статьи
            content (str): Содержимое статьи
            article_url (str): URL статьи
            topic (str): Тема статьи (опционально)
            media_url (str): URL изображения (опционально)
            
        Returns:
            dict: Результат публикации с информацией о посте
        """
        try:
            logger.info(f"Creating and publishing post for: {title[:50]}...")
            
            # Создаем вирусный пост
            post_content = self.create_viral_post(title, content, article_url, topic)
            
            if not post_content or len(post_content.strip()) < 50:
                logger.error("Failed to create viral post - content too short or empty")
                return {
                    'success': False,
                    'error': 'Post creation failed',
                    'post_content': None,
                    'media_path': None
                }
            
            logger.info(f"Created post with {len(post_content)} characters")
            
            # Скачиваем медиа если есть URL
            media_path = None
            if media_url:
                media_path = self.download_media(media_url)
                if media_path:
                    logger.info(f"Downloaded media: {media_path}")
                else:
                    logger.warning("Failed to download media")
            
            # Публикуем в Telegram
            success = await self.publish_to_telegram(post_content, media_path)
            
            result = {
                'success': success,
                'post_content': post_content,
                'media_path': media_path,
                'media_url': media_url
            }
            
            if not success:
                result['error'] = 'Telegram publication failed'
                logger.error("Failed to publish to Telegram")
            else:
                logger.info("✅ Post created and published successfully!")
            
            # Очищаем временные файлы
            if media_path:
                self.cleanup_media(media_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in create_and_publish_post: {e}")
            return {
                'success': False,
                'error': str(e),
                'post_content': None,
                'media_path': None
            }
    
    def create_viral_post(self, title, content, article_url, topic=None):
        """
        Создание вирусного поста с помощью AI
        
        Args:
            title (str): Заголовок статьи
            content (str): Содержимое статьи
            article_url (str): URL статьи
            topic (str): Тема статьи
            
        Returns:
            str: Сгенерированный пост или None в случае ошибки
        """
        try:
            logger.info(f"create_viral_post called with URL: {article_url}")
            
            # Определяем промпт
            if self.custom_prompt:
                # Если в кастомном промпте нет переменных, добавляем информацию о статье
                if '{title}' not in self.custom_prompt and '{content}' not in self.custom_prompt:
                    prompt = f"""
{self.custom_prompt}

ЗАГОЛОВОК: {title}
СОДЕРЖАНИЕ: {content[:1000] + "..." if len(content) > 1000 else content}
ССЫЛКА: {article_url}
ТЕМА: {topic or "Technology"}
"""
                    logger.info("Using custom PROMPT from .env file + article info")
                else:
                    # Подставляем переменные в кастомный промпт
                    try:
                        prompt = self.custom_prompt.format(
                            title=title,
                            content=content[:1000] + "..." if len(content) > 1000 else content,
                            url=article_url,
                            topic=topic or "Technology"
                        )
                        logger.info("Using custom PROMPT from .env file with variable substitution")
                    except Exception as e:
                        logger.warning(f"Variable substitution failed: {e}, using fallback")
                        prompt = f"""
{self.custom_prompt}

ЗАГОЛОВОК: {title}
СОДЕРЖАНИЕ: {content[:1000] + "..." if len(content) > 1000 else content}
ССЫЛКА: {article_url}
ТЕМА: {topic or "Technology"}
"""
            else:
                prompt = f"""
                Создай вирусный пост для Telegram на русском языке на основе этой статьи.
                
                Заголовок: {title}
                Содержание: {content[:1000]}...
                
                Пост должен быть:
                - Интересным и привлекающим внимание
                - Написан на русском языке
                - Содержать эмодзи и форматирование
                - Не длиннее 800 символов
                """
            
            # Определяем системный промпт
            if self.custom_system_prompt:
                system_content = self.custom_system_prompt
                logger.info("Using custom SYSTEM_PROMPT from .env file")
            else:
                system_content = """
                Ты - эксперт по созданию вирусных постов для социальных сетей.
                Твоя задача - создавать увлекательные, информативные и вирусные посты на русском языке.
                Используй эмодзи и форматирование для привлечения внимания.
                Создавай посты не длиннее 800 символов, чтобы они поместились в подпись к изображению в Telegram.
                """
            
            # Генерируем пост
            response = self.openai_client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": system_content + " Создавай посты не длиннее 800 символов, чтобы они поместились в подпись к изображению в Telegram."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=1  # Увеличиваем температуру для более креативных постов
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Добавляем ссылку на статью
            if article_url:
                post_content = self.add_link_to_post(post_content, article_url)
                logger.info(f"Added link to post: {article_url}")
            
            # Добавляем хештеги только для ZDNet (топики Robotics, Latest, Technology)
            if topic and topic in ['Robotics', 'Latest', 'Technology']:
                hashtags = self.get_hashtags_for_topic(topic)
                if hashtags:
                    post_content += f"\n\n{hashtags}"
                    logger.info(f"Added hashtags for topic '{topic}': {hashtags}")
            
            logger.info(f"Created viral post for article: {title[:50]}... ({len(post_content)} chars)")
            return post_content
            
        except Exception as e:
            logger.error(f"Error creating viral post: {e}")
            return None
    
    def add_link_to_post(self, post_content, article_url):
        """Добавление ссылки на статью в пост"""
        if not article_url:
            return post_content
        
        # Проверяем, есть ли уже ссылка в посте
        if article_url in post_content:
            return post_content
        
        # Добавляем ссылку в конец поста
        link_text = f'\n\n🔗 <a href="{article_url}">Read more</a>'
        return post_content + link_text
    
    def get_hashtags_for_topic(self, topic):
        """Получение хештегов для темы"""
        hashtags_map = {
            'AI': '#ИИ #искусственныйинтеллект #технологии #AI',
            'Robotics': '#роботы #робототехника #автоматизация #Robotics',
            'Latest': '#новости #технологии #последние #Latest',
            'Technology': '#технологии #инновации #гаджеты #Technology',
            'Science': '#наука #исследования #открытия #Science'
        }
        
        return hashtags_map.get(topic, '#новости #технологии')
    
    def translate_to_russian(self, text):
        """Перевод текста на русский язык"""
        try:
            if len(text) > 1000:
                # Если текст слишком длинный, рефакторим его
                logger.info("Text too long, refactoring...")
                text = text[:800] + "..."
            
            prompt = f"Переведи этот текст на русский язык, сохранив смысл и стиль:\n\n{text}"
            
            response = self.openai_client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "Ты - профессиональный переводчик с английского на русский. Переводи точно, сохраняя стиль и смысл."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            logger.info(f"Translated text to Russian: {len(translated_text)} characters")
            return translated_text
            
        except Exception as e:
            logger.error(f"Error translating to Russian: {e}")
            return text
    
    def download_media(self, media_url):
        """
        Скачивание медиа файла
        
        Args:
            media_url (str): URL медиа файла
            
        Returns:
            str: Путь к скачанному файлу или None в случае ошибки
        """
        try:
            if not media_url:
                return None
            
            # Создаем временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.webp')
            temp_path = temp_file.name
            temp_file.close()
            
            # Скачиваем файл
            response = requests.get(media_url, timeout=30)
            response.raise_for_status()
            
            # Сохраняем файл
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded media: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None
    
    async def publish_to_telegram(self, post_content, media_path=None):
        """
        Публикация поста в Telegram
        
        Args:
            post_content (str): Текст поста
            media_path (str): Путь к медиа файлу (опционально)
            
        Returns:
            bool: True если публикация успешна, False в противном случае
        """
        try:
            # Конвертируем в HTML
            html_content = self.convert_markdown_to_html(post_content)
            
            # Ограничиваем длину подписи для Telegram (максимум 1024 символа)
            if len(html_content) > 1024:
                # Обрезаем до 1000 символов и добавляем многоточие
                html_content = html_content[:1000] + "..."
                logger.info("Truncated post content to fit Telegram limits")
            
            if media_path and os.path.exists(media_path):
                try:
                    # Отправляем с медиа
                    with open(media_path, 'rb') as media_file:
                        await self.telegram_bot.send_photo(
                            chat_id=self.telegram_channel,
                            photo=media_file,
                            caption=html_content,
                            parse_mode='HTML'
                        )
                    logger.info("Published post with media to Telegram")
                    return True
                except Exception as media_error:
                    logger.warning(f"Failed to send with media: {media_error}, trying text only")
                    # Если не удалось отправить с медиа, пробуем только текст
                    await self.telegram_bot.send_message(
                        chat_id=self.telegram_channel,
                        text=html_content,
                        parse_mode='HTML',
                        disable_web_page_preview=False
                    )
                    logger.info("Published text post to Telegram (fallback)")
                    return True
            else:
                # Отправляем только текст
                await self.telegram_bot.send_message(
                    chat_id=self.telegram_channel,
                    text=html_content,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                )
                logger.info("Published text post to Telegram")
                return True
            
        except Exception as e:
            logger.error(f"Error publishing to Telegram: {e}")
            return False
    
    def convert_markdown_to_html(self, text):
        """Конвертация простого Markdown в HTML для Telegram"""
        if not text:
            return ""
        
        # Заменяем **текст** на <b>текст</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Заменяем *текст* на <i>текст</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Заменяем переносы строк на \n (Telegram поддерживает \n)
        text = text.replace('\n', '\n')
        
        return text
    
    def cleanup_media(self, media_path):
        """Очистка временных медиа файлов"""
        if media_path and os.path.exists(media_path):
            try:
                os.unlink(media_path)
                logger.info(f"Cleaned up temporary file: {media_path}")
                return True
            except Exception as e:
                logger.warning(f"Could not delete temporary file: {e}")
                return False
        return True
