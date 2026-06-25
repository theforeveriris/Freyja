import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from src.database import init_database, get_db
from src.handlers.start import start, help_command
from src.handlers.analyze import analyze, analyze_callback
from src.handlers.expert import expert, expert_callback
from src.handlers.settings import settings, settings_callback
from src.handlers.history import history, view
from src.handlers.delete import delete, delete_all, delete_all_confirm
from config import TELEGRAM_BOT_TOKEN, DB_PATH, AUDIO_DIR, CHARTS_DIR

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context):
    logger.error(f'Update {update} caused error {context.error}')
    try:
        await update.message.reply_text("❌ 发生了错误，请稍后重试")
    except:
        pass

async def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ 错误：未设置 TELEGRAM_BOT_TOKEN 环境变量")
        return
    
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)
    
    db = init_database()
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.bot_data['db'] = db
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('analyze', analyze))
    application.add_handler(CommandHandler('expert', expert))
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CommandHandler('history', history))
    application.add_handler(CommandHandler('view', view))
    application.add_handler(CommandHandler('delete', delete))
    application.add_handler(CommandHandler('deleteall', delete_all))
    
    application.add_handler(CallbackQueryHandler(analyze_callback, pattern='^analyze_'))
    application.add_handler(CallbackQueryHandler(expert_callback, pattern='^expert_'))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern='^settings_'))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_all_confirm))
    
    application.add_error_handler(error_handler)
    
    print("🚀 语音分析机器人已启动！")
    print(f"📊 数据库: {DB_PATH}")
    print(f"🎵 音频目录: {AUDIO_DIR}")
    print(f"📈 图表目录: {CHARTS_DIR}")
    
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
