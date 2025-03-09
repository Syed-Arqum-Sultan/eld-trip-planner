# Django Backend for ELD Trip Planner
# This would be implemented in Django, but here's the core logic

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import math
from datetime import datetime, timedelta

# Utility functions for route calculation
def geocode_address(address):
    """Mock geocoding function - in production use a real geocoding service"""
    # Check if it's already coordinates
    if ',' in address:
        try:
            lat, lng = map(float, address.split(','))
            return {'lat': lat, 'lng': lng}
        except:
            pass
    
    # Mock geocoding for common locations
    locations = {
        'new york': {'lat': 40.7128, 'lng': -74.0060},
        'los angeles': {'lat': 34.0522, 'lng': -118.2437},
        'chicago': {'lat': 41.8781, 'lng': -87.6298},
        'houston': {'lat': 29.7604, 'lng': -95.3698},
        'phoenix': {'lat': 33.4484, 'lng': -112.0740},
        'philadelphia': {'lat': 39.9526, 'lng': -75.1652},
        'san antonio': {'lat': 29.4241, 'lng': -98.4936},
        'san diego': {'lat': 32.7157, 'lng': -117.1611},
        'dallas': {'lat': 32.7767, 'lng': -96.7970},
        'san francisco': {'lat': 37.7749, 'lng': -122.4194},
        'austin': {'lat': 30.2672, 'lng': -97.7431},
        'seattle': {'lat': 47.6062, 'lng': -122.3321},
        'denver': {'lat': 39.7392, 'lng': -104.9903},
    }
    
    # Check if address contains any of our mock locations
    address_lower = address.lower()
    for key, coords in locations.items():
        if key in address_lower:
            return coords
    
    # Default to a random location in the US
    import random
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
    # Geocode locations``
    start_coords = geocode_address(trip_data['current_location'])
    pickup_coords = geocode_address(trip_data['pickup_location'])
    dropoff_coords = geocode_address(trip_data['dropoff_location'])
    
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
    rest_stops = []
    fuel_stops = []
    
    # Current cycle hours from input
    current_cycle_hours = float(trip_data.get('current_cycle_hours', 0))
    
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
            rest_stops.append({
                'coordinates': [route_coordinates[i]['lat'], route_coordinates[i]['lng']],
                'duration': 0.5,
                'reason': "30-minute break (8-hour driving limit)"
            })
            hours_since_last_break = 0
        
        # Check if we need a 10-hour rest period
        if driving_time_covered >= remaining_driving_hours or driving_time_covered >= remaining_on_duty_hours:
            rest_stops.append({
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
            fuel_stops.append({
                'coordinates': [route_coordinates[i]['lat'], route_coordinates[i]['lng']],
                'distance': distance_covered
            })
            last_fuel_stop = distance_covered
    
    # Add 1 hour for pickup and 1 hour for dropoff
    total_trip_time = total_driving_time + sum(stop['duration'] for stop in rest_stops) + 2  # 1 hour each for pickup and dropoff
    
    return {
        'start_location': trip_data['current_location'],
        'pickup_location': trip_data['pickup_location'],
        'dropoff_location': trip_data['dropoff_location'],
        'start_coordinates': [start_coords['lat'], start_coords['lng']],
        'pickup_coordinates': [pickup_coords['lat'], pickup_coords['lng']],
        'dropoff_coordinates': [dropoff_coords['lat'], dropoff_coords['lng']],
        'total_distance': total_distance,
        'driving_time': total_driving_time,
        'total_trip_time': total_trip_time,
        'rest_stops': rest_stops,
        'fuel_stops': fuel_stops,
        'route_coordinates': [[coord['lat'], coord['lng']] for coord in route_coordinates]
    }

def generate_eld_logs(route_data):
    """Generate ELD logs based on the calculated route"""
    if not route_data:
        return None
    
    # Calculate how many days the trip will take
    total_days = math.ceil(route_data['total_trip_time'] / 24)
    days = []
    
    current_hour = 8  # Start at 8 AM on the first day
    current_day = 0
    cycle_hours_used = 0  # Track 70-hour/8-day cycle
    
    # Track remaining times from the route calculation
    remaining_driving_time = route_data['driving_time']
    remaining_rest_stops = route_data['rest_stops'].copy()
    
    # Process each day
    while current_day < total_days:
        date = datetime.now() + timedelta(days=current_day)
        date_string = date.strftime('%a, %b %d')
        
        day_log = {
            'date': date_string,
            'status_blocks': [],
            'events': [],
            'driving_hours': 0,
            'on_duty_hours': 0,
            'off_duty_hours': 0,
            'cycle_hours_used': 0
        }
        
        # Start with off duty if it's the beginning of the day and not the first day
        if current_day > 0 and current_hour == 0:
            day_log['status_blocks'].append({
                'status': 'OFF',
                'start_hour': 0,
                'end_hour': 8
            })
            day_log['events'].append({
                'hour': 0,
                'description': 'Off duty (rest period)'
            })
            day_log['off_duty_hours'] += 8
            current_hour = 8
        
        # Process the day's activities
        while current_hour < 24 and remaining_driving_time > 0:
            # Check if we have a rest stop
            if (remaining_rest_stops and 
                day_log['driving_hours'] + day_log['on_duty_hours'] > 0 and 
                day_log['driving_hours'] + day_log['on_duty_hours'] >= remaining_rest_stops[0]['duration']):
                
                rest_stop = remaining_rest_stops.pop(0)
                rest_duration = rest_stop['duration']
                
                # Add off duty block for the rest stop
                day_log['status_blocks'].append({
                    'status': 'SB' if rest_duration >= 8 else 'OFF',  # Use sleeper berth for long breaks
                    'start_hour': current_hour,
                    'end_hour': min(current_hour + rest_duration, 24)
                })
                
                day_log['events'].append({
                    'hour': current_hour,
                    'description': f"{rest_stop['reason']} ({rest_duration} hours)"
                })
                
                if current_hour + rest_duration <= 24:
                    day_log['off_duty_hours'] += rest_duration
                    current_hour += rest_duration
                else:
                    # Rest continues to next day
                    hours_today = 24 - current_hour
                    day_log['off_duty_hours'] += hours_today
                    current_hour = 24  # End of day
                
                continue
            
            # Handle pickup (1 hour on-duty, not driving)
            if day_log['driving_hours'] == 0 and day_log['on_duty_hours'] == 0 and current_day == 0:
                day_log['status_blocks'].append({
                    'status': 'ON',
                    'start_hour': current_hour,
                    'end_hour': current_hour + 1
                })
                
                day_log['events'].append({
                    'hour': current_hour,
                    'description': 'On duty - Pickup location'
                })
                
                day_log['on_duty_hours'] += 1
                cycle_hours_used += 1
                current_hour += 1
                continue
            
            # Handle dropoff if we're near the end of driving time
            if remaining_driving_time <= 1 and day_log['driving_hours'] > 0:
                day_log['status_blocks'].append({
                    'status': 'ON',
                    'start_hour': current_hour,
                    'end_hour': current_hour + 1
                })
                
                day_log['events'].append({
                    'hour': current_hour,
                    'description': 'On duty - Dropoff location'
                })
                
                day_log['on_duty_hours'] += 1
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
            
            day_log['status_blocks'].append({
                'status': 'D',
                'start_hour': current_hour,
                'end_hour': current_hour + driving_period
            })
            
            day_log['events'].append({
                'hour': current_hour,
                'description': f"Driving ({driving_period:.1f} hours)"
            })
            
            day_log['driving_hours'] += driving_period
            cycle_hours_used += driving_period
            current_hour += driving_period
            remaining_driving_time -= driving_period
        
        # Fill the rest of the day with off-duty if needed
        if current_hour < 24:
            day_log['status_blocks'].append({
                'status': 'OFF',
                'start_hour': current_hour,
                'end_hour': 24
            })
            
            if current_hour < 23:  # Only log if it's a significant period
                day_log['events'].append({
                    'hour': current_hour,
                    'description': 'Off duty'
                })
            
            day_log['off_duty_hours'] += (24 - current_hour)
            current_hour = 24
        
        # Update cycle hours for the day
        day_log['cycle_hours_used'] = cycle_hours_used
        
        # Add the day to our logs
        days.append(day_log)
        
        # Reset for next day
        current_hour = 0
        current_day += 1
    
    return {'days': days}

# Django views
@csrf_exempt
@require_http_methods(["POST"])
def calculate_route_view(request):
    """API endpoint to calculate a route"""
    try:
        data = json.loads(request.body)
        
        # Validate inputs
        required_fields = ['current_location', 'pickup_location', 'dropoff_location']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Calculate route
        route_data = calculate_route({
            'current_location': data['current_location'],
            'pickup_location': data['pickup_location'],
            'dropoff_location': data['dropoff_location'],
            'current_cycle_hours': data.get('current_cycle_hours', 0)
        })
        
        return JsonResponse(route_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def generate_eld_logs_view(request):
    """API endpoint to generate ELD logs"""
    try:
        route_data = json.loads(request.body)
        
        if not route_data:
            return JsonResponse({'error': 'Missing route data'}, status=400)
        
        # Generate ELD logs
        eld_logs = generate_eld_logs(route_data)
        
        return JsonResponse(eld_logs)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# In a real Django project, you would include these in urls.py:
# path('api/calculate-route/', calculate_route_view, name='calculate_route'),
# path('api/generate-eld-logs/', generate_eld_logs_view, name='generate_eld_logs'),