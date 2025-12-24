from src.fetchers.fundamentals import FundamentalFetcher
ff = FundamentalFetcher()
# Fetch Data for TCS
print("Fetching raw data for TCS from Screener...")
# We access the internal method to see raw keys
ff_internal = ff.fetch_screener_data("TCS")

if ff_internal:
    print("Fetched Keys:", list(ff_internal.keys()))
    print("ROE Raw Value:", ff_internal.get('ROE', 'Not Found'))
    # Print all keys to find the right one
    for k, v in ff_internal.items():
        if 'return' in k.lower() or 'equity' in k.lower():
            print(f"Possible ROE Key: '{k}' -> {v}")
else:
    print("Failed to fetch.")
