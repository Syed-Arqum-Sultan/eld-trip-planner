// Mock API functions for the frontend demo
// In a real application, these would make actual API calls to the Django backend

// Helper function to simulate API delay
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// Geocode an address to coordinates (mock implementation)
const geocode = async (address) => {
  // For demo purposes, return mock coordinates
  // In a real app, this would call a geocoding service

  // If it's already coordinates, just parse and return them
  if (address.includes(",")) {
    const [lat, lng] = address.split(",").map((coord) => Number.parseFloat(coord.trim()))
    if (!isNaN(lat) && !isNaN(lng)) {
      return { lat, lng }
    }
  }

  // Mock geocoding for common locations
  const locations = {
    "new york": { lat: 40.7128, lng: -74.006 },
    "los angeles": { lat: 34.0522, lng: -118.2437 },
    chicago: { lat: 41.8781, lng: -87.6298 },
    houston: { lat: 29.7604, lng: -95.3698 },
    phoenix: { lat: 33.4484, lng: -112.074 },
    philadelphia: { lat: 39.9526, lng: -75.1652 },
    "san antonio": { lat: 29.4241, lng: -98.4936 },
    "san diego": { lat: 32.7157, lng: -117.1611 },
    dallas: { lat: 32.7767, lng: -96.797 },
    "san francisco": { lat: 37.7749, lng: -122.4194 },
    austin: { lat: 30.2672, lng: -97.7431 },
    seattle: { lat: 47.6062, lng: -122.3321 },
    denver: { lat: 39.7392, lng: -104.9903 },
  }

  // Check if the address matches any of our mock locations
  const lowercaseAddress = address.toLowerCase()
  for (const [key, coords] of Object.entries(locations)) {
    if (lowercaseAddress.includes(key)) {
      return coords
    }
  }

  // Default to a random location in the US if no match
  return {
    lat: 39.8283 + (Math.random() - 0.5) * 10,
    lng: -98.5795 + (Math.random() - 0.5) * 20,
  }
}

// Calculate distance between two coordinates using Haversine formula
const calculateDistance = (coord1, coord2) => {
  const toRad = (value) => (value * Math.PI) / 180
  const R = 3958.8 // Earth's radius in miles

  const dLat = toRad(coord2.lat - coord1.lat)
  const dLon = toRad(coord2.lng - coord1.lng)

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(coord1.lat)) * Math.cos(toRad(coord2.lat)) * Math.sin(dLon / 2) * Math.sin(dLon / 2)

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

// Generate points along a route (simplified for demo)
const generateRoutePoints = (start, end, numPoints = 10) => {
  const points = []

  for (let i = 0; i <= numPoints; i++) {
    const fraction = i / numPoints
    const lat = start.lat + (end.lat - start.lat) * fraction
    const lng = start.lng + (end.lng - start.lng) * fraction
    points.push({ lat, lng })
  }

  return points
}

