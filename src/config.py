import os

# Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
DB_PATH = os.path.join(DATA_DIR, 'stocks.db')

# APIs / URLs (Placeholders for now)
SCREENER_URL = "https://www.screener.in/company/{}/consolidated/"
MONEYCONTROL_URL = "https://www.moneycontrol.com/"

# Bot Token (Load from env)
# Bot Token (Load from env or direct for local)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8468277745:AAE5EpRJGZOM7Pip8BfHR-_s7UQIUyMIbbM")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-5057435695")

# News API Keys (Free Tiers)
MARKETAUX_API_TOKEN = os.getenv("MARKETAUX_API_TOKEN", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# Scoring Constants
TOTAL_PARAMETERS = 39
