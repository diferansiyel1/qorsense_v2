import numpy as np
import pandas as pd
from scipy import stats, signal
from typing import Dict, Any, List, Tuple
import logging
from datetime import datetime
from backend.models import SensorConfig

logger = logging.getLogger(__name__)

class SensorAnalyzer:
    def __init__(self, config: SensorConfig = SensorConfig()):
        self.config = config

    def preprocessing(self, data: list) -> np.ndarray:
        """
        Preprocessing pipeline:
        1. Gap check (simple)
        2. Interpolation
        3. Median Filter (Spike removal)
        """
        if len(data) < self.config.min_data_points:
            raise ValueError(f"Insufficient data: {len(data)} points provided, minimum {self.config.min_data_points} required.")

        s = pd.Series(data)
        
        # Gap Limit: Don't fill large gaps (simplified logic here as we don't have timestamps in list)
        # Assuming uniform sampling for now.
        s = s.interpolate(method='linear', limit=5).bfill().ffill()
        
        # Median Filter for Spikes
        # Kernel size 3 or 5 usually good
        s_clean = signal.medfilt(s.values, kernel_size=3)
        
        return s_clean

    def calc_bias(self, data: np.ndarray) -> float:
        """Calculate offset from mean of first 10% vs current."""
        if len(data) < 10: return 0.0
        n_ref = max(1, int(len(data) * 0.1))
        ref_mean = np.mean(data[:n_ref])
        curr_mean = np.mean(data[-n_ref:])
        return float(curr_mean - ref_mean)

    def calc_slope(self, data: np.ndarray) -> float:
        """Calculate linear trend slope."""
        if len(data) < 2: return 0.0
        x = np.arange(len(data))
        slope, _, _, _, _ = stats.linregress(x, data)
        return float(slope)

    def calc_snr_db(self, data: np.ndarray) -> float:
        """
        Calculate SNR in dB.
        Signal = Peak-to-Peak
        Noise = RMS of high-pass filtered signal (or residual after detrending)
        """
        if len(data) < 2: return 0.0
        
        # 1. Estimate Signal Amplitude (Peak-to-Peak)
        # We use the raw range, or robust range (percentiles) to avoid outliers
        signal_pp = np.percentile(data, 95) - np.percentile(data, 5)
        if signal_pp == 0: signal_pp = 1e-6

        # 2. Isolate Noise (High-pass filter or Detrend)
        # Simple approach: Subtract linear trend
        x = np.arange(len(data))
        slope, intercept, _, _, _ = stats.linregress(x, data)
        trend = slope * x + intercept
        noise_component = data - trend
        
        # RMS of noise
        noise_rms = np.sqrt(np.mean(noise_component**2))
        if noise_rms < 1e-9: noise_rms = 1e-9
        
        # 3. Calculate SNR (dB)
        snr_db = 20 * np.log10(signal_pp / noise_rms)
        return float(snr_db)

    def calc_hysteresis(self, data: np.ndarray) -> Tuple[float, List[float], List[float]]:
        """
        Calculate Hysteresis based on Area Difference between Rising and Falling edges.
        Simplified Edge Detection.
        """
        if len(data) < 5: return 0.0, [], []
        
        # Smooth heavily to find "edges" (macro movements)
        smooth = pd.Series(data).rolling(window=5, center=True).mean().bfill().ffill().values
        diffs = np.diff(smooth)
        
        # Threshold for "edge"
        threshold = np.std(diffs) * 0.5
        
        rising_indices = np.where(diffs > threshold)[0]
        falling_indices = np.where(diffs < -threshold)[0]
        
        if len(rising_indices) == 0 or len(falling_indices) == 0:
            return 0.0, [], []
            
        avg_rising_val = np.mean(data[rising_indices])
        avg_falling_val = np.mean(data[falling_indices])
        
        # Area difference proxy: Difference in average values during rising vs falling phases
        # Normalized by range
        data_range = np.ptp(data) if np.ptp(data) > 0 else 1.0
        hysteresis_score = abs(avg_rising_val - avg_falling_val) / data_range
        
        return float(hysteresis_score), data.tolist(), smooth.tolist()

    def calc_dfa(self, data: np.ndarray, order: int = 1) -> Tuple[float, float, List[float], List[float]]:
        """
        DFA with R^2 calculation.
        Returns: (hurst, r_squared, scales, fluctuations)
        """
        try:
            if len(data) == 0: return 0.5, 0.0, [], []

            y = np.cumsum(data - np.mean(data))
            N = len(y)
            if N < 20: return 0.5, 0.0, [], []

            min_scale = 4
            max_scale = N // 4
            if max_scale < min_scale: return 0.5, 0.0, [], []
            
            scales = np.unique(np.logspace(np.log10(min_scale), np.log10(max_scale), num=20).astype(int))
            scales = scales[scales > order + 2]
            
            if len(scales) < 3:
                 scales = np.arange(min_scale, max_scale, max(1, (max_scale - min_scale) // 5))
                 scales = np.unique(scales.astype(int))
                 scales = scales[scales > order + 2]

            if len(scales) < 2: return 0.5, 0.0, [], []

            fluctuations = []
            
            # Vectorized-ish loop (still loop over scales, but inner operations are numpy)
            for scale in scales:
                n_segments = N // scale
                # Reshape data into (n_segments, scale) - truncating end
                segments = y[:n_segments*scale].reshape(n_segments, scale)
                x = np.arange(scale)
                
                # Polyfit for each segment? 
                # np.polyfit can handle multiple columns if we transpose, but let's keep loop for safety/clarity first
                # Optimization:
                total_residual_sq = 0.0
                for seg in segments:
                    coeffs = np.polyfit(x, seg, order)
                    trend = np.polyval(coeffs, x)
                    total_residual_sq += np.sum((seg - trend) ** 2)
                
                f_n = np.sqrt(total_residual_sq / (n_segments * scale))
                fluctuations.append(f_n)
            
            fluctuations = np.array(fluctuations)
            valid_idx = fluctuations > 1e-10
            if np.sum(valid_idx) < 3: return 0.5, 0.0, [], []
                
            log_scales = np.log(scales[valid_idx])
            log_flucts = np.log(fluctuations[valid_idx])
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(log_scales, log_flucts)
            
            return float(slope), float(r_value**2), scales[valid_idx].tolist(), fluctuations[valid_idx].tolist()
            
        except Exception as e:
            logger.warning(f"DFA Calculation Error: {e}")
            return 0.5, 0.0, [], []

    def get_trend_line(self, data: np.ndarray) -> Dict[str, List[float]]:
        """Generate coordinates for the linear regression line."""
        if len(data) < 2: return {"x": [], "y": []}
        x = np.arange(len(data))
        slope, intercept, _, _, _ = stats.linregress(x, data)
        trend_y = slope * x + intercept
        return {"x": x.tolist(), "y": trend_y.tolist()}

    def calc_rul(self, data: np.ndarray, slope: float) -> str:
        """
        Calculate Estimated Remaining Useful Life (RUL).
        Based on linear projection of current trend towards critical bias threshold.
        """
        if abs(slope) < 1e-6:
            return "Stable (> 1 year)"
            
        # Current "level" (intercept of trend at end)
        x = np.arange(len(data))
        _, intercept, _, _, _ = stats.linregress(x, data)
        current_val = slope * (len(data) - 1) + intercept
        
        # Distance to critical threshold
        # We assume critical threshold is defined relative to 0 (absolute bias)
        # In reality, it should be relative to initial baseline, but here data is raw.
        # Let's assume critical deviation is from the *initial* value.
        initial_val = data[0] if len(data) > 0 else 0
        
        # Thresholds
        upper_limit = initial_val + self.config.bias_critical
        lower_limit = initial_val - self.config.bias_critical
        
        if slope > 0:
            dist = upper_limit - current_val
        else:
            dist = current_val - lower_limit
            
        if dist <= 0:
            return "Critical Threshold Exceeded"
            
        # Time steps remaining
        steps = dist / abs(slope)
        
        # Convert steps to time (assuming 1 step = 1 second for demo)
        if steps > 3600 * 24 * 365:
            return "Stable (> 1 year)"
        elif steps > 3600 * 24:
            days = int(steps / (3600 * 24))
            return f"{days} days"
        elif steps > 3600:
            hours = int(steps / 3600)
            return f"{hours} hours"
        else:
            mins = int(steps / 60)
            return f"{mins} mins"

    def get_health_score(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Calculate weighted health score based on config."""
        score = 100.0
        diagnosis = []
        flags = []
        recommendation = "System operating normally."
        
        # Slope
        slope = abs(metrics.get("slope", 0))
        if slope > self.config.slope_critical:
            score -= 25
            diagnosis.append("Critical Trend Drift")
            flags.append("DRIFT_CRITICAL")
            recommendation = "Immediate calibration required."
        elif slope > self.config.slope_warning:
            score -= 15
            diagnosis.append("Moderate Trend Drift")
            flags.append("DRIFT_WARNING")
            recommendation = "Schedule maintenance check."
            
        # Bias
        bias = abs(metrics.get("bias", 0))
        if bias > self.config.bias_critical:
            score -= 20
            diagnosis.append("Significant Bias Shift")
            flags.append("BIAS_CRITICAL")
        elif bias > self.config.bias_warning:
            score -= 10
            diagnosis.append("Minor Bias Shift")
            flags.append("BIAS_WARNING")

        # Noise (SNR)
        # Low SNR is bad.
        snr_db = metrics.get("snr_db", 100)
        # Assuming typical industrial sensor: < 20dB is noisy, < 10dB is critical
        if snr_db < 10:
            score -= 20
            diagnosis.append("Critical Signal Noise")
            flags.append("LOW_SNR_CRITICAL")
            recommendation = "Check sensor wiring and shielding."
        elif snr_db < 20:
            score -= 10
            diagnosis.append("High Noise Level")
            flags.append("LOW_SNR_WARNING")
        
        # Hysteresis
        hyst = metrics.get("hysteresis", 0)
        if hyst > self.config.hysteresis_critical:
            score -= 10
            diagnosis.append("Hysteresis Detected")
            flags.append("HYSTERESIS")

        # DFA
        hurst = metrics.get("hurst", 0.5)
        hurst_r2 = metrics.get("hurst_r2", 0.0)
        
        if hurst_r2 < 0.9:
            diagnosis.append("DFA Unreliable (Low R2)")
            flags.append("DFA_UNRELIABLE")
        else:
            if hurst > self.config.dfa_critical:
                score -= 30
                diagnosis.append("Strong Persistence (Drift/Memory)")
                flags.append("DFA_PERSISTENCE")
            elif hurst < 0.2:
                score -= 10
                diagnosis.append("Strong Anti-persistence")
                flags.append("DFA_ANTIPERSISTENCE")

        score = max(0.0, min(100.0, score))
        
        status = "Green"
        if score < 60: status = "Red"
        elif score < 85: status = "Yellow"
            
        if not diagnosis:
            diagnosis.append("System Normal")
            
        return {
            "score": score,
            "status": status,
            "diagnosis": "; ".join(diagnosis),
            "flags": flags,
            "recommendation": recommendation
        }
