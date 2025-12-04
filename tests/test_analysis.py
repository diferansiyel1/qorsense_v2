import unittest
import numpy as np
from backend.analysis import SensorAnalyzer

class TestSensorAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SensorAnalyzer()

    def test_preprocessing(self):
        # Need > 50 points
        data = [1.0] * 50
        data[25] = np.nan
        clean = self.analyzer.preprocessing(data)
        self.assertEqual(len(clean), 50)
        self.assertFalse(np.isnan(clean).any())

    def test_calc_bias(self):
        # 10 points. First 1 (10%) is 0. Last 1 is 10. Bias should be 10.
        data = np.array([0.0] + [5.0]*8 + [10.0])
        bias = self.analyzer.calc_bias(data)
        self.assertAlmostEqual(bias, 10.0)

    def test_calc_slope(self):
        # Perfect line y = x. Slope should be 1.
        data = np.arange(10, dtype=float)
        slope = self.analyzer.calc_slope(data)
        self.assertAlmostEqual(slope, 1.0)

    def test_calc_snr_db(self):
        # Constant data, signal pp = 0 (approx), noise = 0 (approx)
        # With 1e-6 and 1e-9 floors, it should be calculable.
        data = np.ones(50)
        snr = self.analyzer.calc_snr_db(data)
        # It won't be 0, but it should be valid float.
        self.assertIsInstance(snr, float)

    def test_health_score_perfect(self):
        metrics = {
            "bias": 0.0,
            "slope": 0.0,
            "noise_std": 0.0,
            "snr_db": 50.0, # High SNR is good
            "hysteresis": 0.0,
            "hurst": 0.5,
            "hurst_r2": 0.95
        }
        health = self.analyzer.get_health_score(metrics)
        self.assertEqual(health['score'], 100.0)
        self.assertEqual(health['status'], "Green")

    def test_health_score_custom_thresholds(self):
        metrics = {
            "bias": 1.5,
            "slope": 0.0,
            "noise_std": 0.0,
            "snr_db": 50.0,
            "hysteresis": 0.0,
            "hurst": 0.5,
            "hurst_r2": 0.95
        }
        
        from backend.models import SensorConfig
        config = SensorConfig(bias_critical=1.0) # Strict
            
        # We need to re-init analyzer with config or mock it, 
        # but get_health_score uses self.config.
        # So we create a new analyzer instance.
        analyzer_strict = SensorAnalyzer(config=config)
        
        health = analyzer_strict.get_health_score(metrics)
        # Bias 1.5 > 1.0 (Critical) -> -20 points
        self.assertEqual(health['score'], 80.0)

    def test_health_score_critical(self):
        metrics = {
            "bias": 5.0, # High bias
            "slope": 0.2, # High slope
            "noise_std": 2.0, 
            "snr_db": 5.0, # Low SNR (Critical)
            "hysteresis": 1.0,
            "hurst": 0.9, # High persistence
            "hurst_r2": 0.95
        }
        health = self.analyzer.get_health_score(metrics)
        self.assertTrue(health['score'] < 60)
        self.assertEqual(health['status'], "Red")

if __name__ == '__main__':
    unittest.main()
