from telegram import Update
from telegram.ext import CallbackContext
from src.database import get_user_analyses, get_or_create_user
from src.utils import format_number, format_percentage, get_bars

def profile(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    user = get_or_create_user(db, update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
    
    analyses = get_user_analyses(db, user.user_id, limit=100)
    
    if not analyses:
        update.message.reply_text("📭 还没有分析记录，发送语音并使用 `/analyze` 开始分析吧！")
        return
    
    total_analyses = len(analyses)
    
    f0_means = []
    f1_means = []
    f2_means = []
    gender_scores = []
    
    for analysis in analyses:
        if analysis.f0_mean:
            f0_means.append(analysis.f0_mean)
        if analysis.f1_mean:
            f1_means.append(analysis.f1_mean)
        if analysis.f2_mean:
            f2_means.append(analysis.f2_mean)
        if analysis.gender_score:
            gender_scores.append(analysis.gender_score)
    
    avg_f0 = sum(f0_means) / len(f0_means) if f0_means else 0
    avg_f1 = sum(f1_means) / len(f1_means) if f1_means else 0
    avg_f2 = sum(f2_means) / len(f2_means) if f2_means else 0
    avg_gender_score = sum(gender_scores) / len(gender_scores) if gender_scores else 0
    
    gender_desc = "女性化" if avg_gender_score >= 60 else ("男性化" if avg_gender_score <= 40 else "中性")
    
    earliest_date = analyses[-1].analysis_date
    latest_date = analyses[0].analysis_date
    
    report = f"""
👤 **个人档案**

📊 **统计信息**
├ 分析次数: {total_analyses} 次
├ 首次分析: {earliest_date.strftime("%Y-%m-%d")}
└ 最近分析: {latest_date.strftime("%Y-%m-%d %H:%M")}

🎵 **平均音高 (F0)**
└ 平均值: {format_number(avg_f0)} Hz

🎤 **平均共振峰**
├ F1: {format_number(avg_f1)} Hz
├ F2: {format_number(avg_f2)} Hz
└ F2-F1 间距: {format_number(avg_f2 - avg_f1)} Hz

🧭 **平均性别评分**
├ 综合评分: {int(avg_gender_score)}/100 ({gender_desc})
└ 评分趋势: `{get_bars(avg_gender_score)}`

💡 使用 `/compare <id1> <id2>` 对比两次分析结果
"""
    
    update.message.reply_text(report, parse_mode='MarkdownV2')

def compare(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("❌ 请指定两个要对比的记录 ID，如 `/compare 1 2`")
        return
    
    try:
        id1 = int(context.args[0])
        id2 = int(context.args[1])
    except ValueError:
        update.message.reply_text("❌ ID 必须是数字")
        return
    
    db = context.bot_data['db']
    
    analysis1 = db.query(db.query(db.model.Analysis).filter(db.model.Analysis.id == id1).first())
    analysis2 = db.query(db.query(db.model.Analysis).filter(db.model.Analysis.id == id2).first())
    
    analysis1 = analysis1[0] if isinstance(analysis1, list) else analysis1
    analysis2 = analysis2[0] if isinstance(analysis2, list) else analysis2
    
    if not analysis1 or not analysis2:
        update.message.reply_text("❌ 未找到指定记录")
        return
    
    if analysis1.user_id != update.effective_user.id or analysis2.user_id != update.effective_user.id:
        update.message.reply_text("❌ 无权访问该记录")
        return
    
    params1 = analysis1.get_full_params()
    params2 = analysis2.get_full_params()
    
    f0_diff = (params2.get('f0_mean', 0) - params1.get('f0_mean', 0))
    f1_diff = (params2.get('f1_mean', 0) - params1.get('f1_mean', 0))
    f2_diff = (params2.get('f2_mean', 0) - params1.get('f2_mean', 0))
    gender_diff = (params2.get('gender_score', 0) - params1.get('gender_score', 0))
    
    report = f"""
🔄 **对比分析** (#{analysis1.id} ↔ #{analysis2.id})

📅 **时间**
├ #{analysis1.id}: {analysis1.analysis_date.strftime("%Y-%m-%d %H:%M")}
└ #{analysis2.id}: {analysis2.analysis_date.strftime("%Y-%m-%d %H:%M")}

🎵 **音高对比**
├ F0 均值: {format_number(params1.get('f0_mean'))} → {format_number(params2.get('f0_mean'))} ({'↑' if f0_diff > 0 else '↓'}{abs(format_number(f0_diff))} Hz)
├ F0 范围: {format_number(params1.get('f0_min'))}-{format_number(params1.get('f0_max'))} → {format_number(params2.get('f0_min'))}-{format_number(params2.get('f0_max'))}
└ F0 标准差: {format_number(params1.get('f0_std'))} → {format_number(params2.get('f0_std'))}

🎤 **共振峰对比**
├ F1: {format_number(params1.get('f1_mean'))} → {format_number(params2.get('f1_mean'))} ({'↑' if f1_diff > 0 else '↓'}{abs(format_number(f1_diff))} Hz)
├ F2: {format_number(params1.get('f2_mean'))} → {format_number(params2.get('f2_mean'))} ({'↑' if f2_diff > 0 else '↓'}{abs(format_number(f2_diff))} Hz)
└ F3: {format_number(params1.get('f3_mean'))} → {format_number(params2.get('f3_mean'))}

🧭 **性别评分对比**
├ 综合评分: {int(params1.get('gender_score', 0))} → {int(params2.get('gender_score', 0))} ({'↑' if gender_diff > 0 else '↓'}{abs(int(gender_diff))} 分)
├ 基频维度: {format_percentage(params1.get('gender_pitch_pct', 0))} → {format_percentage(params2.get('gender_pitch_pct', 0))}
└ 共振峰维度: {format_percentage(params1.get('gender_formant_pct', 0))} → {format_percentage(params2.get('gender_formant_pct', 0))}
"""
    
    update.message.reply_text(report, parse_mode='MarkdownV2')
