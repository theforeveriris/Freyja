import numpy as np

class AudioPreprocessor:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.sample_rate = self.settings.get('sample_rate', 16000)
        self.channels = self.settings.get('channels', 'mono')
        self.normalize_volume = self.settings.get('normalize_volume', True)
        self.max_duration = self.settings.get('max_duration', 120)

    def process(self, audio_data, original_sr):
        audio_data = self._resample(audio_data, original_sr)
        audio_data = self._convert_to_mono(audio_data)
        if self.normalize_volume:
            audio_data = self._normalize_volume(audio_data)
        # 跳过 _trim_silence（librosa 慢），改用简单阈值
        audio_data = self._simple_trim(audio_data)
        return audio_data, self.sample_rate

    def _resample(self, audio_data, original_sr):
        if original_sr == self.sample_rate:
            return audio_data
        # 用 resample_poly（多相滤波器）替代 resample，快 10 倍以上
        from scipy import signal
        gcd = np.gcd(original_sr, self.sample_rate)
        up = self.sample_rate // gcd
        down = original_sr // gcd
        audio_data = signal.resample_poly(audio_data, up, down)
        return audio_data.astype(np.float32)

    def _convert_to_mono(self, audio_data):
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=0)
        return audio_data.astype(np.float32)

    def _normalize_volume(self, audio_data):
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val * 0.95
        return audio_data

    def _simple_trim(self, audio_data, threshold=0.01):
        """简单的静音裁剪（避免 librosa.effects.trim）"""
        if len(audio_data) < 100:
            return audio_data

        # 找第一个超过阈值的样本
        abs_data = np.abs(audio_data)
        above = np.where(abs_data > threshold)[0]
        if len(above) == 0:
            return audio_data

        start = max(0, above[0] - 100)
        end = min(len(audio_data), above[-1] + 100)
        return audio_data[start:end]

    def validate_duration(self, duration):
        return duration <= self.max_duration
