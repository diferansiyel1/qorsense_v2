"use client";

import { useState, useEffect } from 'react';
import { SmartSensorCard } from "@/components/SmartSensorCard";
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer, YAxis, CartesianGrid } from 'recharts';
import { Activity, ShieldAlert, Microscope } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { api, Sensor } from "@/lib/api";
import { AddSensorModal } from "@/components/AddSensorModal";

// Mock data ONLY for the aggregate chart for now, as we don't have an aggregate endpoint
const deviationData = [
    { time: '00:00', value: 0.12 },
    { time: '04:00', value: 0.15 },
    { time: '08:00', value: 0.28 },
    { time: '12:00', value: 0.45 },
    { time: '16:00', value: 0.42 },
    { time: '20:00', value: 0.38 },
    { time: '24:00', value: 0.35 },
];

export default function Dashboard() {
    const [sensors, setSensors] = useState<any[]>([]); // Using any to mix Sensor + UI props
    const [loading, setLoading] = useState(true);

    const fetchSensors = async () => {
        setLoading(true);
        try {
            const data = await api.getSensors();
            // Map API data to UI compatible format
            // Since we don't have health/status in Sensor model yet, we mock/defaults
            const mapped = data.map(s => ({
                id: s.id,
                name: s.name,
                location: s.location,
                healthScore: s.health_score ?? 0,
                status: s.status ?? 'Unknown',
                type: s.source_type
            }));
            setSensors(mapped);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSensors();
    }, []);

    const handleSensorCreated = (newSensor: Sensor) => {
        // Optimistic update or refetch
        fetchSensors();
    };

    const criticalCount = sensors.filter(s => s.status === 'Critical').length;
    const warningCount = sensors.filter(s => s.status === 'Warning').length;

    return (
        <div className="min-h-screen bg-background p-6 md:p-8">
            <div className="max-w-7xl mx-auto space-y-8">

                {/* Header Section */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
                            <Microscope className="w-8 h-8 text-primary" />
                            Sensor Monitoring
                        </h1>
                        <p className="text-muted-foreground mt-1">Real-time analysis for pH, DO, Flow & Pressure instrumentation.</p>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Global Status Pill */}
                        <div className="hidden md:flex items-center gap-3 bg-card border border-border px-4 py-2 rounded-full shadow-sm">
                            <div className={`w-3 h-3 rounded-full ${criticalCount > 0 ? 'bg-status-red animate-pulse' : 'bg-status-green'} `}></div>
                            <span className="font-medium text-sm text-foreground">
                                {criticalCount > 0 ? "System Attention Required" : "All Systems Nominal"}
                            </span>
                        </div>

                        <AddSensorModal onSensorCreated={handleSensorCreated} />
                    </div>
                </div>

                {/* KPI Overview */}
                {(criticalCount > 0 || warningCount > 0) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {criticalCount > 0 && (
                            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 flex items-center gap-4">
                                <ShieldAlert className="w-8 h-8 text-status-red" />
                                <div>
                                    <h4 className="font-semibold text-status-red">Calibration Required</h4>
                                    <p className="text-sm text-muted-foreground">{criticalCount} probes showing significant drift or failure.</p>
                                </div>
                            </div>
                        )}
                        {warningCount > 0 && (
                            <div className="bg-status-yellow/10 border border-status-yellow/20 rounded-lg p-4 flex items-center gap-4">
                                <Activity className="w-8 h-8 text-status-yellow" />
                                <div>
                                    <h4 className="font-semibold text-status-yellow">Maintenance Warning</h4>
                                    <p className="text-sm text-muted-foreground">{warningCount} probes nearing end of life or require cleaning.</p>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Sensor Grid */}
                <div>
                    <div className="flex justify-between items-end mb-4">
                        <h2 className="text-xl font-semibold text-foreground">Active Instrumentation</h2>
                        <span className="text-sm text-muted-foreground">Total: {sensors.length}</span>
                    </div>
                    {loading ? (
                        <div className="text-center py-20 text-muted-foreground">Loading sensors...</div>
                    ) : sensors.length === 0 ? (
                        <div className="text-center py-20 border border-dashed rounded-lg">
                            <p className="text-muted-foreground mb-4">No sensors found.</p>
                            <AddSensorModal onSensorCreated={handleSensorCreated} />
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {sensors.map((sensor) => (
                                <SmartSensorCard key={sensor.id} {...sensor} />
                            ))}
                        </div>
                    )}
                </div>

                {/* Global Deviation Chart */}
                <div className="bg-card rounded-xl border border-border p-6 shadow-sm">
                    <div className="mb-6">
                        <h3 className="text-lg font-semibold text-foreground">Signal Quality Drift</h3>
                        <p className="text-sm text-muted-foreground">Aggregate noise levels across all analog inputs.</p>
                    </div>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={deviationData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorDeviation" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#00ADB5" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#00ADB5" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#2D3748" />
                                <XAxis
                                    dataKey="time"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: '#94a3b8', fontSize: 12 }}
                                    dy={10}
                                />
                                <YAxis
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: '#94a3b8', fontSize: 12 }}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', color: '#fff' }}
                                    itemStyle={{ color: '#00ADB5' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="value"
                                    stroke="#00ADB5"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorDeviation)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}
