import logging
logging.basicConfig(level=logging.INFO)

from src.fetchers.fundamentals import FundamentalFetcher
from src.fetchers.technicals import TechnicalFetcher

def test_ticker(symbol):
    print(f"\n--- Testing {symbol} ---")
    ff = FundamentalFetcher()
    f_data = ff.get_data(symbol)
    print(f"Fundamentals: {'SUCCESS' if f_data else 'FAILED'}")
    if f_data:
        print(f"  CMP: {f_data.get('Current Price')}")
        print(f"  Mkt Cap: {f_data.get('Market Cap')}")

    tf = TechnicalFetcher()
    t_data = tf.get_data(symbol)
    print(f"Technicals: {'SUCCESS' if t_data else 'FAILED'}")
    if t_data:
        print(f"  Close: {t_data.get('Close')}")

if __name__ == "__main__":
    tickers = ["ANANTRAJ", "M&M", "TATAMOTORS.NS", "CDSL"]
    for t in tickers:
        test_ticker(t)
