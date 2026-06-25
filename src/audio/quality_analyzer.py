import librosa
import numpy as np

class QualityAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.frame_length = self.settings.get('frame_length', 2048)
        self.hop_length = self.settings.get('hop_length', 512)
    
    def analyze(self, audio_data, sample_rate):
        zcr = librosa.feature.zero_crossing_rate(
            y=audio_data,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )
        
        shimmer = self._calculate_shimmer(audio_data, sample_rate)
        hnr = self._calculate_hnr(audio_data, sample_rate)
        apq = self._calculate_apq(audio_data, sample_rate)
        
        auto_corr = self._calculate_autocorrelation(audio_data)
        
        return {
            'zcr_mean': np.mean(zcr),
            'zcr_std': np.std(zcr),
            'zcr_values': zcr[0].tolist(),
            'shimmer_local': shimmer.get('shimmer_local', np.nan),
            'shimmer_apq3': shimmer.get('shimmer_apq3', np.nan),
            'hnr': hnr,
            'apq': apq,
            'autocorrelation_peak': auto_corr
        }
    
    def _calculate_shimmer(self, audio_data, sample_rate):
        frame_length = 512
        hop_length = 128
        n_frames = 1 + (len(audio_data) - frame_length) // hop_length
        
        amplitudes = []
        for i in range(n_frames):
            start = i * hop_length
            end = start + frame_length
            frame = audio_data[start:end]
            if len(frame) > 0:
                amplitudes.append(np.max(np.abs(frame)))
        
        amplitudes = np.array(amplitudes)
        if len(amplitudes) < 2:
            return {'shimmer_local': np.nan, 'shimmer_apq3': np.nan}
        
        mean_amp = np.mean(amplitudes)
        if mean_amp == 0:
            return {'shimmer_local': np.nan, 'shimmer_apq3': np.nan}
        
        diffs = np.abs(np.diff(amplitudes))
        shimmer_local = np.mean(diffs) / mean_amp * 100
        
        shimmer_apq3 = 0
        if len(amplitudes) >= 4:
            apq_sum = 0
            for i in range(1, len(amplitudes) - 2):
                apq_sum += np.abs(amplitudes[i] - (amplitudes[i-1] + amplitudes[i+1] + amplitudes[i+2]) / 3)
            shimmer_apq3 = (apq_sum / (len(amplitudes) - 3)) / mean_amp * 100
        
        return {'shimmer_local': shimmer_local, 'shimmer_apq3': shimmer_apq3}
    
    def _calculate_hnr(self, audio_data, sample_rate):
        autocorr = np.correlate(audio_data, audio_data, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        peak_idx = np.argmax(autocorr[1:]) + 1
        fundamental_period = peak_idx / sample_rate
        
        noise_floor = np.mean(autocorr[len(autocorr)//2:])
        
        if noise_floor == 0 or autocorr[peak_idx] == 0:
            return np.nan
        
        hnr = 20 * np.log10(autocorr[peak_idx] / noise_floor)
        
        if hnr < 0:
            hnr = 0
        
        return hnr
    
    def _calculate_apq(self, audio_data, sample_rate):
        frame_length = 512
        hop_length = 128
        
        apq_values = []
        for i in range(0, len(audio_data) - frame_length, hop_length):
            frame = audio_data[i:i+frame_length]
            frame = frame * np.hanning(len(frame))
            
            autocorr = np.correlate(frame, frame, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            if len(autocorr) < 2:
                continue
            
            peak_idx = np.argmax(autocorr[1:]) + 1
            
            if peak_idx >= len(autocorr) - 1:
                continue
            
            periodic_energy = autocorr[peak_idx]
            total_energy = autocorr[0]
            
            if total_energy == 0:
                continue
            
            apq = 1 - (periodic_energy / total_energy)
            apq_values.append(apq)
        
        if len(apq_values) == 0:
            return np.nan
        
        return np.mean(apq_values) * 100
    
    def _calculate_autocorrelation(self, audio_data):
        autocorr = np.correlate(audio_data, audio_data, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        if np.max(autocorr) == 0:
            return 0
        
        peak_idx = np.argmax(autocorr[1:]) + 1
        return autocorr[peak_idx] / autocorr[0]
