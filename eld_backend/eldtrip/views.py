# filepath: e:\eld-trip-planner\eld_backend\eldtrip\views.py
# Django views using class-based views
import json
import math
from datetime import datetime, timedelta
import requests
import random
import time
from urllib.parse import urlencode
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Utility functions for route calculation
def geocode_address(address):
    """Geocode address using OpenStreetMap Nominatim API"""
    try:
        headers = {
            'User-Agent': 'eldTrip/1.0 (syedarqum1999@gmail.com)'
        }
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': address, 'format': 'json', 'limit': 1},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return {'lat': float(data[0]['lat']), 'lng': float(data[0]['lon'])}
    except Exception as e:
        print(f"Error geocoding address: {e}")
    
    return None

from geopy.distance import geodesic

def calculate_distance(coord1, coord2):
    return geodesic((coord1['lat'], coord1['lng']), (coord2['lat'], coord2['lng'])).miles

def generate_route_points(start, end, num_points=10):
    """Generate points along a route (simplified for demo)"""
    points = []
    
    for i in range(num_points + 1):
        fraction = i / num_points
        lat = start['lat'] + (end['lat'] - start['lat']) * fraction
        lng = start['lng'] + (end['lng'] - start['lng']) * fraction
        points.append({'lat': lat, 'lng': lng})
    
    return points

# def calculate_route(trip_data):
#     """Calculate route with rest stops and fuel stops"""
#     # Geocode locations
#     start_coords = geocode_address(trip_data['currentLocation'])
#     pickup_coords = geocode_address(trip_data['pickupLocation'])
#     dropoff_coords = geocode_address(trip_data['dropoffLocation'])
    
#     # Get road-based routes
#     route_to_pickup = get_road_based_route(start_coords, pickup_coords)
    
#     # Check if routing was successful
#     if not route_to_pickup.get("is_road_based", False):
#         return Response({
#             "error": f"Could not find a valid road route from {trip_data['currentLocation']} to {trip_data['pickupLocation']}. Error: {route_to_pickup.get('error', 'Unknown error')}"
#         },status=status.HTTP_400_BAD_REQUEST)
    
#     route_pickup_to_dropoff = get_road_based_route(pickup_coords, dropoff_coords)
    
#     # Check if routing was successful
#     if not route_pickup_to_dropoff.get("is_road_based", False):
#         return {
#             "error": f"Could not find a valid road route from {trip_data['pickupLocation']} to {trip_data['dropoffLocation']}. Error: {route_pickup_to_dropoff.get('error', 'Unknown error')}"
#         }
    
#     # Calculate distances and times using the road-based routes
#     distance_to_pickup = route_to_pickup["distance"]
#     distance_pickup_to_dropoff = route_pickup_to_dropoff["distance"]
#     total_distance = distance_to_pickup + distance_pickup_to_dropoff
    
#     # Use fixed 55 mph average speed for all calculations
#     avg_speed = 55  # mph
#     driving_time_to_pickup = distance_to_pickup / avg_speed
#     driving_time_pickup_to_dropoff = distance_pickup_to_dropoff / avg_speed
#     total_driving_time = driving_time_to_pickup + driving_time_pickup_to_dropoff
    
#     # Combine route points
#     route_coordinates = route_to_pickup["route_points"] + route_pickup_to_dropoff["route_points"][1:]
    
#     # Calculate rest stops based on HOS regulations
#     restStops = []
#     fuelStops = []
    
#     # Current cycle hours from input
#     current_cycle_hours = float(trip_data.get('currentCycleHours', 0))
    
#     # Calculate rest stops
#     remaining_driving_hours = 11 - (current_cycle_hours % 11)
#     remaining_on_duty_hours = 14 - (current_cycle_hours % 14)
#     hours_since_last_break = current_cycle_hours % 8
    
#     # Track distance covered to place rest stops and fuel stops
#     distance_covered = 0
#     driving_time_covered = 0
#     last_fuel_stop = 0
    
