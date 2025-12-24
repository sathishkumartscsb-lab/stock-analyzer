import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.fetchers.technicals import TechnicalFetcher

def debug_tech(symbol):
    print(f"Fetching technicals for {symbol}...")
    tf = TechnicalFetcher()
    data = tf.get_data(symbol)
    
    if not data:
        print("No data found.")
        return

    print(f"Close: {data.get('Close')}")
    print(f"50DMA: {data.get('50DMA')}")
    print(f"200DMA: {data.get('200DMA')}")
    print(f"Pivot: {data.get('Pivot')}")
    print(f"S1: {data.get('S1')}")
    print(f"R1: {data.get('R1')}")
    
if __name__ == "__main__":
    debug_tech("ANANTRAJ")
