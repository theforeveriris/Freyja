import os
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram import BotCommandScopeAllPrivateChats
from src.database import init_database, SessionLocal
from src.handlers.start import start, help_command
from src.handlers.analyze import analyze, analyze_callback, voice_handler, voice_analyze_callback
from src.handlers.cancel import cancel_command
from src.handlers.expert import expert, expert_callback
from src.handlers.settings import (
    settings,
    settings_callback,
    setting_parameter_callback,
    setting_option_callback,
    reset_settings,
    reset_settings_confirm
)
from src.handlers.history import history, view
from src.handlers.delete import delete, delete_all, delete_all_confirm
from src.handlers.profile import profile, compare
from config import TELEGRAM_BOT_TOKEN, DB_PATH, AUDIO_DIR, CHARTS_DIR

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f'Update {update} caused error {context.error}', exc_info=context.error)
    try:
        if update.message:
            await update.message.reply_text("发生了错误，请稍后重试")
        elif update.callback_query:
            await update.callback_query.answer("发生了错误", show_alert=True)
    except:
        pass

async def post_init(application):
    commands = [
        BotCommand('start', '开始使用'),
        BotCommand('help', '查看帮助'),
        BotCommand('analyze', '分析语音'),
        BotCommand('expert', '专业分析菜单'),
        BotCommand('cancel', '取消当前任务'),
        BotCommand('settings', '设置菜单'),
        BotCommand('history', '历史记录'),
        BotCommand('profile', '个人档案'),
        BotCommand('compare', '对比分析结果'),
        BotCommand('view', '查看详情'),
        BotCommand('delete', '删除记录'),
        BotCommand('deleteall', '删除所有记录'),
        BotCommand('reset_settings', '重置设置'),
    ]
    await application.bot.set_my_commands(commands)
    await application.bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())
    print("命令菜单已设置")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("错误：未设置 TELEGRAM_BOT_TOKEN 环境变量")
        return
    
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)
    
    init_database()
    db = SessionLocal()
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    application.bot_data['db'] = db
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('analyze', analyze))
    application.add_handler(CommandHandler('expert', expert))
    application.add_handler(CommandHandler('cancel', cancel_command))
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CommandHandler('history', history))
    application.add_handler(CommandHandler('view', view))
    application.add_handler(CommandHandler('delete', delete))
    application.add_handler(CommandHandler('deleteall', delete_all))
    application.add_handler(CommandHandler('profile', profile))
    application.add_handler(CommandHandler('compare', compare))
    application.add_handler(CommandHandler('reset_settings', reset_settings))
    
    application.add_handler(CallbackQueryHandler(analyze_callback, pattern='^analyze_'))
    application.add_handler(CallbackQueryHandler(voice_analyze_callback, pattern='^voice_analyze$'))
    application.add_handler(CallbackQueryHandler(expert_callback, pattern='^expert_'))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern='^settings_'))
    application.add_handler(CallbackQueryHandler(setting_parameter_callback, pattern='^setting_'))
    application.add_handler(CallbackQueryHandler(setting_option_callback, pattern='^option_'))
    
    async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await delete_all_confirm(update, context)
        await reset_settings_confirm(update, context)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    
    application.add_error_handler(error_handler)
    
    print("语音分析机器人已启动！")
    print(f"数据库: {DB_PATH}")
    print(f"音频目录: {AUDIO_DIR}")
    print(f"图表目录: {CHARTS_DIR}")
    
    application.run_polling()

if __name__ == '__main__':
    main()
