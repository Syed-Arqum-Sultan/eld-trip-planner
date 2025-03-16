# filepath: e:\eld-trip-planner\eld_backend\eldtrip\views.py
# Django views using class-based views
import json
import math
from datetime import datetime, timedelta
import requests
import random
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
    
    return {
        'lat': 39.8283 + (random.random() - 0.5) * 10,
        'lng': -98.5795 + (random.random() - 0.5) * 20
    }

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates using Haversine formula"""
    R = 3958.8  # Earth's radius in miles
    
    def to_rad(value):
        return (value * math.pi) / 180
    
    d_lat = to_rad(coord2['lat'] - coord1['lat'])
    d_lon = to_rad(coord2['lng'] - coord1['lng'])
    
    a = (
        math.sin(d_lat / 2) * math.sin(d_lat / 2) +
        math.cos(to_rad(coord1['lat'])) * math.cos(to_rad(coord2['lat'])) *
        math.sin(d_lon / 2) * math.sin(d_lon / 2)
    )
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def generate_route_points(start, end, num_points=10):
    """Generate points along a route (simplified for demo)"""
    points = []
    
    for i in range(num_points + 1):
        fraction = i / num_points
        lat = start['lat'] + (end['lat'] - start['lat']) * fraction
        lng = start['lng'] + (end['lng'] - start['lng']) * fraction
        points.append({'lat': lat, 'lng': lng})
    
    return points

def calculate_route(trip_data):
    """Calculate route with rest stops and fuel stops"""
    # Geocode locations
    start_coords = geocode_address(trip_data['currentLocation'])
    pickup_coords = geocode_address(trip_data['pickupLocation'])
    dropoff_coords = geocode_address(trip_data['dropoffLocation'])
    
    # Calculate distances
    distance_to_pickup = calculate_distance(start_coords, pickup_coords)
    distance_pickup_to_dropoff = calculate_distance(pickup_coords, dropoff_coords)
    total_distance = distance_to_pickup + distance_pickup_to_dropoff
    
    # Calculate driving times (assume average speed of 55 mph)
    avg_speed = 55
    driving_time_to_pickup = distance_to_pickup / avg_speed
    driving_time_pickup_to_dropoff = distance_pickup_to_dropoff / avg_speed
    total_driving_time = driving_time_to_pickup + driving_time_pickup_to_dropoff
    
    # Calculate rest stops based on HOS regulations
    restStops = []
    fuelStops = []
    
    # Current cycle hours from input
    current_cycle_hours = float(trip_data.get('currentCycleHours', 0))
    
    # Calculate rest stops
    remaining_driving_hours = 11 - (current_cycle_hours % 11)
    remaining_on_duty_hours = 14 - (current_cycle_hours % 14)
    hours_since_last_break = current_cycle_hours % 8
    
    # Generate route points
    route_to_pickup = generate_route_points(start_coords, pickup_coords, 20)
    route_pickup_to_dropoff = generate_route_points(pickup_coords, dropoff_coords, 30)
    
    # Combine all route points
    route_coordinates = route_to_pickup + route_pickup_to_dropoff[1:]
    
    # Track distance covered to place rest stops and fuel stops
    distance_covered = 0
    driving_time_covered = 0
    last_fuel_stop = 0
    
    # Place stops along the route
    for i in range(1, len(route_coordinates)):
        segment_distance = calculate_distance(route_coordinates[i-1], route_coordinates[i])
        segment_time = segment_distance / avg_speed
        
        distance_covered += segment_distance
        driving_time_covered += segment_time
        hours_since_last_break += segment_time
        
        # Check if we need a 30-minute break
        if hours_since_last_break >= 8:
            restStops.append({
                'coordinates': [route_coordinates[i]['lat'], route_coordinates[i]['lng']],
                'duration': 0.5,
                'reason': "30-minute break (8-hour driving limit)"
            })
            hours_since_last_break = 0
        
        # Check if we need a 10-hour rest period
        if driving_time_covered >= remaining_driving_hours or driving_time_covered >= remaining_on_duty_hours:
            restStops.append({
                'coordinates': [route_coordinates[i]['lat'], route_coordinates[i]['lng']],
                'duration': 10,
                'reason': "10-hour rest (11-hour driving limit)" if driving_time_covered >= remaining_driving_hours 
                          else "10-hour rest (14-hour on-duty limit)"
            })
            remaining_driving_hours = 11
            remaining_on_duty_hours = 14
            hours_since_last_break = 0
        
        # Check if we need a fuel stop (every 1000 miles)
        if distance_covered - last_fuel_stop >= 1000:
            fuelStops.append({
                'coordinates': [route_coordinates[i]['lat'], route_coordinates[i]['lng']],
                'distance': distance_covered
            })
            last_fuel_stop = distance_covered
    
    # Add 1 hour for pickup and 1 hour for dropoff
    total_trip_time = total_driving_time + sum(stop['duration'] for stop in restStops) + 2  # 1 hour each for pickup and dropoff
    
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
        while current_hour < 24 and remaining_driving_time > 0:
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