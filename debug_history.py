import requests
from bs4 import BeautifulSoup

def debug_screener_rows(symbol):
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    def check_row(section_id, search_text):
        try:
            section = soup.find('section', id=section_id)
            if not section: return "Section Not Found"
            # Safer check
            row = section.find('td', string=lambda t: t and search_text.lower() in t.strip().lower())
            if row:
                cols = row.parent.find_all('td')
                # Return last 3 values
                vals = [c.text.strip() for c in cols[-3:]]
                return f"Found: {vals}"
            else:
                return "Row Not Found"
        except Exception as e:
            return f"Error: {e}"

    print(f"--- Data Check for {symbol} ---")
    print("Net Profit (P&L):", check_row('profit-loss', 'Net Profit'))
    print("Cash from Op Activity (CF):", check_row('cash-flow', 'Cash from Operating Activity'))
    print("Sales (P&L):", check_row('profit-loss', 'Sales'))
    print("Inventories (BS):", check_row('balance-sheet', 'Inventories'))
    # Current Liabilities Proxy?
    print("Trade Payables (BS):", check_row('balance-sheet', 'Trade Payables'))
    print("Other Liabilities (BS):", check_row('balance-sheet', 'Other Liabilities'))
    print("Borrowings (BS):", check_row('balance-sheet', 'Borrowings'))

debug_screener_rows("TCS")
