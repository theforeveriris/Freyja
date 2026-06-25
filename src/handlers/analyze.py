import os
import numpy as np
import librosa
from telegram import Update
from telegram.ext import ContextTypes
from src.database import get_or_create_user, create_analysis, get_db
from src.audio import (
    AudioPreprocessor,
    PitchTracker,
    FormantAnalyzer,
    SpectrumAnalyzer,
    EnergyAnalyzer,
    QualityAnalyzer,
    ProsodyAnalyzer,
    GenderClassifier
)
from src.utils import get_bars, format_number, format_percentage

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    if not message.reply_to_message or not message.reply_to_message.voice:
        await message.reply_text("❌ 请回复一条语音消息后再使用 `/analyze` 命令！")
        return
    
    voice = message.reply_to_message.voice
    duration = voice.duration
    
    db = context.bot_data['db']
    user = get_or_create_user(db, update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
    
    settings = user.get_settings()
    max_duration = settings['audio']['max_duration']
    
    if duration > max_duration:
        await message.reply_text(f"❌ 音频时长超过限制（{duration:.1f}秒 > {max_duration}秒），请录制更短的语音！")
        return
    
    await message.reply_text("🔄 正在下载并分析音频...请稍候")
    
    try:
        file = await context.bot.get_file(voice.file_id)
        temp_path = f"/tmp/voice_{update.effective_user.id}_{voice.file_id}.ogg"
        await file.download_to_drive(temp_path)
        
        audio_data, sr = librosa.load(temp_path, sr=None, mono=False)
        
        preprocessor = AudioPreprocessor(settings['audio'])
        audio_data, sample_rate = preprocessor.process(audio_data, sr)
        
        voiced_duration = len(audio_data) / sample_rate
        
        pitch_tracker = PitchTracker(settings['analysis'])
        pitch_params = pitch_tracker.track(audio_data, sample_rate)
        
        formant_analyzer = FormantAnalyzer(settings['analysis'])
        formant_params = formant_analyzer.analyze(audio_data, sample_rate)
        
        spectrum_analyzer = SpectrumAnalyzer(settings['analysis'])
        spectrum_params = spectrum_analyzer.analyze(audio_data, sample_rate)
        
        energy_analyzer = EnergyAnalyzer(settings['analysis'])
        energy_params = energy_analyzer.analyze(audio_data, sample_rate)
        
        quality_analyzer = QualityAnalyzer(settings['analysis'])
        quality_params = quality_analyzer.analyze(audio_data, sample_rate)
        
        prosody_analyzer = ProsodyAnalyzer(settings['analysis'])
        prosody_params = prosody_analyzer.analyze(audio_data, sample_rate, pitch_params.get('f0_values'))
        
        gender_classifier = GenderClassifier(settings['gender'])
        all_params = {
            **pitch_params,
            **formant_params,
            **spectrum_params,
            **energy_params,
            **quality_params,
            **prosody_params,
            'audio_duration': duration,
            'voiced_duration': voiced_duration,
            'sample_rate': sample_rate
        }
        gender_params = gender_classifier.classify(all_params)
        
        all_params.update(gender_params)
        
        analysis = create_analysis(db, user.user_id, temp_path, all_params)
        
        os.remove(temp_path)
        
        report = generate_summary_report(analysis, all_params)
        
        await message.reply_text(report, parse_mode='MarkdownV2')
        
    except Exception as e:
        await message.reply_text(f"❌ 分析失败：{str(e)}")
        print(f"Error during analysis: {e}")

async def analyze_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text("🔍 分析选项功能开发中...")

def generate_summary_report(analysis, params):
    f0_mean = format_number(params.get('f0_mean'))
    f0_min = format_number(params.get('f0_min'))
    f0_max = format_number(params.get('f0_max'))
    f0_median = format_number(params.get('f0_median'))
    
    f1_mean = format_number(params.get('f1_mean'))
    f2_mean = format_number(params.get('f2_mean'))
    f3_mean = format_number(params.get('f3_mean'))
    
    rms_mean = format_number(params.get('rms_mean'), 2)
    
    gender_score = int(params.get('gender_score', 0))
    gender_desc = "女性化" if gender_score >= 60 else ("男性化" if gender_score <= 40 else "中性")
    
    pitch_male = format_percentage(params.get('pitch_male_pct', 0))
    pitch_female = format_percentage(params.get('pitch_female_pct', 0))
    pitch_outside = format_percentage(params.get('pitch_outside_pct', 0))
    
    pitch_pct = int(params.get('gender_pitch_pct', 0))
    formant_pct = int(params.get('gender_formant_pct', 0))
    timbre_pct = int(params.get('gender_timbre_pct', 0))
    prosody_pct = int(params.get('gender_prosody_pct', 0))
    quality_pct = int(params.get('gender_quality_pct', 0))
    
    report = f"""
✅ **分析完成！#00{analysis.id}**

📊 **基本信息**
├ 总时长: {analysis.audio_duration:.1f} 秒
└ 有效语音: {analysis.voiced_duration:.1f} 秒

🎵 **音高 (F0)**
├ 平均: {f0_mean} Hz
├ 范围: {f0_min} - {f0_max} Hz
└ 中位数: {f0_median} Hz

🎤 **共振峰**
├ F1: {f1_mean} Hz
├ F2: {f2_mean} Hz
└ F3: {f3_mean} Hz

🔊 **响度**
└ 平均 RMS: {rms_mean}

🧭 **性别特征评估**
├ 综合评分: {gender_score}/100 ({gender_desc})
├ 基频维度: `{get_bars(pitch_pct)}` {pitch_pct}%
├ 共振峰维度: `{get_bars(formant_pct)}` {formant_pct}%
├ 音色维度: `{get_bars(timbre_pct)}` {timbre_pct}%
├ 韵律维度: `{get_bars(prosody_pct)}` {prosody_pct}%
└ 音质维度: `{get_bars(quality_pct)}` {quality_pct}%

📈 **音高分布**
├ 男性区: `{get_bars(params.get('pitch_male_pct', 0))}` {pitch_male}
├ 女性区: `{get_bars(params.get('pitch_female_pct', 0))}` {pitch_female}
└ 超出区: `{get_bars(params.get('pitch_outside_pct', 0))}` {pitch_outside}

💡 发送 `/expert` 查看专业分析和图表
发送 `/history` 查看历史记录
"""
    
    return report
