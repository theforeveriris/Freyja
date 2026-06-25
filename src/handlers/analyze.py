import os
import tempfile
import time
import asyncio
import subprocess
import numpy as np
import imageio_ffmpeg
import soundfile as sf
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_or_create_user, create_analysis
from src.handlers.cancel import run_analysis_task
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

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

def _load_audio_fast(ogg_path):
    """用 ffmpeg + soundfile 快速加载 ogg 文件"""
    wav_path = ogg_path.replace('.ogg', '_tmp.wav')
    cmd = [FFMPEG_EXE, '-y', '-i', ogg_path, '-ar', '32000', '-ac', '1', wav_path]
    subprocess.run(cmd, capture_output=True, timeout=30)
    audio_data, sr = sf.read(wav_path, dtype='float32')
    try:
        os.remove(wav_path)
    except OSError:
        pass
    return audio_data, sr

def _do_analysis(temp_path, settings, audio_duration):
    """执行分析（同步函数）"""
    t_total = time.time()
    print(f"[分析] 开始分析", flush=True)

    t0 = time.time()
    audio_data, sr = _load_audio_fast(temp_path)
    print(f"[分析] 加载: {time.time()-t0:.2f}秒, sr={sr}, len={len(audio_data)}", flush=True)

    t0 = time.time()
    preprocessor = AudioPreprocessor(settings['audio'])
    audio_data, sample_rate = preprocessor.process(audio_data, sr)
    print(f"[分析] 预处理: {time.time()-t0:.2f}秒", flush=True)

    voiced_duration = len(audio_data) / sample_rate

    t0 = time.time()
    pitch_tracker = PitchTracker(settings['analysis'])
    pitch_params = pitch_tracker.track(audio_data, sample_rate)
    print(f"[分析] 基频: {time.time()-t0:.2f}秒, f0={pitch_params.get('f0_mean')}", flush=True)

    t0 = time.time()
    formant_analyzer = FormantAnalyzer(settings['analysis'])
    formant_params = formant_analyzer.analyze(audio_data, sample_rate)
    print(f"[分析] 共振峰: {time.time()-t0:.2f}秒", flush=True)

    t0 = time.time()
    spectrum_analyzer = SpectrumAnalyzer(settings['analysis'])
    spectrum_params = spectrum_analyzer.analyze(audio_data, sample_rate)
    print(f"[分析] 频谱: {time.time()-t0:.2f}秒", flush=True)

    t0 = time.time()
    energy_analyzer = EnergyAnalyzer(settings['analysis'])
    energy_params = energy_analyzer.analyze(audio_data, sample_rate)
    print(f"[分析] 能量: {time.time()-t0:.2f}秒", flush=True)

    t0 = time.time()
    quality_analyzer = QualityAnalyzer(settings['analysis'])
    quality_params = quality_analyzer.analyze(audio_data, sample_rate)
    print(f"[分析] 音质: {time.time()-t0:.2f}秒", flush=True)

    t0 = time.time()
    prosody_analyzer = ProsodyAnalyzer(settings['analysis'])
    prosody_params = prosody_analyzer.analyze(audio_data, sample_rate, pitch_params.get('f0_values'))
    print(f"[分析] 韵律: {time.time()-t0:.2f}秒", flush=True)

    t0 = time.time()
    gender_classifier = GenderClassifier(settings['gender'])
    all_params = {
        **pitch_params, **formant_params, **spectrum_params,
        **energy_params, **quality_params, **prosody_params,
        'audio_duration': audio_duration,
        'voiced_duration': voiced_duration,
        'sample_rate': sample_rate
    }
    gender_params = gender_classifier.classify(all_params)
    all_params.update(gender_params)
    print(f"[分析] 性别: {time.time()-t0:.2f}秒", flush=True)

    print(f"[分析] 总耗时: {time.time()-t_total:.2f}秒", flush=True)
    return all_params

