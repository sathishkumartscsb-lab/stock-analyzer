import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime
from src.config import MARKETAUX_API_TOKEN, NEWSAPI_KEY

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        self.sources = []
        if MARKETAUX_API_TOKEN:
            self.sources.append(self.fetch_marketaux)
        if NEWSAPI_KEY:
            self.sources.append(self.fetch_newsapi)
        
        # Always include Google RSS as a robust free fallback
        self.sources.append(self.fetch_google_rss)

    def fetch_latest_news(self, symbol):
        """
        Aggregates news from available sources.
        """
        all_news = []
        seen_titles = set()
        
        for fetch_method in self.sources:
            try:
                items = fetch_method(symbol)
                for item in items:
                    # Deduplicate by title
                    if item['title'] not in seen_titles:
                        all_news.append(item)
                        seen_titles.add(item['title'])
            except Exception as e:
                logger.error(f"Error in news source {fetch_method.__name__}: {e}")
                
        # Mock Sentiment Analysis (Simple Keyword Match)
        for item in all_news:
            item['sentiment'] = self._analyze_sentiment(item['title'])
            
        return all_news[:10] # Return top 10

    def fetch_google_rss(self, symbol):
        url = f"https://news.google.com/rss/search?q={symbol}+stock+NSE+India&hl=en-IN&gl=IN&ceid=IN:en"
        response = requests.get(url)
        if response.status_code != 200: return []
        
        root = ET.fromstring(response.content)
        items = []
        for item in root.findall('./channel/item')[:5]:
            items.append({
                'source': 'Google News',
                'title': item.find('title').text,
                'link': item.find('link').text,
                'pubDate': item.find('pubDate').text
            })
        return items

    def fetch_marketaux(self, symbol):
        # Free Tier: 3 requests/day limit usually, handle with care or check quota
        url = f"https://api.marketaux.com/v1/news/all?symbols={symbol}.NS&filter_entities=true&language=en&api_token={MARKETAUX_API_TOKEN}"
        resp = requests.get(url)
        if resp.status_code != 200: return []
        
        data = resp.json()
        items = []
        for article in data.get('data', [])[:3]:
            items.append({
                'source': 'MarketAux',
                'title': article.get('title'),
                'link': article.get('url'),
                'pubDate': article.get('published_at')
            })
        return items

    def fetch_newsapi(self, symbol):
        url = f"https://newsapi.org/v2/everything?q={symbol}+India+Stock&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
        resp = requests.get(url)
        if resp.status_code != 200: return []
        
        data = resp.json()
        items = []
        for article in data.get('articles', [])[:3]:
            items.append({
                'source': 'NewsAPI',
                'title': article.get('title'),
                'link': article.get('url'),
                'pubDate': article.get('publishedAt')
            })
        return items

    def _analyze_sentiment(self, text):
        text = text.lower()
        if any(w in text for w in ['gain', 'jump', 'surge', 'rise', 'profit', 'high', 'buy', 'upgrade']):
            return 'Positive'
        elif any(w in text for w in ['loss', 'fall', 'drop', 'decline', 'crash', 'sell', 'downgrade', 'weak']):
            return 'Negative'
        return 'Neutral'
