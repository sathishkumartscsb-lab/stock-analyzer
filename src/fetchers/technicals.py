try:
    import talib
except ImportError:
    talib = None
import logging
import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

class TechnicalFetcher:
    def __init__(self):
        pass

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
        
        data = {}
        if df is not None:
            data = self.calculate_indicators(df)
        
        if live_price > 0:
            data['Live Price'] = live_price
            # If the market is open, Close[-1] might be delayed.
            # We don't overwrite Close blindly as it's used for indicators, 
            # but we pass Live Price for display.
            
        return data

