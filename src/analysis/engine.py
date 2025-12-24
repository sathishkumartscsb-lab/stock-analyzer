import logging
from src.config import TOTAL_PARAMETERS

logger = logging.getLogger(__name__)

class AnalysisEngine:
    def __init__(self):
        pass

    def evaluate_stock(self, fundamentals, technicals, news):
        """
        Main entry point to evaluate a stock.
        Returns a dictionary with scores and detailed parameter status.
        """
        score_report = {
            'fundamental_score': 0,
            'technical_score': 0,
            'news_score': 0,
            'total_score': 0,
            'details': {} 
        }
        
        # Determine Best Available Price (Live > Fund > Close)
        live_price = technicals.get('Live Price', 0)
        fund_price = fundamentals.get('Current Price', 0) if fundamentals else 0
        tech_close = technicals.get('Close', 0) if technicals else 0
        
        # Logic: If Live Price is valid, use it. Else Fund. Else Close.
        # We assume Live Price from yfinance fast_info is most up to date.
        cmp = live_price if live_price > 0 else (fund_price if fund_price > 0 else tech_close)
        
        # Inject CMP into datasets so analysis uses the unified price
        if fundamentals:
            old_price = float(fundamentals.get('Current Price', 0) or 0)
            fundamentals['Current Price'] = cmp
            
            # --- REAL-TIME RECALCULATION FOR ACCURACY ---
            # If we have a live price different from the snapped fundamental price,
            # we must recalculate P/E, Market Cap, etc. to give accurate valuation insights.
            if cmp > 0 and old_price > 0 and abs(cmp - old_price) > 0.01:
                ratio = cmp / old_price
                
                # 1. Market Cap (Scales linearly with price)
                if 'Market Cap' in fundamentals:
                     fundamentals['Market Cap'] = float(fundamentals['Market Cap']) * ratio
                
                # 2. P/E Ratio (Price / EPS)
                # If we have P/E, we can derive EPS and recalc. Or just scale P/E.
                if 'Stock P/E' in fundamentals:
                    fundamentals['Stock P/E'] = float(fundamentals['Stock P/E']) * ratio
                
                # 3. Dividend Yield (DPS / Price) -> Inverse scale
                if 'Dividend Yield' in fundamentals:
                    fundamentals['Dividend Yield'] = float(fundamentals['Dividend Yield']) / ratio

        if technicals:
            technicals['Close'] = cmp 
            
        score_report['cmp'] = cmp

        # 1. Fundamental Analysis
        f_score, f_details = self._analyze_fundamentals(fundamentals)
        score_report['fundamental_score'] = f_score
        score_report['details'].update(f_details)
        
        # 2. Technical Analysis
        t_score, t_details = self._analyze_technicals(technicals)
        score_report['technical_score'] = t_score
        score_report['details'].update(t_details)
        
        # 3. News Analysis
        n_score, n_details = self._analyze_news(news)
        score_report['news_score'] = n_score
        score_report['details'].update(n_details)
        
        # Total
        score_report['total_score'] = f_score + t_score + n_score
        
        # Verdicts
        verdicts = self._generate_verdicts(score_report['total_score'], fundamentals, technicals)
        score_report.update(verdicts)
        
        return score_report

    def _analyze_fundamentals(self, data):
        score = 0
        details = {}
        
        if not data:
            data = {}

        # Rule Helper
        def evaluate(key, value, threshold, condition='>', positive_if_true=True):
            try: 
                v = float(value) if value is not None else 0.0
                t = float(threshold)
                if condition == '>': res = v > t
                elif condition == '<': res = v < t
                else: res = False
                
                is_good = res if positive_if_true else not res
                return (1, 'Positive') if is_good else (0, 'Negative')
            except: return (0, 'N/A')

        # 24 Parameters Logic
        # 1. Market Cap
        mcap = float(data.get('Market Cap', 0) or 0)
        s = 0
        st = 'Unknown'
        
        if mcap > 20000:
            s = 1; st = 'Large Cap'
        elif mcap > 5000:
            s = 1; st = 'Mid Cap'
        elif mcap > 500:
            s = 0.5; st = 'Small Cap' # Slightly higher risk
        else:
            s = 0; st = 'Micro Cap (Risky)'
            
        score += s; details['Market Cap'] = {'value': f"{float(data.get('Market Cap', 0)):.2f}", 'score': s, 'status': st}
        
        # 2. CMP vs 52W
        low = data.get('Low_52', 0); cmp = data.get('Current Price', 0)
        if low > 0 and cmp > low * 1.1: s=1; st='Positive'
        else: s=0.5; st='Neutral'
        score += s; details['CMP vs 52W'] = {'value': f"{cmp:.2f}", 'score': s, 'status': st}

        # 3. PE vs Peer (Refined Logic)
        pe = data.get('Stock P/E', 0)
        ind_pe = data.get('Industry PE', 0)
        s = 0; st = 'N/A'
        
        if pe > 0:
            if pe < 12: s=1; st='Extremely Oversold'
            elif 12 <= pe < 15: s=1; st='Very Attractive'
            elif 15 <= pe < 20: s=0.5; st='Attractive'
            elif 20 <= pe < 25: s=0.5; st='Expensive'
            else: s=0; st='Overbought' # > 25
            
            # Industry Comparison Bonus/Penalty
            if ind_pe > 0:
                if pe < ind_pe: st += ' (Vs Ind: Attractive)'
                else: st += ' (Vs Ind: Cautious)'
                
        score += s; details['P/E Ratio'] = {'value': f"{pe:.2f} (Ind: {ind_pe:.2f})", 'score': s, 'status': st}
        
        # 4. PEG (< 1 is good)
        s, st = evaluate('PEG Ratio', data.get('PEG Ratio', 2), 1, '<')
        score += s; details['PEG Ratio'] = {'value': f"{data.get('PEG Ratio'):.2f}", 'score': s, 'status': st}
        
        # 5. EPS Trend
        s, st = evaluate('EPS Trend', data.get('EPS Trend', 0), 0)
        score += s; details['EPS Trend'] = {'value': f"{data.get('EPS Trend'):.1f}%", 'score': s, 'status': st}
        
        # 6. EBITDA Trend
        s, st = evaluate('EBITDA Trend', data.get('EBITDA Trend', 0), 0)
        score += s; details['EBITDA Trend'] = {'value': data.get('EBITDA Trend'), 'score': s, 'status': st}
        
        # 7. Debt/Equity (< 1 good)
        s, st = evaluate('Debt / Equity', data.get('Debt / Equity', 0), 1, '<')
        score += s; details['Debt / Equity'] = {'value': data.get('Debt / Equity'), 'score': s, 'status': st}
        
        # 8. Dividend Yield (>0 good)
        s, st = evaluate('Dividend Yield', data.get('Dividend Yield', 0), 0)
        score += s; details['Dividend Yield'] = {'value': f"{float(data.get('Dividend Yield', 0)):.2f}%", 'score': s, 'status': st}
        
        # 9. Intrinsic Value (CMP < Intrinsic)
        intr = data.get('Intrinsic Value', 0)
        if cmp < intr: s=1; st='Undervalued'
        else: s=0; st='Overvalued'
        score += s; details['Intrinsic Value'] = {'value': f"{intr:.1f}", 'score': s, 'status': st}
        
        # 10. Current Ratio (> 1.5)
        s, st = evaluate('Current Ratio', data.get('Current Ratio', 0), 1.5)
        score += s; details['Current Ratio'] = {'value': data.get('Current Ratio'), 'score': s, 'status': st}
        
        # 11. Promoter Holding (> 40%?)
        s, st = evaluate('Promoter Holding', data.get('Promoter Holding', 0), 40)
        score += s; details['Promoter Holding'] = {'value': f"{data.get('Promoter Holding')}%", 'score': s, 'status': st}
        
        # 12. FII/DII Trend (>0)
        # Rule: Positive Change (> 0%) -> Institutional money is entering.
        fii_change = float(data.get('FII/DII Change', 0))
        if fii_change > 0: s=1; st='Positive (Increasing)'
        elif fii_change < 0: s=0; st='Negative (Decreasing)'
        else: s=0.5; st='Neutral'
        score += s; details['FII/DII Trend'] = {'value': f"{fii_change:.2f}%", 'score': s, 'status': st}
        
        # 13. Operating Cash Flow (Advanced 4-Phase)
        ocf = float(data.get('Operating Cash Flow', 0))
        net_profit = float(data.get('Net Profit', 0)) # Need to ensure this is passed from fetcher
        sales = float(data.get('Sales', 0))
        
        s_ocf = 0
        st_ocf_list = []
        
        # Phase 1: Earnings Quality (OCF > Net Profit)
        # Ideally check 3 years, here checking TTM
        if ocf < net_profit:
            st_ocf_list.append("Low Earnings Quality (OCF < Net Profit)")
        else:
             st_ocf_list.append("High Earnings Quality")
             
        # Phase 2: Efficiency (OCF Margin = OCF/Sales)
        # > 15% Cash Cow, 5-15% Standard, < 5% High Risk
        ocf_margin = (ocf / sales * 100) if sales > 0 else 0
        if ocf_margin > 15:
            s_ocf += 1; st_ocf_list.append("Cash Cow (High Eff)")
        elif ocf_margin > 5:
            s_ocf += 0.5; st_ocf_list.append("Standard Eff")
        else:
            s_ocf += 0; st_ocf_list.append("High Risk (Low Margin)")
            
        # Phase 4 (Partial): FCF Conversion check (OCF positive but FCF negative?)
        fcf_val = float(data.get('Free Cash Flow', 0))
        if fcf_val < 0 and ocf > 0:
            st_ocf_list.append("Capital Intensive")
            
        # Final Score Logic for OCF
        # If OCF is negative -> Automatic 0 and Critical Fail
        if ocf < 0:
            s = 0; st = "Negative OCF (CRITICAL)"
        else:
            s = 1 if s_ocf >= 1 else 0.5
            st = " | ".join(st_ocf_list)

        score += s; details['Operating Cash Flow'] = {'value': f"{ocf:.2f}", 'score': s, 'status': st}
        
        # 14. ROCE (>15)
        s, st = evaluate('ROCE', data.get('ROCE', 0), 15)
        score += s; details['ROCE'] = {'value': f"{data.get('ROCE')}%", 'score': s, 'status': st}
        
        # 14b. ROE (>15 good, <10 avoid)
        roe = data.get('ROE', 0)
        s = 0; st = 'Neutral'
        if roe > 15: s=1; st='Good'
        elif roe < 10: s=0; st='Avoid (Low)'
        else: s=0.5; st='Average'
        score += s; details['ROE'] = {'value': f"{roe}%", 'score': s, 'status': st}

        # 15. Rev CAGR (>10)
        s, st = evaluate('Revenue CAGR', data.get('Revenue CAGR', 0), 10)
        score += s; details['Revenue CAGR'] = {'value': f"{data.get('Revenue CAGR'):.1f}%", 'score': s, 'status': st}
        
        # 16. Profit CAGR (>10)
        s, st = evaluate('Profit CAGR', data.get('Profit CAGR', 0), 10)
        score += s; details['Profit CAGR'] = {'value': f"{data.get('Profit CAGR'):.1f}%", 'score': s, 'status': st}
        
        # 17. Interest Coverage (>3)
        s, st = evaluate('Interest Coverage', data.get('Interest Coverage', 0), 3)
        score += s; details['Interest Coverage'] = {'value': f"{data.get('Interest Coverage'):.1f}", 'score': s, 'status': st}
        
        # 18. FCF (>0)
        s, st = evaluate('Free Cash Flow', data.get('Free Cash Flow', 0), 0)
        score += s; details['Free Cash Flow'] = {'value': data.get('Free Cash Flow'), 'score': s, 'status': st}
        
        # 19. Equity Dilution (Mock 0)
        score += 1; details['Equity Dilution'] = {'value': 'No', 'score': 1, 'status': 'Stable'}
        
        # 20. Pledged Shares (<5%)
        s, st = evaluate('Pledged Shares', data.get('Pledged Shares', 0), 5, '<')
        score += s; details['Pledged Shares'] = {'value': f"{data.get('Pledged Shares')}%", 'score': s, 'status': st}
        
        # 21. Contingent Liab (Risk Check)
        # Rule: if Contingent_Liabilities > (0.5 * Net_Worth): Status = ❌
        cont_liab = data.get('Contingent Liabilities', 0)
        net_worth = data.get('Net Worth', 1) # Avoid div/0
        cl_ratio = cont_liab / net_worth if net_worth > 0 else 0
        
        if cl_ratio > 0.5:
             s = 0; st = f"High Risk (>50% NW)"
        else:
             s = 1; st = "Safe"
        score += s * 0.5; details['Contingent Liab'] = {'value': f"{cl_ratio:.1%}", 'score': s*0.5, 'status': st}
        
        # 22. Piotroski F-Score (Refined)
        # > 7 Good, 5-6 Average, < 5 Avoid
        piotroski = data.get('Piotroski Score', 0)
        s = 0; st = 'N/A'
        if piotroski > 7: s=1; st='Good (Strong)'
        elif 5 <= piotroski <= 7: s=0.5; st='Average'
        else: s=0; st='Avoid (Weak)'
        score += s; details['Piotroski Score'] = {'value': piotroski, 'score': s, 'status': st}
        
        # 23. Working Capital (Mock)
        score += 0.5; details['Working Cap Cycle'] = {'value': 'Stable', 'score': 0.5, 'status': 'Neutral'}
        
        # 24. CFO/PAT (>1)
        s, st = evaluate('CFO to PAT', data.get('CFO to PAT', 1), 1)
        score += s; details['CFO / PAT'] = {'value': f"{data.get('CFO to PAT'):.2f}", 'score': s, 'status': st}
        
        # 24b. Book Value Analysis
        # 1. Trend: (Using proxy if historical missing, but assuming positive BV is baseline)
        # 2. Valuation: Price/Book vs Industry P/B
        bv = data.get('Book Value', 0)
        pb = data.get('Price to Book', 0)
        ind_pb = data.get('Industry PB', 0) # Assuming this exists or we mock it
        
        s_bv = 0; st_bv_list = []
        
        # Check 1: Valuation
        if pb > 0 and ind_pb > 0:
            if pb < ind_pb: 
                s_bv += 1; st_bv_list.append("Undervalued (vs Ind)")
            else:
                s_bv += 0; st_bv_list.append("Overvalued (vs Ind)")
        else:
             s_bv += 0.5; st_bv_list.append("Valuation N/A")
             
        # Check 2: Book Value > 0 (Sanity)
        if bv > 0: st_bv_list.append(f"BV: {bv}")
        else: st_bv_list.append("Negative BV (Bad)")
        
        score += s_bv if s_bv <= 1 else 1
        details['Book Value Analysis'] = {'value': f"P/B: {pb:.2f}", 'score': min(s_bv, 1), 'status': " | ".join(st_bv_list)}
        
        return score, details

    def _analyze_technicals(self, data):
        score = 0
        details = {}
        if not data: return 0, {}
        
        # 25. Trend (Moving Average Ribbon)
        # Strong Bullish: Price > 50DMA > 200DMA
        # Falling Knife: Price < 50DMA < 200DMA
        close = data['Close']
        dma50 = data['50DMA']
        dma200 = data['200DMA']
        
        s=0; st='Neutral'
        if close > dma50 and dma50 > dma200: 
            s=1; st='Strong Bullish'
        elif close < dma50 and dma50 < dma200:
            s=0; st='Falling Knife (Bearish)'
        elif close > dma200:
             s=0.5; st='Bullish (>200DMA)'
        else:
             s=0; st='Bearish'
             
        score += s; details['Trend (DMA)'] = {'value': f"{close:.0f} vs {dma200:.0f}", 'score': s, 'status': st}
        
        # 26. RSI (30-70 range logic)
        rsi = data.get('RSI', 50)
        if 40 < rsi < 70: s=0.5; st='Neutral'
        elif rsi <= 40: s=1; st='Oversold (Buy)'
        else: s=0; st='Overbought'
        score += s; details['RSI'] = {'value': f"{rsi:.1f}", 'score': s, 'status': st}
        
        # 27. MACD
        if data['MACD'] > data['MACD_SIGNAL']: s=1; st='Bullish'
        else: s=0; st='Bearish'
        score += s; details['MACD'] = {'value': f"{data['MACD']:.2f}", 'score': s, 'status': st}
        
        # 28. Pivot (Price > Pivot)
        if data['Close'] > data['Pivot']: s=1; st='Above Pivot'
        else: s=0; st='Below Pivot'
        score += s; details['Pivot Support'] = {'value': f"{data['Pivot']:.1f}", 'score': s, 'status': st}
        
        # 29. VWAP/Vol
        if data.get('VWAP_Trend') == 'Bullish': s=1
        else: s=0
        score += s; details['Volume Trend'] = {'value': data.get('Volume_Trend'), 'score': s, 'status': data.get('VWAP_Trend')}

        return score, details

    def _analyze_news(self, news_items):
        score = 0
        details = {}
        
        # Calculate Sentiment Ratio
        pos = sum(1 for n in news_items if n.get('sentiment') == 'Positive')
        neg = sum(1 for n in news_items if n.get('sentiment') == 'Negative')
        total = len(news_items)
        
        # 30. Promoter Pledge Trend (Mock / Placeholder)
        # 31. Management Changes
        # ... Just mapping general sentiment to all strictly for MVP as we don't have specific NLP for each category
        
        sentiment_score = 0.5 # Neutral base
        status = 'Neutral'
        
        if total > 0:
            net = pos - neg
            if net > 1: sentiment_score = 1; status = 'Positive'
            elif net < -1: sentiment_score = 0; status = 'Negative'
            
        # Distribute this sentiment score to the News params (32-37) as a proxy
        # 32. Orders/Business
        score += sentiment_score; details['Orders / Business'] = {'value': f"+{pos}/-{neg}", 'score': sentiment_score, 'status': status}
        
        # 33. Dividends (Manual check normally, using news proxy)
        score += 0.5; details['Dividend / Buyback'] = {'value': 'Check News', 'score': 0.5, 'status': 'Neutral'}
        
        # 34. Results
        score += sentiment_score; details['Results Performance'] = {'value': f"News Sentiment", 'score': sentiment_score, 'status': status}
        
        # 35. Regulatory
        score += 0.5; details['Regulatory / Credit'] = {'value': 'Stable', 'score': 0.5, 'status': 'Neutral'}
        
        # 36. Sector
        score += sentiment_score; details['Sector vs Nifty'] = {'value': 'Trend', 'score': sentiment_score, 'status': status}

        # 37. Peer Comparison (Mock)
        score += 0.5; details['Peer Comparison'] = {'value': 'Fair', 'score': 0.5, 'status': 'Neutral'}
        
        # 30/31 Placeholders
        score += 1; details['Promoter Pledge'] = {'value': 'Stable', 'score': 0.5, 'status': 'Safe'}
        score += 1; details['Management'] = {'value': 'Stable', 'score': 0.5, 'status': 'Safe'}

        return score, details
        
        return score, details
    def _generate_verdicts(self, total_score, fundamentals, technicals):
        if not fundamentals: fundamentals = {}
        if not technicals: technicals = {}
            
        # Critical Hard Rule
        ocf = float(fundamentals.get('Operating Cash Flow', 1) or 1)
        cfo_pat = float(fundamentals.get('CFO to PAT', 1) or 1)
        
        # Expert Rule: OCF < 0 OR (CFO/PAT) < 0.5
        is_risky = (ocf < 0) or (cfo_pat < 0.5)
        
        # Swing
        close = float(technicals.get('Close', 100) or 100)
        dma50 = float(technicals.get('50DMA', 0) or 0)
        
        swing_score = 0
        if close > dma50: swing_score += 1
        if float(technicals.get('MACD', 0) or 0) > float(technicals.get('MACD_SIGNAL', 0) or 0): swing_score += 1
        if float(technicals.get('RSI', 50) or 50) < 40: swing_score += 1 
        
        if swing_score >= 2:
            swing = "✅ BUY"
            s_action = f"Entry: {close:.1f} | Tgt: {close*1.1:.1f} | SL: {close*0.95:.1f}"
        else:
            swing = "❌ AVOID"
            s_action = "Wait for reversal."

        # Long Term
        # --- Construct Detailed Summaries ---
        
        # 1. Fundamental Summary
        f_pros = []
        f_cons = []
        
        # Checking key metrics available in 'fundamentals' dict
        pe = float(fundamentals.get('P/E Ratio', 0) or 0)
        roce = float(fundamentals.get('ROCE', 0) or 0)
        debt = float(fundamentals.get('Debt / Equity', 0) or 0)
        sales_growth = float(fundamentals.get('Revenue CAGR', 0) or 0)
        pledge = float(fundamentals.get('Pledged Shares', 0) or 0)
        
        if 0 < pe < 30: f_pros.append("Attractive Valuation")
        if roce > 20: f_pros.append("High Capital Efficiency (ROCE > 20%)")
        if debt < 0.5: f_pros.append("Low Debt")
        if sales_growth > 15: f_pros.append("Robust Revenue Growth")
        
        if pe > 50: f_cons.append("Expensive Valuation")
        if roce < 10: f_cons.append("Low Effiency")
        if debt > 1: f_cons.append("High Leverage")
        if pledge > 0: f_cons.append("Promoter Pledging Present")
        if ocf < 0: f_cons.append("Negative Operating Cash Flow")

        fund_text = "Strengths: " + ", ".join(f_pros) if f_pros else "No major strengths."
        if f_cons: fund_text += ". Weaknesses: " + ", ".join(f_cons) + "."
        
        # 2. Technical Summary
        t_signals = []
        rsi = float(technicals.get('RSI', 50) or 50)
        macd_val = float(technicals.get('MACD', 0) or 0)
        macd_sig = float(technicals.get('MACD_SIGNAL', 0) or 0)
        
        if close > dma50: t_signals.append("Price above 50DMA (Uptrend)")
        else: t_signals.append("Price below 50DMA (Weakness)")
        
        if rsi < 30: t_signals.append("Oversold (RSI < 30)")
        elif rsi > 70: t_signals.append("Overbought (RSI > 70)")
        
        if macd_val > macd_sig: t_signals.append("Bullish MACD Crossover")
        else: t_signals.append("Bearish MACD Divergence")
        
        tech_text = ", ".join(t_signals) + "."

        # Refined Logic
        if is_risky:
            long_term = "❌ AVOID"
            lt_reason = "Negative Cash Flow / Divergence (Critical Rule)."
            health = "🔴 High Risk (Avoid)"
            retail_conclusion = f"{fundamentals.get('Market Cap', 'The company')} shows critical financial weakness with negative cash flows. Despite any other positives, this is a distinct 'Red Flag'. Capital preservation is priority; look elsewhere."
            fund_summary = f"Bearish 🔴. {fund_text}"
        elif total_score >= 25:
            long_term = "✅ BUY"
            lt_reason = "Strong Fundamentals & Technicals."
            health = "🟢 High Quality"
            retail_conclusion = "A stellar compounding candidate. The company exhibits high efficiency, low leverage, and price momentum. Ideal for long-term allocation, and swing traders can ride the trend."
            fund_summary = f"Bullish 🟢. {fund_text}"
        elif total_score >= 15:
            long_term = "⚠️ HOLD"
            lt_reason = f"Average metrics ({total_score:.1f}/37). Valid for watch."
            health = "🟡 Medium Risk"
            retail_conclusion = "The company is fundamentally sound but lacks a convincing edge right now. It falls into the 'Wait and Watch' category. Accumulate only if you have high conviction in the sector."
            fund_summary = f"Neutral 🟡. {fund_text}"
        else:
            long_term = "❌ AVOID"
            lt_reason = "Weak scores across board."
            health = "🔴 High Risk"
            retail_conclusion = "Avoid this stock. The combination of weak fundamentals and bearish technicals makes it a wealth destroyer. Do not attempt to bottom fish."
            fund_summary = f"Bearish 🔴. {fund_text}"
            
        final_action = f"WATCH for support at {close*0.95:.0f}; initiate Long-Term accumulation ONLY if price stabilizes."

        # Tech Summary Label
        if swing == "✅ BUY":
            tech_summary = f"Bullish 🟢. {tech_text}"
        elif swing == "❌ AVOID":
            tech_summary = f"Bearish 🔴. {tech_text}"
        else:
             tech_summary = f"Neutral 🟡. {tech_text}"

        return {
            'swing_verdict': swing,
            'swing_action': s_action,
            'long_term_verdict': long_term,
            'long_term_reason': lt_reason,
            'final_action': final_action,
            'health_label': health,
            'risk_triggered': is_risky,
            'fundamental_summary': fund_summary,
            'technical_summary': tech_summary,
            'news_summary': "Market sentiment is currently neutral. Check latest exchange filings for specific triggers.",
            'retail_conclusion': retail_conclusion
        }
