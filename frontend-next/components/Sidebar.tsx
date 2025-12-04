"use client";

import { Activity, BarChart3, Settings, FileText, Download, Trash2, Play, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import Image from "next/image";

interface SidebarProps {
    onGenerate: (type: string, length: number) => void;
    onClear: () => void;
    onSettingsChange: (settings: any) => void;
    backendStatus: boolean;
    isLive: boolean;
    onToggleLive: () => void;
    onDataLoad: (data: number[]) => void;
}

export function Sidebar({ onGenerate, onClear, onSettingsChange, backendStatus, isLive, onToggleLive, onDataLoad }: SidebarProps) {
    const [sensorType, setSensorType] = useState("Flow");
    const [windowSize, setWindowSize] = useState([100]);
    const [config, setConfig] = useState({
        slope_critical: 0.1,
        slope_warning: 0.05,
        bias_critical: 2.0,
        bias_warning: 1.0,
        noise_critical: 1.5,
        hysteresis_critical: 0.5,
        dfa_critical: 0.8,
        min_data_points: 50
    });
    const [genType, setGenType] = useState("Normal");
    const [sensorId, setSensorId] = useState("SENSOR-001");

    // Propagate settings changes
    useEffect(() => {
        onSettingsChange({
            sensorType,
            sensorId,
            windowSize: windowSize[0],
            config
        });
    }, [sensorType, sensorId, windowSize, config, onSettingsChange]);

    return (
        <div className="w-80 border-r bg-card h-screen p-4 flex flex-col gap-4 overflow-y-auto">
            <div className="flex items-center justify-center mb-6">
                <div className="relative w-48 h-16">
                    <Image
                        src="/logo_v2.png"
                        alt="QorSense Logo"
                        fill
                        className="object-contain"
                        priority
                    />
                </div>
            </div>

            <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
                <span>System Status:</span>
                <Badge variant={backendStatus ? "default" : "destructive"}>
                    {backendStatus ? "ONLINE" : "OFFLINE"}
                </Badge>
            </div>

            <Separator />

            <div className="space-y-4">
                <h2 className="text-sm font-semibold flex items-center gap-2">
                    <Settings className="h-4 w-4" /> Configuration
                </h2>

                <div className="space-y-2">
                    <label className="text-xs font-medium">Sensor ID</label>
                    <Input value={sensorId} onChange={(e) => setSensorId(e.target.value)} />
                </div>

                <div className="space-y-2">
                    <label className="text-xs font-medium">Sensor Type</label>
                    <Select value={sensorType} onValueChange={setSensorType}>
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="Flow">Flow</SelectItem>
                            <SelectItem value="Pressure">Pressure</SelectItem>
                            <SelectItem value="Temperature">Temperature</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div className="space-y-2">
                    <label className="text-xs font-medium">Window Size: {windowSize[0]}</label>
                    <Slider value={windowSize} onValueChange={setWindowSize} min={10} max={500} step={10} />
                </div>
            </div>

            <Separator />

            <div className="space-y-4">
                <h2 className="text-sm font-semibold flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" /> Data Source
                </h2>

                <div className="space-y-2">
                    <label className="text-xs font-medium">Synthetic Scenario</label>
                    <Select value={genType} onValueChange={setGenType}>
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="Normal">Normal</SelectItem>
                            <SelectItem value="Drifting">Drifting</SelectItem>
                            <SelectItem value="Noisy">Noisy</SelectItem>
                            <SelectItem value="Oscillation">Oscillation</SelectItem>
                        </SelectContent>
                    </Select>
                    <Button
                        className="w-full"
                        variant="outline"
                        onClick={() => onGenerate(genType, 200)}
                        disabled={isLive}
                    >
                        Generate Data
                    </Button>
                </div>

                <div className="space-y-2">
                    <label className="text-xs font-medium">Upload CSV</label>
                    <Input
                        type="file"
                        accept=".csv,.txt"
                        onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;
                            const reader = new FileReader();
                            reader.onload = (event) => {
                                const text = event.target?.result as string;
                                // Simple CSV parse: assume single column or comma separated
                                const values = text.split(/[\n,]+/)
                                    .map(v => parseFloat(v.trim()))
                                    .filter(v => !isNaN(v));
                                if (values.length > 0) {
                                    onDataLoad(values);
                                }
                            };
                            reader.readAsText(file);
                        }}
                    />
                </div>

                <Button
                    variant="destructive"
                    className="w-full"
                    onClick={onClear}
                    disabled={isLive}
                >
                    <Trash2 className="mr-2 h-4 w-4" /> Clear Data
                </Button>
            </div>

            <Separator />

            <div className="space-y-4">
                <h2 className="text-sm font-semibold flex items-center gap-2">
                    <Activity className="h-4 w-4" /> Live Monitoring
                </h2>
                <Button
                    className={`w-full ${isLive ? "bg-red-600 hover:bg-red-700" : "bg-green-600 hover:bg-green-700"}`}
                    onClick={onToggleLive}
                >
                    {isLive ? (
                        <><Square className="mr-2 h-4 w-4 fill-current" /> Stop Live</>
                    ) : (
                        <><Play className="mr-2 h-4 w-4 fill-current" /> Start Live</>
                    )}
                </Button>
            </div>

            <div className="mt-auto text-xs text-center text-muted-foreground">
                © 2025 QorSense Technologies
            </div>
        </div>
    );
}
