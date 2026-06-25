import numpy as np

class GenderClassifier:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.weights = self.settings.get('weights', {
            'pitch': 60,
            'formant': 15,
            'timbre': 10,
            'prosody': 8,
            'quality': 7
        })
        self.male_f0_range = self.settings.get('male_f0_range', [85, 155])
        self.female_f0_range = self.settings.get('female_f0_range', [165, 255])
        self.baseline = self.settings.get('baseline', 'female')
    
    def classify(self, params):
        pitch_score = self._calculate_pitch_score(params)
        formant_score = self._calculate_formant_score(params)
        timbre_score = self._calculate_timbre_score(params)
        prosody_score = self._calculate_prosody_score(params)
        quality_score = self._calculate_quality_score(params)

        print(f"[性别评分] 基频: {pitch_score:.3f} (f0={params.get('f0_mean'):.1f}Hz)", flush=True)
        print(f"[性别评分] 共振峰: {formant_score:.3f} (F1={params.get('f1_mean'):.1f}Hz, F2={params.get('f2_mean'):.1f}Hz)", flush=True)
        print(f"[性别评分] 音色: {timbre_score:.3f} (centroid={params.get('spectral_centroid_mean'):.1f}Hz, rolloff={params.get('spectral_rolloff_mean'):.1f}Hz)", flush=True)
        print(f"[性别评分] 韵律: {prosody_score:.3f} (range={params.get('intonation_range'):.1f}Hz, rate={params.get('speech_rate'):.2f})", flush=True)
        print(f"[性别评分] 音质: {quality_score:.3f} (hnr={params.get('hnr'):.1f}dB)", flush=True)
        
        overall_score = pitch_score
        
        pitch_distribution = self._calculate_pitch_distribution(params)
        
        return {
            'gender_score': overall_score * 100,
            'gender_pitch_pct': pitch_score * 100,
            'gender_formant_pct': formant_score * 100,
            'gender_timbre_pct': timbre_score * 100,
            'gender_prosody_pct': prosody_score * 100,
            'gender_quality_pct': quality_score * 100,
            'pitch_male_pct': pitch_distribution['male'],
            'pitch_female_pct': pitch_distribution['female'],
            'pitch_outside_pct': pitch_distribution['outside']
        }
    
    def _calculate_pitch_score(self, params):
        f0_mean = params.get('f0_mean', np.nan)
        
        if np.isnan(f0_mean):
            return 0.5
        
        male_min, male_max = self.male_f0_range
        female_min, female_max = self.female_f0_range
        
        mid_point = (male_max + female_min) / 2
        
        if f0_mean <= male_min:
            return 0.0
        elif f0_mean <= male_max:
            return 0.25 * (f0_mean - male_min) / (male_max - male_min)
        elif f0_mean <= female_min:
            return 0.25 + 0.5 * (f0_mean - male_max) / (female_min - male_max)
        elif f0_mean <= female_max:
            return 0.75 + 0.25 * (f0_mean - female_min) / (female_max - female_min)
        else:
            return 1.0
    
    def _calculate_formant_score(self, params):
        f1 = params.get('f1_mean', np.nan)
        f2 = params.get('f2_mean', np.nan)
        
        if np.isnan(f1) or np.isnan(f2):
            return 0.5
        
        male_f1_mean = 500
        male_f2_mean = 1500
        female_f1_mean = 700
        female_f2_mean = 2000
        
        f1_norm = (f1 - male_f1_mean) / (female_f1_mean - male_f1_mean) if female_f1_mean > male_f1_mean else 0
        f2_norm = (f2 - male_f2_mean) / (female_f2_mean - male_f2_mean) if female_f2_mean > male_f2_mean else 0
        
        score = (f1_norm + f2_norm) / 2
        
        return max(0, min(1, score))
    
    def _calculate_timbre_score(self, params):
        centroid = params.get('spectral_centroid_mean', np.nan)
        rolloff = params.get('spectral_rolloff_mean', np.nan)
        
        if np.isnan(centroid):
            return 0.5
        
        male_centroid = 2000
        female_centroid = 3500
        
        centroid_norm = (centroid - male_centroid) / (female_centroid - male_centroid) if female_centroid > male_centroid else 0
        
        if not np.isnan(rolloff):
            male_rolloff = 4000
            female_rolloff = 7000
            rolloff_norm = (rolloff - male_rolloff) / (female_rolloff - male_rolloff) if female_rolloff > male_rolloff else 0
            score = (centroid_norm + rolloff_norm) / 2
        else:
            score = centroid_norm
        
        return max(0, min(1, score))
    
    def _calculate_prosody_score(self, params):
        intonation_range = params.get('intonation_range', np.nan)
        speech_rate = params.get('speech_rate', np.nan)
        
        if np.isnan(intonation_range):
            return 0.5
        
        male_range = 50
        female_range = 150
        
        range_norm = (intonation_range - male_range) / (female_range - male_range) if female_range > male_range else 0
        
        if not np.isnan(speech_rate):
            male_rate = 3
            female_rate = 5
            rate_norm = (speech_rate - male_rate) / (female_rate - male_rate) if female_rate > male_rate else 0
            score = (range_norm + rate_norm) / 2
        else:
            score = range_norm
        
        return max(0, min(1, score))
    
    def _calculate_quality_score(self, params):
        hnr = params.get('hnr', np.nan)
        
        if np.isnan(hnr):
            return 0.5
        
        male_hnr = 5
        female_hnr = 15
        
        hnr_norm = (hnr - male_hnr) / (female_hnr - male_hnr) if female_hnr > male_hnr else 0
        
        return max(0, min(1, hnr_norm))
    
    def _calculate_pitch_distribution(self, params):
        f0_values = params.get('f0_values', [])
        
        if f0_values is None or len(f0_values) == 0:
            return {'male': 0, 'female': 0, 'outside': 0}
        
        f0_values = np.array(f0_values)
        valid_f0 = f0_values[~np.isnan(f0_values)]
        
        if len(valid_f0) == 0:
            return {'male': 0, 'female': 0, 'outside': 0}
        
        male_min, male_max = self.male_f0_range
        female_min, female_max = self.female_f0_range
        
        male_count = np.sum((valid_f0 >= male_min) & (valid_f0 <= male_max))
        female_count = np.sum((valid_f0 >= female_min) & (valid_f0 <= female_max))
        outside_count = len(valid_f0) - male_count - female_count
        
        total = len(valid_f0)
        
        return {
            'male': (male_count / total) * 100,
            'female': (female_count / total) * 100,
            'outside': (outside_count / total) * 100
        }
