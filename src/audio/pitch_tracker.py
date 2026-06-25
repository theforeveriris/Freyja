import numpy as np

def _fft_autocorr(x):
    N = len(x)
    fft_size = 1 << (N.bit_length() + 1)
    X = np.fft.rfft(x, n=fft_size)
    acf = np.fft.irfft(X * np.conj(X))[:N]
    return acf

class PitchTracker:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.pitch_range = self.settings.get('pitch_range', [80, 400])
        self.algorithm = 'autocorrelation'
        self.frame_length = self.settings.get('frame_length', 2048)
        self.hop_length = self.settings.get('hop_length', 512)
    
    def track(self, audio_data, sample_rate):
        return self._track_autocorrelation(audio_data, sample_rate)
    
    def _track_pyin(self, audio_data, sample_rate):
        f0, _, _ = librosa.pyin(
            audio_data,
            fmin=self.pitch_range[0],
            fmax=self.pitch_range[1],
            sr=sample_rate,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )
        return self._process_f0(f0)
    
    def _track_crepe(self, audio_data, sample_rate):
        try:
            import crepe
            time, f0, confidence, _ = crepe.predict(
                audio_data,
                sample_rate,
                viterbi=True,
                model_capacity='full'
            )
            f0[f0 < self.pitch_range[0]] = np.nan
            f0[f0 > self.pitch_range[1]] = np.nan
            return self._process_f0(f0)
        except ImportError:
            return self._track_pyin(audio_data, sample_rate)
    
    def _track_autocorrelation(self, audio_data, sample_rate):
        frame_length = self.frame_length
        hop_length = self.hop_length
        f0 = []
        
        min_lag = int(sample_rate / self.pitch_range[1])
        max_lag = int(sample_rate / self.pitch_range[0])
        
        for i in range(0, len(audio_data) - frame_length, hop_length):
            frame = audio_data[i:i+frame_length]
            frame = frame * np.hanning(len(frame))
            
            autocorr = _fft_autocorr(frame)
            
            if min_lag >= len(autocorr):
                f0.append(np.nan)
                continue
            
            max_lag = min(max_lag, len(autocorr) - 1)
            peak_region = autocorr[min_lag:max_lag]
            
            if len(peak_region) == 0:
                f0.append(np.nan)
                continue
            
            peaks = self._find_peaks(peak_region)
            if len(peaks) == 0:
                f0.append(np.nan)
                continue
            
            best_peak = peaks[np.argmax(peak_region[peaks])]
            lag = min_lag + best_peak
            
            if lag > 0:
                f0_val = sample_rate / lag
            else:
                f0_val = np.nan
            
            f0.append(f0_val)
        
        return self._process_f0(np.array(f0))
    
    def _process_f0(self, f0):
        f0 = np.array(f0)
        valid_f0 = f0[~np.isnan(f0)]
        
        if len(valid_f0) == 0:
            return {
                'f0_values': f0,
                'f0_mean': np.nan,
                'f0_median': np.nan,
                'f0_min': np.nan,
                'f0_max': np.nan,
                'f0_std': np.nan,
                'f0_cv': np.nan,
                'f0_percentiles': [np.nan] * 5,
                'jitter_local': np.nan,
                'jitter_rap': np.nan,
                'pitch_contour': f0
            }
        
        f0_mean = np.mean(valid_f0)
        f0_median = np.median(valid_f0)
        f0_min = np.min(valid_f0)
        f0_max = np.max(valid_f0)
        f0_std = np.std(valid_f0)
        f0_cv = f0_std / f0_mean if f0_mean > 0 else 0
        
        f0_percentiles = np.percentile(valid_f0, [5, 25, 50, 75, 95])
        
        jitter_local = self._calculate_jitter(valid_f0, 'local')
        jitter_rap = self._calculate_jitter(valid_f0, 'rap')
        
        return {
            'f0_values': f0,
            'f0_mean': f0_mean,
            'f0_median': f0_median,
            'f0_min': f0_min,
            'f0_max': f0_max,
            'f0_std': f0_std,
            'f0_cv': f0_cv,
            'f0_percentiles': f0_percentiles.tolist(),
            'jitter_local': jitter_local,
            'jitter_rap': jitter_rap,
            'pitch_contour': f0
        }
    
    def _calculate_jitter(self, f0_values, method='local'):
        if len(f0_values) < 2:
            return 0
        
        diffs = np.abs(np.diff(f0_values))
        mean_f0 = np.mean(f0_values)
        
        if mean_f0 == 0:
            return 0
        
        if method == 'local':
            return np.mean(diffs) / mean_f0 * 100
        elif method == 'rap':
            if len(f0_values) < 4:
                return 0
            rap_sum = 0
            for i in range(1, len(f0_values) - 1):
                rap_sum += np.abs(f0_values[i] - (f0_values[i-1] + f0_values[i+1]) / 2)
            return (rap_sum / (len(f0_values) - 2)) / mean_f0 * 100
        
        return 0
    
    def _find_peaks(self, data):
        peaks = []
        for i in range(1, len(data) - 1):
            if data[i] > data[i-1] and data[i] > data[i+1]:
                peaks.append(i)
        return np.array(peaks)
