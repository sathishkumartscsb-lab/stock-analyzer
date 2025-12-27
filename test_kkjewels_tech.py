from src.fetchers.fundamentals import FundamentalFetcher
from src.fetchers.technicals import TechnicalFetcher
from src.analysis.engine import AnalysisEngine

symbol = 'KKJEWELS'
f = FundamentalFetcher().get_data(symbol)
t = TechnicalFetcher().get_data(symbol)

print(f'=== Technical Data ===')
print(f'indicators_available: {t.get("indicators_available")}')
print(f'data_source: {t.get("data_source")}')
print(f'data_note: {t.get("data_note")}')
print(f'Close/Price: {t.get("Close")}')
print(f'50DMA: {t.get("50DMA")}')
print(f'RSI: {t.get("RSI")}')

engine = AnalysisEngine()
res = engine.evaluate_stock(f, t, [])

print(f'\n=== Analysis Results ===')
print(f'Trend (DMA): {res["details"]["Trend (DMA)"]}')
print(f'RSI: {res["details"]["RSI"]}')
print(f'Technical Summary: {res["technical_summary"]}')
