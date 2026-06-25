import numpy as np

class SpectrumAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.frame_length = self.settings.get('frame_length', 2048)
        self.hop_length = self.settings.get('hop_length', 512)
        self.n_mels = 26  # 减少 mel 滤波器数量（原 128）
        self.n_mfcc = 13

    def analyze(self, audio_data, sample_rate):
        # 用 STFT 计算频谱（用 numpy 替代 librosa）
        stft = self._stft(audio_data)
        magnitude = np.abs(stft)  # (n_freqs, n_frames)

        # 频谱质心
        freqs = np.linspace(0, sample_rate / 2, magnitude.shape[0])
        centroid = self._spectral_centroid(magnitude, freqs)

        # 频谱滚降（85%）
        rolloff = self._spectral_rolloff(magnitude, freqs, roll_percent=0.85)

        # 频谱带宽
        bandwidth = self._spectral_bandwidth(magnitude, freqs, centroid)

        # 频谱通量（onset strength）
        flux = self._spectral_flux(magnitude)

        # Mel 频谱
        mel_spec = self._melspectrogram(magnitude, sample_rate)

        # MFCC
        mfcc = self._mfcc(mel_spec)

        return {
            'spectral_centroid_mean': float(np.mean(centroid)),
            'spectral_centroid_std': float(np.std(centroid)),
            'spectral_centroid_values': centroid.tolist(),
            'spectral_rolloff_mean': float(np.mean(rolloff)),
            'spectral_rolloff_std': float(np.std(rolloff)),
            'spectral_rolloff_values': rolloff.tolist(),
            'spectral_bandwidth_mean': float(np.mean(bandwidth)),
            'spectral_bandwidth_std': float(np.std(bandwidth)),
            'spectral_flux_mean': float(np.mean(flux)),
            'spectral_flux_std': float(np.std(flux)),
            'spectral_flux_values': flux.tolist(),
            'mel_spectrogram': mel_spec.tolist(),
            'mfcc_mean': np.mean(mfcc, axis=1).tolist(),
            'mfcc_std': np.std(mfcc, axis=1).tolist(),
            'mfcc_values': mfcc.tolist()
        }

    def _stft(self, audio_data):
        """短时傅里叶变换"""
        n_fft = self.frame_length
        hop = self.hop_length
        n_frames = 1 + (len(audio_data) - n_fft) // hop
        if n_frames <= 0:
            return np.zeros((n_fft // 2 + 1, 1), dtype=complex)

        # 用 stride_tricks 切帧
        frames = np.lib.stride_tricks.sliding_window_view(audio_data, n_fft)[::hop]
        # 加窗
        window = np.hanning(n_fft)
        frames = frames * window

        # FFT
        stft = np.fft.rfft(frames.T, n=n_fft)  # (n_freqs, n_frames)
        return stft

    def _spectral_centroid(self, magnitude, freqs):
        """频谱质心"""
        # magnitude: (n_freqs, n_frames)
        # freqs: (n_freqs,)
        if magnitude.size == 0:
            return np.array([0.0])
        # 归一化
        mag_sum = np.sum(magnitude, axis=0) + 1e-10
        centroid = np.sum(freqs[:, None] * magnitude, axis=0) / mag_sum
        return centroid

    def _spectral_rolloff(self, magnitude, freqs, roll_percent=0.85):
        """频谱滚降"""
        if magnitude.size == 0:
            return np.array([0.0])
        # 累积能量
        cumsum = np.cumsum(magnitude, axis=0)
        total = cumsum[-1:, :] + 1e-10
        threshold = roll_percent * total
        # 找超过阈值的第一个索引
        idx = np.argmax(cumsum >= threshold, axis=0)
        rolloff = freqs[idx]
        return rolloff

    def _spectral_bandwidth(self, magnitude, freqs, centroid):
        """频谱带宽"""
        if magnitude.size == 0:
            return np.array([0.0])
        mag_sum = np.sum(magnitude, axis=0) + 1e-10
        bw = np.sqrt(np.sum(((freqs[:, None] - centroid[None, :])**2) * magnitude, axis=0) / mag_sum)
        return bw

    def _spectral_flux(self, magnitude):
        """频谱通量"""
        if magnitude.shape[1] <= 1:
            return np.array([0.0])
        diff = np.diff(magnitude, axis=1)
        # 半波整流
        flux = np.sum(np.maximum(diff, 0), axis=0)
        return flux

    def _melspectrogram(self, magnitude, sample_rate):
        """Mel 频谱（用三角滤波器手动实现）"""
        n_mels = self.n_mels
        n_fft = (magnitude.shape[0] - 1) * 2
        fmax = sample_rate / 2

        # HTK 风格 Mel 刻度
        def hz_to_mel(f):
            return 2595.0 * np.log10(1.0 + f / 700.0)
        def mel_to_hz(m):
            return 700.0 * (10.0 ** (m / 2595.0) - 1.0)

        mel_max = hz_to_mel(fmax)
        mel_points = np.linspace(0, mel_max, n_mels + 2)
        hz_points = mel_to_hz(mel_points)
        bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

        # 构造三角滤波器组
        n_freqs = magnitude.shape[0]
        filter_bank = np.zeros((n_mels, n_freqs))
        for m in range(1, n_mels + 1):
            f_left = bin_points[m - 1]
            f_center = bin_points[m]
            f_right = bin_points[m + 1]
            for k in range(f_left, f_center):
                if f_center > f_left and k < n_freqs:
                    filter_bank[m - 1, k] = (k - f_left) / (f_center - f_left)
            for k in range(f_center, f_right):
                if f_right > f_center and k < n_freqs:
                    filter_bank[m - 1, k] = (f_right - k) / (f_right - f_center)

        # 应用滤波器
        mel_spec = filter_bank @ magnitude
        # 转为 dB
        mel_spec_db = 20 * np.log10(mel_spec + 1e-10)
        return mel_spec_db

    def _mfcc(self, mel_spec_db):
        """MFCC：对 mel 频谱做 DCT"""
        n_mfcc = self.n_mfcc
        n_mels = mel_spec_db.shape[0]

        # DCT-II
        n = np.arange(n_mels)
        k = np.arange(n_mfcc).reshape(-1, 1)
        dct_basis = np.cos(np.pi * k * (2 * n + 1) / (2 * n_mels))

        mfcc = dct_basis @ mel_spec_db
        return mfcc
