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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.renderer.generator import InfographicGenerator
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
import requests
import json

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

@app.route('/share_telegram', methods=['POST'])
def share_telegram():
    data = request.json
    symbol = data.get('symbol', '').upper()
    
    if not symbol:
        return {"status": "error", "message": "No symbol provided"}
    
    # Re-run analysis to get fresh data for the image
    # (In a prod app, we might cache this)
    try:
        ff = FundamentalFetcher()
        fund_data = ff.get_data(symbol)
        tf = TechnicalFetcher()
        tech_data = tf.get_data(symbol)
        nf = NewsFetcher()
        news_data = nf.fetch_latest_news(symbol)
        
        engine = AnalysisEngine()
        result = engine.evaluate_stock(fund_data, tech_data, news_data)
        result['cmp'] = fund_data.get('Current Price') if fund_data else tech_data.get('Close', 0)
        
        # Generate Image
        gen = InfographicGenerator()
        filename = f"{symbol}_telegram.png"
        gen.generate_report(symbol, result, filename)
        
        # Send via Telegram API (Sync)
        caption = f"📊 *Stock Analysis: {symbol}*\nscore: {result['total_score']:.1f}/37\nVerdict: {result.get('health_label')}"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(filename, 'rb') as f:
            resp = requests.post(url, data={'chat_id': TELEGRAM_CHANNEL_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})
        
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)
            
        if resp.status_code == 200:
            return {"status": "success", "message": "Sent to Telegram!"}
        else:
            logger.error(f"Telegram Error: {resp.text}")
            return {"status": "error", "message": f"Telegram API Error: {resp.text}"}
            
    except Exception as e:
        logger.error(f"Share Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
