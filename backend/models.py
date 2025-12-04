from pydantic import BaseModel
from typing import List, Optional

class SensorConfig(BaseModel):
    slope_critical: float = 0.1
    slope_warning: float = 0.05
    bias_critical: float = 2.0
    bias_warning: float = 1.0
    noise_critical: float = 1.5
    hysteresis_critical: float = 0.5
    dfa_critical: float = 0.8
    min_data_points: int = 50

class SensorDataInput(BaseModel):
    sensor_id: str
    sensor_type: str
    values: List[float]
    timestamps: Optional[List[str]] = None
    config: Optional[SensorConfig] = SensorConfig()

class AnalysisMetrics(BaseModel):
    bias: float
    slope: float
    noise_std: float
    snr_db: float
    hysteresis: float
    hurst: float
    hurst_r2: float

class AnalysisResult(BaseModel):
    sensor_id: str
    timestamp: str
    health_score: float
    status: str
    metrics: AnalysisMetrics
    flags: List[str]
    recommendation: str
    diagnosis: str
    prediction: Optional[str] = None

class SyntheticRequest(BaseModel):
    type: str
    length: int = 100

class ReportRequest(BaseModel):
    sensor_id: str
    health_score: float
    status: str
    metrics: AnalysisMetrics
    diagnosis: str
    flags: List[str] = []
    recommendation: str = ""
    data: Optional[List[float]] = None
