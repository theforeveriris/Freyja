from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import numpy as np
from config import DATABASE_URL, DEFAULT_SETTINGS

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String(100))
    first_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    analysis_count = Column(Integer, default=0)
    settings = Column(Text, default=json.dumps(DEFAULT_SETTINGS))
    
    analyses = relationship('Analysis', back_populates='user')
    
    def get_settings(self):
        return json.loads(self.settings)
    
    def update_settings(self, new_settings):
        self.settings = json.dumps(new_settings)
    
    def increment_analysis_count(self):
        self.analysis_count += 1

class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    audio_path = Column(String(500), nullable=False)
    audio_duration = Column(Float)
    voiced_duration = Column(Float)
    analysis_date = Column(DateTime, default=datetime.now)
    sample_rate = Column(Integer)
    
    f0_mean = Column(Float)
    f0_median = Column(Float)
    f0_min = Column(Float)
    f0_max = Column(Float)
    
    f1_mean = Column(Float)
    f2_mean = Column(Float)
    f3_mean = Column(Float)
    
    rms_mean = Column(Float)
    
    gender_score = Column(Float)
    gender_pitch_pct = Column(Float)
    gender_formant_pct = Column(Float)
    gender_timbre_pct = Column(Float)
    gender_prosody_pct = Column(Float)
    gender_quality_pct = Column(Float)
    
    pitch_male_pct = Column(Float)
    pitch_female_pct = Column(Float)
    pitch_outside_pct = Column(Float)
    
    full_params = Column(Text)
    charts_generated = Column(Text, default='[]')
    
    user = relationship('User', back_populates='analyses')
    
    def get_full_params(self):
        return json.loads(self.full_params) if self.full_params else {}
    
    def get_charts_generated(self):
        return json.loads(self.charts_generated) if self.charts_generated else []
    
    def add_chart_generated(self, chart_type):
        charts = self.get_charts_generated()
        if chart_type not in charts:
            charts.append(chart_type)
            self.charts_generated = json.dumps(charts)

class Chart(Base):
    __tablename__ = 'charts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=False)
    chart_type = Column(String(50))
    file_path = Column(String(500))
    
    Index('idx_charts_analysis', analysis_id)

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    import os
    db_dir = os.path.dirname(DATABASE_URL.replace('sqlite:///', ''))
    os.makedirs(db_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _convert_numpy(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.float64):
        return float(obj)
    elif isinstance(obj, np.float32):
        return float(obj)
    elif isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, np.int32):
        return int(obj)
    elif isinstance(obj, dict):
        return {k: _convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy(item) for item in obj]
    return obj

def get_or_create_user(db, user_id, username=None, first_name=None):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def create_analysis(db, user_id, audio_path, params):
    serializable_params = _convert_numpy(params)
    
    analysis = Analysis(
        user_id=user_id,
        audio_path=audio_path,
        audio_duration=params.get('audio_duration'),
        voiced_duration=params.get('voiced_duration'),
        sample_rate=params.get('sample_rate'),
        f0_mean=params.get('f0_mean'),
        f0_median=params.get('f0_median'),
        f0_min=params.get('f0_min'),
        f0_max=params.get('f0_max'),
        f1_mean=params.get('f1_mean'),
        f2_mean=params.get('f2_mean'),
        f3_mean=params.get('f3_mean'),
        rms_mean=params.get('rms_mean'),
        gender_score=params.get('gender_score'),
        gender_pitch_pct=params.get('gender_pitch_pct'),
        gender_formant_pct=params.get('gender_formant_pct'),
        gender_timbre_pct=params.get('gender_timbre_pct'),
        gender_prosody_pct=params.get('gender_prosody_pct'),
        gender_quality_pct=params.get('gender_quality_pct'),
        pitch_male_pct=params.get('pitch_male_pct'),
        pitch_female_pct=params.get('pitch_female_pct'),
        pitch_outside_pct=params.get('pitch_outside_pct'),
        full_params=json.dumps(serializable_params)
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.increment_analysis_count()
        db.commit()
    
    return analysis

def get_analysis_by_id(db, analysis_id):
    return db.query(Analysis).filter(Analysis.id == analysis_id).first()

def get_user_analyses(db, user_id, limit=20, offset=0):
    return db.query(Analysis).filter(Analysis.user_id == user_id).order_by(Analysis.analysis_date.desc()).offset(offset).limit(limit).all()

def delete_analysis(db, analysis_id):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if analysis:
        db.delete(analysis)
        db.commit()
        return True
    return False

def delete_all_analyses(db, user_id):
    db.query(Analysis).filter(Analysis.user_id == user_id).delete()
    db.commit()
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.analysis_count = 0
        db.commit()
