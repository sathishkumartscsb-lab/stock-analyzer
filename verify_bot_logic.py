import asyncio
from unittest.mock import MagicMock, AsyncMock
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.bot.telegram_bot import analyze

async def verify_bot():
    print("Verifying bot logic for /stock command...")
    
    # Mock Update and Context
    update = MagicMock()
    update.effective_chat.id = 12345
    
    context = MagicMock()
    context.args = ['ANANTRAJ']
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    
    # Run Analyze Handler
    try:
        await analyze(update, context)
        print("Analyze handler executed successfully.")
        
        # Verify calls
        context.bot.send_message.assert_called()
        # Verify photo sent (checking if called at all)
        if context.bot.send_photo.called:
            print("SUCCESS: Photo sent call detected.")
            # Verify file cleanup happens afterwards (we can't easily check file open state here but looking at code logic it removes file)
        else:
            print("FAILURE: send_photo was not called.")
            
    except Exception as e:
        print(f"Error during bot logic verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_bot())
