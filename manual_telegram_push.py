import os
import sys
import requests
import asyncio

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.fetchers.fundamentals import FundamentalFetcher
from src.fetchers.technicals import TechnicalFetcher
from src.fetchers.news import NewsFetcher
from src.analysis.engine import AnalysisEngine
from src.renderer.generator import InfographicGenerator
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

def send_manual_report(symbol):
    print(f"Generating report for {symbol}...")
    
    # 1. Fetch
    ff = FundamentalFetcher()
    fund_data = ff.get_data(symbol)
    
    tf = TechnicalFetcher()
    tech_data = tf.get_data(symbol)
    
    nf = NewsFetcher()
    news_data = nf.fetch_latest_news(symbol)
    
    if not fund_data and not tech_data:
        print(f"Could not fetch data for {symbol}")
        return

    # 2. Analyze
    engine = AnalysisEngine()
    result = engine.evaluate_stock(fund_data, tech_data, news_data)
    result['cmp'] = fund_data.get('Current Price') if fund_data else tech_data.get('Close', 0)
    
    # 3. Generate Image
    output_path = f"{symbol}_manual_report.png"
    gen = InfographicGenerator()
    gen.generate_report(symbol, result, output_path)
    
    # 4. Send Image
    print(f"Sending to Channel ID: {TELEGRAM_CHANNEL_ID}")
    
    caption = (
        f"📊 *{symbol} Manual Analysis*\n"
        f"Score: {result['total_score']:.1f}/37\n"
        f"Risk: {result.get('health_label', 'N/A')}\n"
        f"Swing: {result.get('swing_verdict', 'N/A')}\n"
        f"Long Term: {result.get('long_term_verdict', 'N/A')}"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(output_path, 'rb') as f:
        resp = requests.post(url, data={'chat_id': TELEGRAM_CHANNEL_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': f})
    
    print(f"Response: {resp.status_code} - {resp.text}")
    
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)

if __name__ == "__main__":
    send_manual_report("ANANTRAJ")
