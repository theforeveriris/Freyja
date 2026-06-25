import librosa
import numpy as np

class SpectrumAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.frame_length = self.settings.get('frame_length', 2048)
        self.hop_length = self.settings.get('hop_length', 512)
    
    def analyze(self, audio_data, sample_rate):
        centroid = librosa.feature.spectral_centroid(
            y=audio_data,
            sr=sample_rate,
            n_fft=self.frame_length,
            hop_length=self.hop_length
        )
        
        rolloff = librosa.feature.spectral_rolloff(
            y=audio_data,
            sr=sample_rate,
            n_fft=self.frame_length,
            hop_length=self.hop_length
        )
        
        bandwidth = librosa.feature.spectral_bandwidth(
            y=audio_data,
            sr=sample_rate,
            n_fft=self.frame_length,
            hop_length=self.hop_length
        )
        
        spectral_flux = librosa.onset.onset_strength(
            y=audio_data,
            sr=sample_rate,
            n_fft=self.frame_length,
            hop_length=self.hop_length
        )
        
        mel_spectrogram = librosa.feature.melspectrogram(
            y=audio_data,
            sr=sample_rate,
            n_fft=self.frame_length,
            hop_length=self.hop_length
        )
        
        mfcc = librosa.feature.mfcc(
            y=audio_data,
            sr=sample_rate,
            n_mfcc=13,
            n_fft=self.frame_length,
            hop_length=self.hop_length
        )
        
        return {
            'spectral_centroid_mean': np.mean(centroid),
            'spectral_centroid_std': np.std(centroid),
            'spectral_centroid_values': centroid[0].tolist(),
            'spectral_rolloff_mean': np.mean(rolloff),
            'spectral_rolloff_std': np.std(rolloff),
            'spectral_rolloff_values': rolloff[0].tolist(),
            'spectral_bandwidth_mean': np.mean(bandwidth),
            'spectral_bandwidth_std': np.std(bandwidth),
            'spectral_flux_mean': np.mean(spectral_flux),
            'spectral_flux_std': np.std(spectral_flux),
            'spectral_flux_values': spectral_flux.tolist(),
            'mel_spectrogram': mel_spectrogram.tolist(),
            'mfcc_mean': np.mean(mfcc, axis=1).tolist(),
            'mfcc_std': np.std(mfcc, axis=1).tolist(),
            'mfcc_values': mfcc.tolist()
        }
