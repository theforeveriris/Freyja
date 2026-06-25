import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from src.database import get_or_create_user
from config import DEFAULT_SETTINGS

SETTING_CATEGORIES = {
    'audio': {'name': '🎵 音频预处理设置', 'description': '采样率、声道数、VAD灵敏度等'},
    'analysis': {'name': '📊 分析算法设置', 'description': '基频算法、帧长、LPC阶数等'},
    'gender': {'name': '🧭 性别评估设置', 'description': '各维度权重、F0参考范围等'},
    'charts': {'name': '🖼️ 图表显示设置', 'description': '主题、DPI、网格等'},
    'privacy': {'name': '🔔 通知与隐私设置', 'description': '保存音频、自动删除等'},
    'reset': {'name': '↩️ 恢复默认设置', 'description': '重置所有设置'}
}

AUDIO_SETTINGS = {
    'sample_rate': {
        'name': '采样率',
        'options': [16000, 22050, 32000, 44100],
        'format': lambda x: f"{x//1000}kHz"
    },
    'channels': {
        'name': '声道数',
        'options': ['mono', 'stereo'],
        'format': lambda x: '单声道' if x == 'mono' else '立体声'
    },
    'vad_sensitivity': {
        'name': 'VAD灵敏度',
        'options': ['low', 'medium', 'high'],
        'format': lambda x: {'low': '低', 'medium': '中', 'high': '高'}[x]
    },
    'normalize_volume': {
        'name': '音量归一化',
        'options': [True, False],
        'format': lambda x: '开启' if x else '关闭'
    },
    'max_duration': {
        'name': '最大时长(秒)',
        'options': [30, 60, 120, 300],
        'format': lambda x: f"{x}秒"
    }
}

ANALYSIS_SETTINGS = {
    'pitch_algorithm': {
        'name': '基频检测算法',
        'options': ['pyin', 'autocorrelation'],
        'format': lambda x: {'pyin': 'PYIN', 'autocorrelation': '自相关法'}[x]
    },
    'pitch_range': {
        'name': '基频搜索范围',
        'options': [[60, 300], [80, 400], [100, 500]],
        'format': lambda x: f"{x[0]}-{x[1]} Hz"
    },
    'frame_length': {
        'name': '帧长',
        'options': [1024, 2048, 4096],
        'format': lambda x: str(x)
    },
    'hop_length': {
        'name': '帧移',
        'options': [256, 512, 1024],
        'format': lambda x: str(x)
    },
    'formant_count': {
        'name': '共振峰数量',
        'options': [3, 4, 5],
        'format': lambda x: str(x)
    },
    'lpc_order': {
        'name': 'LPC阶数',
        'options': ['auto', 12, 16, 20, 24],
        'format': lambda x: '自动' if x == 'auto' else str(x)
    }
}

GENDER_SETTINGS = {
    'weights_pitch': {
        'name': '基频维度权重(%)',
        'options': [10, 20, 30, 40, 50, 60],
        'format': lambda x: f"{x}%"
    },
    'weights_formant': {
        'name': '共振峰维度权重(%)',
        'options': [10, 15, 20, 25, 30, 40],
        'format': lambda x: f"{x}%"
    },
    'weights_timbre': {
        'name': '音色维度权重(%)',
        'options': [5, 10, 15, 20, 25],
        'format': lambda x: f"{x}%"
    },
    'weights_prosody': {
        'name': '韵律维度权重(%)',
        'options': [5, 10, 15, 20],
        'format': lambda x: f"{x}%"
    },
    'weights_quality': {
        'name': '音质维度权重(%)',
        'options': [5, 10, 15, 20],
        'format': lambda x: f"{x}%"
    },
    'male_f0_range': {
        'name': '男性典型F0范围',
        'options': [[75, 145], [85, 155], [95, 165]],
        'format': lambda x: f"{x[0]}-{x[1]} Hz"
    },
    'female_f0_range': {
        'name': '女性典型F0范围',
        'options': [[155, 245], [165, 255], [175, 265]],
        'format': lambda x: f"{x[0]}-{x[1]} Hz"
    },
    'baseline': {
        'name': '评分基准',
        'options': ['female', 'male'],
        'format': lambda x: '成年女声' if x == 'female' else '成年男声'
    }
}

CHARTS_SETTINGS = {
    'theme': {
        'name': '图表主题',
        'options': ['dark', 'light', 'blue'],
        'format': lambda x: {'dark': '暗色', 'light': '亮色', 'blue': '蓝色系'}[x]
    },
    'dpi': {
        'name': '图表DPI',
        'options': [90, 120, 150],
        'format': lambda x: str(x)
    },
    'show_grid': {
        'name': '显示网格',
        'options': [True, False],
        'format': lambda x: '开启' if x else '关闭'
    },
    'spectrogram_max_freq': {
        'name': '语谱图频率上限',
        'options': [4000, 8000, 16000],
        'format': lambda x: f"{x//1000}kHz"
    },
    'pitch_min': {
        'name': '基频图最小值',
        'options': [60, 80, 100],
        'format': lambda x: f"{x}Hz"
    },
    'pitch_max': {
        'name': '基频图最大值',
        'options': [300, 400, 500],
        'format': lambda x: f"{x}Hz"
    }
}

PRIVACY_SETTINGS = {
    'save_audio': {
        'name': '保存原始音频',
        'options': [True, False],
        'format': lambda x: '开启' if x else '关闭'
    },
    'notify_on_complete': {
        'name': '分析完成通知',
        'options': [True, False],
        'format': lambda x: '开启' if x else '关闭'
    },
    'auto_delete_days': {
        'name': '自动删除旧记录',
        'options': [0, 7, 30, 90],
        'format': lambda x: '关闭' if x == 0 else f"{x}天"
    }
}