#     # Place stops along the route
#     for i in range(1, len(route_coordinates)):
#         segment_distance = calculate_distance(route_coordinates[i-1], route_coordinates[i])
#         segment_time = segment_distance / avg_speed
        
#         distance_covered += segment_distance
#         driving_time_covered += segment_time
#         hours_since_last_break += segment_time

#         current_coords = [route_coordinates[i]['lat'], route_coordinates[i]['lng']]

        
#         # Check if we need a 30-minute break
#         if hours_since_last_break >= 8 and (not restStops or restStops[-1]['coordinates'] != [route_coordinates[i]['lat'], route_coordinates[i]['lng']]):
#             restStops.append({
#                 'coordinates': current_coords,
#                 'duration': 0.5,
#                 'reason': "30-minute break (8-hour driving limit)"
#             })
#             hours_since_last_break = 0
        
#         # Check if we need a 10-hour rest period
#         if (driving_time_covered >= remaining_driving_hours or driving_time_covered >= remaining_on_duty_hours) and (not restStops or restStops[-1]['coordinates'] != current_coords):
#             restStops.append({
#                 'coordinates': [route_coordinates[i]['lat'], route_coordinates[i]['lng']],
#                 'duration': 10,
#                 'reason': "10-hour rest (11-hour driving limit)" if driving_time_covered >= remaining_driving_hours 
#                           else "10-hour rest (14-hour on-duty limit)"
#             })
#             remaining_driving_hours = 11
#             remaining_on_duty_hours = 14
#             hours_since_last_break = 0
        
#         # Check if we need a fuel stop (every 1000 miles)
#         if distance_covered - last_fuel_stop >= 1000 and distance_covered <= total_distance:
#             if not fuelStops or fuelStops[-1]['coordinates'] != current_coords:
#                 fuelStops.append({
#                     'coordinates': [route_coordinates[i]['lat'], route_coordinates[i]['lng']],
#                     'distance': distance_covered
#                 })
#                 last_fuel_stop = distance_covered
    
#     # Add 1 hour for pickup and 1 hour for dropoff
#     total_trip_time = total_driving_time + sum(stop['duration'] for stop in restStops) + 2  # 1 hour each for pickup and dropoff
    
#     return {
#         'startLocation': trip_data['currentLocation'],
#         'pickupLocation': trip_data['pickupLocation'],
#         'dropoffLocation': trip_data['dropoffLocation'],
#         'startCoordinates': [start_coords['lat'], start_coords['lng']],
#         'pickupCoordinates': [pickup_coords['lat'], pickup_coords['lng']],
#         'dropoffCoordinates': [dropoff_coords['lat'], dropoff_coords['lng']],
#         'totalDistance': total_distance,
#         'drivingTime': total_driving_time,
#         'totalTripTime': total_trip_time,
#         'restStops': restStops,
#         'fuelStops': fuelStops,
#         'routeCoordinates': [[coord['lat'], coord['lng']] for coord in route_coordinates]
#     }

