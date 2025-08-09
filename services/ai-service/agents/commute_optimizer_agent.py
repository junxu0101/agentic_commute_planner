"""
Commute Optimizer Agent - Travel time and route optimization
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from models.workflow_state import CommuteState
from tools.google_maps_mock import MockGoogleMapsTool

logger = logging.getLogger(__name__)


class CommuteOptimizerAgent:
    """Agent responsible for travel time and route optimization"""
    
    # Safety and efficiency constants
    PARKING_BUFFER_MINUTES = 15  # Time for parking and walking
    PRE_MEETING_BUFFER_MINUTES = 30  # Buffer before first meeting (no calls while driving)
    POST_MEETING_BUFFER_MINUTES = 15  # Buffer after last meeting
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.maps_tool = MockGoogleMapsTool(user_id)
        
    async def optimize_commute(self, state: CommuteState) -> CommuteState:
        """
        Optimize commute timing and routes for each office presence block
        
        Steps:
        1. For each valid office presence block, calculate optimal commute times
        2. Factor in parking, walking, and safety buffers
        3. Consider traffic patterns and route alternatives
        4. Generate detailed commute options with timing
        """
        
        logger.info("Optimizing commute timing and routes")
        
        try:
            # Update progress
            state["progress_step"] = "Optimizing commute routes and timing"
            state["progress_percentage"] = 0.7
            
            presence_blocks = state.get("office_presence_blocks", [])
            target_date = state["target_date"]
            
            commute_options = []
            
            for block in presence_blocks:
                if block["type"] == "FULL_REMOTE_RECOMMENDED":
                    # No commute needed for remote work
                    commute_option = self._create_remote_commute_option(block, target_date)
                    commute_options.append(commute_option)
                else:
                    # Calculate commute timing for office presence
                    commute_option = await self._optimize_office_commute(block, target_date)
                    commute_options.append(commute_option)
                    
            # Update state
            state["commute_options"] = commute_options
            state["progress_percentage"] = 0.8
            
            logger.info(f"Generated {len(commute_options)} optimized commute options")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in commute optimization: {e}")
            state["error_message"] = f"Commute optimization failed: {str(e)}"
            return state
            
    async def _optimize_office_commute(self, presence_block: Dict[str, Any], target_date: str) -> Dict[str, Any]:
        """Optimize commute timing for an office presence block"""
        
        arrival_hour = presence_block["arrival_hour"]
        departure_hour = presence_block["departure_hour"]
        
        # Parse target date and create datetime objects without timezone to avoid double timezone
        if target_date.endswith('Z'):
            target_dt = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
        else:
            target_dt = datetime.fromisoformat(target_date)
        
        # Create datetime objects without timezone info to avoid double timezone
        base_date = target_dt.replace(tzinfo=None)
        office_arrival_dt = base_date.replace(
            hour=int(arrival_hour),
            minute=int((arrival_hour - int(arrival_hour)) * 60),
            second=0,
            microsecond=0
        )
        office_departure_dt = base_date.replace(
            hour=int(departure_hour), 
            minute=int((departure_hour - int(departure_hour)) * 60),
            second=0,
            microsecond=0
        )
        
        # Calculate optimal departure time from home
        commute_start_info = await self.maps_tool.calculate_optimal_departure_time(
            destination="office",
            target_arrival=office_arrival_dt.isoformat() + "Z",
            origin="home"
        )
        
        # Calculate return journey timing
        return_commute_info = await self.maps_tool.get_route_duration(
            origin="office",
            destination="home", 
            departure_time=office_departure_dt.isoformat() + "Z"
        )
        
        # Parse commute times with proper timezone handling (make timezone-naive to match other datetimes)
        optimal_departure = commute_start_info["optimal_departure"]
        if optimal_departure.endswith('Z'):
            commute_start_dt = datetime.fromisoformat(optimal_departure.replace('Z', '+00:00')).replace(tzinfo=None)
        else:
            commute_start_dt = datetime.fromisoformat(optimal_departure).replace(tzinfo=None)
        commute_end_dt = office_departure_dt + timedelta(
            seconds=return_commute_info["duration"]["value"]
        )
        
        # Get parking information
        parking_info = await self.maps_tool.get_parking_info("office")
        
        # Calculate total office duration
        office_duration_timedelta = office_departure_dt - office_arrival_dt
        office_duration_str = self._format_duration(office_duration_timedelta)
        
        # Calculate commute efficiency metrics
        total_commute_time = (office_arrival_dt - commute_start_dt) + (commute_end_dt - office_departure_dt)
        total_day_duration = commute_end_dt - commute_start_dt
        
        efficiency_metrics = {
            "total_commute_minutes": int(total_commute_time.total_seconds() / 60),
            "office_minutes": int(office_duration_timedelta.total_seconds() / 60),
            "total_day_minutes": int(total_day_duration.total_seconds() / 60),
            "commute_to_office_ratio": round(
                total_commute_time.total_seconds() / office_duration_timedelta.total_seconds(), 2
            ),
            "day_efficiency": round(
                office_duration_timedelta.total_seconds() / total_day_duration.total_seconds(), 2
            )
        }
        
        return {
            "option_type": presence_block["type"],
            "commute_start": commute_start_dt.isoformat() + "Z",
            "office_arrival": office_arrival_dt.isoformat() + "Z", 
            "office_departure": office_departure_dt.isoformat() + "Z",
            "commute_end": commute_end_dt.isoformat() + "Z",
            "office_duration": office_duration_str,
            "office_meetings": presence_block["office_meetings"],
            "remote_meetings": presence_block["remote_meetings"],
            "business_rule_compliance": presence_block["business_rule_compliance"],
            "commute_details": {
                "morning_commute": {
                    "duration": commute_start_info["travel_duration"]["text"],
                    "route": commute_start_info["route_info"]["route_summary"],
                    "traffic_conditions": commute_start_info["route_info"]["traffic_info"]["conditions"],
                    "confidence": commute_start_info["confidence"]
                },
                "evening_commute": {
                    "duration": return_commute_info["duration"]["text"],
                    "route": return_commute_info["route_summary"],
                    "traffic_conditions": return_commute_info["traffic_info"]["conditions"]
                },
                "parking": {
                    "walking_time": f"{parking_info['parking_options'][0]['walking_time_minutes']} mins",
                    "cost_estimate": f"${parking_info['parking_options'][0]['cost_per_hour'] * presence_block['office_duration_hours']:.0f}",
                    "availability": parking_info['parking_options'][0]['availability']
                }
            },
            "efficiency_metrics": efficiency_metrics,
            "warnings": presence_block.get("warnings", []),
            "compliance_score": presence_block["compliance_score"]
        }
        
    def _create_remote_commute_option(self, presence_block: Dict[str, Any], target_date: str) -> Dict[str, Any]:
        """Create commute option for remote work (no commute)"""
        
        return {
            "option_type": "FULL_REMOTE_RECOMMENDED",
            "commute_start": None,
            "office_arrival": None,
            "office_departure": None, 
            "commute_end": None,
            "office_duration": "0 hours (remote work)",
            "office_meetings": [],
            "remote_meetings": presence_block["remote_meetings"],
            "business_rule_compliance": presence_block["business_rule_compliance"],
            "commute_details": {
                "total_commute_time": "0 mins",
                "environmental_impact": "Zero carbon footprint",
                "cost_savings": "$0 (no parking, gas, or transit costs)",
                "productivity_benefits": [
                    "No commute time = more productive hours",
                    "Flexible schedule for optimal performance", 
                    "Reduced stress from traffic/parking"
                ]
            },
            "efficiency_metrics": {
                "total_commute_minutes": 0,
                "office_minutes": 0,
                "total_day_minutes": 480,  # 8-hour workday
                "commute_to_office_ratio": 0,
                "day_efficiency": 1.0  # 100% efficiency
            },
            "warnings": presence_block.get("warnings", []),
            "compliance_score": presence_block["compliance_score"]
        }
        
    def _format_duration(self, duration: timedelta) -> str:
        """Format timedelta as human-readable duration string"""
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            if minutes > 0:
                return f"{hours} hours {minutes} minutes"
            else:
                return f"{hours} hours"
        else:
            return f"{minutes} minutes"
            
    async def get_route_alternatives(self, origin: str, destination: str, departure_time: str) -> List[Dict[str, Any]]:
        """Get alternative route options for comparison"""
        
        return await self.maps_tool.get_multiple_route_options(origin, destination, departure_time)
        
    def calculate_cost_analysis(self, commute_option: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive cost analysis for commute option"""
        
        if commute_option["option_type"] == "FULL_REMOTE_RECOMMENDED":
            return {
                "parking_cost": 0,
                "gas_cost": 0,
                "transit_cost": 0,
                "time_cost_hours": 0,
                "total_cost": 0,
                "monthly_savings": 500  # Estimated monthly savings vs daily commute
            }
            
        # Estimate costs for office commute
        efficiency = commute_option["efficiency_metrics"]
        commute_minutes = efficiency["total_commute_minutes"]
        
        # Cost estimates (rough calculations)
        parking_cost = 25  # Average NYC parking per day
        gas_cost = 15      # Gas + wear and tear
        time_cost = (commute_minutes / 60) * 30  # Value time at $30/hour
        
        return {
            "parking_cost": parking_cost,
            "gas_cost": gas_cost,
            "time_cost_hours": round(commute_minutes / 60, 1),
            "total_cost": parking_cost + gas_cost + time_cost,
            "efficiency_score": efficiency["day_efficiency"]
        }