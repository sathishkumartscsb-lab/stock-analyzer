from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.config import TELEGRAM_BOT_TOKEN
from src.main import AnalysisEngine, FundamentalFetcher, TechnicalFetcher, NewsFetcher, InfographicGenerator

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome! Type any stock name (e.g., TATAMOTORS) to get a full analysis report.")

async def analyze_stock(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
    cid = update.effective_chat.id
    try:
        logging.info(f"Starting analysis for {symbol}")
        # 1. Fetch
        ff = FundamentalFetcher()
        logging.info(f"[{symbol}] Fetching fundamentals...")
        fund_data = ff.get_data(symbol)
        
        tf = TechnicalFetcher()
        logging.info(f"[{symbol}] Fetching technicals...")
        tech_data = tf.get_data(symbol)
        
        nf = NewsFetcher()
        logging.info(f"[{symbol}] Fetching news...")
        news_data = nf.fetch_latest_news(symbol)
        
        if not fund_data and not tech_data:
             await context.bot.send_message(chat_id=cid, text=f"⚠️ Could not fetch data for {symbol}. Please verify the ticker.")
             return

        # 2. Analyze
        logging.info(f"[{symbol}] Evaluating stock...")
        engine = AnalysisEngine()
        result = engine.evaluate_stock(fund_data, tech_data, news_data)
        result['cmp'] = fund_data.get('Current Price') if fund_data else tech_data.get('Close', 0)
        result['news_items'] = news_data  # Pass news to infographic
        
        # 3. Generate Image
        logging.info(f"[{symbol}] Generating infographic...")
        output_path = f"{symbol}_report.png"
        gen = InfographicGenerator()
        gen.generate_report(symbol, result, output_path)
        
        # 4. Send Image
        logging.info(f"[{symbol}] Sending photo to chat...")
        caption = (
            f"📊 *{symbol} Analysis*\n"
            f"Score: {result['total_score']:.1f}/39\n"
            f"Risk: {result.get('health_label', 'N/A')}\n"
            f"Swing: {result.get('swing_verdict', 'N/A')}\n"
            f"Long Term: {result.get('long_term_verdict', 'N/A')}"
        )
        
        with open(output_path, 'rb') as photo:
            await context.bot.send_photo(chat_id=cid, photo=photo, caption=caption, parse_mode='Markdown')
        
        logging.info(f"[{symbol}] Finished analysis successfully.")
        
    except Exception as e:
        logging.error(f"Error analyzing {symbol}: {str(e)}", exc_info=True)
        await context.bot.send_message(chat_id=cid, text=f"❌ Error analyzing {symbol}: {str(e)}")
    finally:
        # Cleanup
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide a stock name. Usage: /analyze TATAMOTORS")
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Analyzing {context.args[0].upper()}... Please wait.")
    await analyze_stock(update, context, context.args[0].upper())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    logging.info(f"Received message: {text}")
    
    # 1. Try as direct ticker if it matches the pattern
    import re
    ff = FundamentalFetcher()
    if re.match(r'^[A-Za-z0-9&.\-]+$', text):
        symbol = text.upper()
        # Peek at data to see if it's a real ticker
        # We'll just try to analyze it. If it fails, we fall through to search.
        # But wait, analyze_stock is async and does its own messaging.
        # Let's check data first
        logging.info(f"Checking if {symbol} is a direct ticker...")
        fund_data = ff.get_data(symbol)
        tf = TechnicalFetcher()
        tech_data = tf.get_data(symbol)
        
        if fund_data or (tech_data and tech_data.get('indicators_available')):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🔍 Analyzing ticker {symbol}... Please wait.")
            await analyze_stock(update, context, symbol)
            return
        else:
            logging.info(f"{symbol} not found as direct ticker. Trying search...")

    # 2. Treat as Name Search (or fallback from failed ticker)
    results = ff.search_ticker(text)
    
    if not results:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Could not find any stock matching '{text}'. Please try a different name or ticker.")
    elif len(results) == 1:
        name, symbol = results[0]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🎯 Found: *{name}* ({symbol})\nAnalyzing now...", parse_mode='Markdown')
        await analyze_stock(update, context, symbol)
    else:
        best_name, best_symbol = results[0]
        suggestions = "\n".join([f"• `{r[1]}` ({r[0]})" for r in results[1:5]])
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f"🤔 Found multiple matches for '{text}'.\n\nI'll analyze the best match: *{best_name}* (`{best_symbol}`)\n\nOther possibilities:\n{suggestions}",
            parse_mode='Markdown'
        )
        await analyze_stock(update, context, best_symbol)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in config/env.")
        exit(1)
        
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    analyze_handler = CommandHandler('analyze', analyze_command)
    stock_handler = CommandHandler('stock', analyze_command)
    
    # Text handler for direct symbols
    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(analyze_handler)
    application.add_handler(stock_handler)
    application.add_handler(text_handler)
    
    print("Bot is polling...")
    application.run_polling()
