import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import CHART_THEMES

class Visualizer:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.theme = self.settings.get('theme', 'dark')
        self.dpi = self.settings.get('dpi', 120)
        self.show_grid = self.settings.get('show_grid', True)
        self._apply_theme()
    
    def _apply_theme(self):
        theme = CHART_THEMES.get(self.theme, CHART_THEMES['dark'])
        plt.style.use('dark_background' if self.theme == 'dark' else 'default')
        
        self.bg_color = theme['bg_color']
        self.text_color = theme['text_color']
        self.grid_color = theme['grid_color']
        self.line_colors = theme['line_colors']
    
    def _create_figure(self, figsize=(10, 6)):
        fig, ax = plt.subplots(figsize=figsize, dpi=self.dpi)
        ax.set_facecolor(self.bg_color)
        fig.patch.set_facecolor(self.bg_color)
        
        if self.show_grid:
            ax.grid(True, color=self.grid_color, linestyle='--', alpha=0.3)
        
        ax.tick_params(axis='both', colors=self.text_color)
        ax.xaxis.label.set_color(self.text_color)
        ax.yaxis.label.set_color(self.text_color)
        ax.title.set_color(self.text_color)
        
        return fig, ax
    
    def _save_figure(self, fig, file_path):
        plt.tight_layout()
        fig.savefig(file_path, dpi=self.dpi, bbox_inches='tight', facecolor=self.bg_color)
        plt.close(fig)
    
    def plot_spectrogram(self, audio_data, sample_rate, file_path):
        fig, ax = self._create_figure((12, 6))
        
        n_fft = 2048
        hop_length = 512
        
        D = librosa.amplitude_to_db(np.abs(librosa.stft(audio_data, n_fft=n_fft, hop_length=hop_length)), ref=np.max)
        
        img = librosa.display.specshow(D, sr=sample_rate, hop_length=hop_length, x_axis='time', y_axis='hz', ax=ax)
        ax.set_title('语谱图 (Spectrogram)')
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('频率 (Hz)')
        
        cbar = plt.colorbar(img, ax=ax)
        cbar.ax.tick_params(colors=self.text_color)
        cbar.set_label('振幅 (dB)', color=self.text_color)
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_pitch_contour(self, f0_values, sample_rate, file_path):
        fig, ax = self._create_figure((12, 5))
        
        hop_length = 512
        times = librosa.times_like(f0_values, sr=sample_rate, hop_length=hop_length)
        
        ax.plot(times, f0_values, color=self.line_colors[0], linewidth=2, label='F0')
        
        ax.set_title('基频轮廓图 (Pitch Contour)')
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('频率 (Hz)')
        
        ax.fill_between(times, f0_values, alpha=0.2, color=self.line_colors[0])
        ax.legend()
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_pitch_histogram(self, f0_values, file_path, male_range=[85, 155], female_range=[165, 255]):
        fig, ax = self._create_figure((10, 5))
        
        valid_f0 = f0_values[~np.isnan(f0_values)]
        
        ax.hist(valid_f0, bins=50, alpha=0.7, color=self.line_colors[0], edgecolor=self.bg_color)
        
        ax.axvspan(male_range[0], male_range[1], color='#3B82F6', alpha=0.3, label='男性典型区')
        ax.axvspan(female_range[0], female_range[1], color='#EC4899', alpha=0.3, label='女性典型区')
        
        ax.set_title('基频分布直方图 (F0 Distribution)')
        ax.set_xlabel('频率 (Hz)')
        ax.set_ylabel('帧数')
        ax.legend()
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_formants(self, f1_values, f2_values, f3_values, sample_rate, file_path):
        fig, ax = self._create_figure((12, 6))
        
        hop_length = 128
        times = np.arange(len(f1_values)) * hop_length / sample_rate
        
        ax.plot(times, f1_values, color=self.line_colors[0], linewidth=2, label='F1')
        ax.plot(times, f2_values, color=self.line_colors[1], linewidth=2, label='F2')
        ax.plot(times, f3_values, color=self.line_colors[2], linewidth=2, label='F3')
        
        ax.set_title('共振峰轨迹图 (Formant Trajectory)')
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('频率 (Hz)')
        ax.legend()
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_formant_scatter(self, f1_values, f2_values, file_path):
        fig, ax = self._create_figure((8, 8))
        
        ax.scatter(f1_values, f2_values, color=self.line_colors[0], alpha=0.6, s=50)
        
        ax.set_title('共振峰散点图 (F1 vs F2)')
        ax.set_xlabel('F1 (Hz)')
        ax.set_ylabel('F2 (Hz)')
        
        ax.invert_xaxis()
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_energy_envelope(self, energy_values, sample_rate, file_path):
        fig, ax = self._create_figure((12, 5))
        
        hop_length = 512
        times = librosa.times_like(energy_values, sr=sample_rate, hop_length=hop_length)
        
        ax.plot(times, energy_values, color=self.line_colors[3], linewidth=2)
        ax.fill_between(times, energy_values, alpha=0.2, color=self.line_colors[3])
        
        ax.set_title('能量包络图 (Energy Envelope)')
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('RMS 能量')
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_spectral_centroid(self, centroid_values, sample_rate, file_path):
        fig, ax = self._create_figure((12, 5))
        
        hop_length = 512
        times = librosa.times_like(centroid_values, sr=sample_rate, hop_length=hop_length)
        
        ax.plot(times, centroid_values, color=self.line_colors[4], linewidth=2)
        
        ax.set_title('频谱质心时变图 (Spectral Centroid)')
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('频率 (Hz)')
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_waveform(self, audio_data, sample_rate, file_path):
        fig, ax = self._create_figure((12, 4))
        
        times = np.arange(len(audio_data)) / sample_rate
        
        ax.plot(times, audio_data, color=self.line_colors[0], linewidth=1, alpha=0.7)
        ax.fill_between(times, audio_data, alpha=0.1, color=self.line_colors[0])
        
        ax.set_title('波形图 (Waveform)')
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('振幅')
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_gender_radar(self, scores, file_path):
        fig, ax = plt.subplots(figsize=(8, 8), dpi=self.dpi, subplot_kw=dict(polar=True))
        
        categories = ['基频', '共振峰', '音色', '韵律', '音质']
        values = [
            scores.get('gender_pitch_pct', 50),
            scores.get('gender_formant_pct', 50),
            scores.get('gender_timbre_pct', 50),
            scores.get('gender_prosody_pct', 50),
            scores.get('gender_quality_pct', 50)
        ]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]
        
        ax.fill(angles, values, color=self.line_colors[1], alpha=0.3)
        ax.plot(angles, values, color=self.line_colors[1], linewidth=2)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, color=self.text_color)
        ax.set_ylim(0, 100)
        
        ax.set_title('性别特征雷达图', color=self.text_color, y=1.05)
        
        fig.patch.set_facecolor(self.bg_color)
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_mel_spectrogram(self, audio_data, sample_rate, file_path):
        fig, ax = self._create_figure((12, 6))
        
        mel_spec = librosa.feature.melspectrogram(y=audio_data, sr=sample_rate)
        mel_spec_db = librosa.amplitude_to_db(mel_spec, ref=np.max)
        
        img = librosa.display.specshow(mel_spec_db, sr=sample_rate, x_axis='time', y_axis='mel', ax=ax)
        
        ax.set_title('梅尔频谱图 (Mel-spectrogram)')
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('频率 (Hz)')
        
        cbar = plt.colorbar(img, ax=ax)
        cbar.ax.tick_params(colors=self.text_color)
        cbar.set_label('振幅 (dB)', color=self.text_color)
        
        self._save_figure(fig, file_path)
        return file_path
    
    def plot_mfcc(self, mfcc_values, file_path):
        fig, ax = self._create_figure((12, 6))
        
        img = ax.imshow(np.array(mfcc_values), aspect='auto', origin='lower', cmap='viridis')
        
        ax.set_title('MFCC 热力图 (MFCC Heatmap)')
        ax.set_xlabel('时间帧')
        ax.set_ylabel('系数')
        
        cbar = plt.colorbar(img, ax=ax)
        cbar.ax.tick_params(colors=self.text_color)
        
        self._save_figure(fig, file_path)
        return file_path

import librosa
