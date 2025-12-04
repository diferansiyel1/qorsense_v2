from fpdf import FPDF
import tempfile
import os
import plotly.graph_objects as go

def generate_chart_image(data: list) -> str:
    """Generates a static image of the data trend."""
    try:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=data, mode='lines', name='Sensor Data'))
        fig.update_layout(
            title="Sensor Data Trend",
            xaxis_title="Time",
            yaxis_title="Value",
            width=800,
            height=400
        )
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig.write_image(temp_file.name)
        return temp_file.name
    except Exception as e:
        print(f"Chart generation failed: {e}")
        return None

def create_pdf(metrics: dict, diagnosis: str, health_score: float, chart_image_path: str = None) -> str:
    """Generates a PDF report and returns the file path."""
    pdf = FPDF()
    pdf.add_page()
    
    # Header with Color Bar
    pdf.set_fill_color(139, 92, 246) # Purple color matching new logo
    pdf.rect(0, 0, 210, 25, 'F')
    
    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        # Image(name, x, y, w, h)
        pdf.image(logo_path, x=10, y=2, h=20)
        
        # Adjust text position if logo exists
        pdf.set_xy(60, 5)
        pdf.set_font("Arial", "B", 24)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "QorSense", ln=True, align="L")
        
        pdf.set_xy(60, 15)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 5, "Industrial Sensor Health Report", ln=True, align="L")
    else:
        # Fallback to text only
        pdf.set_xy(10, 5)
        pdf.set_font("Arial", "B", 24)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "QorSense", ln=True, align="L")
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 5, "Industrial Sensor Health Report", ln=True, align="L")
    
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    
    # Sensor Info & Timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, f"Sensor ID: {metrics.get('sensor_id', 'N/A')}", ln=0)
    pdf.cell(0, 10, f"Date: {timestamp}", ln=1, align="R")
    pdf.line(10, 35, 200, 35)
    pdf.ln(5)
    
    # Health Score Section
    pdf.set_font("Arial", "B", 16)
    color = (0, 128, 0) if health_score >= 85 else (255, 165, 0) if health_score >= 60 else (255, 0, 0)
    pdf.set_text_color(*color)
    pdf.cell(0, 10, f"Health Score: {health_score:.1f} / 100", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Diagnosis
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "AI Diagnosis:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, diagnosis)
    pdf.ln(5)

    # Recommendation
    if metrics.get("recommendation"):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Recommendation:", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, metrics.get("recommendation"))
        pdf.ln(5)

    # Flags
    if metrics.get("flags"):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "System Flags:", ln=True)
        pdf.set_font("Arial", "", 10)
        # Join flags with comma or list them
        flags_str = ", ".join(metrics.get("flags"))
        pdf.multi_cell(0, 10, flags_str)
        pdf.ln(5)
    
    # Metrics Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Technical Metrics:", ln=True)
    pdf.set_font("Arial", "", 11)
    
    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, "Metric", 1, 0, 'C', 1)
    pdf.cell(60, 10, "Value", 1, 1, 'C', 1)
    
    # Table Rows
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            pdf.cell(60, 10, key.replace("_", " ").title(), 1)
            pdf.cell(60, 10, f"{value:.4f}", 1, 1)
        
    pdf.ln(10)
    
    # Chart
    if chart_image_path and os.path.exists(chart_image_path):
        pdf.image(chart_image_path, x=10, w=190)
        
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name
