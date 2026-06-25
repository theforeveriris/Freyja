import numpy as np

class FormantAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.formant_count = self.settings.get('formant_count', 3)
        self.lpc_order = self.settings.get('lpc_order', 'auto')
    
    def analyze(self, audio_data, sample_rate):
        frame_length = 512
        hop_length = 128
        n_frames = 1 + (len(audio_data) - frame_length) // hop_length
        
        f1_values = []
        f2_values = []
        f3_values = []
        
        for i in range(n_frames):
            start = i * hop_length
            end = start + frame_length
            frame = audio_data[start:end]
            
            if len(frame) < frame_length:
                continue
            
            frame = frame * np.hanning(len(frame))
            
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
            order = int(2 + sample_rate / 1000)
        else:
            order = self.lpc_order
        
        if order < 4:
            order = 4
        
        autocorr = np.correlate(frame, frame, mode='full')
        autocorr = autocorr[len(autocorr) // 2 : len(autocorr) // 2 + order + 1]
        
        R = autocorr[:order]
        r = autocorr[1:order+1]
        
        R_matrix = np.zeros((order, order))
        for i in range(order):
            for j in range(order):
                if i == j:
                    R_matrix[i, j] = R[0]
                else:
                    idx = abs(i - j)
                    if idx < len(R):
                        R_matrix[i, j] = R[idx]
        
        try:
            lpc_coeffs = np.linalg.solve(R_matrix, r)
            lpc_coeffs = np.concatenate([[1], -lpc_coeffs])
            return lpc_coeffs
        except np.linalg.LinAlgError:
            return None
    
    def _find_formants(self, lpc_coeffs, sample_rate):
        roots = np.roots(lpc_coeffs)
        roots = roots[np.imag(roots) >= 0]
        
        angles = np.arctan2(np.imag(roots), np.real(roots))
        
        formants = []
        for angle in angles:
            if angle > 0:
                freq = angle * sample_rate / (2 * np.pi)
                if freq > 80 and freq < 4000:
                    formants.append(freq)
        
        formants = sorted(formants)
        
        bandwidths = []
        for root in roots:
            if np.imag(root) >= 0 and np.real(root) > 0:
                angle = np.arctan2(np.imag(root), np.real(root))
                freq = angle * sample_rate / (2 * np.pi)
                if freq > 80 and freq < 4000:
                    bw = -np.log(np.abs(root)) * sample_rate / np.pi
                    bandwidths.append(bw)
        
        valid_formants = []
        for i, f in enumerate(formants):
            if i < len(bandwidths) and bandwidths[i] < 500:
                valid_formants.append(f)
        
        return valid_formants[:self.formant_count]
    
    def _compute_formant_stats(self, f1_values, f2_values, f3_values):
        stats = {}
        
        for name, values in [('f1', f1_values), ('f2', f2_values), ('f3', f3_values)]:
            if len(values) > 0:
                stats[f'{name}_mean'] = np.mean(values)
                stats[f'{name}_median'] = np.median(values)
                stats[f'{name}_std'] = np.std(values)
                stats[f'{name}_min'] = np.min(values)
                stats[f'{name}_max'] = np.max(values)
                stats[f'{name}_values'] = values
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
