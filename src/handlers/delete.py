import os
from telegram import Update
from telegram.ext import ContextTypes
from src.database import delete_analysis, delete_all_analyses, get_analysis_by_id, get_db
from config import AUDIO_DIR, CHARTS_DIR

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ 请指定要删除的记录 ID，如 `/delete 1`")
        return
    
    try:
        analysis_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID 必须是数字")
        return
    
    db = context.bot_data['db']
    analysis = get_analysis_by_id(db, analysis_id)
    
    if not analysis or analysis.user_id != update.effective_user.id:
        await update.message.reply_text("❌ 未找到该记录")
        return
    
    audio_path = analysis.audio_path
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    charts_dir = os.path.join(CHARTS_DIR, str(update.effective_user.id), str(analysis_id))
    if os.path.exists(charts_dir):
        import shutil
        shutil.rmtree(charts_dir)
    
    delete_analysis(db, analysis_id)
    
    await update.message.reply_text(f"🗑️ 已删除记录 #{analysis_id}")

async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    
    await update.message.reply_text(
        "⚠️ **警告**：此操作将删除所有分析记录，包括音频文件和图表！\n\n"
        "请回复 `确认删除` 来确认此操作，或发送任意其他消息取消。",
        parse_mode='MarkdownV2'
    )
    
    context.user_data['delete_all_pending'] = True

async def delete_all_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('delete_all_pending'):
        return
    
    if update.message.text == '确认删除':
        db = context.bot_data['db']
        
        user_audio_dir = os.path.join(AUDIO_DIR, str(update.effective_user.id))
        if os.path.exists(user_audio_dir):
            import shutil
            shutil.rmtree(user_audio_dir)
        
        user_charts_dir = os.path.join(CHARTS_DIR, str(update.effective_user.id))
        if os.path.exists(user_charts_dir):
            import shutil
            shutil.rmtree(user_charts_dir)
        
        delete_all_analyses(db, update.effective_user.id)
        
        await update.message.reply_text("🗑️ 已清空所有分析记录")
    else:
        await update.message.reply_text("✅ 操作已取消")
    
    context.user_data['delete_all_pending'] = False
