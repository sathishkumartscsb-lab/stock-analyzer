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
        
        # Always include NSE India and Google RSS as robust free fallbacks
        self.sources.append(self.fetch_nse_news)
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

    def fetch_nse_news(self, symbol):
        """
        Fetch corporate announcements and news from NSE India
        """
        try:
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            items = []
            
            # Extract corporate actions and info
            info = data.get('info', {})
            metadata = data.get('metadata', {})
            
            # Create news items from corporate actions
            if info.get('purpose'):
                items.append({
                    'source': 'NSE India',
                    'title': f"{symbol}: {info.get('purpose', 'Corporate Action')}",
                    'link': f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}",
                    'pubDate': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
                })
            
            # Add listing date info if recent
            if metadata.get('listingDate'):
                items.append({
                    'source': 'NSE India',
                    'title': f"{symbol}: Listed on NSE - {metadata.get('listingDate')}",
                    'link': f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}",
                    'pubDate': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
                })
            
            return items[:2]  # Return max 2 items from NSE
        except Exception as e:
            logger.error(f"NSE news fetch error for {symbol}: {e}")
            return []
    
    def fetch_google_rss(self, symbol):
        url = f"https://news.google.com/rss/search?q={symbol}+stock+NSE+India&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            response = requests.get(url, timeout=10)
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
        except: return []

    def fetch_marketaux(self, symbol):
        # Free Tier: 3 requests/day limit usually, handle with care or check quota
        url = f"https://api.marketaux.com/v1/news/all?symbols={symbol}.NS&filter_entities=true&language=en&api_token={MARKETAUX_API_TOKEN}"
        try:
            resp = requests.get(url, timeout=10)
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
        except: return []

    def fetch_newsapi(self, symbol):
        url = f"https://newsapi.org/v2/everything?q={symbol}+India+Stock&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
        try:
            resp = requests.get(url, timeout=10)
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
        except: return []
    
    def fetch_corporate_actions(self, symbol):
        """
        Fetch corporate actions from NSE (dividends, splits, buybacks)
        """
        try:
            url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            items = []
            for action in data[:3]:  # Latest 3 actions
                purpose = action.get('subject', action.get('purpose', ''))
                ex_date = action.get('exDate', '')
                items.append({
                    'category': 'Corporate Action',
                    'source': 'NSE India',
                    'title': f"{symbol}: {purpose}",
                    'detail': f"Ex-Date: {ex_date}" if ex_date else '',
                    'link': f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}",
                    'pubDate': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
                })
            return items
        except Exception as e:
            logger.error(f"Corporate actions fetch error: {e}")
            return []
    
    def categorize_news(self, news_items):
        """
        Categorize news into specific types based on keywords
        """
        categories = {
            'Management': ['CEO', 'CFO', 'Board', 'Director', 'resignation', 'appointed', 'management'],
            'Orders/Contracts': ['order', 'contract', 'deal', 'partnership', 'agreement', 'wins', 'bags'],
            'Analyst': ['buy', 'sell', 'rating', 'target price', 'recommendation', 'upgrade', 'downgrade'],
            'Results': ['Q1', 'Q2', 'Q3', 'Q4', 'quarterly', 'results', 'earnings', 'profit', 'revenue']
        }
        
        categorized = []
        for item in news_items:
            title_lower = item['title'].lower()
            item['category'] = 'General'
            
            for category, keywords in categories.items():
                if any(keyword.lower() in title_lower for keyword in keywords):
                    item['category'] = category
                    break
            
            categorized.append(item)
        
        return categorized
    
    def fetch_comprehensive_news(self, symbol):
        """
        Fetch and categorize all news types
        """
        all_news = []
        
        # 1. Corporate Actions (highest priority)
        corporate_actions = self.fetch_corporate_actions(symbol)
        all_news.extend(corporate_actions)
        
        # 2. Regular news sources (categorized)
        regular_news = self.fetch_latest_news(symbol)
        categorized_news = self.categorize_news(regular_news)
        all_news.extend(categorized_news)
        
        # Sort by priority: Corporate Action > Analyst > Orders > Management > Results > General
        priority_order = {
            'Corporate Action': 1,
            'Analyst': 2,
            'Orders/Contracts': 3,
            'Management': 4,
            'Results': 5,
            'General': 6
        }
        
        all_news.sort(key=lambda x: priority_order.get(x.get('category', 'General'), 6))
        
        return all_news[:8]  # Return top 8 categorized news items
    
    def _analyze_sentiment(self, text):
        text = text.lower()
        if any(w in text for w in ['gain', 'jump', 'surge', 'rise', 'profit', 'high', 'buy', 'upgrade']):
            return 'Positive'
        elif any(w in text for w in ['loss', 'fall', 'drop', 'decline', 'crash', 'sell', 'downgrade', 'weak']):
            return 'Negative'
        return 'Neutral'
