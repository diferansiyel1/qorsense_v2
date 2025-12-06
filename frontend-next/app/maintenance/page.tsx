import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { CalendarClock } from "lucide-react";

export default function MaintenancePage() {
    return (
        <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
            <Card className="w-full max-w-md text-center border-dashed bg-card/50">
                <CardHeader className="flex flex-col items-center">
                    <div className="p-4 rounded-full bg-primary/10 mb-4">
                        <CalendarClock className="w-8 h-8 text-primary" />
                    </div>
                    <CardTitle className="text-2xl">Maintenance & Calibration</CardTitle>
                    <CardDescription>Schedule and track sensor maintenance.</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-muted-foreground">This module is under construction.</p>
                </CardContent>
            </Card>
        </div>
    );
}