def calculate_route(trip_data):
    """Calculate route with realistic rest stops and fuel stops"""
    # Geocode locations
    start_coords = geocode_address(trip_data['currentLocation'])
    pickup_coords = geocode_address(trip_data['pickupLocation'])
    dropoff_coords = geocode_address(trip_data['dropoffLocation'])
    
    # Get road-based routes
    route_to_pickup = get_road_based_route(start_coords, pickup_coords)
    
    # Check if routing was successful
    if not route_to_pickup.get("is_road_based", False):
        return {
            "error": f"Could not find a valid road route from {trip_data['currentLocation']} to {trip_data['pickupLocation']}. Error: {route_to_pickup.get('error', 'Unknown error')}"
        }
    
    route_pickup_to_dropoff = get_road_based_route(pickup_coords, dropoff_coords)
    
    # Check if routing was successful
    if not route_pickup_to_dropoff.get("is_road_based", False):
        return {
            "error": f"Could not find a valid road route from {trip_data['pickupLocation']} to {trip_data['dropoffLocation']}. Error: {route_pickup_to_dropoff.get('error', 'Unknown error')}"
        }
    
    # Calculate distances and times using the road-based routes
    distance_to_pickup = route_to_pickup["distance"]
    distance_pickup_to_dropoff = route_pickup_to_dropoff["distance"]
    total_distance = distance_to_pickup + distance_pickup_to_dropoff
    
    # Use fixed 55 mph average speed for all calculations
    avg_speed = 55  # mph
    driving_time_to_pickup = distance_to_pickup / avg_speed
    driving_time_pickup_to_dropoff = distance_pickup_to_dropoff / avg_speed
    total_driving_time = driving_time_to_pickup + driving_time_pickup_to_dropoff
    
    # Combine route points
    route_coordinates = route_to_pickup["route_points"] + route_pickup_to_dropoff["route_points"][1:]
    
    # Calculate rest stops based on HOS regulations
    restStops = []
    fuelStops = []
    
    # Current cycle hours from input
    current_cycle_hours = float(trip_data.get('currentCycleHours', 0))
    
    # Initialize HOS tracking variables
    remaining_driving_hours = 11 - current_cycle_hours if current_cycle_hours < 11 else 0
    remaining_on_duty_hours = 14 - current_cycle_hours if current_cycle_hours < 14 else 0
    hours_since_last_break = min(current_cycle_hours, 8)  # Cap at 8 hours
    
    # Sampling interval for potential rest stops (approximately every 50 miles)
    # This prevents checking every single route point and makes rest stops more realistic
    sampling_interval = max(1, int(len(route_coordinates) / (total_distance / 50)))
    
    # Track distance and time for rest stop placement
    distance_covered = 0
    driving_time_accumulated = 0
    last_fuel_distance = 0
    last_rest_stop_distance = 0
    
    # First, calculate all distances between consecutive points
    segment_distances = []
    for i in range(1, len(route_coordinates)):
        segment_distance = calculate_distance(route_coordinates[i-1], route_coordinates[i])
        segment_distances.append(segment_distance)
    
    # Place stops along the route at reasonable intervals
    current_index = 0
    
    # Handle the leg to pickup location
    while current_index < len(segment_distances) and distance_covered < distance_to_pickup:
        segment_distance = segment_distances[current_index]
        segment_time = segment_distance / avg_speed
        
        distance_covered += segment_distance
        driving_time_accumulated += segment_time
        hours_since_last_break += segment_time
        
        # Only check for rest stops at reasonable intervals
        if current_index % sampling_interval == 0 and current_index > 0:
            current_coords = [route_coordinates[current_index+1]['lat'], route_coordinates[current_index+1]['lng']]
            
            # Check if we need a 30-minute break (after 8 hours of driving)
            if hours_since_last_break >= 8 and distance_covered - last_rest_stop_distance >= 100:
                restStops.append({
                    'coordinates': current_coords,
                    'duration': 0.5,
                    'reason': "30-minute break (8-hour driving limit)",
                    'distance': distance_covered,
                    'location': "En route to pickup"
                })
                hours_since_last_break = 0
                last_rest_stop_distance = distance_covered
                remaining_driving_hours -= segment_time
                remaining_on_duty_hours -= (segment_time + 0.5)  # Driving time + break time
            
            # Check if we need a 10-hour rest period
            if remaining_driving_hours <= 1 or remaining_on_duty_hours <= 1:
                restStops.append({
                    'coordinates': current_coords,
                    'duration': 10,
                    'reason': "10-hour rest (11-hour driving limit)" if remaining_driving_hours <= 1 
                              else "10-hour rest (14-hour on-duty limit)",
                    'distance': distance_covered,
                    'location': "En route to pickup"
                })
                remaining_driving_hours = 11
                remaining_on_duty_hours = 14
                hours_since_last_break = 0
                last_rest_stop_distance = distance_covered
            
            # Check if we need a fuel stop (every 500-600 miles is more realistic)
            if distance_covered - last_fuel_distance >= 550:
                fuelStops.append({
                    'coordinates': current_coords,
                    'distance': distance_covered,
                    'location': "En route to pickup"
                })
                last_fuel_distance = distance_covered
        
        current_index += 1
    
    # Add a stop at pickup location
    pickup_index = min(current_index, len(route_coordinates) - 1)
    pickup_coords_list = [route_coordinates[pickup_index]['lat'], route_coordinates[pickup_index]['lng']]
    
    # Deduct 1 hour for pickup from remaining hours
    remaining_driving_hours = max(0, remaining_driving_hours - 0)  # No driving during pickup
    remaining_on_duty_hours = max(0, remaining_on_duty_hours - 1)  # 1 hour for pickup
    
    # Handle the leg from pickup to dropoff
    while current_index < len(segment_distances):
        segment_distance = segment_distances[current_index]
        segment_time = segment_distance / avg_speed
        
        distance_covered += segment_distance
        driving_time_accumulated += segment_time
        hours_since_last_break += segment_time
        
        # Only check for rest stops at reasonable intervals
        if current_index % sampling_interval == 0:
            current_coords = [route_coordinates[current_index+1]['lat'], route_coordinates[current_index+1]['lng']]
            
            # Check if we need a 30-minute break
            if hours_since_last_break >= 8 and distance_covered - last_rest_stop_distance >= 100:
                restStops.append({
                    'coordinates': current_coords,
                    'duration': 0.5,
                    'reason': "30-minute break (8-hour driving limit)",
                    'distance': distance_covered,
                    'location': "En route to dropoff"
                })
                hours_since_last_break = 0
                last_rest_stop_distance = distance_covered
                remaining_driving_hours -= segment_time
                remaining_on_duty_hours -= (segment_time + 0.5)
            
            # Check if we need a 10-hour rest period
            if remaining_driving_hours <= 1 or remaining_on_duty_hours <= 1:
                restStops.append({
                    'coordinates': current_coords,
                    'duration': 10,
                    'reason': "10-hour rest (11-hour driving limit)" if remaining_driving_hours <= 1 
                              else "10-hour rest (14-hour on-duty limit)",
                    'distance': distance_covered,
                    'location': "En route to dropoff"
                })
                remaining_driving_hours = 11
                remaining_on_duty_hours = 14
                hours_since_last_break = 0
                last_rest_stop_distance = distance_covered
            
            # Check if we need a fuel stop
            if distance_covered - last_fuel_distance >= 550:
                fuelStops.append({
                    'coordinates': current_coords,
                    'distance': distance_covered,
                    'location': "En route to dropoff"
                })
                last_fuel_distance = distance_covered
        
        current_index += 1
    
    # Calculate total trip time including rest stops and pickup/dropoff
    total_rest_time = sum(stop['duration'] for stop in restStops)
    total_trip_time = total_driving_time + total_rest_time + 2  # 1 hour each for pickup and dropoff
    
    return {
        'startLocation': trip_data['currentLocation'],
        'pickupLocation': trip_data['pickupLocation'],
        'dropoffLocation': trip_data['dropoffLocation'],
        'startCoordinates': [start_coords['lat'], start_coords['lng']],
        'pickupCoordinates': [pickup_coords['lat'], pickup_coords['lng']],
        'dropoffCoordinates': [dropoff_coords['lat'], dropoff_coords['lng']],
        'totalDistance': total_distance,
        'drivingTime': total_driving_time,
        'totalTripTime': total_trip_time,
        'restStops': restStops,
        'fuelStops': fuelStops,
        'routeCoordinates': [[coord['lat'], coord['lng']] for coord in route_coordinates]
    }

