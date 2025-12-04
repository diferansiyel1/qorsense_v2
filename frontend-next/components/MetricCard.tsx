import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MetricCardProps {
    title: string;
    value: string | number;
    status?: "Green" | "Yellow" | "Red";
    className?: string;
}

export function MetricCard({ title, value, status, className }: MetricCardProps) {
    let statusColor = "text-foreground";
    if (status === "Green") statusColor = "text-green-500";
    if (status === "Yellow") statusColor = "text-yellow-500";
    if (status === "Red") statusColor = "text-red-500";

    return (
        <Card className={cn("hover:shadow-lg transition-all duration-300 hover:-translate-y-1 border-primary/20", className)}>
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className={cn("text-2xl font-bold", statusColor)}>
                    {value}
                </div>
            </CardContent>
        </Card>
    );
}
