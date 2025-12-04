# Changelog

All notable changes to the "QorSense v1" project will be documented in this file.

## [1.0.0] - 2025-12-03

### Added
- **Backend**:
    - FastAPI application with `/analyze` and `/generate-synthetic` endpoints.
    - `SensorAnalyzer` class with Bias, Slope, Noise (SNR), Hysteresis, and DFA (Hurst) algorithms.
    - PDF Report generation with `FPDF` and `Kaleido` for charts.
    - Logging configuration.
- **Frontend**:
    - Streamlit dashboard with "Dark Industrial" theme.
    - **New**: Live Monitoring Mode with real-time updates.
    - Interactive Plotly charts for Trend and Noise distribution.
    - Sidebar configuration for Sensor Type, Window Size, and Analysis Thresholds.
    - "Download Synthetic Data" and "Clear Data" features.
    - PDF Report download.
    - System Architecture diagram in "About" section.
- **Documentation**:
    - Comprehensive `README.md` with installation and usage instructions.
    - `walkthrough.md` for a quick tour.
    - Architecture diagrams.
- **DevOps**:
    - `run_demo.sh` for one-click startup with health checks.
    - `Makefile` for common tasks.
    - `setup.sh` for environment initialization.
    - Unit tests (`tests/test_analysis.py`) and API integration tests (`tests/test_api.py`).

### Fixed
- Handled deprecated Pandas `fillna` methods.
- Fixed `httpx` dependency for API testing.
- Improved robustness of `run_demo.sh` script.
