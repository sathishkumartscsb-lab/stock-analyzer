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
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch Screener data for {symbol}: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            data = {}
            
            # --- 1. Parsing Top Ratios ---
            ratios = soup.find_all('li', class_='flex flex-space-between')
            for ratio in ratios:
                name = ratio.find('span', class_='name').text.strip().lower()
                value = ratio.find('span', class_='number').text.strip().replace(',', '')
                data[name] = value
                data[name] = value
            
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
                            return float(val) if val else 0
                    return 0
                except: return 0

            # --- 2. Extracting the 24 Fundamental Parameters ---
            
            # 1. Market Cap
            mcap = float(data.get('market cap', 0))
            
            # 2. CMP vs 52W (Parse High/Low)
            hl = data.get('high / low', '0 / 0').split('/')
            high52 = float(hl[0].strip()) if len(hl)>0 else 0
            low52 = float(hl[1].strip()) if len(hl)>1 else 0
            cmp = float(data.get('current price', 0))
            
            # 3. PE
            pe = float(data.get('stock p/e', 0))
            
            # Industry PE (Often provided as 'industry pe')
            industry_pe = float(data.get('industry pe', 0)) # Might need to check if this key exists on Screener top ratio logic
            
            # ROE
            roe_val = float(data.get('return on equity', 0))
            if roe_val == 0:
                 roe_val = float(data.get('roe', 0))
            
            # Book Value & Price to Book
            book_value = float(data.get('book value', 0))
            price_to_book = float(data.get('price to book value', 0))
            if price_to_book == 0:
                price_to_book = float(data.get('pb', 0))
                
            # Industry PB (Approximation: if not present, we can't compare exactly to Industry BV, but can try)
            industry_pb = float(data.get('industry pb', 0))
            
            # Piotroski (Screener often has 'Piotroski score')
            piotroski_val = float(data.get('piotroski score', 0))
            
            # 5. EPS Trend (Latest Quarter vs Previous)
            eps_last = get_table_row('quarters', 'EPS', -1)
            eps_prev = get_table_row('quarters', 'EPS', -2)
            
            # 6. EBITDA Trend (Operating Profit in Quarters)
            ebitda_last = get_table_row('quarters', 'Operating Profit', -1)
            
            # 7. Debt / Equity
            # Sometimes in ratios or inferred from Borrowings/Equity
            de = float(data.get('debt \/ eq', 0)) # Try top ratios first
            if de == 0: # Try calculating
                borrowings = get_table_row('balance-sheet', 'Borrowings', -1)
                equity = get_table_row('balance-sheet', 'Share Capital', -1) + get_table_row('balance-sheet', 'Reserves', -1)
                de = borrowings / equity if equity else 0

            # 8. Dividend Yield
            dy = float(data.get('dividend yield', 0))
            
            # 10. Current Ratio
            # Usually in ratios section check generic scraping
            curr_ratio = 1.5 # Placeholder if not in top ratios
            
            # 11. Promoter Holding
            prom_hold = get_table_row('shareholding', 'Promoters', -1)
            
            # 12. FII/DII Trend
            fii_last = get_table_row('shareholding', 'FIIs', -1)
            fii_prev = get_table_row('shareholding', 'FIIs', -2)
            dii_last = get_table_row('shareholding', 'DIIs', -1)
            
            # 13. OCF
            ocf = get_table_row('cash-flow', 'Cash from Operating Activity', -1)
            
            # 14. ROCE
            roce = float(data.get('roce', 0))
            
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
            int_cov = float(data.get('int coverage', 0)) # often in top ratios
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
                'Intrinsic Value': eps_last * 15, # Very Rough Graham approx (EPS * 8.5 + 2g) or just PE 15
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
