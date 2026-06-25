import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
CHARTS_DIR = os.path.join(DATA_DIR, "charts")
DATABASE_DIR = os.path.join(DATA_DIR, "database")

DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'voice_analysis.db')}"
DB_PATH = os.path.join(DATABASE_DIR, 'voice_analysis.db')

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

DEFAULT_SETTINGS = {
    "audio": {
        "sample_rate": 32000,
        "channels": "mono",
        "vad_sensitivity": "medium",
        "normalize_volume": True,
        "max_duration": 120
    },
    "analysis": {
        "pitch_algorithm": "pyin",
        "pitch_range": [80, 400],
        "frame_length": 2048,
        "hop_length": 512,
        "formant_count": 3,
        "lpc_order": "auto"
    },
    "gender": {
        "weights": {
            "pitch": 40,
            "formant": 25,
            "timbre": 15,
            "prosody": 10,
            "quality": 10
        },
        "male_f0_range": [85, 155],
        "female_f0_range": [165, 255],
        "baseline": "female"
    },
    "charts": {
        "theme": "dark",
        "dpi": 120,
        "show_grid": True,
        "spectrogram_max_freq": 8000,
        "pitch_min": 80,
        "pitch_max": 400
    },
    "privacy": {
        "save_audio": True,
        "notify_on_complete": True,
        "auto_delete_days": 0
    }
}

GENDER_COLORS = {
    "male": "#3B82F6",
    "female": "#EC4899",
    "outside": "#6B7280"
}

CHART_THEMES = {
    "dark": {
        "bg_color": "#1E293B",
        "text_color": "#F1F5F9",
        "grid_color": "#334155",
        "line_colors": ["#3B82F6", "#EC4899", "#10B981", "#F59E0B", "#EF4444"]
    },
    "light": {
        "bg_color": "#FFFFFF",
        "text_color": "#1E293B",
        "grid_color": "#E2E8F0",
        "line_colors": ["#3B82F6", "#EC4899", "#10B981", "#F59E0B", "#EF4444"]
    },
    "blue": {
        "bg_color": "#0F172A",
        "text_color": "#E0F2FE",
        "grid_color": "#1E3A5F",
        "line_colors": ["#60A5FA", "#93C5FD", "#BFDBFE", "#22D3EE", "#0EA5E9"]
    }
}
