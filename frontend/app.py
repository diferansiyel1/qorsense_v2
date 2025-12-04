import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import json
import math

# Configuration
API_URL = "http://localhost:8000"

st.set_page_config(page_title="QorSense v1", layout="wide", page_icon="🏭")

# Custom CSS for Industrial Design
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    .metric-card {
        background-color: #262730;
        border: 1px solid #41444C;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 173, 181, 0.3);
        border-color: #00ADB5;
    }
    .metric-label {
        color: #A6A9B6;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        color: #FAFAFA;
        font-size: 28px;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(45deg, #00ADB5, #007A80);
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #00FFF5, #00ADB5);
        color: #0E1117;
        box-shadow: 0 0 15px rgba(0, 173, 181, 0.6);
    }
    h1 {
        background: linear-gradient(90deg, #00ADB5, #EEEEEE);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Roboto', sans-serif;
    }
    h2, h3 {
        color: #00ADB5;
        font-family: 'Roboto', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🏭 Configuration")

data_source = st.sidebar.radio("Data Source", ["Generate Synthetic", "Upload CSV"])
sensor_type = st.sidebar.selectbox("Sensor Type", ["Flow", "Pressure", "Temperature"])
window_size = st.sidebar.slider("Analysis Window Size", 10, 500, 100)

with st.sidebar.expander("⚙️ Analysis Thresholds"):
    # Defaults
    defaults = {"t_slope": 0.1, "t_bias": 2.0, "t_noise": 1.5, "t_dfa": 0.8}
    
    # Initialize session state if not present
    if "t_slope" not in st.session_state: st.session_state.t_slope = defaults["t_slope"]
    if "t_bias" not in st.session_state: st.session_state.t_bias = defaults["t_bias"]
    if "t_noise" not in st.session_state: st.session_state.t_noise = defaults["t_noise"]
    if "t_dfa" not in st.session_state: st.session_state.t_dfa = defaults["t_dfa"]

    def reset_thresholds():
        st.session_state.t_slope = defaults["t_slope"]
        st.session_state.t_bias = defaults["t_bias"]
        st.session_state.t_noise = defaults["t_noise"]
        st.session_state.t_dfa = defaults["t_dfa"]

    st.button("Reset to Defaults", on_click=reset_thresholds)
    
    t_slope = st.slider("Critical Slope", 0.01, 0.5, key="t_slope", step=0.01)
    t_bias = st.slider("Critical Bias", 0.1, 10.0, key="t_bias", step=0.1)
    t_noise = st.slider("Critical Noise (Std)", 0.1, 5.0, key="t_noise", step=0.1)
    t_dfa = st.slider("Critical DFA (Hurst)", 0.5, 1.0, key="t_dfa", step=0.05)

st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ About QorSense"):
    st.markdown("""
    **Version:** 1.0.0
    **Engine:** Python 3.9+
    **Backend:** FastAPI
    **Frontend:** Streamlit
    
    Designed for predictive maintenance of industrial process sensors.
    
    [API Documentation (Swagger UI)](http://localhost:8000/docs)
    """)
    
    st.markdown("### 🏗 Architecture")
    st.markdown("""
    ```mermaid
    graph TD
        A[Sensor Data] -->|CSV/Synthetic| B(Streamlit Frontend)
        B -->|JSON| C{FastAPI Backend}
        C -->|Preprocessing| D[Analysis Engine]
        D -->|Bias/Slope/Noise| E[Health Score]
        D -->|DFA| E
        E -->|Result| B
        B -->|Request| F[PDF Report Gen]
        F -->|PDF| B
    ```
    """)

# Backend Status Check
st.sidebar.markdown("---")
st.sidebar.subheader("System Status")
try:
    health_check = requests.get(f"{API_URL}/", timeout=1)
    if health_check.status_code == 200:
        st.sidebar.success("Backend: ONLINE")
    else:
        st.sidebar.error(f"Backend: ERROR {health_check.status_code}")
except requests.exceptions.ConnectionError:
    st.sidebar.error("Backend: OFFLINE")

# Main Dashboard
st.title("QorSense v1 - Process Sensor Health Monitor")

# Mode Selection
mode = st.sidebar.radio("Operation Mode", ["Static Analysis", "Live Monitoring"])

if mode == "Live Monitoring":
    st.subheader("🔴 Live Sensor Monitoring")
    
    # Live Settings
    live_scenario = st.sidebar.selectbox("Live Scenario", ["Normal", "Drifting", "Oscillation"])
    refresh_rate = st.sidebar.slider("Refresh Rate (s)", 0.1, 2.0, 1.0, 0.1)
    
    col_start, col_stop = st.sidebar.columns(2)
    start_btn = col_start.button("Start Live")
    stop_btn = col_stop.button("Stop")
    
    if "live_running" not in st.session_state:
        st.session_state.live_running = False
        
    if start_btn:
        st.session_state.live_running = True
    if stop_btn:
        st.session_state.live_running = False
        
    # Placeholders for live updates
    ph_metrics = st.empty()
    ph_charts = st.empty()
    ph_diag = st.empty()
    
    # Initialize live data buffer if needed
    if "live_data" not in st.session_state:
        st.session_state.live_data = [10.0] * 50 # Start with some baseline
        
    import time
    import random
    
    if st.session_state.live_running:
        # Simulation Loop (one iteration per rerun, but we use a loop inside with sleep for smoother feel if needed, 
        # but Streamlit reruns script on interaction. For auto-update we need a loop with empty placeholders)
        
        # Actually, best way in Streamlit is a loop that updates placeholders and sleeps
        
        while st.session_state.live_running:
            # 1. Generate new point
            last_val = st.session_state.live_data[-1]
            t = len(st.session_state.live_data)
            
            new_val = last_val
            if live_scenario == "Normal":
                new_val = 10.0 + random.gauss(0, 0.5)
            elif live_scenario == "Drifting":
                new_val = 10.0 + (t * 0.05) + random.gauss(0, 0.5)
            elif live_scenario == "Oscillation":
                new_val = 10.0 + (5 * math.sin(t * 0.5)) + random.gauss(0, 0.2)
                
            st.session_state.live_data.append(new_val)
            # Keep buffer size constant-ish for display
            if len(st.session_state.live_data) > 100:
                st.session_state.live_data.pop(0)
                
            current_window = st.session_state.live_data
            
            # 2. Analyze
            try:
                payload = {
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "data": current_window,
                    "window_size": 5, # Smaller window for live
                    "thresholds": {
                        "slope_critical": st.session_state.t_slope,
                        "bias_critical": st.session_state.t_bias,
                        "noise_critical": st.session_state.t_noise,
                        "dfa_critical": st.session_state.t_dfa
                    }
                }
                resp = requests.post(f"{API_URL}/analyze", json=payload)
                if resp.status_code == 200:
                    results = resp.json()
                    
                    # Update Metrics
                    with ph_metrics.container():
                        c1, c2, c3, c4 = st.columns(4)
                        health_score = results["health_score"]
                        status = results["status"]
                        score_color = "#00FF00" if status == "Green" else "#FFA500" if status == "Yellow" else "#FF0000"
                        
                        with c1:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">Health Score</div>
                                <div class="metric-value" style="color: {score_color}">{health_score:.1f}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"""<div class="metric-card"><div class="metric-label">Bias</div><div class="metric-value">{results['metrics']['bias']:.2f}</div></div>""", unsafe_allow_html=True)
                        with c3:
                            st.markdown(f"""<div class="metric-card"><div class="metric-label">Slope</div><div class="metric-value">{results['metrics']['slope']:.3f}</div></div>""", unsafe_allow_html=True)
                        with c4:
                            st.markdown(f"""<div class="metric-card"><div class="metric-label">Noise</div><div class="metric-value">{results['metrics']['noise_std']:.2f}</div></div>""", unsafe_allow_html=True)

                    # Update Charts
                    with ph_charts.container():
                        fig = px.line(y=current_window, title="Live Sensor Data")
                        fig.update_layout(
                            plot_bgcolor="#262730", paper_bgcolor="#262730", font_color="#FAFAFA",
                            xaxis_title="Time", yaxis_title="Value", height=300,
                            margin=dict(l=20, r=20, t=40, b=20)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    # Update Diagnosis
                    with ph_diag.container():
                        if status == "Red":
                            st.error(f"⚠️ {results['diagnosis']}")
                        elif status == "Yellow":
                            st.warning(f"⚠️ {results['diagnosis']}")
                        else:
                            st.success(f"✅ {results['diagnosis']}")
                            
                time.sleep(refresh_rate)
                
            except Exception as e:
                st.error(f"Live Update Error: {e}")
                break

elif mode == "Static Analysis":
    # Data Loading
    data_values = []
    if data_source == "Generate Synthetic":
        scenario = st.sidebar.selectbox("Scenario", ["Normal", "Drifting", "Noisy", "Oscillation"])
        if st.sidebar.button("Generate Data"):
            try:
                resp = requests.post(f"{API_URL}/generate-synthetic", json={"type": scenario, "length": 200})
                if resp.status_code == 200:
                    data = resp.json()
                    data_values = data["data"]
                    st.session_state["data"] = data_values
                    st.success("Data Generated Successfully!")
                else:
                    st.error("Failed to generate data")
            except Exception as e:
                st.error(f"Connection Error: {e}")
                
        if "data" in st.session_state and data_source == "Generate Synthetic":
            # Convert to CSV for download
            df_download = pd.DataFrame({"value": st.session_state["data"]})
            csv = df_download.to_csv(index=False).encode('utf-8')
            st.sidebar.download_button(
                label="Download Generated Data (CSV)",
                data=csv,
                file_name="synthetic_sensor_data.csv",
                mime="text/csv",
            )
    elif data_source == "Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                numeric_cols = df.select_dtypes(include=['float', 'int']).columns.tolist()
                
                if len(numeric_cols) > 0:
                    # Allow user to select column if multiple exist
                    if len(numeric_cols) > 1:
                        target_col = st.sidebar.selectbox("Select Value Column", numeric_cols)
                    else:
                        target_col = numeric_cols[0]
                    
                    # Preview
                    st.sidebar.write(f"Selected: **{target_col}**")
                    st.sidebar.dataframe(df.head(3), height=100)
                    
                    data_values = df[target_col].tolist()
                    st.session_state["data"] = data_values
                else:
                    st.warning("No numeric columns found in CSV.")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    st.sidebar.markdown("---")
    sensor_id = st.sidebar.text_input("Sensor ID", value="SENSOR-001")

    if "data" in st.session_state and len(st.session_state["data"]) > 0:
        st.sidebar.markdown("### 📊 Quick Stats")
        data_series = pd.Series(st.session_state["data"])
        st.sidebar.write(f"**Count:** {len(data_series)}")
        st.sidebar.write(f"**Mean:** {data_series.mean():.2f}")
        st.sidebar.write(f"**Std:** {data_series.std():.2f}")

    if st.sidebar.button("Clear Data"):
        if "data" in st.session_state:
            del st.session_state["data"]
        st.rerun()

    # Use session state to persist data
    if "data" in st.session_state:
        data_values = st.session_state["data"]

    if data_values:
        # Analysis
        if st.button("Run Analysis"):
            payload = {
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "data": data_values,
                "window_size": window_size,
                "thresholds": {
                    "slope_critical": st.session_state.t_slope,
                    "bias_critical": st.session_state.t_bias,
                    "noise_critical": st.session_state.t_noise,
                    "dfa_critical": st.session_state.t_dfa
                }
            }
            try:
                resp = requests.post(f"{API_URL}/analyze", json=payload)
                if resp.status_code == 200:
                    results = resp.json()
                    
                    # Top Row: Metrics
                    c1, c2, c3, c4 = st.columns(4)
                    
                    health_score = results["health_score"]
                    status = results["status"]
                    score_color = "#00FF00" if status == "Green" else "#FFA500" if status == "Yellow" else "#FF0000"
                    
                    with c1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Health Score</div>
                            <div class="metric-value" style="color: {score_color}">{health_score:.1f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with c2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Bias</div>
                            <div class="metric-value">{results['metrics']['bias']:.3f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with c3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Slope</div>
                            <div class="metric-value">{results['metrics']['slope']:.4f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with c4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">DFA (Hurst)</div>
                            <div class="metric-value">{results['metrics']['dfa_hurst']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Middle Row: Charts
                    col_left, col_right = st.columns(2)
                    
                    with col_left:
                        st.subheader("Sensor Data Trend")
                        fig_trend = px.line(y=data_values, title="Raw Data", markers=True)
                        
                        # Highlight Reference Window (First 10%)
                        ref_window = max(1, int(len(data_values) * 0.1))
                        fig_trend.add_vrect(
                            x0=0, x1=ref_window,
                            fillcolor="green", opacity=0.1,
                            layer="below", line_width=0,
                            annotation_text="Reference", annotation_position="top left"
                        )
                        
                        fig_trend.update_layout(
                            plot_bgcolor="#262730",
                            paper_bgcolor="#262730",
                            font_color="#FAFAFA",
                            xaxis_title="Time Step",
                            yaxis_title="Sensor Value"
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                        
                    with col_right:
                        st.subheader("Noise Distribution")
                        fig_hist = px.histogram(x=data_values, nbins=30, title="Value Distribution")
                        fig_hist.update_layout(
                            plot_bgcolor="#262730",
                            paper_bgcolor="#262730",
                            font_color="#FAFAFA",
                            xaxis_title="Sensor Value",
                            yaxis_title="Count"
                        )
                        st.plotly_chart(fig_hist, use_container_width=True)
                    
                    # Bottom Row: Diagnostics
                    st.subheader("AI Diagnosis")
                    st.info(results["diagnosis"])
                    
                    # Report Generation
                    st.subheader("Report")
                    if st.button("Generate PDF Report"):
                        try:
                            # We need to send the full result back to the report endpoint
                            # Construct ReportRequest payload
                            report_payload = results
                            report_payload["data"] = data_values # Add the raw data
                            
                            with st.spinner("Generating Report..."):
                                resp_pdf = requests.post(f"{API_URL}/report", json=report_payload)
                                
                                if resp_pdf.status_code == 200:
                                    st.download_button(
                                        label="Download PDF",
                                        data=resp_pdf.content,
                                        file_name=f"sensor_report_{payload['sensor_id']}.pdf",
                                        mime="application/pdf"
                                    )
                                else:
                                    st.error(f"Report Generation Failed: {resp_pdf.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                        
                else:
                    st.error(f"Analysis Failed: {resp.text}")
            except Exception as e:
                st.error(f"API Connection Error: {e}. Make sure backend is running.")
else:
    # Landing Page Content
    st.markdown("""
    ### 👋 Welcome to QorSense v1
    
    This application demonstrates **predictive maintenance** capabilities for industrial sensors.
    
    #### 🚀 How to use:
    1.  **Select Data Source**: Choose **"Generate Synthetic"** in the sidebar to simulate sensor behavior.
    2.  **Choose Scenario**: 
        - **Normal**: Healthy sensor operation.
        - **Drifting**: Simulates a gradual calibration drift (linear trend).
        - **Noisy**: Simulates sensor degradation via increased variance.
    3.  **Generate & Analyze**: Click **"Generate Data"** then **"Run Analysis"**.
    
    #### 🧠 Algorithms Used:
    - **Bias & Slope**: Detects systematic offsets and trends.
    - **DFA (Detrended Fluctuation Analysis)**: Advanced fractal analysis to detect long-term persistence (early warning for drift).
    - **Signal-to-Noise Ratio**: Monitors signal quality.
    
    *Select an option in the sidebar to get started.*
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 12px;">
        © 2025 QorSense Technologies | v1.0.0-beta | Industrial AI Division
    </div>
    """,
    unsafe_allow_html=True
)
