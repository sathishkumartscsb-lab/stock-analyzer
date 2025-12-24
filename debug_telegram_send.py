import asyncio
from telegram import Bot
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

async def send_test_message():
    print(f"Token: {TELEGRAM_BOT_TOKEN}")
    print(f"Chat ID: {TELEGRAM_CHANNEL_ID}")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("Missing credentials.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        print("Sending message...")
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text="Test message from Stock Analyzer App!")
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_message())
