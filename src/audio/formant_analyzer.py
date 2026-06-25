import numpy as np

class FormantAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.formant_count = self.settings.get('formant_count', 3)
        self.lpc_order = self.settings.get('lpc_order', 'auto')
        # 帧跳跃：每 4 帧分析 1 帧，速度提升 4 倍
        self.frame_skip = 4

    def analyze(self, audio_data, sample_rate):
        frame_length = 512
        hop_length = 128
        # 限制最大分析时长为 30 秒（避免长音频卡死）
        max_samples = min(len(audio_data), 30 * sample_rate)
        audio_data = audio_data[:max_samples]

        n_frames = 1 + (len(audio_data) - frame_length) // hop_length
        # 只分析前 1/4 的帧（其他帧贡献较小）
        n_frames = min(n_frames, max(1, n_frames // 4))

        f1_values = []
        f2_values = []
        f3_values = []

        window = np.hanning(frame_length)

        for i in range(0, n_frames, self.frame_skip):
            start = i * hop_length
            end = start + frame_length
            if end > len(audio_data):
                break

            frame = audio_data[start:end] * window

            lpc_coeffs = self._compute_lpc(frame, sample_rate)
            if lpc_coeffs is None:
                continue

            formants = self._find_formants(lpc_coeffs, sample_rate)

            if len(formants) >= 1:
                f1_values.append(formants[0])
            if len(formants) >= 2:
                f2_values.append(formants[1])
            if len(formants) >= 3:
                f3_values.append(formants[2])

        return self._compute_formant_stats(f1_values, f2_values, f3_values)

    def _compute_lpc(self, frame, sample_rate):
        if self.lpc_order == 'auto':
            # 降低 LPC 阶数（原 2 + sr/1000 太大），减少计算量
            order = min(12, max(8, int(sample_rate / 1500)))
        else:
            order = self.lpc_order

        if order < 4:
            order = 4

        # 限制帧长度（去掉 padding）
        N = len(frame)
        # 用 FFT 计算自相关，比 correlate 快很多
        fft_frame = np.fft.rfft(frame, n=2*N)
        acf = np.fft.irfft(fft_frame * np.conj(fft_frame))[:N]
        acf = acf / (N - np.arange(N) + 1e-10)  # 偏置校正

        R = acf[:order]
        r = acf[1:order+1]

        # 向量化构造 Toeplitz 矩阵（替代双层 for 循环）
        idx = np.arange(order)
        R_matrix = R[np.abs(idx[:, None] - idx[None, :])]

        try:
            lpc_coeffs = np.linalg.solve(R_matrix, r)
            lpc_coeffs = np.concatenate([[1.0], -lpc_coeffs])
            return lpc_coeffs
        except np.linalg.LinAlgError:
            return None

    def _find_formants(self, lpc_coeffs, sample_rate):
        roots = np.roots(lpc_coeffs)
        roots = roots[np.imag(roots) >= 0]

        if len(roots) == 0:
            return []

        angles = np.arctan2(np.imag(roots), np.real(roots))

        # 向量化筛选共振峰
        positive_mask = angles > 0
        freqs = angles[positive_mask] * sample_rate / (2 * np.pi)
        in_range = (freqs > 80) & (freqs < 4000)

        if not np.any(in_range):
            return []

        valid_freqs = freqs[in_range]
        valid_roots = roots[positive_mask][in_range]

        # 计算带宽并筛选
        mags = np.abs(valid_roots)
        # 避免 log(0)
        mags = np.maximum(mags, 1e-10)
        bandwidths = -np.log(mags) * sample_rate / np.pi

        # 只保留带宽 < 500 Hz 的共振峰
        valid_mask = bandwidths < 500
        valid_formants = valid_freqs[valid_mask]

        # 排序并取前 N 个
        valid_formants = np.sort(valid_formants)
        return valid_formants[:self.formant_count].tolist()

    def _compute_formant_stats(self, f1_values, f2_values, f3_values):
        stats = {}

        for name, values in [('f1', f1_values), ('f2', f2_values), ('f3', f3_values)]:
            if len(values) > 0:
                arr = np.array(values)
                stats[f'{name}_mean'] = float(np.mean(arr))
                stats[f'{name}_median'] = float(np.median(arr))
                stats[f'{name}_std'] = float(np.std(arr))
                stats[f'{name}_min'] = float(np.min(arr))
                stats[f'{name}_max'] = float(np.max(arr))
                stats[f'{name}_values'] = list(values)
            else:
                stats[f'{name}_mean'] = np.nan
                stats[f'{name}_median'] = np.nan
                stats[f'{name}_std'] = np.nan
                stats[f'{name}_min'] = np.nan
                stats[f'{name}_max'] = np.nan
                stats[f'{name}_values'] = []

        if not np.isnan(stats['f1_mean']) and not np.isnan(stats['f2_mean']):
            stats['f2_f1_diff'] = stats['f2_mean'] - stats['f1_mean']
        else:
            stats['f2_f1_diff'] = np.nan

        if not np.isnan(stats['f1_mean']) and not np.isnan(stats['f2_mean']) and stats['f1_mean'] > 0:
            stats['f2_f1_ratio'] = stats['f2_mean'] / stats['f1_mean']
        else:
            stats['f2_f1_ratio'] = np.nan

        if not np.isnan(stats['f2_mean']) and not np.isnan(stats['f3_mean']) and stats['f2_mean'] > 0:
            stats['f3_f2_ratio'] = stats['f3_mean'] / stats['f2_mean']
        else:
            stats['f3_f2_ratio'] = np.nan

        return stats