SETTING_MAPS = {
    'audio': AUDIO_SETTINGS,
    'analysis': ANALYSIS_SETTINGS,
    'gender': GENDER_SETTINGS,
    'charts': CHARTS_SETTINGS,
    'privacy': PRIVACY_SETTINGS
}

def settings(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    user = get_or_create_user(db, update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
    
    keyboard = [
        [InlineKeyboardButton(f"{SETTING_CATEGORIES[key]['name']}", callback_data=f"settings_{key}")]
        for key in SETTING_CATEGORIES
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "⚙️ **设置菜单**\n\n请选择要调整的设置分类：",
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )

def settings_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    db = context.bot_data['db']
    user = get_or_create_user(db, query.from_user.id, query.from_user.username, query.from_user.first_name)
    
    data = query.data.replace('settings_', '')
    
    if data == 'reset':
        user.update_settings(DEFAULT_SETTINGS)
        db.commit()
        query.edit_message_text("✅ 所有设置已恢复为默认值！")
        return
    
    category = data
    settings_data = user.get_settings()
    category_settings = SETTING_MAPS.get(category, {})
    
    keyboard = []
    for key, config in category_settings.items():
        if key.startswith('weights_'):
            actual_key = key.replace('weights_', '')
            current_value = settings_data[category]['weights'].get(actual_key, 0)
        else:
            current_value = settings_data[category].get(key, '')
        
        formatted_value = config['format'](current_value)
        keyboard.append([InlineKeyboardButton(
            f"{config['name']}: {formatted_value}",
            callback_data=f"setting_{category}_{key}"
        )])
    
    keyboard.append([InlineKeyboardButton("← 返回设置主菜单", callback_data="settings_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        f"⚙️ **{SETTING_CATEGORIES[category]['name']}**\n\n{SETTING_CATEGORIES[category]['description']}\n\n请选择要修改的参数：",
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )

def setting_parameter_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    db = context.bot_data['db']
    user = get_or_create_user(db, query.from_user.id, query.from_user.username, query.from_user.first_name)
    
    data = query.data.replace('setting_', '')
    parts = data.split('_', 2)
    
    if len(parts) == 1 and parts[0] == 'main':
        keyboard = [
            [InlineKeyboardButton(f"{SETTING_CATEGORIES[key]['name']}", callback_data=f"settings_{key}")]
            for key in SETTING_CATEGORIES
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            "⚙️ **设置菜单**\n\n请选择要调整的设置分类：",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
        return
    
    category, key = parts[:2]
    
    settings_data = user.get_settings()
    category_settings = SETTING_MAPS.get(category, {})
    config = category_settings.get(key, {})
    
    if not config:
        query.edit_message_text("❌ 参数不存在")
        return
    
    options = config['options']
    
    if key.startswith('weights_'):
        actual_key = key.replace('weights_', '')
        current_value = settings_data[category]['weights'].get(actual_key, 0)
    else:
        current_value = settings_data[category].get(key, '')
    
    keyboard = []
    for option in options:
        is_current = option == current_value
        prefix = "✅ " if is_current else ""
        keyboard.append([InlineKeyboardButton(
            f"{prefix}{config['format'](option)}",
            callback_data=f"option_{category}_{key}_{json.dumps(option)}"
        )])
    
    keyboard.append([InlineKeyboardButton("← 返回", callback_data=f"settings_{category}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        f"⚙️ **{config['name']}**\n\n当前值: {config['format'](current_value)}\n\n请选择新的值：",
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )

def setting_option_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    db = context.bot_data['db']
    user = get_or_create_user(db, query.from_user.id, query.from_user.username, query.from_user.first_name)
    
    data = query.data.replace('option_', '')
    parts = data.split('_', 2)
    
    if len(parts) != 3:
        query.edit_message_text("❌ 参数错误")
        return
    
    category, key, option_str = parts
    
    try:
        option = json.loads(option_str)
    except json.JSONDecodeError:
        query.edit_message_text("❌ 参数解析错误")
        return
    
    settings_data = user.get_settings()
    category_settings = SETTING_MAPS.get(category, {})
    config = category_settings.get(key, {})
    
    if key.startswith('weights_'):
        actual_key = key.replace('weights_', '')
        settings_data[category]['weights'][actual_key] = option
        
        total_weight = sum(settings_data[category]['weights'].values())
        if total_weight != 100:
            query.edit_message_text(
                f"⚠️ **权重总和不为100%**\n\n当前总和: {total_weight}%\n请调整其他权重使总和为100%",
                parse_mode='MarkdownV2'
            )
            user.update_settings(settings_data)
            db.commit()
            return
    else:
        settings_data[category][key] = option
    
    user.update_settings(settings_data)
    db.commit()
    
    query.edit_message_text(
        f"✅ **{config['name']}** 已设置为: {config['format'](option)}",
        parse_mode='MarkdownV2'
    )

def reset_settings(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    user = get_or_create_user(db, update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
    
    update.message.reply_text(
        "⚠️ **警告**：此操作将重置所有设置为默认值！\n\n"
        "请回复 `确认重置` 来确认此操作，或发送任意其他消息取消。",
        parse_mode='MarkdownV2'
    )
    
    context.user_data['reset_settings_pending'] = True

def reset_settings_confirm(update: Update, context: CallbackContext):
    if not context.user_data.get('reset_settings_pending'):
        return
    
    if update.message.text == '确认重置':
        db = context.bot_data['db']
        user = get_or_create_user(db, update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
        user.update_settings(DEFAULT_SETTINGS)
        db.commit()
        update.message.reply_text("✅ 所有设置已恢复为默认值")
    else:
        update.message.reply_text("✅ 操作已取消")
    
    context.user_data['reset_settings_pending'] = False
