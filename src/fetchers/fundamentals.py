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

    def fetch_screener_data(self, symbol):
        """
        Scrapes data from Screener.in including Quarters, P&L, Balance Sheet, Cash Flow, Shareholding.
        """
        url = SCREENER_URL.format(symbol)
        try:
            data = {}
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logger.error(f"Failed to fetch Screener data for {symbol}: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            def safe_float(val, default=0.0):
                try:
                    if not val or str(val).strip() == "": return default
                    # Remove any non-numeric except . and -
                    clean_val = "".join(c for c in str(val) if c.isdigit() or c in ".-")
                    return float(clean_val) if clean_val else default
                except:
                    return default

            # --- Helpers to parse tables ---
            def get_table_row(table_id, row_name, index=-1): # index -1 means latest (TTM or last quarter)
                try:
                    section = soup.find('section', id=table_id)
                    if not section: return 0
                    
                    rows = section.find_all('tr')
                    for row in rows:
                        # Check text of the row (or first cell)
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
                name_span = ratio.find('span', class_='name')
                num_span = ratio.find('span', class_='number')
                if name_span and num_span:
                    name = name_span.text.strip().lower()
                    value = num_span.text.strip().replace(',', '')
                    data[name] = value
            
            # --- 2. Extracting the 24 Fundamental Parameters ---
            
            # 1. Market Cap
            mcap = safe_float(data.get('market cap'))
            
            # 2. CMP vs 52W (Parse High/Low)
            hl = data.get('high / low', '0 / 0').split('/')
            high52 = safe_float(hl[0]) if len(hl)>0 else 0
            low52 = safe_float(hl[1]) if len(hl)>1 else 0
            cmp = safe_float(data.get('current price'))
            
            # 3. PE
            pe = safe_float(data.get('stock p/e'))
            
            # Industry PE
            industry_pe = safe_float(data.get('industry pe')) 
            
            # ROE
            roe_val = safe_float(data.get('return on equity'))
            if roe_val == 0:
                 roe_val = safe_float(data.get('roe'))
            
            # Book Value & Price to Book
            book_value = safe_float(data.get('book value'))
            price_to_book = safe_float(data.get('price to book value'))
            
            # Piotroski
            piotroski_val = safe_float(data.get('piotroski score'))
            
            # Industry PB (Approximation)
            industry_pb = safe_float(data.get('industry pb'))
            
            # 5. EPS Trend (Latest Quarter vs Previous)
            eps_last = get_table_row('quarters', 'EPS', -1)
            eps_prev = get_table_row('quarters', 'EPS', -2)
            
            # 6. EBITDA Trend (Operating Profit in Quarters)
            ebitda_last = get_table_row('quarters', 'Operating Profit', -1)
            
            # 7. Debt / Equity
            de = safe_float(data.get('debt / eq'))
            if de == 0: 
                borrowings = get_table_row('balance-sheet', 'Borrowings', -1)
                equity = get_table_row('balance-sheet', 'Share Capital', -1) + get_table_row('balance-sheet', 'Reserves', -1)
                de = borrowings / equity if equity else 0
                
            # 8. Dividend Yield
            dy = safe_float(data.get('dividend yield'))
            
            # 10. Current Ratio
            curr_ratio = 1.5 
            
            # 11. Promoter Holding
            prom_hold = get_table_row('shareholding', 'Promoters', -1)
            
            # 12. FII/DII Trend
            fii_last = get_table_row('shareholding', 'FIIs', -1)
            fii_prev = get_table_row('shareholding', 'FIIs', -2)
            dii_last = get_table_row('shareholding', 'DIIs', -1)
            
            # 13. OCF
            ocf = get_table_row('cash-flow', 'Cash from Operating Activity', -1)
            
            # 14. ROCE
            roce = safe_float(data.get('roce'))
            
            # 15/16. CAGR (Sales/Profit)
            # Screener has a specific "Compounded Sales Growth" table, hard to parse generically by ID.
            # approximating from P&L 3yr back
            sales_now = get_table_row('profit-loss', 'Sales', -1)
            sales_3y = get_table_row('profit-loss', 'Sales', -4)
            rev_cagr = ((sales_now/sales_3y)**(1/3) - 1)*100 if sales_3y else 0
            
            net_profit = get_table_row('profit-loss', 'Net Profit', -1)
            prof_3y = get_table_row('profit-loss', 'Net Profit', -4)
            prof_cagr = ((net_profit/prof_3y)**(1/3) - 1)*100 if prof_3y else 0
            
            # 17. Interest Coverage
            int_cov = safe_float(data.get('interest coverage')) # fixed key
            if int_cov == 0:
                 int_cov = safe_float(data.get('int coverage'))
            if int_cov == 0:
                 op_profit = get_table_row('profit-loss', 'Operating Profit', -1)
                 interest = get_table_row('profit-loss', 'Interest', -1)
                 int_cov = op_profit / interest if interest else 10
                 
            # 18. FCF = OCF - Capex (Fixed Assets Purchased)
            # Cash from Investing -> Fixed Assets Purchased usually negative
            capex = get_table_row('cash-flow', 'Fixed Assets', -1) 
            fcf = ocf + capex # Capex is negative in cash flow
            
            # 20. Pledged Shares -- Hard to scrape without deep dive, assume 0 for MVP or parsing 'Pledged' text in shareholding
            pledged = 0 
            
            # 21. Contingent Liabilities
            # Usually in "Annual Reports" or "Other Liabilities", harder to get generically.
            # We will try to fetch "Other Liabilities" as a proxy if explicit "Contingent" is missing, or default to 0.
            cont_liab = get_table_row('balance-sheet', 'Other Liabilities', -1)
            
            # Net Worth = Share Capital + Reserves
            share_cap = get_table_row('balance-sheet', 'Share Capital', -1)
            reserves = get_table_row('balance-sheet', 'Reserves', -1)
            net_worth = share_cap + reserves
            
            # 22. Piotroski - often in Ratios
            piotroski = 5 # Default
            
            # 24. CFO/PAT
            cfo_pat = ocf / net_profit if net_profit else 0

            # --- Intrinsic Value Calculation Details (Moved outside dict) ---
            # Graham Formula Modified = (EPS * (8.5 + 2g) * 4.4) / Y
            # g = Growth Rate (Capped at 20%), Y = AAA Bond Yield (~7.5%)
            
            # 1. Calculate EPS (TTM)
            eps_ttm = cmp / pe if (pe and pe > 0) else eps_last
            
            # 2. Determine Growth (g) - Use Profit CAGR, capped at 20%
            g_rate = min(prof_cagr, 20)
            if g_rate < 0: g_rate = 0
            
            # 3. Calculate IV
            # Graham Number (Deep Value)
            # Need Book Value - checking if we fetched it? 
            # Often data.get('book value') works if screener props are clean.
            bv_val = safe_float(data.get('book value'))
            graham_num = (22.5 * eps_ttm * bv_val)**0.5 if (eps_ttm > 0 and bv_val > 0) else 0
            
            # Graham Formula (Growth Value)
            graham_formula = (eps_ttm * (8.5 + 2 * g_rate) * 4.4) / 7.5
            
            # Final Value Selection
            final_iv = graham_formula if graham_formula > 0 else (graham_num if graham_num > 0 else eps_ttm * 15)

            mapped_data = {
                'Market Cap': mcap,
                'Current Price': cmp,
                'High_52': high52,
                'Low_52': low52,
                'Stock P/E': pe,
                'PEG Ratio': pe / prof_cagr if prof_cagr > 0 else 0, # Approx
                'EPS Trend': (eps_last - eps_prev)/eps_prev*100 if eps_prev else 0,
                'EBITDA Trend': ebitda_last,
                'Debt / Equity': de,
                'Dividend Yield': dy,
                'Intrinsic Value': final_iv,
                'Current Ratio': curr_ratio,
                'Promoter Holding': prom_hold,
                'FII/DII Change': (fii_last - fii_prev),
                'Operating Cash Flow': ocf,
                'ROCE': roce,
                'Operating Cash Flow': ocf,
                'ROCE': roce,
                'ROE': roe_val,
                'Industry PE': industry_pe,
                'Revenue CAGR': rev_cagr,
                'Profit CAGR': prof_cagr,
                'Interest Coverage': int_cov,
                'Free Cash Flow': fcf,
                'Equity Dilution': 0, # Placeholder
                'Pledged Shares': pledged,
                'Contingent Liabilities': 0, # Placeholder
                'Piotroski Score': piotroski,
                'Working Capital Cycle': 0, # Placeholder
                'CFO to PAT': cfo_pat,
                'Net Profit': net_profit, # Helper
                'Book Value': book_value,
                'Price to Book': price_to_book,
                'Industry PB': industry_pb,
                'Piotroski Score': piotroski_val if piotroski_val > 0 else 5,
                'Contingent Liabilities': cont_liab,
                'Net Worth': net_worth
            }
            
            return mapped_data

        except Exception as e:
            logger.error(f"Error scraping Screener for {symbol}: {e}")
            return None

    def get_data(self, symbol):
        # We can aggregate from multiple sources here
        screener_data = self.fetch_screener_data(symbol)
        
        # Determine Status/Score (This might belong in the Analysis Engine, 
        # but fetcher should likely return raw numbers).
        
        return screener_data
