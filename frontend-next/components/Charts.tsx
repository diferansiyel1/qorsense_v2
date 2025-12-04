"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AnalysisMetrics } from '@/types';

interface ChartsProps {
    data: number[];
    windowSize: number;
    metrics?: AnalysisMetrics;
}

export function Charts({ data, windowSize, metrics }: ChartsProps) {
    // Transform data for Recharts
    const chartData = data.map((val, idx) => ({ index: idx, value: val }));

    // Calculate histogram data
    const bins = 20;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const step = (max - min) / bins;
    const histData = Array.from({ length: bins }, (_, i) => {
        const start = min + i * step;
        const end = start + step;
        const count = data.filter(v => v >= start && v < end).length;
        return { bin: start.toFixed(2), count };
    });

    // Reference window (first 10%)
    const refEnd = Math.max(1, Math.floor(data.length * 0.1));

    // Radar Data Preparation
    const radarData = metrics ? [
        { subject: 'Bias', A: Math.min(100, Math.abs(metrics.bias) * 20), fullMark: 100 }, // Scale for visibility
        { subject: 'Slope', A: Math.min(100, Math.abs(metrics.slope) * 1000), fullMark: 100 },
        { subject: 'Noise', A: Math.min(100, metrics.noise_std * 50), fullMark: 100 },
        { subject: 'Hysteresis', A: Math.min(100, metrics.hysteresis * 100), fullMark: 100 },
        { subject: 'Hurst', A: metrics.hurst * 100, fullMark: 100 },
        { subject: 'SNR', A: Math.min(100, metrics.snr_db), fullMark: 100 },
    ] : [];

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card className="col-span-1 lg:col-span-2 border-primary/20">
                <CardHeader>
                    <CardTitle>Sensor Data Trend</CardTitle>
                </CardHeader>
                <CardContent className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted-foreground))" strokeOpacity={0.2} />
                            <XAxis dataKey="index" stroke="hsl(var(--muted-foreground))" />
                            <YAxis stroke="hsl(var(--muted-foreground))" />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
                                itemStyle={{ color: 'hsl(var(--foreground))' }}
                            />
                            <ReferenceArea x1={0} x2={refEnd} strokeOpacity={0.3} fill="hsl(var(--primary))" fillOpacity={0.1} />
                            <Line type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            <Card className="col-span-1 border-primary/20">
                <CardHeader>
                    <CardTitle>Multi-Metric Radar</CardTitle>
                </CardHeader>
                <CardContent className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                            <PolarGrid stroke="hsl(var(--muted-foreground))" strokeOpacity={0.3} />
                            <PolarAngleAxis dataKey="subject" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                            <Radar
                                name="Metrics"
                                dataKey="A"
                                stroke="hsl(var(--primary))"
                                fill="hsl(var(--primary))"
                                fillOpacity={0.4}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
                            />
                        </RadarChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            <Card className="col-span-1 lg:col-span-3 border-primary/20">
                <CardHeader>
                    <CardTitle>Noise Distribution</CardTitle>
                </CardHeader>
                <CardContent className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={histData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted-foreground))" strokeOpacity={0.2} />
                            <XAxis dataKey="bin" stroke="hsl(var(--muted-foreground))" fontSize={10} />
                            <YAxis stroke="hsl(var(--muted-foreground))" />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
                                itemStyle={{ color: 'hsl(var(--foreground))' }}
                            />
                            <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>
        </div>
    );
}
