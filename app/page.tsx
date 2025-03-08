"use client"

import { useState } from "react"
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet"
import "leaflet/dist/leaflet.css"
import { Icon } from "leaflet"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { calculateRoute, generateEldLogs } from "@/lib/api"
import { EldLogSheet } from "@/components/eld-log-sheet"
import { RouteDetails } from "@/components/route-details"
import { useToast } from "@/components/ui/use-toast"
import { Loader2, MapPin, Truck } from "lucide-react"

// Fix for Leaflet marker icon issue in Next.js
const customIcon = new Icon({
  iconUrl: "/marker-icon.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: "/marker-shadow.png",
  shadowSize: [41, 41],
})

export default function TripPlanner() {
  const [currentLocation, setCurrentLocation] = useState("")
  const [pickupLocation, setPickupLocation] = useState("")
  const [dropoffLocation, setDropoffLocation] = useState("")
  const [currentCycleHours, setCurrentCycleHours] = useState("0")
  const [loading, setLoading] = useState(false)
  const [route, setRoute] = useState(null)
  const [eldLogs, setEldLogs] = useState(null)
  const [activeTab, setActiveTab] = useState("map")
  const { toast } = useToast()

  const handleGetCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords
          setCurrentLocation(`${latitude}, ${longitude}`)
          toast({
            title: "Location detected",
            description: `Your current location has been set to ${latitude}, ${longitude}`,
          })
        },
        (error) => {
          toast({
            title: "Error detecting location",
            description: error.message,
            variant: "destructive",
          })
        },
      )
    } else {
      toast({
        title: "Geolocation not supported",
        description: "Your browser doesn't support geolocation",
        variant: "destructive",
      })
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!currentLocation || !pickupLocation || !dropoffLocation) {
      toast({
        title: "Missing information",
        description: "Please fill in all location fields",
        variant: "destructive",
      })
      return
    }

    setLoading(true)

    try {
      // Calculate route
      const routeData = await calculateRoute({
        currentLocation,
        pickupLocation,
        dropoffLocation,
        currentCycleHours: Number.parseFloat(currentCycleHours),
      })

      setRoute(routeData)

      // Generate ELD logs
      const logsData = await generateEldLogs(routeData)
      setEldLogs(logsData)

      setActiveTab("map")
    } catch (error) {
      toast({
        title: "Error calculating route",
        description: error.message || "An unexpected error occurred",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-6 space-y-8">
      <header className="text-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight">ELD Trip Planner</h1>
        <p className="text-muted-foreground mt-2">Calculate routes, generate ELD logs, and visualize your journey</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Trip Details</CardTitle>
            <CardDescription>Enter your trip information</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="currentLocation">Current Location</Label>
                <div className="flex gap-2">
                  <Input
                    id="currentLocation"
                    placeholder="Address or coordinates"
                    value={currentLocation}
                    onChange={(e) => setCurrentLocation(e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleGetCurrentLocation}
                    title="Get current location"
                  >
                    <MapPin className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="pickupLocation">Pickup Location</Label>
                <Input
                  id="pickupLocation"
                  placeholder="Address or coordinates"
                  value={pickupLocation}
                  onChange={(e) => setPickupLocation(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="dropoffLocation">Dropoff Location</Label>
                <Input
                  id="dropoffLocation"
                  placeholder="Address or coordinates"
                  value={dropoffLocation}
                  onChange={(e) => setDropoffLocation(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="currentCycleHours">Current Cycle Used (Hours)</Label>
                <Select value={currentCycleHours} onValueChange={setCurrentCycleHours}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select hours" />
                  </SelectTrigger>
                  <SelectContent>
                    {[...Array(71).keys()].map((i) => (
                      <SelectItem key={i} value={i.toString()}>
                        {i} hours
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </form>
          </CardContent>
          <CardFooter>
            <Button onClick={handleSubmit} className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Calculating...
                </>
              ) : (
                <>
                  <Truck className="mr-2 h-4 w-4" />
                  Calculate Route
                </>
              )}
            </Button>
          </CardFooter>
        </Card>

        <div className="lg:col-span-2">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="map">Map View</TabsTrigger>
              <TabsTrigger value="logs">ELD Logs</TabsTrigger>
            </TabsList>
            <TabsContent value="map" className="border rounded-md p-4 min-h-[500px]">
              {route ? (
                <div className="space-y-4">
                  <RouteDetails route={route} />
                  <div className="h-[400px] rounded-md overflow-hidden border">
                    <MapContainer center={route.startCoordinates} zoom={5} style={{ height: "100%", width: "100%" }}>
                      <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      />

                      {/* Start marker */}
                      <Marker position={route.startCoordinates} icon={customIcon}>
                        <Popup>Starting Point</Popup>
                      </Marker>

                      {/* Pickup marker */}
                      <Marker position={route.pickupCoordinates} icon={customIcon}>
                        <Popup>Pickup Location</Popup>
                      </Marker>

                      {/* Dropoff marker */}
                      <Marker position={route.dropoffCoordinates} icon={customIcon}>
                        <Popup>Dropoff Location</Popup>
                      </Marker>

                      {/* Rest stops */}
                      {route.restStops.map((stop, index) => (
                        <Marker key={`rest-${index}`} position={stop.coordinates} icon={customIcon}>
                          <Popup>
                            <div>
                              <strong>Rest Stop #{index + 1}</strong>
                              <p>Duration: {stop.duration} hours</p>
                              <p>Reason: {stop.reason}</p>
                            </div>
                          </Popup>
                        </Marker>
                      ))}

                      {/* Fuel stops */}
                      {route.fuelStops.map((stop, index) => (
                        <Marker key={`fuel-${index}`} position={stop.coordinates} icon={customIcon}>
                          <Popup>
                            <div>
                              <strong>Fuel Stop #{index + 1}</strong>
                              <p>Distance: {stop.distance.toFixed(1)} miles</p>
                            </div>
                          </Popup>
                        </Marker>
                      ))}

                      {/* Route lines */}
                      <Polyline positions={route.routeCoordinates} color="blue" />
                    </MapContainer>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                  <MapPin className="h-12 w-12 mb-4" />
                  <h3 className="text-lg font-medium">No Route Calculated</h3>
                  <p>Enter your trip details and click "Calculate Route" to see the map</p>
                </div>
              )}
            </TabsContent>
            <TabsContent value="logs" className="border rounded-md p-4 min-h-[500px]">
              {eldLogs ? (
                <EldLogSheet logs={eldLogs} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                  <Truck className="h-12 w-12 mb-4" />
                  <h3 className="text-lg font-medium">No ELD Logs Generated</h3>
                  <p>Calculate a route first to generate ELD logs</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}

