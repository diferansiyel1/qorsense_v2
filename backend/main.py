from fastapi import FastAPI, HTTPException
from backend.models import SensorDataInput, AnalysisResult, AnalysisMetrics, SyntheticRequest, ReportRequest
from backend.analysis import SensorAnalyzer
import numpy as np
import math
import logging
import os

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("backend.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="QorSense v1 API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"], # Next.js and Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = SensorAnalyzer()

from backend.models import SensorDataInput, AnalysisResult, AnalysisMetrics, SyntheticRequest, ReportRequest
from datetime import datetime

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_sensor(data: SensorDataInput):
    logger.info(f"Received analysis request for sensor: {data.sensor_id} (Type: {data.sensor_type})")
    
    # Initialize analyzer with config from request or default
    current_analyzer = SensorAnalyzer(config=data.config) if data.config else analyzer
    
    try:
        # Preprocessing
        clean_data = current_analyzer.preprocessing(data.values)
        
        # Calculate Metrics
        bias = current_analyzer.calc_bias(clean_data)
        slope = current_analyzer.calc_slope(clean_data)
        
        noise_std = float(np.std(clean_data))
        snr_db = current_analyzer.calc_snr_db(clean_data)
        hysteresis, hyst_x, hyst_y = current_analyzer.calc_hysteresis(clean_data)
        hurst, hurst_r2, dfa_scales, dfa_flucts = current_analyzer.calc_dfa(clean_data)
        
        metrics_dict = {
            "bias": bias,
            "slope": slope,
            "noise_std": noise_std,
            "snr_db": snr_db,
            "hysteresis": hysteresis,
            "hysteresis_x": hyst_x,
            "hysteresis_y": hyst_y,
            "hurst": hurst,
            "hurst_r2": hurst_r2,
            "dfa_scales": dfa_scales,
            "dfa_fluctuations": dfa_flucts
        }
        
        # Health Score
        health = current_analyzer.get_health_score(metrics_dict)
        
        # Prediction (RUL)
        rul_prediction = current_analyzer.calc_rul(clean_data, slope)
        
        return AnalysisResult(
            sensor_id=data.sensor_id,
            timestamp=datetime.now().isoformat(),
            health_score=health["score"],
            status=health["status"],
            diagnosis=health["diagnosis"],
            metrics=AnalysisMetrics(**metrics_dict),
            flags=health["flags"],
            recommendation=health["recommendation"],
            prediction=rul_prediction
        )
    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-synthetic")
async def generate_synthetic(request: SyntheticRequest):
    t = np.linspace(0, 10, request.length)
    base_signal = np.sin(t) * 10  # Base sine wave
    
    if request.type == "Normal":
        noise = np.random.normal(0, 0.5, request.length)
        data = base_signal + noise
        
    elif request.type == "Drifting":
        noise = np.random.normal(0, 0.5, request.length)
        drift = np.linspace(0, 5, request.length) # Linear drift
        data = base_signal + noise + drift
        
    elif request.type == "Noisy":
        noise = np.random.normal(0, 3.0, request.length) # High noise
        data = base_signal + noise
        
    elif request.type == "Oscillation":
        # High frequency oscillation added to base signal
        oscillation = np.sin(t * 10) * 5
        noise = np.random.normal(0, 0.2, request.length)
        data = base_signal + oscillation + noise
        
    else:
        raise HTTPException(status_code=400, detail="Invalid type")
        
    return {"data": data.tolist(), "timestamps": t.tolist()}

@app.get("/")
async def root():
    return {"message": "QorSense v1 Backend Running"}

@app.post("/report")
async def generate_report(request: ReportRequest):
    try:
        from backend.report_gen import create_pdf, generate_chart_image
        from fastapi.responses import FileResponse
        
        chart_path = None
        if request.data:
            chart_path = generate_chart_image(request.data)
        
        # Add sensor_id to metrics for report
        metrics_data = request.metrics.dict()
        metrics_data["sensor_id"] = request.sensor_id
        metrics_data["flags"] = request.flags
        metrics_data["recommendation"] = request.recommendation
        
        pdf_path = create_pdf(
            metrics=metrics_data,
            diagnosis=request.diagnosis,
            health_score=request.health_score,
            chart_image_path=chart_path
        )
        
        # Clean up chart image if created
        if chart_path and os.path.exists(chart_path):
             # We might want to keep it for a bit or rely on OS temp cleanup, 
             # but let's leave it for now to ensure PDF generation works.
             pass
        
        return FileResponse(
            pdf_path, 
            media_type='application/pdf', 
            filename=f"report_{request.sensor_id}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
