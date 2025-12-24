from PIL import Image, ImageDraw, ImageFont
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class InfographicGenerator:
    def __init__(self):
        self.width = 1200 # Widened slightly
        self.height = 1900 # Taller for all params
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
        
        # 3. Decision Cards (Swing & Long Term)
        # Swing Card
        draw.rounded_rectangle([50, y_cards, 580, y_cards + 200], radius=15, fill=self.card_bg, outline="#334155")
        draw.text((80, y_cards + 20), "SWING TRADING", font=self.body_font, fill="#94A3B8")
        
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
        draw.text((650, y_cards + 20), "LONG TERM", font=self.body_font, fill="#94A3B8")
        
        lt_verdict = data.get('long_term_verdict', 'AVOID')
        l_color = self.green if "BUY" in lt_verdict else (self.red if "AVOID" in lt_verdict else self.yellow)
        draw.text((650, y_cards + 60), lt_verdict, font=self.header_font, fill=l_color)
        
        lt_reason = data.get('long_term_reason', '')
        if len(lt_reason) > 40: lt_reason = lt_reason[:37] + "..."
        draw.text((650, y_cards + 110), lt_reason, font=self.small_font, fill="#E2E8F0")

        # 4. Footer (Final Action)
        y_final = y_cards + 240
        draw.rectangle([0, y_final, self.width, self.height], fill=self.card_bg)
        
        final_action = data.get('final_action', 'Analyze more data.')
        draw.text((50, y_final + 30), "FINAL VERDICT", font=self.subheader_font, fill=self.yellow)
        draw.text((50, y_final + 80), final_action, font=self.header_font, fill="#FFFFFF")
        
        draw.text((50, self.height - 50), "generated by Samvruddhi Stock Analyzer | Educational Purpose Only", font=self.small_font, fill="#64748B")
        
        img.save(output_path)
        return output_path
