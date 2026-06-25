import numpy as np

def fft_autocorr(x):
    """FFT-based autocorrelation, O(N log N) instead of O(N^2)"""
    N = len(x)
    fft_size = 1
    while fft_size < 2 * N:
        fft_size *= 2
    X = np.fft.rfft(x, n=fft_size)
    acf = np.fft.irfft(X * np.conj(X))[:N]
    return acf

class QualityAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.frame_length = self.settings.get('frame_length', 2048)
        self.hop_length = self.settings.get('hop_length', 512)

    def analyze(self, audio_data, sample_rate):
        # 用 numpy 直接计算 ZCR（避免 librosa）
        zcr = self._zero_crossing_rate(audio_data)

        # 只对有声音的片段分析（避免静音帧影响）
        voiced_mask = np.abs(audio_data) > 0.01
        if np.sum(voiced_mask) > sample_rate // 2:
            voiced_audio = audio_data[voiced_mask]
        else:
            voiced_audio = audio_data

        shimmer = self._calculate_shimmer(voiced_audio, sample_rate)
        hnr = self._calculate_hnr(voiced_audio, sample_rate)
        apq = self._calculate_apq(voiced_audio, sample_rate)
        auto_corr = self._calculate_autocorrelation(voiced_audio)

        return {
            'zcr_mean': float(np.mean(zcr)),
            'zcr_std': float(np.std(zcr)),
            'zcr_values': zcr.tolist(),
            'shimmer_local': shimmer.get('shimmer_local', np.nan),
            'shimmer_apq3': shimmer.get('shimmer_apq3', np.nan),
            'hnr': hnr,
            'apq': apq,
            'autocorrelation_peak': auto_corr
        }

    def _zero_crossing_rate(self, audio_data):
        """向量化 ZCR（避免 librosa）"""
        frame_length = self.frame_length
        hop_length = self.hop_length
        n_frames = 1 + (len(audio_data) - frame_length) // hop_length

        # 用 stride_tricks 创建帧视图（零拷贝）
        frames = np.lib.stride_tricks.sliding_window_view(audio_data, frame_length)[::hop_length]

        # 计算每帧的过零率
        signs = np.sign(frames)
        # 处理零值
        signs[signs == 0] = 1
        zcr = np.mean(np.abs(np.diff(signs, axis=1)) > 0, axis=1) / 2.0

        return zcr

    def _calculate_shimmer(self, audio_data, sample_rate):
        frame_length = 512
        hop_length = 128
        n_frames = 1 + (len(audio_data) - frame_length) // hop_length
        if n_frames <= 0:
            return {'shimmer_local': np.nan, 'shimmer_apq3': np.nan}

        # 向量化取每帧的峰值
        frames = np.lib.stride_tricks.sliding_window_view(audio_data, frame_length)[::hop_length]
        amplitudes = np.max(np.abs(frames), axis=1)

        if len(amplitudes) < 2:
            return {'shimmer_local': np.nan, 'shimmer_apq3': np.nan}

        mean_amp = np.mean(amplitudes)
        if mean_amp == 0:
            return {'shimmer_local': np.nan, 'shimmer_apq3': np.nan}

        diffs = np.abs(np.diff(amplitudes))
        shimmer_local = np.mean(diffs) / mean_amp * 100

        shimmer_apq3 = 0
        if len(amplitudes) >= 4:
            # 向量化 APQ3
            apq_sum = np.sum(np.abs(amplitudes[1:-2] - (amplitudes[:-3] + amplitudes[1:-2] + amplitudes[2:-1]) / 3))
            shimmer_apq3 = (apq_sum / (len(amplitudes) - 3)) / mean_amp * 100

        return {'shimmer_local': float(shimmer_local), 'shimmer_apq3': float(shimmer_apq3)}

    def _calculate_hnr(self, audio_data, sample_rate):
        # 用 FFT 计算自相关（O(N log N) 替代 O(N^2)）
        autocorr = fft_autocorr(audio_data)

        if len(autocorr) < 2:
            return np.nan

        # 跳过 lag=0，找第一个峰值
        peak_idx = np.argmax(autocorr[1:]) + 1

        if peak_idx == 0 or peak_idx >= len(autocorr):
            return np.nan

        # 噪声基底：取中段的平均值
        noise_floor = np.mean(autocorr[len(autocorr)//2:])

        if noise_floor <= 0 or autocorr[peak_idx] <= 0:
            return np.nan

        hnr = 20 * np.log10(autocorr[peak_idx] / noise_floor)
        return float(max(0, hnr))

    def _calculate_apq(self, audio_data, sample_rate):
        frame_length = 512
        hop_length = 128

        n_frames = 1 + (len(audio_data) - frame_length) // hop_length
        if n_frames <= 0:
            return np.nan

        # 向量化加窗
        frames = np.lib.stride_tricks.sliding_window_view(audio_data, frame_length)[::hop_length]
        window = np.hanning(frame_length)
        frames = frames * window

        # 对每帧用 FFT 计算自相关
        apq_values = []
        for frame in frames:
            if np.max(np.abs(frame)) < 0.001:
                continue

            # 用 FFT 计算自相关
            N = len(frame)
            fft_size = 1
            while fft_size < 2 * N:
                fft_size *= 2
            F = np.fft.rfft(frame, n=fft_size)
            acf = np.fft.irfft(F * np.conj(F))[:N]

            if len(acf) < 2 or acf[0] == 0:
                continue

            peak_idx = np.argmax(acf[1:]) + 1
            if peak_idx >= len(acf) - 1:
                continue

            apq = 1 - (acf[peak_idx] / acf[0])
            apq_values.append(apq)

        if len(apq_values) == 0:
            return np.nan

        return float(np.mean(apq_values) * 100)

    def _calculate_autocorrelation(self, audio_data):
        acf = fft_autocorr(audio_data)
        if len(acf) < 2 or acf[0] == 0:
            return 0
        peak_idx = np.argmax(acf[1:]) + 1
        return float(acf[peak_idx] / acf[0])
