export interface SensorConfig {
    slope_critical: number;
    slope_warning: number;
    bias_critical: number;
    bias_warning: number;
    noise_critical: number;
    hysteresis_critical: number;
    dfa_critical: number;
    min_data_points: number;
}

export interface SensorDataInput {
    sensor_id: string;
    sensor_type: string;
    values: number[];
    timestamps?: string[];
    config?: SensorConfig;
}

export interface AnalysisMetrics {
    bias: number;
    slope: number;
    noise_std: number;
    snr_db: number;
    hysteresis: number;
    hurst: number;
    hurst_r2: number;
}

export interface AnalysisResult {
    sensor_id: string;
    timestamp: string;
    health_score: number;
    status: "Green" | "Yellow" | "Red";
    diagnosis: string;
    metrics: AnalysisMetrics;
    flags: string[];
    recommendation: string;
    prediction?: string;
}

export interface SyntheticRequest {
    type: "Normal" | "Drifting" | "Noisy" | "Oscillation";
    length: number;
}

export interface SyntheticResponse {
    data: number[];
}
