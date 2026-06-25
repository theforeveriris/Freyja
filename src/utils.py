import os
import json
import numpy as np
from config import AUDIO_DIR, CHARTS_DIR

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_user_audio_dir(user_id):
    dir_path = os.path.join(AUDIO_DIR, str(user_id))
    ensure_dir(dir_path)
    return dir_path

def get_user_charts_dir(user_id, analysis_id=None):
    dir_path = os.path.join(CHARTS_DIR, str(user_id))
    if analysis_id:
        dir_path = os.path.join(dir_path, str(analysis_id))
    ensure_dir(dir_path)
    return dir_path

def save_audio_file(audio_data, sample_rate, user_id, analysis_id):
    import soundfile as sf
    audio_dir = get_user_audio_dir(user_id)
    file_path = os.path.join(audio_dir, f"{analysis_id}.wav")
    sf.write(file_path, audio_data, sample_rate)
    return file_path

def load_audio_file(file_path):
    import soundfile as sf
    data, sr = sf.read(file_path)
    return data, sr

def format_number(value, decimals=1):
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"

def format_percentage(value, decimals=1):
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"

def get_bars(value, max_value=100, bar_count=20):
    if value is None or value < 0:
        return ""
    filled = int(round((value / max_value) * bar_count))
    return "█" * filled + "░" * (bar_count - filled)

def merge_dicts(*dicts):
    result = {}
    for d in dicts:
        result.update(d)
    return result

def safe_divide(a, b, default=0):
    if b == 0:
        return default
    return a / b

def calculate_percentile(data, percentile):
    if len(data) == 0:
        return 0
    return np.percentile(data, percentile)

def moving_average(data, window_size=5):
    if len(data) < window_size:
        return data
    cumsum = np.cumsum(np.insert(data, 0, 0))
    return (cumsum[window_size:] - cumsum[:-window_size]) / float(window_size)

def normalize_array(arr):
    if np.max(arr) == np.min(arr):
        return arr
    return (arr - np.min(arr)) / (np.max(arr) - np.min(arr))

def interpolate_nan(arr):
    nans = np.isnan(arr)
    if np.all(nans):
        return arr
    if not np.any(nans):
        return arr
    x = np.arange(len(arr))
    arr[nans] = np.interp(x[nans], x[~nans], arr[~nans])
    return arr

def detect_voice_segments(audio, sample_rate, frame_duration_ms=30):
    import webrtcvad
    vad = webrtcvad.Vad(2)
    frame_size = int(sample_rate * frame_duration_ms / 1000)
    
    audio = np.array(audio)
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    
    audio = audio * 32767
    audio = audio.astype(np.int16)
    
    frames = []
    for i in range(0, len(audio), frame_size):
        frame = audio[i:i+frame_size]
        if len(frame) < frame_size:
            frame = np.pad(frame, (0, frame_size - len(frame)))
        frames.append(frame)
    
    voice_flags = []
    for frame in frames:
        try:
            voice_flags.append(vad.is_speech(frame.tobytes(), sample_rate))
        except:
            voice_flags.append(False)
    
    return np.array(voice_flags)

def calculate_voiced_duration(audio, sample_rate):
    voice_segments = detect_voice_segments(audio, sample_rate)
    frame_duration = 0.03
    voiced_frames = np.sum(voice_segments)
    return voiced_frames * frame_duration
