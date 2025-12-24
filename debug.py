from src.fetchers.technicals import TechnicalFetcher
tf = TechnicalFetcher()
# Fetch Data for TCS
print("Fetching data for TCS...")
data = tf.get_data("TCS")
print("Data Keys:", data.keys())
print("Live Price:", data.get('Live Price'))
print("Close (History):", data.get('Close'))

if data.get('Live Price', 0) > 0:
    print("SUCCESS: Live Price fetched.")
else:
    print("FAILURE: No Live Price.")
