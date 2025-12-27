import requests
import json

# Check NSE API for news/announcements
symbol = 'RELIANCE'

# Try different NSE endpoints
endpoints = [
    f'https://www.nseindia.com/api/quote-equity?symbol={symbol}',
    f'https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={symbol}',
    f'https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol={symbol}'
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9'
}

for endpoint in endpoints:
    print(f"\n{'='*60}")
    print(f"Endpoint: {endpoint}")
    print('='*60)
    try:
        r = requests.get(endpoint, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"Error: {e}")
