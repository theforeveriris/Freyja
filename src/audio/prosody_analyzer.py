import numpy as np

class ProsodyAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.hop_length = self.settings.get('hop_length', 512)
        self.frame_length = self.settings.get('frame_length', 2048)

    def analyze(self, audio_data, sample_rate, f0_values=None):
        # 用 RMS 能量包络替代 onset_strength（快得多）
        onset_env = self._rms_envelope(audio_data)

        # 简单的 onset 检测（基于能量变化）
        onsets = self._detect_onsets(audio_data, sample_rate)

        speech_rate = len(onsets) / (len(audio_data) / sample_rate) if len(audio_data) > 0 else 0

        pause_durations = []
        if len(onsets) > 1:
            for i in range(1, len(onsets)):
                pause = onsets[i] - onsets[i-1]
                if pause > 0.15:
                    pause_durations.append(pause)

        avg_pause_duration = float(np.mean(pause_durations)) if len(pause_durations) > 0 else 0
        pause_count = len(pause_durations)

        if f0_values is not None and len(f0_values) > 0:
            valid_f0 = f0_values[~np.isnan(f0_values)]
            if len(valid_f0) > 0:
                intonation_range = float(np.max(valid_f0) - np.min(valid_f0))
                intonation_mean = float(np.mean(valid_f0))
            else:
                intonation_range = 0
                intonation_mean = 0
        else:
            intonation_range = 0
            intonation_mean = 0

        return {
            'speech_rate': float(speech_rate),
            'onset_count': len(onsets),
            'onset_times': onsets.tolist(),
            'pause_count': pause_count,
            'avg_pause_duration': avg_pause_duration,
            'pause_durations': [float(p) for p in pause_durations],
            'intonation_range': intonation_range,
            'intonation_mean': intonation_mean,
            'onset_envelope': onset_env.tolist()
        }

    def _rms_envelope(self, audio_data):
        """RMS 能量包络"""
        frame_length = self.frame_length
        hop_length = self.hop_length
        n_frames = 1 + (len(audio_data) - frame_length) // hop_length
        if n_frames <= 0:
            return np.array([np.sqrt(np.mean(audio_data**2))])

        frames = np.lib.stride_tricks.sliding_window_view(audio_data, frame_length)[::hop_length]
        rms = np.sqrt(np.mean(frames**2, axis=1))
        return rms

    def _detect_onsets(self, audio_data, sample_rate):
        """简单的 onset 检测：基于能量突变"""
        frame_length = 512
        hop_length = 128
        n_frames = 1 + (len(audio_data) - frame_length) // hop_length
        if n_frames <= 0:
            return np.array([])

        frames = np.lib.stride_tricks.sliding_window_view(audio_data, frame_length)[::hop_length]
        energy = np.sum(frames**2, axis=1)

        # 计算能量变化
        if len(energy) < 2:
            return np.array([])

        # 归一化
        energy_norm = energy / (np.max(energy) + 1e-10)

        # 找局部最大值，且能量 > 阈值
        threshold = 0.1
        min_interval_frames = int(0.1 * sample_rate / hop_length)  # 最小间隔 100ms

        onsets = []
        last_onset = -min_interval_frames
        for i in range(1, len(energy_norm) - 1):
            if (energy_norm[i] > threshold and
                energy_norm[i] > energy_norm[i-1] and
                energy_norm[i] >= energy_norm[i+1] and
                i - last_onset >= min_interval_frames):
                onsets.append(i * hop_length / sample_rate)
                last_onset = i

        return np.array(onsets)
