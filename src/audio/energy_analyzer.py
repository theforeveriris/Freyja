import librosa
import numpy as np

class EnergyAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.frame_length = self.settings.get('frame_length', 2048)
        self.hop_length = self.settings.get('hop_length', 512)
    
    def analyze(self, audio_data, sample_rate):
        rms = librosa.feature.rms(
            y=audio_data,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )
        
        peak_amplitude = np.max(np.abs(audio_data))
        
        if np.min(rms) > 0:
            dynamic_range = 20 * np.log10(np.max(rms) / np.min(rms))
        else:
            dynamic_range = 0
        
        energy_envelope = rms[0]
        
        if len(energy_envelope) > 1:
            energy_rate = np.mean(np.abs(np.diff(energy_envelope)))
        else:
            energy_rate = 0
        
        energy_percentiles = np.percentile(rms, [10, 25, 50, 75, 90])
        
        return {
            'rms_mean': np.mean(rms),
            'rms_std': np.std(rms),
            'rms_values': rms[0].tolist(),
            'peak_amplitude': peak_amplitude,
            'dynamic_range': dynamic_range,
            'energy_envelope': energy_envelope.tolist(),
            'energy_rate': energy_rate,
            'energy_percentiles': energy_percentiles.tolist()
        }
