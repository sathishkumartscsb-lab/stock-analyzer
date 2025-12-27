import requests
from bs4 import BeautifulSoup
import logging
from src.config import SCREENER_URL

logger = logging.getLogger(__name__)

class FundamentalFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def search_ticker(self, query):
        """
        Searches for a ticker symbol given a stock name using Screener API.
        """
        search_url = f"https://www.screener.in/api/company/search/?q={query}"
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                results = response.json()
                if results:
                    # Ticker extraction logic:
                    # Screener URLs look like /company/SYMBOL/ or /company/SYMBOL/consolidated/
                    tickers = []
                    for r in results[:5]:
                        parts = [p for p in r['url'].split('/') if p]
                        if len(parts) >= 2 and parts[0] == 'company':
                            tickers.append((r['name'], parts[1]))
                    return tickers
            return []
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            return []

    def fetch_screener_data(self, symbol):
        """
        Scrapes data from Screener.in. Falls back to standalone if consolidated is empty.
        """
        urls = [
            f"https://www.screener.in/company/{symbol}/consolidated/",
            f"https://www.screener.in/company/{symbol}/"
        ]
        
        for url in urls:
            try:
                logger.info(f"Attempting Scrape: {url}")
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                data = {}
                
                def safe_float(val, default=0.0):
                    try:
                        if not val or str(val).strip() == "": return default
                        clean_val = "".join(c for c in str(val) if c.isdigit() or c in ".-")
                        return float(clean_val) if clean_val else default
                    except: return default

                def get_table_row(table_id, row_name, index=-1):
                    try:
                        section = soup.find('section', id=table_id)
                        if not section: return 0
                        rows = section.find_all('tr')
                        for row in rows:
                            if row_name.lower() in row.text.lower():
                                cols = row.find_all('td')
                                if not cols: continue
                                val = cols[index].text.strip().replace(',', '').replace('%', '')
                                return safe_float(val)
                        return 0
                    except: return 0

                # --- 1. Parsing Top Ratios ---
                ratios = soup.find_all('li', class_='flex flex-space-between')
                for ratio in ratios:
                    name_ptr = ratio.find('span', class_='name')
                    val_ptr = ratio.find('span', class_='number') or ratio.find('span', class_='value') or ratio.find('span', class_='nowrap value')
                    if name_ptr and val_ptr:
                        name = name_ptr.text.strip().lower()
                        val_text = val_ptr.text.strip().replace(',', '')
                        data[name] = val_text

                # Check if this view is empty (Screener often shows a blank page with title only)
                mcap = safe_float(data.get('market cap'))
                if mcap == 0:
                    if url == urls[0]: 
                        logger.info(f"No consolidated data for {symbol}, trying standalone...")
                        continue
                    else:
                        logger.warning(f"No fundamental data found for {symbol} at all.")
                        return None # Both failed

                # --- 2. Extracting Parameters ---
                hl = data.get('high / low', '0 / 0').split('/')
                high52 = safe_float(hl[0]) if len(hl)>0 else 0
                low52 = safe_float(hl[1]) if len(hl)>1 else 0
                cmp = safe_float(data.get('current price'))
                pe = safe_float(data.get('stock p/e'))
                industry_pe = safe_float(data.get('industry pe')) 
                roe_val = safe_float(data.get('return on equity')) or safe_float(data.get('roe'))
                book_value = safe_float(data.get('book value'))
                price_to_book = safe_float(data.get('price to book value'))
                industry_pb = safe_float(data.get('industry pb'))
                piotroski_val = safe_float(data.get('piotroski score'))
                
                eps_last = get_table_row('quarters', 'EPS', -1)
                eps_prev = get_table_row('quarters', 'EPS', -2)
                ebitda_last = get_table_row('quarters', 'Operating Profit', -1)
                
                de = safe_float(data.get('debt / eq'))
                if de == 0: 
                    borr = get_table_row('balance-sheet', 'Borrowings', -1)
                    eq = get_table_row('balance-sheet', 'Share Capital', -1) + get_table_row('balance-sheet', 'Reserves', -1)
                    de = borr / eq if eq else 0
                    
                dy = safe_float(data.get('dividend yield'))
                prom_hold = get_table_row('shareholding', 'Promoters', -1)
                fii_last = get_table_row('shareholding', 'FIIs', -1)
                fii_prev = get_table_row('shareholding', 'FIIs', -2)
                ocf = get_table_row('cash-flow', 'Cash from Operating Activity', -1)
                roce = safe_float(data.get('roce'))
                
                sales_now = get_table_row('profit-loss', 'Sales', -1)
                sales_3y = get_table_row('profit-loss', 'Sales', -4)
                rev_cagr = ((sales_now/sales_3y)**(1/3) - 1)*100 if (sales_3y and sales_now) else 0
                
                net_profit = get_table_row('profit-loss', 'Net Profit', -1)
                prof_3y = get_table_row('profit-loss', 'Net Profit', -4)
                prof_cagr = ((net_profit/prof_3y)**(1/3) - 1)*100 if (prof_3y and net_profit) else 0
                
                int_cov = safe_float(data.get('interest coverage')) or safe_float(data.get('int coverage'))
                if int_cov == 0:
                     op_p = get_table_row('profit-loss', 'Operating Profit', -1)
                     intr = get_table_row('profit-loss', 'Interest', -1)
                     int_cov = op_p / intr if intr else 10
                     
                capex = get_table_row('cash-flow', 'Fixed Assets', -1) 
                fcf = ocf + capex 
                cont_liab = get_table_row('balance-sheet', 'Other Liabilities', -1)
                cfo_pat = ocf / net_profit if net_profit else 0

                # Intrinsic Value
                eps_ttm = cmp / pe if (pe and pe > 0) else eps_last
                g_rate = min(max(prof_cagr, 0), 20)
                graham_num = (22.5 * eps_ttm * book_value)**0.5 if (eps_ttm > 0 and book_value > 0) else 0
                graham_formula = (eps_ttm * (8.5 + 2 * g_rate) * 4.4) / 7.5
                final_iv = graham_formula if graham_formula > 0 else (graham_num if graham_num > 0 else eps_ttm * 15)

                mapped_data = {
                    'Market Cap': mcap,
                    'Current Price': cmp,
                    'High_52': high52,
                    'Low_52': low52,
                    'Stock P/E': pe,
                    'PEG Ratio': pe / prof_cagr if prof_cagr > 0 else 0,
                    'EPS Trend': (eps_last - eps_prev)/eps_prev*100 if eps_prev else 0,
                    'EBITDA Trend': ebitda_last,
                    'Debt / Equity': de,
                    'Dividend Yield': dy,
                    'Intrinsic Value': final_iv,
                    'Current Ratio': 1.5,
                    'Promoter Holding': prom_hold,
                    'FII/DII Change': (fii_last - fii_prev),
                    'ROCE': roce,
                    'ROE': roe_val,
                    'Industry PE': industry_pe,
                    'Revenue CAGR': rev_cagr,
                    'Profit CAGR': prof_cagr,
                    'Interest Coverage': int_cov,
                    'Free Cash Flow': fcf,
                    'Piotroski Score': piotroski_val if piotroski_val > 0 else 5,
                    'CFO to PAT': cfo_pat,
                    'Net Profit': net_profit,
                    'Book Value': book_value,
                    'Price to Book': price_to_book,
                    'Industry PB': industry_pb,
                    'Contingent Liabilities': cont_liab,
                    'Net Worth': (get_table_row('balance-sheet', 'Share Capital', -1) + get_table_row('balance-sheet', 'Reserves', -1))
                }
                return mapped_data

            except Exception as e:
                logger.error(f"Error scraping Screener at {url}: {e}")
                continue
                
        return None

    def get_data(self, symbol):
        return self.fetch_screener_data(symbol)
