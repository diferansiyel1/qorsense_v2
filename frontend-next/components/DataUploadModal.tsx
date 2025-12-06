"use client"

import { useState, useRef } from "react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Upload, FileText, CheckCircle, AlertCircle } from "lucide-react"
import { api } from "@/lib/api"
// import { useToast } from "@/components/ui/use-toast"

interface DataUploadModalProps {
    sensorId: string
    onUploadSuccess: () => void
}

export function DataUploadModal({ sensorId, onUploadSuccess }: DataUploadModalProps) {
    const [open, setOpen] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [file, setFile] = useState<File | null>(null)
    const [error, setError] = useState<string | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        const droppedFile = e.dataTransfer.files[0]
        validateAndSetFile(droppedFile)
    }

    const validateAndSetFile = (f: File) => {
        setError(null)
        if (f && f.name.endsWith(".csv")) {
            setFile(f)
        } else {
            setError("Please upload a .csv file")
        }
    }

    const handleUpload = async () => {
        if (!file) return
        setUploading(true)
        setError(null)

        const formData = new FormData()
        formData.append("file", file)
        formData.append("sensor_id", sensorId)

        try {
            await api.uploadReadings(sensorId, formData)
            onUploadSuccess()
            setOpen(false)
            setFile(null)
            // toast({ title: "Upload Successful", description: "Sensor data imported." })
            window.alert("Upload Successful: Sensor data imported.") // Fallback until toast is ready
        } catch (err) {
            console.error(err)
            setError("Failed to upload data. Please try again.")
        } finally {
            setUploading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline">
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Data
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Upload Sensor Data</DialogTitle>
                    <DialogDescription>
                        Drag and drop a CSV file or click to select.
                    </DialogDescription>
                </DialogHeader>

                <div
                    className="flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-10 cursor-pointer hover:bg-accent/50 transition-colors"
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        accept=".csv"
                        onChange={(e) => {
                            if (e.target.files?.[0]) validateAndSetFile(e.target.files[0])
                        }}
                    />

                    {file ? (
                        <div className="text-center">
                            <FileText className="h-10 w-10 mx-auto text-primary mb-2" />
                            <p className="font-medium">{file.name}</p>
                            <p className="text-sm text-muted-foreground">{(file.size / 1024).toFixed(2)} KB</p>
                        </div>
                    ) : (
                        <div className="text-center">
                            <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-2" />
                            <p className="font-medium text-muted-foreground">Drop CSV here</p>
                        </div>
                    )}
                </div>

                {error && (
                    <div className="flex items-center text-destructive text-sm gap-2">
                        <AlertCircle className="h-4 w-4" /> {error}
                    </div>
                )}

                <div className="flex justify-end gap-2 mt-4">
                    <Button variant="ghost" onClick={() => setFile(null)} disabled={!file || uploading}>Clear</Button>
                    <Button onClick={handleUpload} disabled={!file || uploading}>
                        {uploading ? "Uploading..." : "Upload"}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    )
}
