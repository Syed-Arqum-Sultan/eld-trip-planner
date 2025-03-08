"use client"

import { useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Download } from "lucide-react"

export function EldLogSheet({ logs }) {
  if (!logs || !logs.days || logs.days.length === 0) return null

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">ELD Log Sheets</h3>
        <Button variant="outline" size="sm" className="gap-2">
          <Download className="h-4 w-4" />
          Download PDF
        </Button>
      </div>

      <Tabs defaultValue="0" className="w-full">
        <TabsList className="w-full flex overflow-x-auto">
          {logs.days.map((day, index) => (
            <TabsTrigger key={index} value={index.toString()} className="flex-1">
              Day {index + 1}
            </TabsTrigger>
          ))}
        </TabsList>

        {logs.days.map((day, index) => (
          <TabsContent key={index} value={index.toString()}>
            <DailyLogSheet day={day} index={index} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

function DailyLogSheet({ day, index }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Set up dimensions
    const width = canvas.width
    const height = canvas.height
    const hourWidth = width / 24
    const statusHeight = height / 5

    // Draw grid
    ctx.strokeStyle = "#e2e8f0"
    ctx.lineWidth = 1

    // Vertical lines (hours)
    for (let i = 0; i <= 24; i++) {
      const x = i * hourWidth
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, height)
      ctx.stroke()

      // Hour labels
      if (i < 24) {
        ctx.fillStyle = "#64748b"
        ctx.font = "10px sans-serif"
        ctx.textAlign = "center"
        ctx.fillText(`${i}:00`, x + hourWidth / 2, height - 5)
      }
    }

    // Horizontal lines (status types)
    const statusTypes = ["OFF", "SB", "D", "ON"]
    for (let i = 0; i <= 4; i++) {
      const y = i * statusHeight
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(width, y)
      ctx.stroke()

      // Status labels
      if (i < 4) {
        ctx.fillStyle = "#64748b"
        ctx.font = "10px sans-serif"
        ctx.textAlign = "left"
        ctx.fillText(statusTypes[i], 5, y + statusHeight / 2 + 3)
      }
    }

    // Draw status blocks
    day.statusBlocks.forEach((block) => {
      const startX = block.startHour * hourWidth
      const endX = block.endHour * hourWidth
      const blockWidth = endX - startX

      let y
      switch (block.status) {
        case "OFF":
          y = 0
          break
        case "SB":
          y = statusHeight
          break
        case "D":
          y = statusHeight * 2
          break
        case "ON":
          y = statusHeight * 3
          break
        default:
          y = 0
      }

      // Draw block
      ctx.fillStyle = getStatusColor(block.status, 0.5)
      ctx.fillRect(startX, y, blockWidth, statusHeight)

      // Draw border
      ctx.strokeStyle = getStatusColor(block.status, 1)
      ctx.lineWidth = 2
      ctx.strokeRect(startX, y, blockWidth, statusHeight)

      // Add label if block is wide enough
      if (blockWidth > 30) {
        ctx.fillStyle = "#1e293b"
        ctx.font = "10px sans-serif"
        ctx.textAlign = "center"
        ctx.fillText(
          `${formatHour(block.startHour)}-${formatHour(block.endHour)}`,
          startX + blockWidth / 2,
          y + statusHeight / 2 + 3,
        )
      }
    })

    // Draw current cycle information
    ctx.fillStyle = "#1e293b"
    ctx.font = "12px sans-serif"
    ctx.textAlign = "left"
    ctx.fillText(`Day ${index + 1}: ${day.date}`, 10, height - 40)
    ctx.fillText(`Cycle Hours: ${day.cycleHoursUsed.toFixed(1)} / 70 hours`, 10, height - 25)
  }, [day, index])

  const getStatusColor = (status, alpha) => {
    switch (status) {
      case "OFF":
        return `rgba(74, 222, 128, ${alpha})` // Green
      case "SB":
        return `rgba(250, 204, 21, ${alpha})` // Yellow
      case "D":
        return `rgba(248, 113, 113, ${alpha})` // Red
      case "ON":
        return `rgba(96, 165, 250, ${alpha})` // Blue
      default:
        return `rgba(203, 213, 225, ${alpha})`
    }
  }

  const formatHour = (hour) => {
    const h = Math.floor(hour)
    const m = Math.round((hour - h) * 60)
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>Daily Log - {day.date}</CardTitle>
        <CardDescription>
          Driving: {day.drivingHours.toFixed(1)}h, On-Duty: {day.onDutyHours.toFixed(1)}h, Off-Duty:{" "}
          {day.offDutyHours.toFixed(1)}h
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="border rounded-md p-2 bg-white">
          <canvas ref={canvasRef} width={800} height={300} className="w-full h-auto" />
        </div>

        <div className="mt-4 text-sm">
          <h4 className="font-medium mb-2">Status Legend:</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-green-400 mr-2"></div>
              <span>OFF: Off Duty</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-yellow-400 mr-2"></div>
              <span>SB: Sleeper Berth</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-red-400 mr-2"></div>
              <span>D: Driving</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-400 mr-2"></div>
              <span>ON: On Duty (Not Driving)</span>
            </div>
          </div>
        </div>

        <div className="mt-4 border-t pt-4">
          <h4 className="font-medium mb-2">Daily Summary:</h4>
          <ul className="text-sm space-y-1">
            {day.events.map((event, i) => (
              <li key={i} className="flex items-start">
                <span className="font-medium mr-2">{formatHour(event.hour)}:</span>
                <span>{event.description}</span>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}

