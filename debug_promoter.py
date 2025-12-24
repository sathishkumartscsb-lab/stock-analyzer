from src.fetchers.fundamentals import FundamentalFetcher
import logging

# Enable logging to see errors
logging.basicConfig(level=logging.ERROR)

ff = FundamentalFetcher()
print("Fetching TCS data...")
data = ff.fetch_screener_data("TCS")

if data:
    print(f"Promoter Holding: {data.get('Promoter Holding')}")
    print(f"All Keys: {list(data.keys())}")
else:
    print("No data fetched.")
