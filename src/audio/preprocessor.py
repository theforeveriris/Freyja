import librosa
import numpy as np

class AudioPreprocessor:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.sample_rate = self.settings.get('sample_rate', 32000)
        self.channels = self.settings.get('channels', 'mono')
        self.normalize_volume = self.settings.get('normalize_volume', True)
        self.max_duration = self.settings.get('max_duration', 120)
    
    def process(self, audio_data, original_sr):
        audio_data = self._resample(audio_data, original_sr)
        audio_data = self._convert_to_mono(audio_data)
        if self.normalize_volume:
            audio_data = self._normalize_volume(audio_data)
        audio_data = self._trim_silence(audio_data)
        return audio_data, self.sample_rate
    
    def _resample(self, audio_data, original_sr):
        if original_sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=self.sample_rate)
        return audio_data
    
    def _convert_to_mono(self, audio_data):
        if len(audio_data.shape) > 1:
            audio_data = librosa.to_mono(audio_data)
        return audio_data
    
    def _normalize_volume(self, audio_data):
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        return audio_data
    
    def _trim_silence(self, audio_data, top_db=30):
        return librosa.effects.trim(audio_data, top_db=top_db)[0]
    
    def validate_duration(self, duration):
        return duration <= self.max_duration
