#!/usr/bin/env python3
"""
Article Selector Module
Собирает статьи со всех источников и использует LLM для выбора наиболее интересной технической статьи
"""

import os
import logging
import asyncio
from typing import List, Dict, Optional
from dotenv import load_dotenv
import requests
from published_urls_manager import get_urls_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('article_selector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ArticleSelector:
    """Класс для сбора и выбора наиболее интересных статей через LLM"""
    
    def __init__(self):
        load_dotenv()
        
        # OpenRouter/AI Configuration
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.openrouter_base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.ai_model = os.getenv('AI_MODEL', 'google/gemini-pro')
        
        # Менеджер для проверки опубликованных URL
        self.urls_manager = get_urls_manager()
        
        # Промпт для выбора статьи
        self.selection_prompt = os.getenv(
            'ARTICLE_SELECTION_PROMPT',
            """Ты - эксперт по техническим новостям в области ИИ, робототехники и технологий.
            
Твоя задача: из предоставленного списка статей выбрать ОДНУ наиболее интересную и значимую для технической аудитории.

Критерии выбора (по приоритету):
1. Практическое применение для обычного программиста(например вышла новая LLM модель)
2. Техническая глубина и инновационность
3. Актуальность и новизна информации
4. Потенциальный интерес для технической аудитории

Формат ответа: верни ТОЛЬКО номер статьи (число от 1 до N), без дополнительного текста."""
        )
        
        logger.info("Article Selector initialized successfully")
    
    async def collect_all_articles(self, scrapers_list: List) -> List[Dict]:
        """
        Собирает заголовки статей со всех скраперов
        
        Args:
            scrapers_list: Список инициализированных скраперов
            
        Returns:
            Список словарей с информацией о статьях (только неопубликованные)
        """
        all_articles = []
        total_filtered = 0
        
        for scraper in scrapers_list:
            try:
                scraper_name = scraper.__class__.__name__
                logger.info(f"📰 Collecting articles from {scraper_name}...")
                
                # Каждый скрапер должен иметь метод get_article_headlines()
                if hasattr(scraper, 'get_article_headlines'):
                    articles = await scraper.get_article_headlines()
                    
                    if articles:
                        # Получаем source_name для проверки в published_urls_manager
                        source_name = getattr(scraper, 'source_name', scraper_name.lower())
                        
                        # Дополнительная проверка: исключаем уже опубликованные статьи
                        unpublished_articles = []
                        for article in articles:
                            article_url = article.get('url', '')
                            
                            # Проверяем через urls_manager
                            if not self.urls_manager.is_url_published(source_name, article_url):
                                article['source'] = scraper_name
                                article['scraper'] = scraper
                                unpublished_articles.append(article)
                            else:
                                logger.debug(f"🚫 Filtered out already published: {article.get('title', 'Unknown')[:50]}...")
                                total_filtered += 1
                        
                        all_articles.extend(unpublished_articles)
                        logger.info(f"✅ Found {len(unpublished_articles)} unpublished articles from {scraper_name}")
                        
                        if len(articles) > len(unpublished_articles):
                            filtered_count = len(articles) - len(unpublished_articles)
                            logger.info(f"🚫 Filtered out {filtered_count} already published articles from {scraper_name}")
                    else:
                        logger.info(f"ℹ️ No articles found from {scraper_name}")
                else:
                    logger.warning(f"⚠️ {scraper_name} doesn't have get_article_headlines() method")
                    
            except Exception as e:
                logger.error(f"❌ Error collecting from {scraper.__class__.__name__}: {e}")
                continue
        
        logger.info(f"📊 Total unpublished articles collected: {len(all_articles)}")
        if total_filtered > 0:
            logger.info(f"🚫 Total published articles filtered out: {total_filtered}")
        
        return all_articles
    
    def format_articles_for_llm(self, articles: List[Dict]) -> str:
        """
        Форматирует список статей для отправки в LLM
        
        Args:
            articles: Список статей
            
        Returns:
            Форматированная строка со списком статей
        """
        formatted = "Список статей для анализа:\n\n"
        
        for idx, article in enumerate(articles, 1):
            formatted += f"{idx}. [{article['source']}] {article['title']}\n"
            formatted += f"   URL: {article['url']}\n"
            if article.get('description'):
                # Ограничиваем описание до 200 символов
                desc = article['description'][:200] + "..." if len(article['description']) > 200 else article['description']
                formatted += f"   Описание: {desc}\n"
            formatted += f"   Дата: {article['date']}\n\n"
        
        return formatted
    
    async def select_best_article_with_llm(self, articles: List[Dict]) -> Optional[Dict]:
        """
        Использует LLM для выбора наиболее интересной статьи
        
        Args:
            articles: Список статей для выбора
            
        Returns:
            Выбранная статья или None
        """
        if not articles:
            logger.warning("No articles to select from")
            return None
        
        if len(articles) == 1:
            logger.info("Only one article available, selecting it by default")
            return articles[0]
        
        try:
            logger.info(f"🤖 Sending {len(articles)} articles to LLM for selection...")
            
            # Форматируем статьи для LLM
            articles_text = self.format_articles_for_llm(articles)
            
            # Формируем промпт
            full_prompt = f"{self.selection_prompt}\n\n{articles_text}"
            
            # Отправляем запрос к LLM
            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/your-repo',
                'X-Title': 'News Scraper Article Selector'
            }
            
            payload = {
                'model': self.ai_model,
                'messages': [
                    {
                        'role': 'user',
                        'content': full_prompt
                    }
                ],
                'max_tokens': 50,
                'temperature': 0.3  # Низкая температура для более детерминированного выбора
            }
            
            response = requests.post(
                f"{self.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            selected_number = result['choices'][0]['message']['content'].strip()
            
            # Извлекаем номер из ответа
            import re
            match = re.search(r'\d+', selected_number)
            if match:
                selected_idx = int(match.group()) - 1  # Конвертируем в 0-based индекс
                
                if 0 <= selected_idx < len(articles):
                    selected_article = articles[selected_idx]
                    logger.info(f"✅ LLM selected article #{selected_idx + 1}: {selected_article['title']}")
                    logger.info(f"   Source: {selected_article['source']}")
                    logger.info(f"   URL: {selected_article['url']}")
                    return selected_article
                else:
                    logger.error(f"LLM returned invalid index: {selected_idx + 1}")
                    # Fallback: выбираем первую статью
                    logger.info("Falling back to first article")
                    return articles[0]
            else:
                logger.error(f"Could not parse LLM response: {selected_number}")
                # Fallback: выбираем первую статью
                logger.info("Falling back to first article")
                return articles[0]
                
        except Exception as e:
            logger.error(f"❌ Error selecting article with LLM: {e}")
            # Fallback: выбираем первую статью
            logger.info("Falling back to first article due to error")
            return articles[0] if articles else None
    
    async def get_best_article(self, scrapers_list: List) -> Optional[Dict]:
        """
        Основной метод: собирает статьи и выбирает лучшую через LLM
        
        Args:
            scrapers_list: Список инициализированных скраперов
            
        Returns:
            Выбранная статья с дополнительной информацией о скрапере
        """
        logger.info("🚀 Starting article collection and selection process...")
        
        # Собираем все статьи
        all_articles = await self.collect_all_articles(scrapers_list)
        
        if not all_articles:
            logger.warning("No articles collected from any source")
            return None
        
        # Выбираем лучшую статью через LLM
        best_article = await self.select_best_article_with_llm(all_articles)
        
        return best_article


async def main():
    """Тестовая функция"""
    selector = ArticleSelector()
    # Здесь нужно передать список инициализированных скраперов
    # result = await selector.get_best_article(scrapers_list)
    logger.info("Article Selector module loaded successfully")


if __name__ == "__main__":
    asyncio.run(main())

