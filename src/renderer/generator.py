from PIL import Image, ImageDraw, ImageFont
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class InfographicGenerator:
    def __init__(self):
        self.width = 1200 # Widened slightly
        self.height = 2700 # Taller for all params + Summaries + News + Charts
        self.bg_color = "#0F172A"
        self.text_color = "#FFFFFF"
        self.green = "#22C55E"
        self.yellow = "#FACC15"
        self.red = "#EF4444"
        self.card_bg = "#1E293B"
        
        # Load Fonts
        try:
            self.title_font = ImageFont.truetype("arial.ttf", 70)
            self.header_font = ImageFont.truetype("arial.ttf", 45)
            self.subheader_font = ImageFont.truetype("arial.ttf", 35) # New for section headers
            self.body_font = ImageFont.truetype("arial.ttf", 26)
            self.small_font = ImageFont.truetype("arial.ttf", 20)
        except:
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.subheader_font = ImageFont.load_default()
            self.body_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()

    def generate_report(self, stock_name, data, output_path):
        img = Image.new('RGB', (self.width, self.height), color=self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # 1. Header (0 - 180)
        draw.text((50, 40), stock_name, font=self.title_font, fill=self.text_color)
        
        cmp = data.get('cmp', 0)
        draw.text((50, 120), f"CMP: ₹{cmp:.2f}", font=self.header_font, fill=self.text_color)
        
        # Score Badge
        score = data.get('total_score', 0)
        risk_label = data.get('health_label', 'Unknown')
        score_color = self.green if score > 25 else (self.yellow if score > 15 else self.red)
        
        draw.rounded_rectangle([750, 40, 1150, 160], radius=20, fill=self.card_bg, outline=score_color, width=4)
        draw.text((800, 60), f"Score: {score:.1f}/37", font=self.header_font, fill=score_color)
        draw.text((800, 110), f"{risk_label}", font=self.body_font, fill=score_color)

        # 2. DATA GRID (200 - 1300)
        y_start = 200
        details = data.get('details', {})
        
        # Define Columns
        col1_x = 50   # Fundamentals 1
        col2_x = 600  # Fundamentals 2 / Technials
        
        # Helper to draw list
        def draw_section(title, keys, start_x, start_y):
            draw.text((start_x, start_y), title, font=self.subheader_font, fill=self.yellow)
            y = start_y + 50
            for k in keys:
                if k in details:
                    val = details[k]
                    # Status Dot
                    dot_color = self.green if val['score'] >= 1 else (self.yellow if val['score'] == 0.5 else self.red)
                    
                    # Truncate value if too long
                    v_str = str(val['value'])
                    if len(v_str) > 15: v_str = v_str[:12] + "..."
                    
                    draw.text((start_x, y), f"{k}", font=self.body_font, fill="#94A3B8") # Label
                    draw.text((start_x + 280, y), f"{v_str}", font=self.body_font, fill=self.text_color) # Value
                    draw.ellipse([start_x + 480, y+8, start_x + 495, y+23], fill=dot_color) # Dot
                    y += 40
            return y

        # --- Fundamentals (Split into 2 cols to fit 26 items) --
        fund_keys_1 = [
            'Market Cap', 'CMP vs 52W', 'P/E Ratio', 'PEG Ratio', 'EPS Trend', 
            'EBITDA Trend', 'Debt / Equity', 'Dividend Yield', 'Intrinsic Value',
            'Current Ratio', 'Promoter Holding', 'FII/DII Trend', 'Operating Cash Flow'
        ]
        fund_keys_2 = [
            'ROCE', 'ROE', 'Revenue CAGR', 'Profit CAGR', 'Interest Coverage',
            'Free Cash Flow', 'Equity Dilution', 'Pledged Shares', 'Contingent Liab',
            'Piotroski Score', 'Working Cap Cycle', 'CFO / PAT', 'Book Value Analysis'
        ]
        
        y_end_1 = draw_section("FUNDAMENTALS (1/2)", fund_keys_1, col1_x, y_start)
        y_end_2 = draw_section("FUNDAMENTALS (2/2)", fund_keys_2, col2_x, y_start)
        
        next_section_y = max(y_end_1, y_end_2) + 40
        
        # --- Technicals & News ---
        tech_keys = ['Trend (DMA)', 'RSI', 'MACD', 'Pivot Support', 'Volume Trend']
        news_keys = [
            'Orders / Business', 'Dividend / Buyback', 'Results Performance',
            'Regulatory / Credit', 'Sector vs Nifty', 'Peer Comparison', 
            'Promoter Pledge', 'Management'
        ]
        
        y_tech = draw_section("TECHNICALS", tech_keys, col1_x, next_section_y)
        y_news = draw_section("NEWS & OTHERS", news_keys, col2_x, next_section_y)
        
        y_cards = max(y_tech, y_news) + 50
        
        # 3. Summary Boxes (Web Layout Match)
        # Fund Summary
        f_summary = data.get('fundamental_summary', 'No summary.')
        t_summary = data.get('technical_summary', 'No summary.')
        n_summary = data.get('news_summary', 'No summary.')
        
        def draw_summary_box(title, text, x, y, width, color="#FFFFFF"):
            draw.rounded_rectangle([x, y, x + width, y + 150], radius=15, fill="#F8FAFC", outline="#CBD5E1") # Light BG
            
            # Determine Title Color
            if "Bullish" in text: title_color = self.green
            elif "Bearish" in text: title_color = self.red
            else: title_color = "#B45309" # Dark Amber/Yellow
            
            draw.text((x + 20, y + 20), title, font=self.small_font, fill=title_color)
            
            # Wrap Text logic (Simple)
            import textwrap
            wrapped = textwrap.fill(text, width=35) 
            draw.text((x + 20, y + 50), wrapped, font=self.small_font, fill="#0F172A") # Dark text

        # Draw 3 boxes
        box_w = 360
        draw_summary_box("Fundamental Summary", f_summary, 50, y_cards, box_w)
        draw_summary_box("Technical Summary", t_summary, 430, y_cards, box_w)
        draw_summary_box("News Summary", n_summary, 810, y_cards, box_w)
        
        y_cards += 180 # Push down for decision cards

        # 4. Decision Cards (Swing & Long Term)
        # Swing Card
        draw.rounded_rectangle([50, y_cards, 580, y_cards + 200], radius=15, fill=self.card_bg, outline="#334155")
        draw.text((80, y_cards + 20), "Swing Trading", font=self.body_font, fill="#94A3B8")
        
        swing_verdict = data.get('swing_verdict', 'WAIT')
        s_color = self.green if "BUY" in swing_verdict else (self.red if "AVOID" in swing_verdict else self.yellow)
        draw.text((80, y_cards + 60), swing_verdict, font=self.header_font, fill=s_color)
        
        # Swing Action Details (Entry/SL/Tgt)
        swing_action = data.get('swing_action', '')
        swing_reason = data.get('swing_reason', '')
        
        draw.text((80, y_cards + 110), swing_reason, font=self.small_font, fill="#E2E8F0")
        if swing_action:
            draw.text((80, y_cards + 140), swing_action, font=self.small_font, fill=self.yellow)
        
        # Long Term Card
        draw.rounded_rectangle([620, y_cards, 1150, y_cards + 200], radius=15, fill=self.card_bg, outline="#334155")
        draw.text((650, y_cards + 20), "Long-Term Investment", font=self.body_font, fill="#94A3B8")
        
        lt_verdict = data.get('long_term_verdict', 'AVOID')
        l_color = self.green if "BUY" in lt_verdict else (self.red if "AVOID" in lt_verdict else self.yellow)
        draw.text((650, y_cards + 60), lt_verdict, font=self.header_font, fill=l_color)
        
        lt_reason = data.get('long_term_reason', '')
        if len(lt_reason) > 40: lt_reason = lt_reason[:37] + "..."
        draw.text((650, y_cards + 110), lt_reason, font=self.small_font, fill="#E2E8F0")
        
        y_cards += 220 # Push down

        # Retail Conclusion (Bottom Text)
        retail_conc = data.get('retail_conclusion', '')
        import textwrap
        wrapped_conc = textwrap.fill(f"Retail Conclusion: {retail_conc}", width=90)
        
        draw.rounded_rectangle([50, y_cards, 1150, y_cards + 120], radius=15, fill="#F8FAFC", outline="#CBD5E1")
        draw.text((80, y_cards + 20), "Overall:", font=self.small_font, fill="#0F172A")
        draw.text((160, y_cards + 20), data.get('health_label',''), font=self.small_font, fill=self.green if "High" in data.get('health_label','') else self.red)
        draw.text((80, y_cards + 50), wrapped_conc, font=self.small_font, fill="#334155")

        # 5. Footer (Final Action)
        y_final = y_cards + 150
        draw.rectangle([0, y_final, self.width, self.height], fill=self.card_bg)
        
        final_action = data.get('final_action', 'Analyze more data.')
        draw.text((50, y_final + 30), "FINAL VERDICT", font=self.subheader_font, fill=self.yellow)
        draw.text((50, y_final + 80), final_action, font=self.header_font, fill="#FFFFFF")
        
        # 6. News Section
        y_news = y_final + 180
        draw.text((50, y_news), "📰 LATEST NEWS", font=self.subheader_font, fill=self.yellow)
        
        news_items = data.get('news_items', [])
        y_news += 50
        for i, news in enumerate(news_items[:4]):
            if y_news > self.height - 400:  # Leave space for charts
                break
            source = news.get('source', 'News')
            title = news.get('title', '')
            if len(title) > 80:
                title = title[:77] + "..."
            
            draw.text((50, y_news), f"• [{source}]", font=self.small_font, fill=self.green)
            draw.text((200, y_news), title, font=self.small_font, fill="#E2E8F0")
            y_news += 35
        
        # 7. Pie Charts Section
        y_charts = y_news + 40
        draw.text((50, y_charts), "📊 KEY METRICS", font=self.subheader_font, fill=self.yellow)
        y_charts += 60
        
        # Helper function to draw pie chart
        def draw_pie_chart(x, y, radius, percentage, color1, color2, label, value_text):
            # Background circle
            draw.ellipse([x, y, x + radius*2, y + radius*2], fill="#1E293B", outline="#334155", width=2)
            
            # Pie slice (percentage)
            if percentage > 0:
                angle = int(360 * (percentage / 100))
                draw.pieslice([x, y, x + radius*2, y + radius*2], start=-90, end=-90 + angle, fill=color1)
            
            # Center circle (donut effect)
            inner_r = radius * 0.6
            offset = (radius - inner_r)
            draw.ellipse([x + offset, y + offset, x + radius*2 - offset, y + radius*2 - offset], fill=self.bg_color)
            
            # Center text
            center_x = x + radius
            center_y = y + radius
            draw.text((center_x - 20, center_y - 15), f"{percentage:.0f}%", font=self.body_font, fill="#FFFFFF")
            
            # Label below
            draw.text((x, y + radius*2 + 10), label, font=self.small_font, fill="#94A3B8")
            draw.text((x, y + radius*2 + 35), value_text, font=self.small_font, fill="#FFFFFF")
        
        # Chart 1: Promoter Holding
        promoter = float(data.get('details', {}).get('Promoter Holding', {}).get('value', '0').replace('%', '') or 0)
        draw_pie_chart(80, y_charts, 70, promoter, self.green, "#334155", "Promoter", f"{promoter:.1f}%")
        
        # Chart 2: Score Breakdown
        total = data.get('total_score', 1)
        fund_pct = (data.get('fundamental_score', 0) / max(total, 1)) * 100
        draw_pie_chart(400, y_charts, 70, fund_pct, "#3B82F6", "#334155", "Fundamental", f"{fund_pct:.0f}%")
        
        # Chart 3: Debt Level
        debt = float(data.get('details', {}).get('Debt / Equity', {}).get('value', '0') or 0)
        debt_pct = min((debt / 2) * 100, 100) if debt > 0 else 0
        debt_color = self.red if debt > 1 else self.green
        draw_pie_chart(720, y_charts, 70, debt_pct, debt_color, "#334155", "Debt Level", f"{debt:.2f}")
        
        # Chart 4: Technical Score
        tech_pct = (data.get('technical_score', 0) / 5) * 100
        draw_pie_chart(1040, y_charts, 70, tech_pct, "#F59E0B", "#334155", "Technical", f"{tech_pct:.0f}%")
        
        draw.text((50, self.height - 50), "generated by Samvruddhi Stock Analyzer | Educational Purpose Only", font=self.small_font, fill="#64748B")
        
        img.save(output_path)
        return output_path
