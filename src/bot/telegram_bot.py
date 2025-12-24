from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import logging
import os
from src.config import TELEGRAM_BOT_TOKEN
from src.main import AnalysisEngine, FundamentalFetcher, TechnicalFetcher, NewsFetcher, InfographicGenerator

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome! Use /analyze <STOCK_NAME> to get a report.")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide a stock name. Usage: /analyze TATAMOTORS")
        return

    symbol = context.args[0].upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Analyzing {symbol}... Please wait.")
    
    # Run the pipeline (This is blocking, should ideally be in a thread/process for asyncio, but ok for MVP)
    # 1. Fetch
    ff = FundamentalFetcher()
    fund_data = ff.get_data(symbol)
    
    tf = TechnicalFetcher()
    tech_data = tf.get_data(symbol)
    
    nf = NewsFetcher()
    news_data = nf.fetch_latest_news(symbol)
    
    if not fund_data and not tech_data:
         await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Could not fetch data for {symbol}.")
         return

    # 2. Analyze
    engine = AnalysisEngine()
    result = engine.evaluate_stock(fund_data, tech_data, news_data)
    result['cmp'] = fund_data.get('Current Price') if fund_data else tech_data.get('Close', 0)
    
    # 3. Generate Image
    output_path = f"{symbol}_report.png"
    gen = InfographicGenerator()
    gen.generate_report(symbol, result, output_path)
    
    # 4. Send Image
    caption = (
        f"*{symbol} Analysis*\n"
        f"Score: {result['total_score']:.1f}/37\n"
        f"Risk: {result.get('health_label', 'N/A')}\n"
        f"Swing: {result.get('swing_verdict', 'N/A')}\n"
        f"Long Term: {result.get('long_term_verdict', 'N/A')}"
    )
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(output_path, 'rb'), caption=caption, parse_mode='Markdown')
    
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in config/env.")
        exit(1)
        
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    analyze_handler = CommandHandler('analyze', analyze)
    
    application.add_handler(start_handler)
    application.add_handler(analyze_handler)
    
    print("Bot is polling...")
    application.run_polling()
