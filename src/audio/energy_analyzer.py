import numpy as np

class EnergyAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.frame_length = self.settings.get('frame_length', 2048)
        self.hop_length = self.settings.get('hop_length', 512)

    def analyze(self, audio_data, sample_rate):
        # 用 numpy 直接计算 RMS（避免 librosa）
        rms = self._rms(audio_data)

        peak_amplitude = np.max(np.abs(audio_data))

        if np.min(rms) > 0:
            dynamic_range = 20 * np.log10(np.max(rms) / np.min(rms))
        else:
            dynamic_range = 0

        energy_envelope = rms

        if len(energy_envelope) > 1:
            energy_rate = np.mean(np.abs(np.diff(energy_envelope)))
        else:
            energy_rate = 0

        energy_percentiles = np.percentile(rms, [10, 25, 50, 75, 90])

        return {
            'rms_mean': float(np.mean(rms)),
            'rms_std': float(np.std(rms)),
            'rms_values': rms.tolist(),
            'peak_amplitude': float(peak_amplitude),
            'dynamic_range': float(dynamic_range),
            'energy_envelope': energy_envelope.tolist(),
            'energy_rate': float(energy_rate),
            'energy_percentiles': energy_percentiles.tolist()
        }

    def _rms(self, audio_data):
        """向量化 RMS（避免 librosa）"""
        frame_length = self.frame_length
        hop_length = self.hop_length
        n_frames = 1 + (len(audio_data) - frame_length) // hop_length
        if n_frames <= 0:
            return np.array([np.sqrt(np.mean(audio_data**2))])

        # 用 stride_tricks 创建帧视图
        frames = np.lib.stride_tricks.sliding_window_view(audio_data, frame_length)[::hop_length]
        # 向量化计算 RMS
        rms = np.sqrt(np.mean(frames**2, axis=1))
        return rms
