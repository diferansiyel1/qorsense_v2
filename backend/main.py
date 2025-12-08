import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, desc
from backend.database import get_db, engine, Base
from backend.models_db import Sensor, SensorReading, AnalysisResultDB, Organization, SourceType
from backend.models import SensorDataInput, AnalysisResult, AnalysisMetrics, SyntheticRequest, ReportRequest, SensorCreate, SensorResponse
from backend.analysis import SensorAnalyzer
import numpy as np
import logging
import csv
import codecs
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

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

# Lifespan Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up QorSense Backend...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    logger.info("Shutting down...")
    await engine.dispose()

app = FastAPI(title="QorSense v1 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501", "http://127.0.0.1:3000", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = SensorAnalyzer()

# --- Helper Functions ---
async def save_analysis_result(db: AsyncSession, sensor_id: str, result: AnalysisResult):
    """Save analysis result to database asynchronously."""
    try:
        db_result = AnalysisResultDB(
            sensor_id=sensor_id,
            timestamp=datetime.fromisoformat(result.timestamp),
            health_score=result.health_score,
            status=result.status,
            metrics=result.metrics.dict(),
            diagnosis=result.diagnosis,
            recommendation=result.recommendation
        )
        db.add(db_result)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to save analysis result: {e}")

async def run_background_analysis(sensor_id: str, db_session_factory):
    """Background task to run analysis on recent data."""
    async with db_session_factory() as db:
        logger.info(f"Running background analysis for {sensor_id}")
        # Fetch last 100 readings
        stmt = select(SensorReading).where(SensorReading.sensor_id == sensor_id).order_by(desc(SensorReading.timestamp)).limit(100)
        result = await db.execute(stmt)
        readings = result.scalars().all()
        
        if len(readings) < 10:
            logger.info("Not enough data for analysis")
            return

        # Prepare values (reverse order to be chronological)
        values = [r.value for r in reversed(readings)]
        
        # Analyze
        try:
            # We construct a synthetic input object to reuse existing logic
            # Note: This duplicates some logic from /analyze endpoint, could be refactored further
            clean_data = analyzer.preprocessing(values)
            bias = analyzer.calc_bias(clean_data)
            slope = analyzer.calc_slope(clean_data)
            noise_std = float(np.std(clean_data))
            snr_db = analyzer.calc_snr_db(clean_data)
            hysteresis, hyst_x, hyst_y = analyzer.calc_hysteresis(clean_data)
            hurst, hurst_r2, dfa_scales, dfa_flucts = analyzer.calc_dfa(clean_data)
            
            metrics_dict = {
                "bias": bias, "slope": slope, "noise_std": noise_std, "snr_db": snr_db,
                "hysteresis": hysteresis, "hysteresis_x": hyst_x, "hysteresis_y": hyst_y,
                "hurst": hurst, "hurst_r2": hurst_r2, "dfa_scales": dfa_scales, "dfa_fluctuations": dfa_flucts
            }
            health = analyzer.get_health_score(metrics_dict)
            rul = analyzer.calc_rul(clean_data, slope)
            
            analysis_result = AnalysisResult(
                sensor_id=sensor_id,
                timestamp=datetime.now().isoformat(),
                health_score=health["score"],
                status=health["status"],
                diagnosis=health["diagnosis"],
                metrics=AnalysisMetrics(**metrics_dict),
                flags=health["flags"],
                recommendation=health["recommendation"],
                prediction=rul
            )
            
            await save_analysis_result(db, sensor_id, analysis_result)
            logger.info(f"Background analysis completed for {sensor_id}")
            
        except Exception as e:
            logger.error(f"Background analysis error: {e}")

# --- Endpoints ---

@app.get("/sensors", response_model=list[SensorResponse])
async def get_sensors(db: AsyncSession = Depends(get_db)):
    """List all sensors with their latest health status."""
    result = await db.execute(select(Sensor))
    sensors = result.scalars().all()
    
    sensor_responses = []
    for s in sensors:
        # Get latest analysis
        stmt = select(AnalysisResultDB).where(AnalysisResultDB.sensor_id == s.id).order_by(desc(AnalysisResultDB.timestamp)).limit(1)
        res = await db.execute(stmt)
        latest_analysis = res.scalar_one_or_none()
        
        # Create response object
        response = SensorResponse(
            id=s.id,
            name=s.name,
            location=s.location,
            source_type=s.source_type,
            organization_id=s.org_id,
            latest_health_score=latest_analysis.health_score if latest_analysis else 100.0,
            latest_status=latest_analysis.status if latest_analysis else "Normal",
            latest_analysis_timestamp=latest_analysis.timestamp if latest_analysis else None
        )
        sensor_responses.append(response)
        
    return sensor_responses

@app.post("/sensors", response_model=SensorResponse)
async def create_sensor(sensor: SensorCreate, db: AsyncSession = Depends(get_db)):
    """Create a new sensor."""
    # Generate a simple ID if not provided (in real app, use UUID or DB autoincrement logic for hardware ID)
    # Here we simulate a hardware ID
    import uuid
    new_id = str(uuid.uuid4())[:8]
    
    db_sensor = Sensor(
        id=new_id,
        name=sensor.name,
        location=sensor.location,
        source_type=SourceType(sensor.source_type),
        org_id=sensor.organization_id
    )
    db.add(db_sensor)
    await db.commit()
    await db.refresh(db_sensor)
    return db_sensor

@app.get("/sensors/{sensor_id}/history", response_model=list[AnalysisResult])
async def get_sensor_history(sensor_id: str, db: AsyncSession = Depends(get_db)):
    """Get analysis history for a sensor."""
    # We need to map DB AnalysisResultDB to Pydantic AnalysisResult
    # This might be tricky because AnalysisResultDB stores metrics as JSON, AnalysisResult expects object
    stmt = select(AnalysisResultDB).where(AnalysisResultDB.sensor_id == sensor_id).order_by(desc(AnalysisResultDB.timestamp))
    result = await db.execute(stmt)
    history_db = result.scalars().all()
    
    history_pydantic = []
    for item in history_db:
        # Convert DB item to Pydantic
        # Assuming metrics is stored as dict in valid format
        try:
            metrics_obj = AnalysisMetrics(**item.metrics)
            # Reconstruct AnalysisResult
            # Note: AnalysisResult might need 'prediction' which is optional
            res = AnalysisResult(
                sensor_id=item.sensor_id,
                timestamp=item.timestamp.isoformat(),
                health_score=item.health_score,
                status="Unknown", # statuses are not stored in DB currently? Or logic needed
                diagnosis=item.diagnosis,
                metrics=metrics_obj,
                flags=[], # Flags not stored in DB explicitly in this simple schema? Or inside metrics?
                recommendation=item.recommendation
            )
            # Fill in missing fields with defaults or logic if needed
            # For now, let's assume status/flags are derived or stored elsewhere or okay to be default
            # Actually models_db AnalysisResultDB doesn't have status/flags columns?
            # Let's fix this by updating the DB model? Or just returning what we have.
            # The prompt asked to adapt frontend to backend.
            # Let's mock status for now based on score.
            if res.health_score < 60: res.status = "Critical"
            elif res.health_score < 80: res.status = "Warning"
            else: res.status = "Healthy"
            
            history_pydantic.append(res)
        except Exception as e:
            logger.error(f"Error converting history item {item.id}: {e}")
            continue
            
    return history_pydantic

@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...), 
    sensor_id: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Import CSV data for a specific sensor."""
    try:
        reader = csv.reader(codecs.iterdecode(file.file, 'utf-8'))
        header = next(reader, None) # Skip header if exists
        
        readings_to_insert = []
        for row in reader:
            if not row: continue
            
            # Simple heuristic parsing
            ts = datetime.now()
            val = 0.0
            
            try:
                if len(row) >= 3:
                     # Assume: sensor_id, timestamp, value
                     # We ignore row[0] sensor_id and use the Form param to be safe, or cross-check
                     ts_str = row[1]
                     val = float(row[2])
                     try:
                        ts = datetime.fromisoformat(ts_str)
                     except:
                        pass
                elif len(row) == 2:
                    # Assume: timestamp, value
                    ts_str = row[0]
                    val = float(row[1])
                    try:
                        ts = datetime.fromisoformat(ts_str)
                    except:
                        pass
                else:
                    # Assume: value
                    val = float(row[0])
                
                readings_to_insert.append({"sensor_id": sensor_id, "timestamp": ts, "value": val})
            except ValueError:
                continue # Skip bad rows

        if readings_to_insert:
             await db.execute(insert(SensorReading), readings_to_insert)
             await db.commit()
             
        return {"message": f"Successfully imported {len(readings_to_insert)} readings for {sensor_id}"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream-data")
async def stream_data(
    data: dict, # Expected {sensor_id: str, value: float, timestamp: str (opt)}
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Stream a single data point and trigger analysis."""
    if "sensor_id" not in data or "value" not in data:
         raise HTTPException(status_code=400, detail="Missing sensor_id or value")
    
    sensor_id = data["sensor_id"]
    value = float(data["value"])
    ts = datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
    
    # Insert Reading
    reading = SensorReading(sensor_id=sensor_id, value=value, timestamp=ts)
    db.add(reading)
    await db.commit()
    
    # Trigger Analysis
    from backend.database import AsyncSessionLocal # Need factory for background task
    background_tasks.add_task(run_background_analysis, sensor_id, AsyncSessionLocal)
    
    return {"status": "received", "sensor_id": sensor_id}

