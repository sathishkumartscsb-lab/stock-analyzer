from src.fetchers.fundamentals import FundamentalFetcher

def debug_anantraj():
    symbol = "ANANTRAJ"
    print(f"Fetching data for {symbol}...")
    
    ff = FundamentalFetcher()
    data = ff.get_data(symbol)
    
    if not data:
        print("Failed to fetch data.")
        return

    print("\n--- Key Metrics ---")
    print(f"Operating Cash Flow: {data.get('Operating Cash Flow')}")
    print(f"Net Profit: {data.get('Net Profit')}")
    print(f"CFO to PAT: {data.get('CFO to PAT')}")
    print(f"Debt / Equity: {data.get('Debt / Equity')}")
    print(f"Current Price: {data.get('Current Price')}")
    print(f"Market Cap: {data.get('Market Cap')}")

if __name__ == "__main__":
    debug_anantraj()
