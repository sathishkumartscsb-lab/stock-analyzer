import argparse
import logging
from src.fetchers.fundamentals import FundamentalFetcher
from src.fetchers.technicals import TechnicalFetcher
from src.fetchers.news import NewsFetcher
from src.analysis.engine import AnalysisEngine
from src.renderer.generator import InfographicGenerator
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Stock Infographic Generator")
    parser.add_argument("--stock", type=str, required=True, help="Stock Symbol (e.g., RELIANCE)")
    parser.add_argument("--output", type=str, default="output.png", help="Output image path")
    args = parser.parse_args()
    
    symbol = args.stock.upper()
    logger.info(f"Starting analysis for {symbol}...")
    
    # 1. Fetch Data
    logger.info("Fetching Fundamentals...")
    ff = FundamentalFetcher()
    fund_data = ff.get_data(symbol)
    
    logger.info("Fetching Technicals...")
    tf = TechnicalFetcher()
    tech_data = tf.get_data(symbol)
    
    logger.info("Fetching News...")
    nf = NewsFetcher()
    news_data = nf.fetch_latest_news(symbol)
    
    if not fund_data and not tech_data:
        logger.error("Failed to fetch sufficient data.")
        return
    
    # 2. Analyze
    logger.info("Running Analysis Engine...")
    engine = AnalysisEngine()
    analysis_result = engine.evaluate_stock(fund_data, tech_data, news_data)
    
    # Add CMP to result for display
    analysis_result['cmp'] = fund_data.get('Current Price') if fund_data else tech_data.get('Close', 0)
    
    logger.info(f"Score: {analysis_result['total_score']}/37 - Risk: {analysis_result.get('health_label', 'N/A')}")
    
    # 3. Generate Image
    logger.info("Generating Infographic...")
    gen = InfographicGenerator()
    gen.generate_report(symbol, analysis_result, args.output)
    
    logger.info(f"Report saved to {args.output}")

if __name__ == "__main__":
    main()
