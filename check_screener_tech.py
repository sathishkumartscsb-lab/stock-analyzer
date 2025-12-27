import requests
from bs4 import BeautifulSoup
import re

# Check what technical data Screener.in provides
url = 'https://www.screener.in/company/KKJEWELS/'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(r.text, 'html.parser')

# Look for price and technical indicators
print("=== Checking Screener.in for Technical Data ===\n")

# Check for current price
price_elem = soup.find('span', class_='number')
if price_elem:
    print(f"Current Price: {price_elem.text}")

# Look for any DMA mentions
text = soup.get_text()
dma_matches = re.findall(r'(\d+)\s*DMA', text, re.IGNORECASE)
if dma_matches:
    print(f"DMA mentions found: {dma_matches}")

# Check for chart data or technical section
chart_section = soup.find('section', id='chart')
if chart_section:
    print("\nChart section found!")
    print(chart_section.get_text()[:300])

# Look for any technical indicators in the page
tech_keywords = ['RSI', 'MACD', 'Moving Average', 'Support', 'Resistance']
for keyword in tech_keywords:
    if keyword.lower() in text.lower():
        print(f"\n'{keyword}' found in page")
        # Find context around the keyword
        idx = text.lower().find(keyword.lower())
        if idx != -1:
            context = text[max(0, idx-50):min(len(text), idx+100)]
            print(f"Context: {context[:150]}")