// Calculate route with rest stops and fuel stops
export const calculateRoute = async (tripData) => {
  await delay(2000) // Simulate API delay

  // Geocode locations
  const startCoords = await geocode(tripData.currentLocation)
  const pickupCoords = await geocode(tripData.pickupLocation)
  const dropoffCoords = await geocode(tripData.dropoffLocation)

  // Calculate distances
  const distanceToPickup = calculateDistance(startCoords, pickupCoords)
  const distancePickupToDropoff = calculateDistance(pickupCoords, dropoffCoords)
  const totalDistance = distanceToPickup + distancePickupToDropoff

  // Calculate driving times (assume average speed of 55 mph)
  const avgSpeed = 55
  const drivingTimeToPickup = distanceToPickup / avgSpeed
  const drivingTimePickupToDropoff = distancePickupToDropoff / avgSpeed
  const totalDrivingTime = drivingTimeToPickup + drivingTimePickupToDropoff

  // Calculate rest stops based on HOS regulations
  // - 11 hour driving limit
  // - 14 hour on-duty limit
  // - 30 minute break after 8 hours of driving
  // - 10 hour off-duty period before resetting

  const restStops = []
  const fuelStops = []

  // Current cycle hours from input
  const currentCycleHours = Number.parseFloat(tripData.currentCycleHours)

  // Calculate rest stops
  let remainingDrivingHours = 11 - (currentCycleHours % 11)
  let remainingOnDutyHours = 14 - (currentCycleHours % 14)
  let hoursSinceLastBreak = currentCycleHours % 8

  // Generate route points
  const routeToPickup = generateRoutePoints(startCoords, pickupCoords, 20)
  const routePickupToDropoff = generateRoutePoints(pickupCoords, dropoffCoords, 30)

  // Combine all route points
  const routeCoordinates = [...routeToPickup, ...routePickupToDropoff.slice(1)]

  // Track distance covered to place rest stops and fuel stops
  let distanceCovered = 0
  let drivingTimeCovered = 0
  let lastFuelStop = 0

  // Place stops along the route
  for (let i = 1; i < routeCoordinates.length; i++) {
    const segmentDistance = calculateDistance(routeCoordinates[i - 1], routeCoordinates[i])
    const segmentTime = segmentDistance / avgSpeed

    distanceCovered += segmentDistance
    drivingTimeCovered += segmentTime
    hoursSinceLastBreak += segmentTime

    // Check if we need a 30-minute break
    if (hoursSinceLastBreak >= 8) {
      restStops.push({
        coordinates: [routeCoordinates[i].lat, routeCoordinates[i].lng],
        duration: 0.5,
        reason: "30-minute break (8-hour driving limit)",
      })
      hoursSinceLastBreak = 0
    }

    // Check if we need a 10-hour rest period
    if (drivingTimeCovered >= remainingDrivingHours || drivingTimeCovered >= remainingOnDutyHours) {
      restStops.push({
        coordinates: [routeCoordinates[i].lat, routeCoordinates[i].lng],
        duration: 10,
        reason:
          drivingTimeCovered >= remainingDrivingHours
            ? "10-hour rest (11-hour driving limit)"
            : "10-hour rest (14-hour on-duty limit)",
      })
      remainingDrivingHours = 11
      remainingOnDutyHours = 14
      hoursSinceLastBreak = 0
    }

    // Check if we need a fuel stop (every 1000 miles)
    if (distanceCovered - lastFuelStop >= 1000) {
      fuelStops.push({
        coordinates: [routeCoordinates[i].lat, routeCoordinates[i].lng],
        distance: distanceCovered,
      })
      lastFuelStop = distanceCovered
    }
  }

  // Add 1 hour for pickup and 1 hour for dropoff
  const totalTripTime = totalDrivingTime + restStops.reduce((total, stop) => total + stop.duration, 0) + 2 // 1 hour each for pickup and dropoff

  return {
    startLocation: tripData.currentLocation,
    pickupLocation: tripData.pickupLocation,
    dropoffLocation: tripData.dropoffLocation,
    startCoordinates: [startCoords.lat, startCoords.lng],
    pickupCoordinates: [pickupCoords.lat, pickupCoords.lng],
    dropoffCoordinates: [dropoffCoords.lat, dropoffCoords.lng],
    totalDistance,
    drivingTime: totalDrivingTime,
    totalTripTime,
    restStops,
    fuelStops,
    routeCoordinates: routeCoordinates.map((coord) => [coord.lat, coord.lng]),
  }
}