def generate_eld_logs(route_data):
    """Generate ELD logs based on the calculated route"""
    if not route_data:
        return None
    
    # Calculate how many days the trip will take
    total_days = math.ceil(route_data['totalTripTime'] / 24)
    days = []
    
    current_hour = 8  # Start at 8 AM on the first day
    current_day = 0
    cycle_hours_used = 0  # Track 70-hour/8-day cycle
    
    # Track remaining times from the route calculation
    remaining_driving_time = route_data['drivingTime']
    remaining_resStops = route_data['restStops'].copy()
    
    # Process each day
    while current_day < total_days:
        date = datetime.now() + timedelta(days=current_day)
        date_string = date.strftime('%a, %b %d')
        
        day_log = {
            'date': date_string,
            'statusBlocks': [],
            'events': [],
            'drivingHours': 0,
            'onDutyHours': 0,
            'offDutyHours': 0,
            'cycleHoursUsed': 0
        }
        
        # Start with off duty if it's the beginning of the day and not the first day
        if current_day > 0 and current_hour == 0:
            day_log['statusBlocks'].append({
                'status': 'OFF',
                'startHour': 0,
                'endHour': 8
            })
            day_log['events'].append({
                'hour': 0,
                'description': 'Off duty (rest period)'
            })
            day_log['offDutyHours'] += 8
            current_hour = 8
        
        # Process the day's activities
        while current_hour < 24 and remaining_driving_time > 0 and len(day_log['statusBlocks']) < 4:  # Limit to 4 shifts per day
            # Check if we have a rest stop
            if (remaining_resStops and 
                day_log['drivingHours'] + day_log['onDutyHours'] > 0 and 
                day_log['drivingHours'] + day_log['onDutyHours'] >= remaining_resStops[0]['duration']):
                
                rest_stop = remaining_resStops.pop(0)
                rest_duration = rest_stop['duration']
                
                # Add off duty block for the rest stop
                day_log['statusBlocks'].append({
                    'status': 'SB' if rest_duration >= 8 else 'OFF',  # Use sleeper berth for long breaks
                    'startHour': current_hour,
                    'endHour': min(current_hour + rest_duration, 24)
                })
                
                day_log['events'].append({
                    'hour': current_hour,
                    'description': f"{rest_stop['reason']} ({rest_duration} hours)"
                })
                
                if current_hour + rest_duration <= 24:
                    day_log['offDutyHours'] += rest_duration
                    current_hour += rest_duration
                else:
                    # Rest continues to next day
                    hours_today = 24 - current_hour
                    day_log['offDutyHours'] += hours_today
                    current_hour = 24  # End of day
                
                continue
            
            # Handle pickup (1 hour on-duty, not driving)
            if day_log['drivingHours'] == 0 and day_log['onDutyHours'] == 0 and current_day == 0:
                day_log['statusBlocks'].append({
                    'status': 'ON',
                    'startHour': current_hour,
                    'endHour': current_hour + 1
                })
                
                day_log['events'].append({
                    'hour': current_hour,
                    'description': 'On duty - Pickup location'
                })
                
                day_log['onDutyHours'] += 1
                cycle_hours_used += 1
                current_hour += 1
                continue
            
            # Handle dropoff if we're near the end of driving time
            if remaining_driving_time <= 1 and day_log['drivingHours'] > 0:
                day_log['statusBlocks'].append({
                    'status': 'ON',
                    'startHour': current_hour,
                    'endHour': current_hour + 1
                })
                
                day_log['events'].append({
                    'hour': current_hour,
                    'description': 'On duty - Dropoff location'
                })
                
                day_log['onDutyHours'] += 1
                cycle_hours_used += 1
                current_hour += 1
                remaining_driving_time = 0
                continue
            
            # Regular driving period
            driving_period = min(
                4,  # Drive in 4-hour chunks max
                remaining_driving_time,
                24 - current_hour
            )
            
            day_log['statusBlocks'].append({
                'status': 'D',
                'startHour': current_hour,
                'endHour': current_hour + driving_period
            })
            
            day_log['events'].append({
                'hour': current_hour,
                'description': f"Driving ({driving_period:.1f} hours)"
            })
            
            day_log['drivingHours'] += driving_period
            cycle_hours_used += driving_period
            current_hour += driving_period
            remaining_driving_time -= driving_period
        
        # Fill the rest of the day with off-duty if needed
        if current_hour < 24:
            day_log['statusBlocks'].append({
                'status': 'OFF',
                'startHour': current_hour,
                'endHour': 24
            })
            
            if current_hour < 23:  # Only log if it's a significant period
                day_log['events'].append({
                    'hour': current_hour,
                    'description': 'Off duty'
                })
            
            day_log['offDutyHours'] += (24 - current_hour)
            current_hour = 24
        
        # Update cycle hours for the day
        day_log['cycleHoursUsed'] = cycle_hours_used
        
        # Add the day to our logs
        days.append(day_log)
        
        # Reset for next day
        current_hour = 0
        current_day += 1
    
    return {'days': days}

