from fastapi.testclient import TestClient
from backend.main import app
import unittest

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "QorSense v1 Backend Running"})

    def test_generate_synthetic(self):
        payload = {"type": "Normal", "length": 50}
        response = self.client.post("/generate-synthetic", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertEqual(len(data["data"]), 50)

    def test_analyze_flow(self):
        # 1. Generate data
        gen_resp = self.client.post("/generate-synthetic", json={"type": "Drifting", "length": 100})
        data_values = gen_resp.json()["data"]

        # 2. Analyze data
        payload = {
            "sensor_id": "TEST-SENSOR",
            "sensor_type": "Flow",
            "values": data_values,
        }
        response = self.client.post("/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertEqual(result["sensor_id"], "TEST-SENSOR")
        self.assertIn("health_score", result)
        self.assertIn("metrics", result)
        # Drifting data should have slope > 0
        self.assertGreater(abs(result["metrics"]["slope"]), 0.0)

    def test_analyze_invalid_data(self):
        payload = {
            "sensor_id": "TEST-SENSOR",
            "sensor_type": "Flow",
            "values": [1.0] * 10 # Insufficient data (<50)
        }
        response = self.client.post("/analyze", json=payload)
        # Should return 400 due to validation error
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