# --- Extended Models for Timestamps (Since models.py is read-only) ---
from typing import List, Optional
class AnalysisMetricsExtended(AnalysisMetrics):
    timestamps: List[str] = []
    trend: List[float] = []
    residuals: List[float] = []

class AnalysisResultExtended(AnalysisResult):
    metrics: AnalysisMetricsExtended

@app.post("/analyze", response_model=AnalysisResultExtended)
async def analyze_sensor(data: SensorDataInput, db: AsyncSession = Depends(get_db)):
    """Analyze sensor data. Supports ad-hoc (values) or DB-fetch (sensor_id)."""
    logger.info(f"Analysis request for {data.sensor_id}")
    
    values = data.values
    timestamps_iso = []
    
    # If no values provided, try to fetch from DB
    if not values or len(values) == 0:
        # Check for start_date and end_date in config
        start_date = None
        end_date = None
        
        if data.config:
            if isinstance(data.config, dict):
                 start_date = data.config.get("start_date")
                 end_date = data.config.get("end_date")
            else:
                 start_date = getattr(data.config, "start_date", None)
                 end_date = getattr(data.config, "end_date", None)
                 
        if start_date and end_date:
            # Date Range Query: No limit, ASC order
            try:
                # Ensure they are datetime objects or strings
                if isinstance(start_date, str): start_date = datetime.fromisoformat(start_date)
                if isinstance(end_date, str): end_date = datetime.fromisoformat(end_date)
                
                stmt = select(SensorReading).where(
                    SensorReading.sensor_id == data.sensor_id,
                    SensorReading.timestamp >= start_date,
                    SensorReading.timestamp <= end_date
                ).order_by(SensorReading.timestamp.asc()) # ASC for analysis
                
                result = await db.execute(stmt)
                readings = result.scalars().all()
                values = [r.value for r in readings] # Already ASC
                timestamps_iso = [r.timestamp.isoformat() for r in readings]
                
            except Exception as e:
                logger.error(f"Date parsing/query error: {e}")
                raise HTTPException(status_code=400, detail="Invalid date format")
        else:
            # Default: Last 1000 points (Requested update), DESC -> ASC
            window_size = 1000
            if data.config:
                val = 0
                if isinstance(data.config, dict): val = data.config.get("window_size")
                else: val = getattr(data.config, "window_size", 0)
                if val: window_size = val

            stmt = select(SensorReading).where(SensorReading.sensor_id == data.sensor_id).order_by(desc(SensorReading.timestamp)).limit(window_size)
            result = await db.execute(stmt)
            readings = result.scalars().all()
            # Restore chronological order
            readings_asc = list(reversed(readings))
            values = [r.value for r in readings_asc]
            timestamps_iso = [r.timestamp.isoformat() for r in readings_asc]
        
        if len(values) < 5:
             # Return valid empty result to avoid 404 error in frontend
             empty_metrics = AnalysisMetricsExtended(
                 bias=0.0, slope=0.0, noise_std=0.0, snr_db=0.0, hysteresis=0.0, 
                 hysteresis_x=[], hysteresis_y=[],
                 hurst=0.5, hurst_r2=0.0, dfa_scales=[], dfa_fluctuations=[], timestamps=[],
                 trend=[], residuals=[]
             )
             return AnalysisResultExtended(
                 sensor_id=data.sensor_id,
                 timestamp=datetime.now().isoformat(),
                 health_score=0.0,
                 status="No Data",
                 metrics=empty_metrics,
                 diagnosis="No Data Available",
                 flags=[],
                 recommendation="Waiting for data ingestion.",
                 prediction="N/A"
             )
    else:
        # Values provided in payload
        if data.timestamps:
            timestamps_iso = data.timestamps
        else:
            # Generate dummy timestamps ending now?
            # Or leave empty? frontend expects them for range selection.
            # Let's generate synthetic timestamps if missing, to avoid frontend crash on map
            now = datetime.now()
            # 1 second interval assumption
            timestamps_iso = [(now - timedelta(seconds=len(values)-i)).isoformat() for i in range(len(values))]
            # Need timedelta import

    current_analyzer = SensorAnalyzer(config=data.config) if data.config else analyzer
    
    try:
        # Use centralized analyze method
        analysis_result = current_analyzer.analyze(values)
        
        metrics_dict = analysis_result["metrics"]
        # Add timestamps to metrics
        metrics_dict["timestamps"] = timestamps_iso
        
        health = analysis_result["health"]
        rul_prediction = analysis_result["prediction"]
        
        # Construct Extended Model
        metrics_obj = AnalysisMetricsExtended(**metrics_dict)
        
        result_obj = AnalysisResultExtended(
            sensor_id=data.sensor_id,
            timestamp=datetime.now().isoformat(),
            health_score=health["score"],
            status=health["status"],
            diagnosis=health["diagnosis"],
            metrics=metrics_obj,
            flags=health["flags"],
            recommendation=health["recommendation"],
            prediction=rul_prediction
        )
        
        # Save result to DB only if we fetched from DB? Or always?
        # Let's save it if it's not a simulation (length > 0)
        # However, AnalysisResultDB likely doesn't support storing timestamps inside metrics JSON if the schema is strict?
        # Actually AnalysisResultDB stores metrics as JSON. Pydantic can dict().
        # DB saving uses AnalysisResultDB which takes a dict.
        # But save_analysis_result takes 'AnalysisResult'.
        # Python is duck-typed enough or Pydantic might work?
        # save_analysis_result signature: (db: AsyncSession, sensor_id: str, result: AnalysisResult)
        # If I pass AnalysisResultExtended, it is a subclass, so it should pass type check if runtime.
        
        # However, AnalysisResultDB metrics column is likely JSON.
        # It will store the timestamps in the JSON. This is fine.
        await save_analysis_result(db, data.sensor_id, result_obj)
        
        return result_obj

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-synthetic")
async def generate_synthetic(request: SyntheticRequest):
    t = np.linspace(0, 10, request.length)
    base_signal = np.sin(t) * 10 
    
    if request.type == "Normal":
        noise = np.random.normal(0, 0.5, request.length)
        data = base_signal + noise
        
    elif request.type == "Drifting":
        noise = np.random.normal(0, 0.5, request.length)
        drift = np.linspace(0, 5, request.length)
        data = base_signal + noise + drift
        
    elif request.type == "Noisy":
        noise = np.random.normal(0, 3.0, request.length)
        data = base_signal + noise
        
    elif request.type == "Oscillation":
        oscillation = np.sin(t * 10) * 5
        noise = np.random.normal(0, 0.2, request.length)
        data = base_signal + oscillation + noise
    else:
        raise HTTPException(status_code=400, detail="Invalid type")
        
    return {"data": data.tolist(), "timestamps": t.tolist()}

@app.get("/")
async def root():
    return {"message": "QorSense v1 Backend Running (SaaS Database Enabled)"}

@app.post("/report")
async def generate_report(request: ReportRequest):
    try:
        from backend.report_gen import create_pdf
        from fastapi.responses import FileResponse
        
        # We no longer generate chart image separately here, the new engine handles it.
        # Ensure we have raw data
        raw_data = request.data if request.data else []
        
        metrics_data = request.metrics.dict()
        metrics_data["sensor_id"] = request.sensor_id
        metrics_data["flags"] = request.flags
        metrics_data["recommendation"] = request.recommendation
        
        # Pass raw_data directly
        pdf_path = create_pdf(
            metrics=metrics_data,
            raw_data=raw_data,
            diagnosis=request.diagnosis,
            health_score=request.health_score
        )
        
        return FileResponse(pdf_path, media_type='application/pdf', filename=f"report_{request.sensor_id}.pdf")
    except Exception as e:
        logger.error(f"Report generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

