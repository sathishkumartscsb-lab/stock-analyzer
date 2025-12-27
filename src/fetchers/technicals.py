try:
    import talib
except ImportError:
    talib = None
import logging
import pandas as pd
import numpy as np
import yfinance as yf
import requests

logger = logging.getLogger(__name__)

class TechnicalFetcher:
    def __init__(self):
        pass
    
    def fetch_nse_price(self, symbol):
        """
        Fetch current price from NSE India API as fallback
        """
        try:
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                price_info = data.get('priceInfo', {})
                current_price = price_info.get('lastPrice', 0)
                if current_price > 0:
                    logger.info(f"NSE API: Got price {current_price} for {symbol}")
                    return {
                        'price': current_price,
                        'change': price_info.get('change', 0),
                        'pChange': price_info.get('pChange', 0),
                        'source': 'NSE India'
                    }
        except Exception as e:
            logger.error(f"NSE API error for {symbol}: {e}")
        return None

    def get_live_price(self, symbol):
        """
        Fetches the latest available price.
        Uses history(period='1d') as it's more reliable than fast_info in some yf versions.
        """
        try:
            # Handle suffix
            suffix = ""
            if "." not in symbol:
                suffix = ".NS"
            ns_symbol = f"{symbol.strip().upper()}{suffix}"
            
            ticker = yf.Ticker(ns_symbol)
            
            # Robust price fetch
            df = ticker.history(period='1d')
            if not df.empty:
                return float(df['Close'].iloc[-1])
            
            # Legacy fallback
            price = ticker.info.get('regularMarketPrice') or ticker.info.get('currentPrice')
            return float(price) if price else 0.0
        except Exception as e:
            logger.error(f"Error fetching live price for {symbol}: {e}")
            return 0.0

    def fetch_ohlc_history(self, symbol, period="1y"):
        """
        Fetches historical data using yfinance.
        """
        try:
            suffix = ""
            if "." not in symbol:
                suffix = ".NS"
            ns_symbol = f"{symbol.strip().upper()}{suffix}"
            
            logger.info(f"fetch_ohlc_history: symbols={ns_symbol}, period={period}")
            ticker = yf.Ticker(ns_symbol)
            df = ticker.history(period=period)
            
            if df.empty and suffix == ".NS":
                logger.info(f"NSE empty, trying BSE for {symbol}")
                ns_symbol = f"{symbol.strip().upper()}.BO"
                ticker = yf.Ticker(ns_symbol)
                df = ticker.history(period=period)
            
            if df.empty:
                logger.warning(f"No history found for {symbol} via yfinance (Final ticker: {ns_symbol})")
                return None
            
            logger.info(f"fetch_ohlc_history: success for {ns_symbol}, rows={len(df)}")
            return df
        except Exception as e:
            logger.error(f"Error fetching technicals for {symbol}: {e}")
            return None

    def calculate_indicators(self, df):
        if df is None:
            logger.warning("calculate_indicators: df is None")
            return {}
        if len(df) < 30: # Reduced from 200 for flexibility
            logger.warning(f"calculate_indicators: df too short ({len(df)})")
            return {}

        close = df['Close'].values
        # ... Rest of indices logic ...
        
        # 50 DMA & 200 DMA
        # 50 DMA & 200 DMA - Manual calculation if talib missing
        if talib:
            dma_50 = talib.SMA(close, timeperiod=50)[-1]
            dma_200 = talib.SMA(close, timeperiod=200)[-1]
            rsi = talib.RSI(close, timeperiod=14)[-1]
            macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            macd_val = macd[-1]
            signal_val = macdsignal[-1]
        else:
            # Pandas fallback
            dma_50 = pd.Series(close).rolling(window=50).mean().iloc[-1]
            dma_200 = pd.Series(close).rolling(window=200).mean().iloc[-1]
            
            # Simple RSI approx
            delta = pd.Series(close).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # Simple MACD approx
            exp1 = pd.Series(close).ewm(span=12, adjust=False).mean()
            exp2 = pd.Series(close).ewm(span=26, adjust=False).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_val = macd_line.iloc[-1]
            signal_val = signal_line.iloc[-1]

        # Pivots (Classic)
        high = df['High'].values[-1]
        low = df['Low'].values[-1]
        pivot = (high + low + close[-1]) / 3
        r1 = 2*pivot - low
        s1 = 2*pivot - high
        
        # Volume Trend
        # Check if Volume column exists
        if 'Volume' in df.columns:
            vol = df['Volume'].values
            vol_sma_20 = pd.Series(vol).rolling(window=20).mean().iloc[-1]
            vol_trend = "Increasing" if vol[-1] > vol_sma_20 else "Decreasing"
        else:
            vol_trend = "N/A"
            
        # VWAP Trend (Approx)
        # Using Typical Price * Volume / Cumulative Volume for the session. 
        # Since we have daily data, we can't do true intraday VWAP. 
        # We will compare Close to a short term VWAP-like MA or just Typical Price.
        # Let's use TP vs SMA(TP, 20) as a proxy for value trend.
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        tp_sma = tp.rolling(window=20).mean().iloc[-1]
        vwap_signal = "Bullish" if tp.iloc[-1] > tp_sma else "Bearish"

        data = {
            '50DMA': dma_50,
            '200DMA': dma_200,
            'RSI': rsi,
            'MACD': macd_val,
            'MACD_SIGNAL': signal_val,
            'Close': close[-1],
            'Pivot': pivot,
            'R1': r1,
            'S1': s1,
            'Volume_Trend': vol_trend,
            'VWAP_Trend': vwap_signal
        }
        
        return data

    def get_data(self, symbol):
        df = self.fetch_ohlc_history(symbol)
        live_price = self.get_live_price(symbol)
        
        # Try NSE API if yfinance didn't give us a price
        nse_data = None
        if not live_price or live_price == 0:
            logger.info(f"yfinance failed for {symbol}, trying NSE API...")
            nse_data = self.fetch_nse_price(symbol)
            if nse_data:
                live_price = nse_data['price']
        
        # Base Data Structure (Defaults)
        data = {
            '50DMA': 0, '200DMA': 0, 'RSI': 50, 'MACD': 0, 'MACD_SIGNAL': 0,
            'Close': live_price or 0, 'Pivot': 0, 'R1': 0, 'S1': 0,
            'Volume_Trend': 'N/A', 'VWAP_Trend': 'Neutral', 'Live Price': live_price,
            'indicators_available': False,
            'data_source': nse_data['source'] if nse_data else 'Yahoo Finance',
            'data_note': 'Historical data unavailable for technical analysis' if nse_data else None
        }
        
        if df is not None and not df.empty and len(df) >= 30:
            indicators = self.calculate_indicators(df)
            data.update(indicators)
            data['indicators_available'] = True
            data['data_note'] = None  # Clear note if we have full data
            if live_price > 0:
                 data['Live Price'] = live_price
                 data['Close'] = live_price # Prioritize live
        
        return data

