from telegram import Update
from telegram.ext import ContextTypes
from src.database import get_user_analyses, get_analysis_by_id
from src.utils import get_bars, format_number

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    analyses = get_user_analyses(db, update.effective_user.id, limit=20)
    
    if not analyses:
        await update.message.reply_text("📭 还没有分析记录，发送语音并使用 `/analyze` 开始分析吧！")
        return
    
    message = "📜 **历史分析记录**\n\n"
    for i, analysis in enumerate(analyses, 1):
        date_str = analysis.analysis_date.strftime("%m-%d %H:%M")
        gender_score = int(analysis.gender_score) if analysis.gender_score else 0
        bars = get_bars(gender_score)
        
        message += f"#{analysis.id} | {date_str} | {analysis.audio_duration:.1f}秒\n"
        message += f"   评分: {gender_score}/100 `{bars}`\n"
        message += f"   F0: {format_number(analysis.f0_mean)}Hz | F1-F2-F3: "
        message += f"{format_number(analysis.f1_mean)}-{format_number(analysis.f2_mean)}-{format_number(analysis.f3_mean)}Hz\n\n"
    
    message += "💡 使用 `/view <id>` 查看详细报告，使用 `/expert <id>` 获取专业分析"
    
    await update.message.reply_text(message, parse_mode='MarkdownV2')

async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ 请指定记录 ID，如 `/view 1`")
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
    
    params = analysis.get_full_params()
    
    f0_mean = format_number(params.get('f0_mean'))
    f0_min = format_number(params.get('f0_min'))
    f0_max = format_number(params.get('f0_max'))
    
    f1_mean = format_number(params.get('f1_mean'))
    f2_mean = format_number(params.get('f2_mean'))
    f3_mean = format_number(params.get('f3_mean'))
    
    gender_score = int(params.get('gender_score', 0))
    gender_desc = "女性化" if gender_score >= 60 else ("男性化" if gender_score <= 40 else "中性")
    
    pitch_male = format_number(params.get('pitch_male_pct', 0), 1)
    pitch_female = format_number(params.get('pitch_female_pct', 0), 1)
    
    report = f"""
📋 **记录 #00{analysis.id}**

📅 分析时间: {analysis.analysis_date.strftime("%Y-%m-%d %H:%M:%S")}
⏱️ 时长: {analysis.audio_duration:.1f} 秒

🎵 **音高 (F0)**
├ 平均: {f0_mean} Hz
├ 范围: {f0_min} - {f0_max} Hz
└ 标准差: {format_number(params.get('f0_std'))} Hz

🎤 **共振峰**
├ F1: {f1_mean} Hz
├ F2: {f2_mean} Hz
└ F3: {f3_mean} Hz

🔊 **能量**
└ RMS: {format_number(params.get('rms_mean'), 2)}

🧭 **性别评估**
├ 综合评分: {gender_score}/100 ({gender_desc})
├ 基频: {format_number(params.get('gender_pitch_pct', 0), 1)}%
├ 共振峰: {format_number(params.get('gender_formant_pct', 0), 1)}%
└ 音高分布: 男{pitch_male}% / 女{pitch_female}%

💡 发送 `/expert {analysis.id}` 获取专业分析和图表
"""
    
    await update.message.reply_text(report, parse_mode='MarkdownV2')
