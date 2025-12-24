from PIL import Image, ImageDraw, ImageFont
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class InfographicGenerator:
    def __init__(self):
        self.width = 1080
        self.height = 1350
        self.bg_color = "#0F172A"
        self.text_color = "#FFFFFF"
        self.green = "#22C55E"
        self.yellow = "#FACC15"
        self.red = "#EF4444"
        
        # Load Fonts (Fallback to default if custom not found)
        try:
            self.title_font = ImageFont.truetype("arial.ttf", 60)
            self.header_font = ImageFont.truetype("arial.ttf", 40)
            self.body_font = ImageFont.truetype("arial.ttf", 24)
            self.small_font = ImageFont.truetype("arial.ttf", 18)
        except:
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.body_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()

    def generate_report(self, stock_name, data, output_path):
        """
        Generates the infographic strictly following the locked layout.
        data keys: cmp, total_score, health_label, swing_verdict, long_term_verdict, final_action, details
        """
        img = Image.new('RGB', (self.width, self.height), color=self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # --- 1. Header Bar (0-200px approx) ---
        # Stock Name
        draw.text((50, 40), stock_name, font=self.title_font, fill=self.text_color)
        
        # CMP
        cmp = data.get('cmp', 'N/A')
        draw.text((50, 110), f"CMP: ₹{cmp}", font=self.header_font, fill=self.text_color)
        
        # Score & Risk Badge (Top Right)
        score = data.get('total_score', 0)
        risk_label = data.get('health_label', 'Unknown')
        
        # Color based on score/risk
        score_color = self.green if score > 25 else (self.yellow if score > 15 else self.red)
        
        draw.rounded_rectangle([700, 40, 1030, 150], radius=20, fill="#1E293B", outline=score_color, width=3)
        draw.text((730, 60), f"Score: {score:.1f}/37", font=self.header_font, fill=score_color)
        draw.text((730, 105), f"Risk: {risk_label}", font=self.body_font, fill=self.text_color)

        # --- 2. Fundamentals & Technicals Split (200px - 700px) ---
        y_start = 220
        
        # Headers
        draw.text((50, y_start), "FUNDAMENTALS", font=self.header_font, fill=self.yellow)
        draw.text((550, y_start), "TECHNICALS", font=self.header_font, fill=self.yellow)
        
        details = data.get('details', {})
        
        # Fundamentals Column (Left)
        fund_keys = ['P/E Ratio', 'ROCE', 'ROE', 'Debt/Equity'] # MVP subset, can expand
        y_f = y_start + 60
        for i, k in enumerate(fund_keys):
            if k in details:
                val = details[k]
                status_color = self.green if val['score'] == 1 else (self.yellow if val['score'] == 0.5 else self.red)
                draw.text((50, y_f), f"{k}: {val['value']}", font=self.body_font, fill=self.text_color)
                draw.ellipse([400, y_f+5, 415, y_f+20], fill=status_color)
                y_f += 50

        # Technicals Column (Right)
        tech_keys = ['Trend (DMA)', 'RSI', 'MACD']
        y_t = y_start + 60
        for i, k in enumerate(tech_keys):
            if k in details:
                val = details[k]
                status_color = self.green if val['score'] == 1 else (self.yellow if val['score'] == 0.5 else self.red)
                draw.text((550, y_t), f"{k}: {val['value']}", font=self.body_font, fill=self.text_color)
                draw.ellipse([900, y_t+5, 915, y_t+20], fill=status_color)
                y_t += 50

        # --- 3. News & Trends (720px - 900px) ---
        y_news = 720
        draw.line((50, y_news, 1030, y_news), fill="#334155", width=2)
        draw.text((50, y_news + 20), "NEWS & TRENDS", font=self.header_font, fill=self.yellow)
        
        # Placeholder news text
        news_sentiment = details.get('News Sentiment', {}).get('status', 'No Major News')
        draw.text((50, y_news + 80), f"Recent Sentiment: {news_sentiment}", font=self.body_font, fill=self.text_color)
        draw.text((50, y_news + 120), "Latest: Check App for specific headlines.", font=self.small_font, fill="#94A3B8")

        # --- 4. Decision Cards (920px - 1100px) ---
        y_decision = 920
        
        # Draw 2 Boxes
        # Swing
        draw.rounded_rectangle([50, y_decision, 515, y_decision + 150], radius=15, fill="#1E293B", outline="#334155")
        draw.text((80, y_decision + 20), "SWING TRADING", font=self.body_font, fill="#94A3B8")
        swing = data.get('swing_verdict', 'WAIT')
        s_color = self.green if "BUY" in swing else (self.red if "AVOID" in swing else self.yellow)
        draw.text((80, y_decision + 60), swing, font=self.header_font, fill=s_color)

        # Long Term
        draw.rounded_rectangle([565, y_decision, 1030, y_decision + 150], radius=15, fill="#1E293B", outline="#334155")
        draw.text((595, y_decision + 20), "LONG TERM", font=self.body_font, fill="#94A3B8")
        lt = data.get('long_term_verdict', 'AVOID')
        l_color = self.green if "BUY" in lt else (self.red if "AVOID" in lt else self.yellow)
        draw.text((595, y_decision + 60), lt, font=self.header_font, fill=l_color)

        # --- 5. Final Action Bar (1150px+) ---
        y_final = 1150
        draw.rectangle([0, y_final, 1080, 1350], fill="#1E293B") # Darker footer bg
        
        final_action = data.get('final_action', 'Analyze more data.')
        draw.text((50, y_final + 40), "FINAL VERDICT & ACTION", font=self.body_font, fill=self.yellow)
        draw.text((50, y_final + 80), final_action, font=self.header_font, fill="#FFFFFF")
        
        draw.text((50, 1300), "Auto-Generated by StockInfographicBot | Educational Use Only", font=self.small_font, fill="#64748B")
        
        img.save(output_path)
        return output_path
