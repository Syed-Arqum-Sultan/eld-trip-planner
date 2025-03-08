import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Clock, MapPin, Truck, Coffee } from "lucide-react"

export function RouteDetails({ route }) {
  if (!route) return null

  const formatDuration = (hours) => {
    const wholeHours = Math.floor(hours)
    const minutes = Math.round((hours - wholeHours) * 60)
    return `${wholeHours}h ${minutes}m`
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Total Distance</CardDescription>
          <CardTitle className="flex items-center">
            <MapPin className="mr-2 h-4 w-4 text-primary" />
            {route.totalDistance.toFixed(1)} miles
          </CardTitle>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Driving Time</CardDescription>
          <CardTitle className="flex items-center">
            <Truck className="mr-2 h-4 w-4 text-primary" />
            {formatDuration(route.drivingTime)}
          </CardTitle>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Total Trip Time</CardDescription>
          <CardTitle className="flex items-center">
            <Clock className="mr-2 h-4 w-4 text-primary" />
            {formatDuration(route.totalTripTime)}
          </CardTitle>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Stops</CardDescription>
          <CardTitle className="flex items-center">
            <Coffee className="mr-2 h-4 w-4 text-primary" />
            {route.restStops.length} rest, {route.fuelStops.length} fuel
          </CardTitle>
        </CardHeader>
      </Card>

      <Card className="md:col-span-2 lg:col-span-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Trip Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              <div className="flex items-center">
                <MapPin className="mr-2 h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Start:</span>
                <span className="ml-1 text-muted-foreground">{route.startLocation}</span>
              </div>
              <div className="flex items-center">
                <MapPin className="mr-2 h-4 w-4 text-blue-500" />
                <span className="font-medium">Pickup:</span>
                <span className="ml-1 text-muted-foreground">{route.pickupLocation}</span>
              </div>
              <div className="flex items-center">
                <MapPin className="mr-2 h-4 w-4 text-green-500" />
                <span className="font-medium">Dropoff:</span>
                <span className="ml-1 text-muted-foreground">{route.dropoffLocation}</span>
              </div>
            </div>

            <div className="pt-2 border-t">
              <p className="text-xs text-muted-foreground">
                This trip includes {route.restStops.length} required rest stops and {route.fuelStops.length} fuel stops.
                The total trip time includes 1 hour each at pickup and dropoff locations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

