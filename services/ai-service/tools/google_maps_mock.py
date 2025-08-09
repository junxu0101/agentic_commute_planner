"""
Mock Google Maps tool with realistic travel time scenarios
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MockGoogleMapsTool:
    """Mock Google Maps API tool with realistic travel time variations"""
    
    # Base commute times for different scenarios (in minutes)
    BASE_COMMUTE_TIMES = {
        "brooklyn_to_midtown": {
            "base": 45,
            "rush_hour_multiplier": 1.8,
            "off_peak_multiplier": 0.7,
            "weekend_multiplier": 0.6
        },
        "queens_to_midtown": {
            "base": 35,
            "rush_hour_multiplier": 1.6,
            "off_peak_multiplier": 0.8,
            "weekend_multiplier": 0.7
        },
        "new_jersey_to_midtown": {
            "base": 60,
            "rush_hour_multiplier": 2.0,
            "off_peak_multiplier": 0.8,
            "weekend_multiplier": 0.6
        },
        "westchester_to_midtown": {
            "base": 55,
            "rush_hour_multiplier": 1.7,
            "off_peak_multiplier": 0.9,
            "weekend_multiplier": 0.7
        }
    }
    
    # Rush hour definitions
    MORNING_RUSH = (7, 10)  # 7 AM - 10 AM
    EVENING_RUSH = (17, 19)  # 5 PM - 7 PM
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        # Choose commute scenario based on user_id for consistency
        scenarios = list(self.BASE_COMMUTE_TIMES.keys())
        self.scenario = scenarios[hash(user_id) % len(scenarios)]
        
    async def get_route_duration(
        self,
        origin: str,
        destination: str,
        departure_time: str = None,
        arrival_time: str = None
    ) -> Dict[str, Any]:
        """Get mock route duration with realistic traffic patterns"""
        
        scenario_data = self.BASE_COMMUTE_TIMES[self.scenario]
        base_duration = scenario_data["base"]
        
        # Determine time of day for traffic calculations
        if departure_time:
            if departure_time.endswith('Z'):
                dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(departure_time)
        elif arrival_time:
            if arrival_time.endswith('Z'):
                dt = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(arrival_time)
        else:
            dt = datetime.now()
            
        hour = dt.hour
        is_weekend = dt.weekday() >= 5
        
        # Apply multipliers based on time
        if is_weekend:
            multiplier = scenario_data["weekend_multiplier"]
            traffic_description = "Light weekend traffic"
        elif self.MORNING_RUSH[0] <= hour <= self.MORNING_RUSH[1]:
            multiplier = scenario_data["rush_hour_multiplier"]
            traffic_description = "Heavy morning rush hour traffic"
        elif self.EVENING_RUSH[0] <= hour <= self.EVENING_RUSH[1]:
            multiplier = scenario_data["rush_hour_multiplier"]
            traffic_description = "Heavy evening rush hour traffic"
        else:
            multiplier = scenario_data["off_peak_multiplier"]
            traffic_description = "Light off-peak traffic"
            
        # Add some randomness for realism (±10%)
        random_factor = random.Random(hash(f"{self.user_id}_{departure_time}")).uniform(0.9, 1.1)
        
        final_duration = int(base_duration * multiplier * random_factor)
        
        # Calculate distance (roughly 1 mile per 2-3 minutes in city traffic)
        distance_miles = final_duration / 2.5
        
        return {
            "duration": {
                "value": final_duration * 60,  # Convert to seconds
                "text": f"{final_duration} mins"
            },
            "distance": {
                "value": int(distance_miles * 1609),  # Convert to meters
                "text": f"{distance_miles:.1f} miles"
            },
            "traffic_info": {
                "conditions": traffic_description,
                "delay_minutes": max(0, final_duration - base_duration)
            },
            "route_summary": f"Via {self.scenario.replace('_to_', ' → ').title()}",
            "departure_time": departure_time,
            "arrival_time": arrival_time
        }
        
    async def get_multiple_route_options(
        self,
        origin: str,
        destination: str,
        departure_time: str
    ) -> List[Dict[str, Any]]:
        """Get multiple route options with different timing"""
        
        base_route = await self.get_route_duration(origin, destination, departure_time)
        
        # Generate alternative routes with slight variations
        routes = [base_route]
        
        # Alternative route 1: Slightly longer but potentially faster
        alt_route_1 = base_route.copy()
        alt_route_1["duration"]["value"] = int(base_route["duration"]["value"] * 0.95)
        alt_route_1["duration"]["text"] = f"{alt_route_1['duration']['value'] // 60} mins"
        alt_route_1["distance"]["value"] = int(base_route["distance"]["value"] * 1.1)
        alt_route_1["distance"]["text"] = f"{alt_route_1['distance']['value'] * 0.000621371:.1f} miles"
        alt_route_1["route_summary"] = "Via Highway (longer but faster)"
        routes.append(alt_route_1)
        
        # Alternative route 2: Scenic route (longer)
        alt_route_2 = base_route.copy()
        alt_route_2["duration"]["value"] = int(base_route["duration"]["value"] * 1.15)
        alt_route_2["duration"]["text"] = f"{alt_route_2['duration']['value'] // 60} mins"
        alt_route_2["distance"]["value"] = int(base_route["distance"]["value"] * 1.2)
        alt_route_2["distance"]["text"] = f"{alt_route_2['distance']['value'] * 0.000621371:.1f} miles"
        alt_route_2["route_summary"] = "Via Local Streets (scenic route)"
        routes.append(alt_route_2)
        
        return routes
        
    async def calculate_optimal_departure_time(
        self,
        destination: str,
        target_arrival: str,
        origin: str = None
    ) -> Dict[str, Any]:
        """Calculate optimal departure time to arrive by target time"""
        
        # Parse target arrival time and handle timezone properly
        if target_arrival.endswith('Z'):
            target_dt = datetime.fromisoformat(target_arrival.replace('Z', '+00:00'))
        else:
            target_dt = datetime.fromisoformat(target_arrival)
        
        # Get route duration for target arrival time
        route_info = await self.get_route_duration(
            origin or "home",
            destination,
            arrival_time=target_arrival
        )
        
        # Calculate departure time (add 5-minute buffer)
        travel_seconds = route_info["duration"]["value"]
        buffer_seconds = 5 * 60  # 5-minute buffer
        
        # Remove timezone info before calculation to avoid double timezone
        target_dt_naive = target_dt.replace(tzinfo=None)
        departure_dt = target_dt_naive - timedelta(seconds=travel_seconds + buffer_seconds)
        
        return {
            "optimal_departure": departure_dt.isoformat() + "Z",
            "travel_duration": route_info["duration"],
            "buffer_time": "5 mins",
            "arrival_time": target_arrival,
            "route_info": route_info,
            "confidence": "high" if route_info["traffic_info"]["delay_minutes"] < 10 else "medium"
        }
        
    async def get_parking_info(self, destination: str) -> Dict[str, Any]:
        """Get mock parking information"""
        # Generate consistent parking info based on destination
        parking_scenarios = [
            {
                "availability": "high",
                "cost_per_hour": 8,
                "walking_time_minutes": 3,
                "type": "street_parking"
            },
            {
                "availability": "medium", 
                "cost_per_hour": 15,
                "walking_time_minutes": 1,
                "type": "parking_garage"
            },
            {
                "availability": "low",
                "cost_per_hour": 25,
                "walking_time_minutes": 8,
                "type": "premium_lot"
            }
        ]
        
        scenario_idx = hash(destination) % len(parking_scenarios)
        scenario = parking_scenarios[scenario_idx]
        
        return {
            "parking_options": [scenario],
            "recommended_buffer_minutes": 15,  # Standard 15-minute buffer
            "peak_hours": ["8:00-10:00", "17:00-19:00"]
        }