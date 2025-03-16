// API functions for the frontend to interact with the Django backend

// Helper function to simulate API delay (if needed)
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// Helper function to make API calls
const apiCall = async (url, method = 'GET', data = null) => {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  }
  if (data) {
    options.body = JSON.stringify(data)
  }

  const response = await fetch(url, options)
  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`)
  }
  return response.json()
}

// Geocode an address to coordinates using the Django backend
const geocode = async (address) => {
  const url = `http://127.0.0.1:8000/api/geocode/?address=${encodeURIComponent(address)}`
  return apiCall(url)
}

// Calculate distance between two coordinates using the Django backend
const calculateDistance = async (coord1, coord2) => {
  const url = `http://127.0.0.1:8000/api/calculate-distance/`
  const data = { coord1, coord2 }
  return apiCall(url, 'POST', data)
}

// Generate points along a route using the Django backend
const generateRoutePoints = async (start, end, numPoints = 10) => {
  const url = `http://127.0.0.1:8000/api/generate-route-points/`
  const data = { start, end, numPoints }
  return apiCall(url, 'POST', data)
}

// Calculate route with rest stops and fuel stops using the Django backend
export const calculateRoute = async (tripData) => {
  await delay(2000) // Simulate API delay (if needed)

  const url = `http://127.0.0.1:8000/api/calculate-route/`
  return apiCall(url, 'POST', tripData)
}

// Generate ELD logs based on the calculated route using the Django backend
export const generateEldLogs = async (routeData) => {
  await delay(1000) // Simulate API delay (if needed)

  if (!routeData) return null

  const url = `http://127.0.0.1:8000/api/generate-eld-logs/`
  return apiCall(url, 'POST', routeData)
}

