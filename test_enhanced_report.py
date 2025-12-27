from src.fetchers.fundamentals import FundamentalFetcher
from src.fetchers.technicals import TechnicalFetcher
from src.fetchers.news import NewsFetcher
from src.analysis.engine import AnalysisEngine
from src.renderer.generator import InfographicGenerator

symbol = 'RELIANCE'
f = FundamentalFetcher().get_data(symbol)
t = TechnicalFetcher().get_data(symbol)
n = NewsFetcher().fetch_latest_news(symbol)

print(f'Fetched {len(n)} news items')

engine = AnalysisEngine()
res = engine.evaluate_stock(f, t, n)
res['cmp'] = f.get('Current Price', 0)
res['news_items'] = n

gen = InfographicGenerator()
gen.generate_report(symbol, res, 'reliance_enhanced.png')
print('Enhanced report generated!')
