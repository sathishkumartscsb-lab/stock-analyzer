from flask import Flask, render_template, request
import logging
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.fetchers.fundamentals import FundamentalFetcher
from src.fetchers.technicals import TechnicalFetcher
from src.fetchers.news import NewsFetcher
from src.analysis.engine import AnalysisEngine

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    symbol = request.form.get('stock_name', '').upper().strip()
    if not symbol:
        return render_template('index.html', error="Please enter a stock name")
    
    logger.info(f"Analyzing {symbol} via Web App...")
    
    # 1. Fetch
    ff = FundamentalFetcher()
    fund_data = ff.get_data(symbol)
    
    tf = TechnicalFetcher()
    tech_data = tf.get_data(symbol)
    
    nf = NewsFetcher()
    news_data = nf.fetch_latest_news(symbol)
    
    if not fund_data and not tech_data:
        return render_template('index.html', error=f"Could not fetch data for {symbol}. Try another.")
    
    # 2. Analyze
    engine = AnalysisEngine()
    result = engine.evaluate_stock(fund_data, tech_data, news_data)
    result['cmp'] = fund_data.get('Current Price') if fund_data else tech_data.get('Close', 0)
    result['symbol'] = symbol
    
    # Map for Template
    # We need to construct the 'sections' and 'summary' objects the template expects
    # For now, pass 'result' and 'details' and handle logic in Jinja or pre-process here.
    
    return render_template('report.html', data=result, details=result.get('details', {}))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
