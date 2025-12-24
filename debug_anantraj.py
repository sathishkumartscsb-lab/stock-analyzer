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
    print(f"Book Value: {data.get('Book Value')}")
    # Simulate Logic
    eps = float(data.get('Current Price')) / float(data.get('Stock P/E'))
    bv = float(data.get('Book Value'))
    graham = (22.5 * eps * bv)**0.5
    print(f"Calculated EPS: {eps:.2f}")
    print(f"Manual Graham: {graham:.2f}")
    
    # Re-fetch to see if 'Intrinsic Value' key is populated in data dict (it isn't by default in ff.get_data return unless we look at mapped_data logic which is internal)
    # The debug script calls get_data which returns cleaned dictionary. let's check keys available.
    print(f"Keys available: {data.keys()}")

if __name__ == "__main__":
    debug_anantraj()
