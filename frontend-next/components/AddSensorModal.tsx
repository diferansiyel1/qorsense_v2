"use client"

import { useState } from "react"
import { useForm } from "react-hook-form" // Assuming react-hook-form is available or we use controlled inputs? Let's use simple state for now to minimize deps
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "@/components/ui/select" // This exists
import { api, CreateSensorData, Sensor } from "@/lib/api"
// import { useToast } from "@/components/ui/use-toast" // If installed
import { Plus } from "lucide-react"

interface AddSensorModalProps {
    onSensorCreated: (sensor: Sensor) => void
}

export function AddSensorModal({ onSensorCreated }: AddSensorModalProps) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState<CreateSensorData>({
        name: "",
        location: "",
        source_type: "CSV"
    })

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        try {
            const sensor = await api.createSensor(formData)
            onSensorCreated(sensor)
            setOpen(false)
            // toast({ title: "Sensor Created", description: `${sensor.name} added successfully.` }) 
            setFormData({ name: "", location: "", source_type: "CSV" }) // Reset
        } catch (error) {
            console.error("Failed to create sensor", error)
            // toast({ variant: "destructive", title: "Error", description: "Failed to create sensor." })
        } finally {
            setLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add Sensor
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Add New Sensor</DialogTitle>
                    <DialogDescription>
                        Create a new sensor to start monitoring.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="name" className="text-right">
                            Name
                        </Label>
                        <Input
                            id="name"
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            className="col-span-3"
                            required
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="location" className="text-right">
                            Location
                        </Label>
                        <Input
                            id="location"
                            value={formData.location}
                            onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                            className="col-span-3"
                            required
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="source" className="text-right">
                            Source
                        </Label>
                        <div className="col-span-3">
                            <Select
                                value={formData.source_type}
                                onValueChange={(val: "CSV" | "SCADA") => setFormData(prev => ({ ...prev, source_type: val }))}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select source type" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="CSV">CSV File</SelectItem>
                                    <SelectItem value="SCADA">SCADA / IoT</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="submit" disabled={loading}>
                            {loading ? "Creating..." : "Save Sensor"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