async def _run_analysis_threaded(temp_path, settings, duration):
    """在线程池中运行分析（不阻塞事件循环）"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _do_analysis, temp_path, settings, duration)

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message.reply_to_message or not message.reply_to_message.voice:
        await message.reply_text("请回复一条语音消息后再使用 `/analyze` 命令！")
        return

    voice = message.reply_to_message.voice
    duration = voice.duration

    db = context.bot_data['db']
    user = get_or_create_user(db, update.effective_user.id, update.effective_user.username, update.effective_user.first_name)

    settings = user.get_settings()
    max_duration = settings['audio']['max_duration']

    if duration > max_duration:
        await message.reply_text(f"音频时长超过限制（{duration:.1f}秒 > {max_duration}秒），请录制更短的语音！")
        return

    status_msg = await message.reply_text("正在下载并分析音频...请稍候")

    async def _do_analyze():
        try:
            t0 = time.time()
            file = await context.bot.get_file(voice.file_id)
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"voice_{update.effective_user.id}_{voice.file_id}.ogg")
            await file.download_to_drive(temp_path)
            print(f"[分析] 下载耗时: {time.time()-t0:.2f}秒")

            all_params = await _run_analysis_threaded(temp_path, settings, duration)

            t0 = time.time()
            analysis = create_analysis(db, user.user_id, temp_path, all_params)
            print(f"[分析] 保存数据库耗时: {time.time()-t0:.2f}秒")

            try:
                os.remove(temp_path)
            except OSError:
                pass

            report = generate_summary_report(analysis, all_params)
            await status_msg.edit_text(report, parse_mode='Markdown')

        except asyncio.CancelledError:
            await status_msg.edit_text("分析已被取消。")
            try:
                os.remove(temp_path)
            except:
                pass
        except Exception as e:
            await status_msg.edit_text(f"分析失败：{str(e)}")
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()

    await run_analysis_task(update, context, _do_analyze)

async def analyze_callback(update, context):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("分析选项功能开发中...")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    duration = voice.duration

    # 存储 file_id 在 user_data 中，避免 callback_data 超长
    context.user_data['voice_file_id'] = voice.file_id
    context.user_data['voice_duration'] = duration

    keyboard = [
        [InlineKeyboardButton("开始分析", callback_data="voice_analyze")],
        [InlineKeyboardButton("专业分析", callback_data="voice_expert")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"收到语音消息（时长 {duration:.1f} 秒）\n\n选择下方按钮开始分析：",
        reply_markup=reply_markup
    )

async def voice_analyze_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 从 user_data 获取 file_id
    file_id = context.user_data.get('voice_file_id')
    if not file_id:
        await query.edit_message_text("未找到语音文件，请重新发送")
        return

    duration = context.user_data.get('voice_duration', 0)

    db = context.bot_data['db']
    user = get_or_create_user(db, query.from_user.id, query.from_user.username, query.from_user.first_name)

    settings = user.get_settings()

    await query.edit_message_text("正在下载并分析音频...请稍候")

    async def _do_analyze():
        try:
            t0 = time.time()
            file = await context.bot.get_file(file_id)
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"voice_{query.from_user.id}_{file_id}.ogg")
            await file.download_to_drive(temp_path)
            print(f"[分析] 下载耗时: {time.time()-t0:.2f}秒")

            all_params = await _run_analysis_threaded(temp_path, settings, duration)

            t0 = time.time()
            analysis = create_analysis(db, user.user_id, temp_path, all_params)
            print(f"[分析] 保存数据库耗时: {time.time()-t0:.2f}秒")

            try:
                os.remove(temp_path)
            except OSError:
                pass

            report = generate_summary_report(analysis, all_params)
            await query.edit_message_text(report, parse_mode='Markdown')

        except asyncio.CancelledError:
            await query.edit_message_text("分析已被取消。")
            try:
                os.remove(temp_path)
            except:
                pass
        except Exception as e:
            await query.edit_message_text(f"分析失败：{str(e)}")
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()

    await run_analysis_task(query, context, _do_analyze)

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

    report = f"""
**分析完成！#00{analysis.id}**

**基本信息**
├ 总时长: {analysis.audio_duration:.1f} 秒
└ 有效语音: {analysis.voiced_duration:.1f} 秒

**音高 (F0)**
├ 平均: {f0_mean} Hz
├ 范围: {f0_min} - {f0_max} Hz
└ 中位数: {f0_median} Hz

**共振峰**
├ F1: {f1_mean} Hz
├ F2: {f2_mean} Hz
└ F3: {f3_mean} Hz

**响度**
└ 平均 RMS: {rms_mean}

**性别特征评估**
└ 基频维度: `{get_bars(pitch_pct)}` {pitch_pct}% ({gender_desc})

**音高分布**
├ 男性区: `{get_bars(params.get('pitch_male_pct', 0))}` {pitch_male}
├ 女性区: `{get_bars(params.get('pitch_female_pct', 0))}` {pitch_female}
└ 超出区: `{get_bars(params.get('pitch_outside_pct', 0))}` {pitch_outside}

发送 `/expert` 查看专业分析和图表
发送 `/history` 查看历史记录
"""

    return report