// Generate ELD logs based on the calculated route
export const generateEldLogs = async (routeData) => {
  await delay(1000) // Simulate API delay

  if (!routeData) return null

  // Calculate how many days the trip will take
  const totalDays = Math.ceil(routeData.totalTripTime / 24)
  const days = []

  let currentHour = 8 // Start at 8 AM on the first day
  let currentDay = 0
  let cycleHoursUsed = 0 // Track 70-hour/8-day cycle

  // Track remaining times from the route calculation
  let remainingDrivingTime = routeData.drivingTime
  const remainingRestStops = [...routeData.restStops]

  // Process each day
  while (currentDay < totalDays) {
    const date = new Date()
    date.setDate(date.getDate() + currentDay)
    const dateString = date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    })

    const dayLog = {
      date: dateString,
      statusBlocks: [],
      events: [],
      drivingHours: 0,
      onDutyHours: 0,
      offDutyHours: 0,
      cycleHoursUsed: 0,
    }

    // Start with off duty if it's the beginning of the day and not the first day
    if (currentDay > 0 && currentHour === 0) {
      dayLog.statusBlocks.push({
        status: "OFF",
        startHour: 0,
        endHour: 8,
      })
      dayLog.events.push({
        hour: 0,
        description: "Off duty (rest period)",
      })
      dayLog.offDutyHours += 8
      currentHour = 8
    }

    // Process the day's activities
    while (currentHour < 24 && remainingDrivingTime > 0) {
      // Check if we have a rest stop
      if (
        remainingRestStops.length > 0 &&
        dayLog.drivingHours + dayLog.onDutyHours > 0 &&
        dayLog.drivingHours + dayLog.onDutyHours >= remainingRestStops[0].duration
      ) {
        const restStop = remainingRestStops.shift()
        const restDuration = restStop.duration

        // Add off duty block for the rest stop
        dayLog.statusBlocks.push({
          status: restDuration >= 8 ? "SB" : "OFF", // Use sleeper berth for long breaks
          startHour: currentHour,
          endHour: Math.min(currentHour + restDuration, 24),
        })

        dayLog.events.push({
          hour: currentHour,
          description: `${restStop.reason} (${restDuration} hours)`,
        })

        if (currentHour + restDuration <= 24) {
          dayLog.offDutyHours += restDuration
          currentHour += restDuration
        } else {
          // Rest continues to next day
          const hoursToday = 24 - currentHour
          dayLog.offDutyHours += hoursToday
          currentHour = 24 // End of day
        }

        continue
      }

      // Handle pickup (1 hour on-duty, not driving)
      if (dayLog.drivingHours === 0 && dayLog.onDutyHours === 0 && currentDay === 0) {
        dayLog.statusBlocks.push({
          status: "ON",
          startHour: currentHour,
          endHour: currentHour + 1,
        })

        dayLog.events.push({
          hour: currentHour,
          description: "On duty - Pickup location",
        })

        dayLog.onDutyHours += 1
        cycleHoursUsed += 1
        currentHour += 1
        continue
      }

      // Handle dropoff if we're near the end of driving time
      if (remainingDrivingTime <= 1 && dayLog.drivingHours > 0) {
        dayLog.statusBlocks.push({
          status: "ON",
          startHour: currentHour,
          endHour: currentHour + 1,
        })

        dayLog.events.push({
          hour: currentHour,
          description: "On duty - Dropoff location",
        })

        dayLog.onDutyHours += 1
        cycleHoursUsed += 1
        currentHour += 1
        remainingDrivingTime = 0
        continue
      }

      // Regular driving period
      const drivingPeriod = Math.min(
        4, // Drive in 4-hour chunks max
        remainingDrivingTime,
        24 - currentHour,
      )

      dayLog.statusBlocks.push({
        status: "D",
        startHour: currentHour,
        endHour: currentHour + drivingPeriod,
      })

      dayLog.events.push({
        hour: currentHour,
        description: `Driving (${drivingPeriod.toFixed(1)} hours)`,
      })

      dayLog.drivingHours += drivingPeriod
      cycleHoursUsed += drivingPeriod
      currentHour += drivingPeriod
      remainingDrivingTime -= drivingPeriod
    }

    // Fill the rest of the day with off-duty if needed
    if (currentHour < 24) {
      dayLog.statusBlocks.push({
        status: "OFF",
        startHour: currentHour,
        endHour: 24,
      })

      if (currentHour < 23) {
        // Only log if it's a significant period
        dayLog.events.push({
          hour: currentHour,
          description: "Off duty",
        })
      }

      dayLog.offDutyHours += 24 - currentHour
      currentHour = 24
    }

    // Update cycle hours for the day
    dayLog.cycleHoursUsed = cycleHoursUsed

    // Add the day to our logs
    days.push(dayLog)

    // Reset for next day
    currentHour = 0
    currentDay++
  }

  return { days }
}