# import requests
# import time

def get_road_based_route(start_coords, end_coords, 
                         api_key=settings.OPEN_ROUTE_KEY,
                         max_retries=3):
    """
    Get a road-based route using OpenRouteService (ORS).
    
    Parameters:
    - start_coords: dict with 'lat' and 'lng' keys
    - end_coords: dict with 'lat' and 'lng' keys
    - api_key: ORS API key
    - max_retries: number of retry attempts if the request fails
    
    Returns:
    - dict with route information or error
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Prepare the API request
            coords = [[start_coords['lng'], start_coords['lat']], 
                      [end_coords['lng'], end_coords['lat']]]
            
            response = requests.post(
                "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
                json={
                    "coordinates": coords,
                },
                headers={
                    "Authorization": api_key,
                    "Content-Type": "application/json"
                },
                timeout=10 + (attempt * 5)  # Increase timeout with each retry
            )
            # response.raise_for_status()
            data = response.json()

            # Check for errors in the response
            if "error" in data:
                error_code = data["error"].get("code")
                error_message = data["error"].get("message")
                print(f"Error {error_code}: {error_message}")
                return {
                    "error": f"ORS API Error {error_code}: {error_message}",
                    "is_road_based": False
                }

            # Extract coordinates from the route
            coordinates = data["features"][0]["geometry"]["coordinates"]
            # Convert from [lng, lat] to [lat, lng] format
            route_points = [{"lat": point[1], "lng": point[0]} for point in coordinates]

            # Extract distance and duration
            distance_miles = data["features"][0]["properties"]["segments"][0]["distance"] / 1609.34
            duration_hours = data["features"][0]["properties"]["segments"][0]["duration"] / 3600
            
            return {
                "route_points": route_points,
                "distance": distance_miles,
                "duration": duration_hours,
                "is_road_based": True,
                "endpoint_used": "OpenRouteService"
            }
        
        except requests.RequestException as e:
            last_error = str(e)
            print(f"ORS attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                # Exponential backoff between retries
                backoff_time = 2 ** attempt
                print(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
    
    # If all retries fail, return error
    return {
        "error": f"All {max_retries} attempts failed with OpenRouteService: {last_error}",
        "is_road_based": False
    }

# Example usage
# start = {"lat": 25.0306, "lng": 67.1353}
# end = {"lat": 32.4464, "lng": -99.7476}
# print(get_road_based_route(start, end, api_key="YOUR_API_KEY"))


class CalculateRouteView(APIView):
    def post(self, request):
        """API endpoint to calculate a route"""
        try:
            data = request.data
            
            # Validate inputs
            required_fields = ['currentLocation', 'pickupLocation', 'dropoffLocation']
            for field in required_fields:
                if field not in data:
                    return Response({'error': f'Missing required field: {field}'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate route
            route_data = calculate_route({
                'currentLocation': data['currentLocation'],
                'pickupLocation': data['pickupLocation'],
                'dropoffLocation': data['dropoffLocation'],
                'currentCycleHours': data.get('currentCycleHours', 0)
            })
            
            return Response(route_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenerateEldLogsView(APIView):
    def post(self, request):
        """API endpoint to generate ELD logs"""
        try:
            route_data = request.data
            
            if not route_data:
                return Response({'error': 'Missing route data'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate ELD logs
            eld_logs = generate_eld_logs(route_data)
            
            return Response(eld_logs)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GeocodeView(APIView):
    def post(self, request):
        """API endpoint to geocode an address"""
        address = request.data.get('address')
        if not address:
            return Response({'error': 'Address is required'}, status=status.HTTP_400_BAD_REQUEST)
        coords = geocode_address(address)
        return Response(coords)