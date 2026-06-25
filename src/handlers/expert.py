import os
import asyncio
import numpy as np
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_analysis_by_id, get_or_create_user, get_user_analyses
from src.visualizer import Visualizer
from src.utils import get_user_charts_dir, format_number, format_percentage

EXPERT_CATEGORIES = {
    'pitch': {'name': '基频详细分析', 'description': 'F0分布 / Jitter / 音高轮廓图'},
    'formant': {'name': '共振峰详细分析', 'description': 'F1-F3轨迹 / 共振峰比 / 元音图'},
    'spectrum': {'name': '频谱特征分析', 'description': '质心 / 滚降 / 通量 / 语谱图'},
    'energy': {'name': '能量与响度分析', 'description': 'RMS / 动态范围 / 能量包络'},
    'quality': {'name': '音质与稳定性', 'description': 'Shimmer / HNR / APQ / ZCR'},
    'prosody': {'name': '发声模式分析', 'description': 'VOT / 开商 / 气息声 / 起音'},
    'gender': {'name': '性别特征深度分析', 'description': '五维雷达图 / 详细解读'},
    'charts_all': {'name': '全部可视化图表', 'description': '一次性发送所有12张图'}
}

async def expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data['db']
    user = get_or_create_user(db, update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
    
    if context.args:
        try:
            analysis_id = int(context.args[0])
            analysis = get_analysis_by_id(db, analysis_id)
            if not analysis or analysis.user_id != user.user_id:
                await update.message.reply_text(" 未找到该记录")
                return
        except ValueError:
            await update.message.reply_text(" ID 必须是数字")
            return
    else:
        analyses = get_user_analyses(db, user.user_id, limit=1)
        analysis = analyses[0] if analyses else None
        if not analysis:
            await update.message.reply_text(" 没有可用的分析记录，请先使用 `/analyze` 分析语音")
            return
    
    context.user_data['expert_analysis_id'] = analysis.id
    
    keyboard = [
        [InlineKeyboardButton(f"{EXPERT_CATEGORIES[key]['name']}\n{EXPERT_CATEGORIES[key]['description']}", callback_data=f"expert_{key}")]
        for key in EXPERT_CATEGORIES
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f" **#00{analysis.id} 专业分析菜单**\n\n请选择要查看的详细项目：",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def expert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        db = context.bot_data['db']
        user = get_or_create_user(db, query.from_user.id, query.from_user.username, query.from_user.first_name)
        
        analysis_id = context.user_data.get('expert_analysis_id')
        if not analysis_id:
            await query.edit_message_text("未找到分析记录")
            return
        
        analysis = get_analysis_by_id(db, analysis_id)
        if not analysis:
            await query.edit_message_text("记录已被删除")
            return
        
        params = analysis.get_full_params()
        settings = user.get_settings()
        
        category = query.data.replace('expert_', '')
        print(f"[expert] category={category}, analysis_id={analysis_id}", flush=True)
        
        if category == 'charts_all':
            await send_all_charts(query, analysis, params, settings)
        else:
            await send_category_report(query, analysis, params, settings, category)
    except Exception as e:
        import traceback
        import io
        buf = io.StringIO()
        traceback.print_exc(file=buf)
        error_msg = buf.getvalue()
        print(f"[expert] 错误: {e}", flush=True)
        print(f"[expert] 堆栈:\n{error_msg}", flush=True)
        try:
            await query.message.reply_text(f"处理失败: {e}")
        except Exception as e2:
            print(f"[expert] 发送错误消息也失败了: {e2}", flush=True)

async def send_category_report(query, analysis, params, settings, category):
    print(f"[expert] send_category_report start: category={category}", flush=True)
    visualizer = Visualizer(settings['charts'])
    charts_dir = get_user_charts_dir(query.from_user.id, analysis.id)
    print(f"[expert] charts_dir={charts_dir}", flush=True)
    
    report = ""
    
    if category == 'pitch':
        report = f"""
 **基频详细分析**

 **F0 统计**
├ 均值: {format_number(params.get('f0_mean'))} Hz
├ 中位数: {format_number(params.get('f0_median'))} Hz
├ 范围: {format_number(params.get('f0_min'))} - {format_number(params.get('f0_max'))} Hz
├ 标准差: {format_number(params.get('f0_std'))} Hz
└ 变异系数: {format_number(params.get('f0_cv'), 3)}

 **Jitter (基频微扰)**
├ Local: {format_percentage(params.get('jitter_local'), 2)}
└ RAP: {format_percentage(params.get('jitter_rap'), 2)}

 **百分位分布**
├ 5%: {format_number(params.get('f0_percentiles', [0]*5)[0])} Hz
├ 25%: {format_number(params.get('f0_percentiles', [0]*5)[1])} Hz
├ 50%: {format_number(params.get('f0_percentiles', [0]*5)[2])} Hz
├ 75%: {format_number(params.get('f0_percentiles', [0]*5)[3])} Hz
└ 95%: {format_number(params.get('f0_percentiles', [0]*5)[4])} Hz
"""
        
        f0_values = np.array(params.get('f0_values', []))
        print(f"[expert] pitch: f0_values len={len(f0_values)}", flush=True)
        if len(f0_values) > 0:
            pitch_contour_path = os.path.join(charts_dir, 'pitch_contour.png')
            print(f"[expert] pitch: generating contour...", flush=True)
            await asyncio.to_thread(visualizer.plot_pitch_contour, f0_values, analysis.sample_rate, pitch_contour_path)
            print(f"[expert] pitch: contour done", flush=True)
            
            pitch_hist_path = os.path.join(charts_dir, 'pitch_histogram.png')
            male_range = settings['gender']['male_f0_range']
            female_range = settings['gender']['female_f0_range']
            print(f"[expert] pitch: generating histogram...", flush=True)
            await asyncio.to_thread(visualizer.plot_pitch_histogram, f0_values, pitch_hist_path, male_range, female_range)
            print(f"[expert] pitch: histogram done", flush=True)
            
            print(f"[expert] pitch: sending report...", flush=True)
            await query.message.reply_text(report, parse_mode='Markdown')
            print(f"[expert] pitch: report sent", flush=True)
            await query.message.reply_photo(open(pitch_contour_path, 'rb'), caption='基频轮廓图')
            print(f"[expert] pitch: contour photo sent", flush=True)
            await query.message.reply_photo(open(pitch_hist_path, 'rb'), caption='基频分布直方图')
            print(f"[expert] pitch: all done", flush=True)
        else:
            await query.message.reply_text(report, parse_mode='Markdown')
    
    elif category == 'formant':
        report = f"""
 **共振峰详细分析**

 **共振峰频率**
├ F1: {format_number(params.get('f1_mean'))} Hz (喉部开放度)
├ F2: {format_number(params.get('f2_mean'))} Hz (舌位前后)
└ F3: {format_number(params.get('f3_mean'))} Hz (音色明亮度)

 **共振峰统计**
├ F1 标准差: {format_number(params.get('f1_std'))} Hz
├ F2 标准差: {format_number(params.get('f2_std'))} Hz
└ F3 标准差: {format_number(params.get('f3_std'))} Hz

 **共振峰关系**
├ F2-F1 间距: {format_number(params.get('f2_f1_diff'))} Hz
├ F2/F1 比值: {format_number(params.get('f2_f1_ratio'), 2)}
└ F3/F2 比值: {format_number(params.get('f3_f2_ratio'), 2)}
"""
        
        f1_values = params.get('f1_values', [])
        f2_values = params.get('f2_values', [])
        f3_values = params.get('f3_values', [])
        
        if len(f1_values) > 0:
            formant_path = os.path.join(charts_dir, 'formants.png')
            await asyncio.to_thread(visualizer.plot_formants, f1_values, f2_values, f3_values, analysis.sample_rate, formant_path)
            
            scatter_path = os.path.join(charts_dir, 'formant_scatter.png')
            await asyncio.to_thread(visualizer.plot_formant_scatter, f1_values, f2_values, scatter_path)
            
            await query.message.reply_text(report, parse_mode='Markdown')
            await query.message.reply_photo(open(formant_path, 'rb'), caption='共振峰轨迹图')
            await query.message.reply_photo(open(scatter_path, 'rb'), caption='共振峰散点图')
        else:
            await query.message.reply_text(report, parse_mode='Markdown')
    
    elif category == 'spectrum':
        report = f"""
 **频谱特征分析**

 **频谱质心 (明亮度)**
├ 均值: {format_number(params.get('spectral_centroid_mean'))} Hz
└ 标准差: {format_number(params.get('spectral_centroid_std'))} Hz

 **频谱滚降**
├ 均值: {format_number(params.get('spectral_rolloff_mean'))} Hz
└ 标准差: {format_number(params.get('spectral_rolloff_std'))} Hz

 **其他频谱特征**
├ 频谱带宽: {format_number(params.get('spectral_bandwidth_mean'))} Hz
├ 频谱通量均值: {format_number(params.get('spectral_flux_mean'), 3)}
└ 频谱通量标准差: {format_number(params.get('spectral_flux_std'), 3)}
"""
        
        await query.message.reply_text(report, parse_mode='Markdown')
    
    elif category == 'energy':
        report = f"""
 **能量与响度分析**

 **RMS 能量**
├ 均值: {format_number(params.get('rms_mean'), 3)}
└ 标准差: {format_number(params.get('rms_std'), 3)}

 **动态范围**
├ 动态范围: {format_number(params.get('dynamic_range'))} dB
├ 峰值振幅: {format_number(params.get('peak_amplitude'), 3)}
└ 能量变化率: {format_number(params.get('energy_rate'), 4)}

 **能量百分位**
├ 10%: {format_number(params.get('energy_percentiles', [0]*5)[0], 3)}
├ 25%: {format_number(params.get('energy_percentiles', [0]*5)[1], 3)}
├ 50%: {format_number(params.get('energy_percentiles', [0]*5)[2], 3)}
├ 75%: {format_number(params.get('energy_percentiles', [0]*5)[3], 3)}
└ 90%: {format_number(params.get('energy_percentiles', [0]*5)[4], 3)}
"""
        
        energy_values = np.array(params.get('energy_envelope', []))
        if len(energy_values) > 0:
            energy_path = os.path.join(charts_dir, 'energy_envelope.png')
            await asyncio.to_thread(visualizer.plot_energy_envelope, energy_values, analysis.sample_rate, energy_path)
            await query.message.reply_text(report, parse_mode='Markdown')
            await query.message.reply_photo(open(energy_path, 'rb'), caption='能量包络图')
        else:
            await query.message.reply_text(report, parse_mode='Markdown')
    
    elif category == 'quality':
        report = f"""
 **音质与稳定性分析**

 **Shimmer (振幅微扰)**
├ Local: {format_percentage(params.get('shimmer_local'), 2)}
└ APQ3: {format_percentage(params.get('shimmer_apq3'), 2)}

 **谐噪比 (HNR)**
└ HNR: {format_number(params.get('hnr'))} dB

 **非周期性指标**
├ APQ: {format_percentage(params.get('apq'), 1)}
├ 过零率均值: {format_number(params.get('zcr_mean'), 3)}
├ 过零率标准差: {format_number(params.get('zcr_std'), 3)}
└ 自相关峰值: {format_number(params.get('autocorrelation_peak'), 3)}
"""
        
        await query.message.reply_text(report, parse_mode='Markdown')
    
    elif category == 'prosody':
        report = f"""
 **语言节奏与语调分析**

 **语速**
├ 每秒音节数: {format_number(params.get('speech_rate'), 2)}
└ 音节总数: {params.get('onset_count', 0)}

 **停顿模式**
├ 停顿次数: {params.get('pause_count', 0)}
└ 平均停顿时长: {format_number(params.get('avg_pause_duration'), 2)} 秒

 **语调特征**
├ 语调范围: {format_number(params.get('intonation_range'))} Hz
└ 平均语调: {format_number(params.get('intonation_mean'))} Hz
"""
        
        await query.message.reply_text(report, parse_mode='Markdown')
    
    elif category == 'gender':
        report = f"""
 **性别特征深度分析**

 **各维度评分**
├ 基频维度: {format_percentage(params.get('gender_pitch_pct', 0))}
├ 共振峰维度: {format_percentage(params.get('gender_formant_pct', 0))}
├ 音色维度: {format_percentage(params.get('gender_timbre_pct', 0))}
├ 韵律维度: {format_percentage(params.get('gender_prosody_pct', 0))}
└ 音质维度: {format_percentage(params.get('gender_quality_pct', 0))}

 **综合评估**
└ 综合评分: {int(params.get('gender_score', 0))}/100

 **权重配置**
├ 基频: {settings['gender']['weights']['pitch']}%
├ 共振峰: {settings['gender']['weights']['formant']}%
├ 音色: {settings['gender']['weights']['timbre']}%
├ 韵律: {settings['gender']['weights']['prosody']}%
└ 音质: {settings['gender']['weights']['quality']}%
"""
        
        radar_path = os.path.join(charts_dir, 'gender_radar.png')
        await asyncio.to_thread(visualizer.plot_gender_radar, params, radar_path)
        
        await query.message.reply_text(report, parse_mode='Markdown')
        await query.message.reply_photo(open(radar_path, 'rb'), caption='性别特征雷达图')

async def send_all_charts(query, analysis, params, settings):
    visualizer = Visualizer(settings['charts'])
    charts_dir = get_user_charts_dir(query.from_user.id, analysis.id)
    
    await query.message.reply_text(" 正在生成所有图表...请稍候")
    
    try:
        import librosa
        audio_data, sr = await asyncio.to_thread(librosa.load, analysis.audio_path, sr=None)
        
        waveform_path = os.path.join(charts_dir, 'waveform.png')
        await asyncio.to_thread(visualizer.plot_waveform, audio_data, sr, waveform_path)
        await query.message.reply_photo(open(waveform_path, 'rb'), caption='波形图')
        
        spectrogram_path = os.path.join(charts_dir, 'spectrogram.png')
        await asyncio.to_thread(visualizer.plot_spectrogram, audio_data, sr, spectrogram_path)
        await query.message.reply_photo(open(spectrogram_path, 'rb'), caption='语谱图')
        
        f0_values = np.array(params.get('f0_values', []))
        if len(f0_values) > 0:
            pitch_contour_path = os.path.join(charts_dir, 'pitch_contour.png')
            await asyncio.to_thread(visualizer.plot_pitch_contour, f0_values, sr, pitch_contour_path)
            await query.message.reply_photo(open(pitch_contour_path, 'rb'), caption='基频轮廓图')
            
            pitch_hist_path = os.path.join(charts_dir, 'pitch_histogram.png')
            male_range = settings['gender']['male_f0_range']
            female_range = settings['gender']['female_f0_range']
            await asyncio.to_thread(visualizer.plot_pitch_histogram, f0_values, pitch_hist_path, male_range, female_range)
            await query.message.reply_photo(open(pitch_hist_path, 'rb'), caption='基频分布直方图')
        
        f1_values = params.get('f1_values', [])
        f2_values = params.get('f2_values', [])
        f3_values = params.get('f3_values', [])
        if len(f1_values) > 0:
            formant_path = os.path.join(charts_dir, 'formants.png')
            await asyncio.to_thread(visualizer.plot_formants, f1_values, f2_values, f3_values, sr, formant_path)
            await query.message.reply_photo(open(formant_path, 'rb'), caption='共振峰轨迹图')
            
            scatter_path = os.path.join(charts_dir, 'formant_scatter.png')
            await asyncio.to_thread(visualizer.plot_formant_scatter, f1_values, f2_values, scatter_path)
            await query.message.reply_photo(open(scatter_path, 'rb'), caption='共振峰散点图')
        
        energy_values = np.array(params.get('energy_envelope', []))
        if len(energy_values) > 0:
            energy_path = os.path.join(charts_dir, 'energy_envelope.png')
            await asyncio.to_thread(visualizer.plot_energy_envelope, energy_values, sr, energy_path)
            await query.message.reply_photo(open(energy_path, 'rb'), caption='能量包络图')
        
        centroid_values = np.array(params.get('spectral_centroid_values', []))
        if len(centroid_values) > 0:
            centroid_path = os.path.join(charts_dir, 'spectral_centroid.png')
            await asyncio.to_thread(visualizer.plot_spectral_centroid, centroid_values, sr, centroid_path)
            await query.message.reply_photo(open(centroid_path, 'rb'), caption='频谱质心时变图')
        
        mel_spec_path = os.path.join(charts_dir, 'mel_spectrogram.png')
        await asyncio.to_thread(visualizer.plot_mel_spectrogram, audio_data, sr, mel_spec_path)
        await query.message.reply_photo(open(mel_spec_path, 'rb'), caption='梅尔频谱图')
        
        mfcc_values = params.get('mfcc_values', [])
        if len(mfcc_values) > 0:
            mfcc_path = os.path.join(charts_dir, 'mfcc.png')
            await asyncio.to_thread(visualizer.plot_mfcc, mfcc_values, mfcc_path)
            await query.message.reply_photo(open(mfcc_path, 'rb'), caption='MFCC 热力图')
        
        radar_path = os.path.join(charts_dir, 'gender_radar.png')
        await asyncio.to_thread(visualizer.plot_gender_radar, params, radar_path)
        await query.message.reply_photo(open(radar_path, 'rb'), caption='性别特征雷达图')
        
        await query.message.reply_text(" 所有图表已发送完毕！")
        
    except Exception as e:
        await query.message.reply_text(f" 图表生成失败：{str(e)}")
        print(f"Error generating charts: {e}")
