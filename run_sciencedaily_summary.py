#!/usr/bin/env python3
"""
Script to run ScienceDaily Summary Scraper
"""

import asyncio
from sciencedaily_summary_scraper import ScienceDailySummaryScraper

async def main():
    """Main function"""
    try:
        scraper = ScienceDailySummaryScraper()
        result = await scraper.run_daily_summary()
        
        if result:
            print(f"✅ Summary published successfully!")
            print(f"📊 Articles included: {result['articles_count']}")
            print(f"📝 Post length: {len(result['post_content'])} characters")
        else:
            print("ℹ️ No summary published")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
