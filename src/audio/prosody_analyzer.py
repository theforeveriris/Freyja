import librosa
import numpy as np

class ProsodyAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.hop_length = self.settings.get('hop_length', 512)
    
    def analyze(self, audio_data, sample_rate, f0_values=None):
        onset_env = librosa.onset.onset_strength(
            y=audio_data,
            sr=sample_rate,
            hop_length=self.hop_length
        )
        
        onsets = librosa.onset.onset_detect(
            y=audio_data,
            sr=sample_rate,
            hop_length=self.hop_length,
            units='time'
        )
        
        speech_rate = len(onsets) / (len(audio_data) / sample_rate) if len(audio_data) > 0 else 0
        
        pause_durations = []
        if len(onsets) > 1:
            for i in range(1, len(onsets)):
                pause = onsets[i] - onsets[i-1]
                if pause > 0.15:
                    pause_durations.append(pause)
        
        avg_pause_duration = np.mean(pause_durations) if len(pause_durations) > 0 else 0
        pause_count = len(pause_durations)
        
        if f0_values is not None and len(f0_values) > 0:
            valid_f0 = f0_values[~np.isnan(f0_values)]
            if len(valid_f0) > 0:
                intonation_range = np.max(valid_f0) - np.min(valid_f0)
                intonation_mean = np.mean(valid_f0)
            else:
                intonation_range = 0
                intonation_mean = 0
        else:
            intonation_range = 0
            intonation_mean = 0
        
        return {
            'speech_rate': speech_rate,
            'onset_count': len(onsets),
            'onset_times': onsets.tolist(),
            'pause_count': pause_count,
            'avg_pause_duration': avg_pause_duration,
            'pause_durations': pause_durations,
            'intonation_range': intonation_range,
            'intonation_mean': intonation_mean,
            'onset_envelope': onset_env.tolist()
        }
