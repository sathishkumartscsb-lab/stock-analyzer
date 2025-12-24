from src.renderer.generator import InfographicGenerator
import os

# Mock Data simulating a full analysis result
mock_data = {
    'cmp': 3319.0,
    'total_score': 28.5,
    'health_label': '🟢 High Quality',
    'swing_verdict': '✅ BUY',
    'long_term_verdict': '✅ BUY',
    'final_action': 'Accumulate at support.',
    'swing_action': 'Entry: 3319.0 | Tgt: 3650.0 | SL: 3150.0',
    'swing_reason': 'Price > 50DMA & Momentum Positive',
    'long_term_reason': 'Strong Fundamentals & Technicals.',
    'details': {
        # Fundamentals
        'Market Cap': {'value': '1200788.21', 'score': 1, 'status': 'Large Cap'},
        'CMP vs 52W': {'value': '3319.00', 'score': 0.5, 'status': 'Neutral'},
        'P/E Ratio': {'value': '23.89 (Ind: 0.00)', 'score': 0.5, 'status': 'Expensive'},
        'PEG Ratio': {'value': '4.34', 'score': 0, 'status': 'Negative'},
        'EPS Trend': {'value': '-5.4%', 'score': 0, 'status': 'Negative'},
        'EBITDA Trend': {'value': '17978.0', 'score': 1, 'status': 'Positive'},
        'Debt / Equity': {'value': '0.0', 'score': 1, 'status': 'Positive'},
        'Dividend Yield': {'value': '1.81%', 'score': 1, 'status': 'Positive'},
        'Intrinsic Value': {'value': '500.5', 'score': 0, 'status': 'Overvalued'},
        'Current Ratio': {'value': '1.5', 'score': 0, 'status': 'Negative'},
        'Promoter Holding': {'value': '71.77%', 'score': 1, 'status': 'Positive'},
        'FII/DII Trend': {'value': '-1.15%', 'score': 0, 'status': 'Negative'},
        'Operating Cash Flow': {'value': '48908.00', 'score': 0.5, 'status': 'Neutral'},
        'ROCE': {'value': '64.6%', 'score': 1, 'status': 'Positive'},
        'ROE': {'value': '52.4%', 'score': 1, 'status': 'Good'},
        'Revenue CAGR': {'value': '4.6%', 'score': 0, 'status': 'Negative'},
        'Profit CAGR': {'value': '5.5%', 'score': 0, 'status': 'Negative'},
        'Interest Coverage': {'value': '77.8', 'score': 1, 'status': 'Positive'},
        'Free Cash Flow': {'value': '45000', 'score': 1, 'status': 'Positive'},
        'Equity Dilution': {'value': 'No', 'score': 1, 'status': 'Stable'},
        'Pledged Shares': {'value': '0.0%', 'score': 1, 'status': 'Positive'},
        'Contingent Liab': {'value': '10.5%', 'score': 1, 'status': 'Safe'},
        'Piotroski Score': {'value': 8, 'score': 1, 'status': 'Good (Strong)'},
        'Working Cap Cycle': {'value': 'Stable', 'score': 0.5, 'status': 'Neutral'},
        'CFO / PAT': {'value': '1.12', 'score': 1, 'status': 'Positive'},
        'Book Value Analysis': {'value': 'P/B: 12.5', 'score': 0, 'status': 'Overvalued'},
        
        # Technicals
        'Trend (DMA)': {'value': '3319 vs 3228', 'score': 1, 'status': 'Bullish'},
        'RSI': {'value': '70.4', 'score': 0, 'status': 'Overbought'},
        'MACD': {'value': '51.49', 'score': 1, 'status': 'Bullish'},
        'Pivot Support': {'value': '3314.1', 'score': 1, 'status': 'Above Pivot'},
        'Volume Trend': {'value': 'Increasing', 'score': 1, 'status': 'Bullish'},
        
        # News/Other
        'Orders / Business': {'value': '+5/-2', 'score': 1, 'status': 'Positive'},
        'Dividend / Buyback': {'value': 'Check News', 'score': 0.5, 'status': 'Neutral'},
        'Results Performance': {'value': 'Positive', 'score': 1, 'status': 'Positive'},
        'Regulatory / Credit': {'value': 'Stable', 'score': 0.5, 'status': 'Neutral'},
        'Sector vs Nifty': {'value': 'Trend', 'score': 0.5, 'status': 'Neutral'},
        'Peer Comparison': {'value': 'Fair', 'score': 0.5, 'status': 'Neutral'},
        'Promoter Pledge': {'value': 'Stable', 'score': 1, 'status': 'Safe'},
        'Management': {'value': 'Stable', 'score': 1, 'status': 'Safe'}
    }
}

gen = InfographicGenerator()
# We will temporarily modify the generator in the actual file, then run this to verify.
# or we can rely on this script using the *current* generator to see baseline, then modify.

output_path = "debug_full_report.png"
gen.generate_report("TCS", mock_data, output_path)
print(f"Generated {output_path}")
