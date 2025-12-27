import requests
from bs4 import BeautifulSoup
import json

symbol = 'RELIANCE'

print("=" * 80)
print("EXPLORING DATA SOURCES FOR COMPREHENSIVE NEWS")
print("=" * 80)

# 1. NSE Corporate Actions
print("\n1. NSE Corporate Actions API")
try:
    url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    }
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
        print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f"Error: {e}")

# 2. Screener.in Shareholding Pattern
print("\n2. Screener.in Shareholding Data")
try:
    url = f"https://www.screener.in/company/{symbol}/"
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Look for shareholding table
    shareholding_section = soup.find('section', id='shareholding')
    if shareholding_section:
        print("Found shareholding section!")
        tables = shareholding_section.find_all('table')
        print(f"Tables found: {len(tables)}")
        if tables:
            print(tables[0].get_text()[:300])
except Exception as e:
    print(f"Error: {e}")

# 3. NSE Bulk Deals (FII/DII activity indicator)
print("\n3. NSE Bulk/Block Deals")
try:
    url = "https://www.nseindia.com/api/snapshot-capital-market-largedeal"
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print("Bulk deals data available!")
except Exception as e:
    print(f"Error: {e}")

# 4. Screener.in Quarterly Results
print("\n4. Screener.in Quarterly Results")
try:
    url = f"https://www.screener.in/company/{symbol}/"
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    quarters_section = soup.find('section', id='quarters')
    if quarters_section:
        print("Found quarterly results section!")
except Exception as e:
    print(f"Error: {e}")
