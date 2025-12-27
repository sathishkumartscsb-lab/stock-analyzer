from src.fetchers.fundamentals import FundamentalFetcher
from src.fetchers.technicals import TechnicalFetcher
from src.analysis.engine import AnalysisEngine
from src.renderer.generator import InfographicGenerator

symbol = 'KKJEWELS'
f = FundamentalFetcher().get_data(symbol)
t = TechnicalFetcher().get_data(symbol)

print(f'Price from NSE: {t.get("Close")}')
print(f'Data Source: {t.get("data_source")}')
print(f'Data Note: {t.get("data_note")}')

engine = AnalysisEngine()
res = engine.evaluate_stock(f, t, [])
res['cmp'] = t.get('Close', 0)

gen = InfographicGenerator()
gen.generate_report(symbol, res, 'kkjewels_final.png')
print('Report generated with NSE price!')
