"use client";

import { useState, useEffect, useRef } from "react";
import { Sidebar } from "@/components/Sidebar";
import { MetricCard } from "@/components/MetricCard";
import { Charts } from "@/components/Charts";
import { api } from "@/lib/api";
import { AnalysisResult, SensorDataInput } from "@/types";
import { Button } from "@/components/ui/button";
import { PlayCircle, Download } from "lucide-react";

export default function Dashboard() {
  const [data, setData] = useState<number[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState(false);
  const [settings, setSettings] = useState<any>({});
  const [isLive, setIsLive] = useState(false);

  // Live Monitoring Loop
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLive) {
      interval = setInterval(async () => {
        // Simulate new data point
        const lastVal = data.length > 0 ? data[data.length - 1] : 10;
        const t = data.length;
        let newVal = lastVal;

        // Simple simulation logic based on previous "Live Scenario" (hardcoded to Normal for MVP live loop unless passed)
        // Ideally we pass live scenario from sidebar.
        // For now, let's just add random noise to simulate "Normal"
        newVal = 10 + Math.random() - 0.5;

        const newData = [...data, newVal].slice(-100); // Keep last 100
        setData(newData);

        // Auto-analyze
        if (newData.length >= 50) {
          handleAnalyze(newData);
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isLive, data]);

  // Initial Health Check
  useEffect(() => {
    api.healthCheck().then(setBackendStatus);
  }, []);

  const handleGenerate = async (type: string, length: number) => {
    setLoading(true);
    try {
      const newData = await api.generateSynthetic({ type: type as any, length });
      setData(newData);
      setAnalysis(null); // Reset analysis
    } catch (e) {
      console.error(e);
      alert("Failed to generate data");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (currentData: number[] = data) => {
    if (currentData.length < 50) return; // Ensure minimum data points

    try {
      const payload: SensorDataInput = {
        sensor_id: settings.sensorId || "SENSOR-001",
        sensor_type: settings.sensorType || "Flow",
        values: currentData,
        config: settings.config
      };
      const result = await api.analyze(payload);
      setAnalysis(result);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDownloadReport = async () => {
    if (!analysis) return;
    try {
      const blob = await api.generateReport(analysis, data);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${analysis.sensor_id}.pdf`);
      document.body.appendChild(link);
      link.click();
    } catch (e) {
      console.error(e);
      alert("Failed to download report");
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans">
      <Sidebar
        onGenerate={handleGenerate}
        onClear={() => { setData([]); setAnalysis(null); }}
        onSettingsChange={setSettings}
        backendStatus={backendStatus}
        isLive={isLive}
        onToggleLive={() => setIsLive(!isLive)}
        onDataLoad={(newData) => {
          setData(newData);
          setAnalysis(null);
        }}
      />

      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto space-y-8">

          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
              <p className="text-muted-foreground">Real-time sensor health monitoring</p>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => handleAnalyze()} disabled={data.length < 50 || isLive}>
                <PlayCircle className="mr-2 h-4 w-4" /> Run Analysis
              </Button>
              <Button variant="outline" onClick={handleDownloadReport} disabled={!analysis}>
                <Download className="mr-2 h-4 w-4" /> Export Report
              </Button>
            </div>
          </div>

          {/* Metrics Dashboard */}
          {analysis && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Health Gauge */}
              <div className="md:col-span-1 bg-card border rounded-xl p-6 flex flex-col items-center justify-center relative overflow-hidden">
                <h3 className="text-lg font-semibold mb-4">System Health</h3>
                <div className="relative w-48 h-48 flex items-center justify-center">
                  {/* Simple CSS Gauge */}
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="10" className="text-muted/20" />
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="10"
                      strokeDasharray={`${analysis.health_score * 2.83} 283`}
                      className={`${analysis.status === 'Green' ? 'text-green-500' :
                        analysis.status === 'Yellow' ? 'text-yellow-500' : 'text-red-500'
                        } transition-all duration-1000 ease-out`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-4xl font-bold">{analysis.health_score.toFixed(1)}</span>
                    <span className={`text-sm font-medium px-2 py-0.5 rounded-full mt-1 ${analysis.status === 'Green' ? 'bg-green-100 text-green-700' :
                      analysis.status === 'Yellow' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
                      }`}>
                      {analysis.status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Key Metrics & RUL */}
              <div className="md:col-span-2 grid grid-cols-2 lg:grid-cols-4 gap-4">
                {/* RUL Card */}
                <div className="col-span-2 bg-primary/5 border border-primary/20 rounded-xl p-4 flex flex-col justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Estimated RUL</p>
                    <h4 className="text-2xl font-bold mt-1">{analysis.prediction || "Calculating..."}</h4>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Time until critical threshold is reached based on current drift.
                  </p>
                </div>

                <MetricCard title="Bias" value={analysis.metrics.bias.toFixed(3)} />
                <MetricCard title="Slope" value={analysis.metrics.slope.toFixed(4)} />
                <MetricCard title="SNR (dB)" value={analysis.metrics.snr_db.toFixed(1)} />
                <MetricCard title="Hurst" value={analysis.metrics.hurst.toFixed(2)} />
                <MetricCard title="Hysteresis" value={analysis.metrics.hysteresis.toFixed(3)} />
                <MetricCard title="Noise Std" value={analysis.metrics.noise_std.toFixed(3)} />
              </div>
            </div>
          )}

          {/* Diagnosis & Flags */}
          {analysis && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className={`p-4 rounded-lg border ${analysis.status === 'Red' ? 'bg-red-100 border-red-200 text-red-900 dark:bg-red-900/30 dark:border-red-800 dark:text-red-200' :
                analysis.status === 'Yellow' ? 'bg-yellow-100 border-yellow-200 text-yellow-900 dark:bg-yellow-900/30 dark:border-yellow-800 dark:text-yellow-200' :
                  'bg-green-100 border-green-200 text-green-900 dark:bg-green-900/30 dark:border-green-800 dark:text-green-200'
                }`}>
                <h3 className="font-semibold mb-1">AI Diagnosis</h3>
                <p>{analysis.diagnosis}</p>
              </div>

              <div className="p-4 rounded-lg border bg-card text-card-foreground">
                <h3 className="font-semibold mb-1">Recommendation</h3>
                <p className="text-sm text-muted-foreground">{analysis.recommendation}</p>
                {analysis.flags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {analysis.flags.map(flag => (
                      <span key={flag} className="px-2 py-1 text-xs font-mono bg-destructive/10 text-destructive rounded border border-destructive/20">
                        {flag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Charts */}
          {data.length > 0 ? (
            <Charts
              data={data}
              windowSize={settings.windowSize || 100}
              metrics={analysis?.metrics}
            />
          ) : (
            <div className="flex items-center justify-center h-[400px] border-2 border-dashed border-muted rounded-lg">
              <div className="text-center text-muted-foreground">
                <p>No data available</p>
                <p className="text-sm">Generate synthetic data or start live monitoring to begin.</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
