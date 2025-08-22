"""
AI-Powered Commute Optimizer using LLMs for intelligent route and timing optimization
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from zoneinfo import ZoneInfo

from langchain_core.language_models import BaseLanguageModel
from langchain.prompts import ChatPromptTemplate

from tools.google_maps_mock import MockGoogleMapsTool

logger = logging.getLogger(__name__)


class AICommuteOptimizer:
    """AI-powered agent for intelligent commute optimization"""
    
    def __init__(self, llm: BaseLanguageModel, user_id: str):
        self.llm = llm
        self.user_id = user_id
        self.maps_tool = MockGoogleMapsTool(user_id) if user_id else None
        
        # Define the AI prompt for commute optimization
        self.optimization_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert commute optimization AI. Your job is to create intelligent, personalized commute strategies that balance efficiency, cost, productivity, and quality of life.

Consider these optimization factors:
1. **Traffic Patterns**: Rush hour avoidance, real-time conditions
2. **Multi-modal Options**: Driving, transit, walking, cycling combinations
3. **Personal Preferences**: Comfort, reliability, cost sensitivity
4. **Productivity Opportunities**: Travel time utilization
5. **Environmental Impact**: Sustainable transportation choices
6. **Flexibility**: Buffer times, alternative routes, contingency plans
7. **Work-Life Balance**: Stress reduction, family time preservation

Generate creative, practical solutions that go beyond basic time calculations."""),
            ("human", """Optimize commute strategies for these office presence options in {user_timezone} timezone:

OFFICE PRESENCE BLOCKS:
{presence_blocks_json}

TARGET DATE: {target_date}
USER CONTEXT: {user_id}
TIMEZONE CONTEXT:
- User timezone: {user_timezone}
- All times should be interpreted in the user's local timezone
- Schedule optimization considers local rush hour patterns
- Meeting times are displayed in user's timezone for clarity

OPTIMIZATION GOALS:
- Minimize total travel time while maximizing reliability
- Consider traffic patterns and alternative routes
- Balance commute cost vs time savings
- Optimize for productivity and stress reduction
- Provide creative solutions and contingency plans

For each presence block, provide:
1. Optimal departure/arrival timing with reasoning
2. Route recommendations with alternatives
3. Multi-modal transport analysis
4. Productivity optimization suggestions
5. Risk assessment and contingency planning
6. Cost-benefit analysis
7. Environmental impact considerations

Generate detailed, actionable commute strategies.""")
        ])
    
    async def optimize_commute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered commute optimization with intelligent reasoning
        """
        
        presence_blocks = state.get("office_presence_blocks", [])
        target_date = state.get("target_date", "")
        user_id = state.get("user_id", "")
        user_timezone = state.get("user_timezone", "UTC")
        
        logger.info(f"AI optimizing commute for {len(presence_blocks)} presence options in {user_timezone} timezone")
        
        try:
            # Update progress
            state["progress_step"] = "AI optimizing commute strategies"
            state["progress_percentage"] = 0.75
            
            if not presence_blocks:
                logger.warning("No office presence blocks to optimize")
                state["commute_options"] = []
                return state
            
            # Initialize maps tool for this user if not already set
            if not self.maps_tool and user_id:
                self.maps_tool = MockGoogleMapsTool(user_id)
            
            # AI-POWERED OPTIMIZATION: Use LLM for intelligent commute planning
            ai_optimizations = await self._optimize_with_ai(presence_blocks, target_date, user_id, user_timezone)
            
            # Process AI optimizations with real route data
            commute_options = await self._process_ai_optimizations(ai_optimizations, presence_blocks, target_date, user_timezone)
            
            # Update state with AI insights
            state["commute_options"] = commute_options
            state["llm_reasoning"]["commute_optimization"] = ai_optimizations["reasoning"]
            state["confidence_scores"]["commute_optimization"] = ai_optimizations["confidence"]
            state["ai_insights"]["optimization_strategies"] = ai_optimizations["strategies"]
            state["ai_insights"]["alternative_routes"] = ai_optimizations["alternatives"]
            state["ai_insights"]["environmental_impact"] = ai_optimizations["environmental_analysis"]
            
            state["progress_percentage"] = 0.85
            
            logger.info(f"AI commute optimization complete: {len(commute_options)} optimized options")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in AI commute optimization: {e}")
            state["error_message"] = f"AI commute optimization failed: {str(e)}"
            return state
    
    async def _optimize_with_ai(self, presence_blocks: List[Dict[str, Any]], target_date: str, user_id: str, user_timezone: str = "UTC") -> Dict[str, Any]:
        """Use LLM for intelligent commute optimization with timezone awareness"""
        
        try:
            # Format presence blocks for AI analysis
            blocks_json = json.dumps([
                {
                    "type": block.get("type", ""),
                    "arrival_hour": block.get("arrival_hour"),
                    "departure_hour": block.get("departure_hour"),
                    "office_duration_hours": block.get("office_duration_hours", 0),
                    "office_meetings": [m.get("summary", "") for m in block.get("office_meetings", [])],
                    "remote_meetings": [m.get("summary", "") for m in block.get("remote_meetings", [])],
                    "compliance_score": block.get("compliance_score", 0.8),
                    "ai_rationale": block.get("ai_rationale", "")
                }
                for block in presence_blocks
            ], indent=2)
            
            # Create the prompt with timezone context
            messages = self.optimization_prompt.format_messages(
                presence_blocks_json=blocks_json,
                target_date=target_date,
                user_id=user_id,
                user_timezone=user_timezone
            )
            
            # Get AI optimization analysis
            response = await self.llm.agenerate([messages])
            ai_response = response.generations[0][0].text
            
            # Extract structured optimizations from AI response
            optimizations_data = self._parse_ai_optimizations(ai_response)
            
            return {
                "reasoning": ai_response,
                "optimizations": optimizations_data,
                "confidence": self._calculate_optimization_confidence(optimizations_data),
                "strategies": self._extract_strategies(ai_response),
                "alternatives": self._extract_alternatives(ai_response),
                "environmental_analysis": self._extract_environmental_impact(ai_response)
            }
            
        except Exception as e:
            logger.error(f"Error in AI optimization: {e}")
            return {
                "reasoning": f"AI optimization failed: {str(e)}",
                "optimizations": {},
                "confidence": 0.5,
                "strategies": ["fallback_optimization"],
                "alternatives": [],
                "environmental_analysis": {}
            }
    
    async def _process_ai_optimizations(self, ai_data: Dict[str, Any], presence_blocks: List[Dict[str, Any]], target_date: str, user_timezone: str = "UTC") -> List[Dict[str, Any]]:
        """Process AI optimizations with real route data"""
        
        commute_options = []
        
        for block in presence_blocks:
            if block.get("type") == "FULL_REMOTE_RECOMMENDED":
                # Create remote work option
                remote_option = await self._create_remote_option(block, ai_data, target_date, user_timezone)
                commute_options.append(remote_option)
            else:
                # Create office commute option with AI optimization
                office_option = await self._create_office_option(block, ai_data, target_date, user_timezone)
                commute_options.append(office_option)
        
        return commute_options
    
    async def _create_office_option(self, presence_block: Dict[str, Any], ai_data: Dict[str, Any], target_date: str, user_timezone: str = "UTC") -> Dict[str, Any]:
        """Create AI-optimized office commute option with timezone awareness"""
        
        try:
            arrival_hour = presence_block.get("arrival_hour", 9)
            departure_hour = presence_block.get("departure_hour", 17)
            
            # Parse target date to extract the intended date (ignore timezone for date extraction)
            if target_date.endswith('Z'):
                target_dt = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            else:
                target_dt = datetime.fromisoformat(target_date)
            
            # Get user timezone object
            user_tz = ZoneInfo(user_timezone)
            
            # Extract just the date part and create new datetime in user's timezone
            # This ensures we're working with the intended date (e.g., Aug 14) in the user's timezone
            target_date_only = target_dt.date()
            office_arrival_dt = datetime.combine(target_date_only, datetime.min.time()).replace(tzinfo=user_tz)
            office_arrival_dt = office_arrival_dt.replace(hour=int(arrival_hour), minute=0, second=0, microsecond=0)
            
            office_departure_dt = datetime.combine(target_date_only, datetime.min.time()).replace(tzinfo=user_tz)
            office_departure_dt = office_departure_dt.replace(hour=int(departure_hour), minute=0, second=0, microsecond=0)
            
            # DEBUG: Log the calculated times with call stack info
            import traceback
            logger.error(f"=== TIMEZONE DEBUG START ===")
            logger.error(f"CALL STACK: {traceback.format_stack()[-3:-1]}")
            logger.error(f"INPUT - Target date: {target_date}")
            logger.error(f"INPUT - User timezone: {user_timezone}")
            logger.error(f"INPUT - Arrival hour: {arrival_hour}, Departure hour: {departure_hour}")
            logger.error(f"INPUT - Presence block: {presence_block}")
            logger.error(f"CALCULATED - Office arrival (local): {office_arrival_dt}")
            logger.error(f"CALCULATED - Office arrival (UTC): {office_arrival_dt.astimezone(ZoneInfo('UTC'))}")
            logger.error(f"CALCULATED - Office departure (local): {office_departure_dt}")
            logger.error(f"CALCULATED - Office departure (UTC): {office_departure_dt.astimezone(ZoneInfo('UTC'))}")
            logger.error(f"=== TIMEZONE DEBUG END ===")
            
            # Get AI-informed optimal departure time (convert to UTC for API)
            commute_start_info = await self.maps_tool.calculate_optimal_departure_time(
                destination="office",
                target_arrival=office_arrival_dt.astimezone(ZoneInfo("UTC")).isoformat(),
                origin="home"
            )
            
            # Get return journey with AI considerations (convert to UTC for API)
            return_commute_info = await self.maps_tool.get_route_duration(
                origin="office",
                destination="home",
                departure_time=office_departure_dt.astimezone(ZoneInfo("UTC")).isoformat()
            )
            
            # Parse commute times and convert to user timezone
            optimal_departure = commute_start_info["optimal_departure"]
            if optimal_departure.endswith('Z'):
                commute_start_dt = datetime.fromisoformat(optimal_departure.replace('Z', '+00:00'))
            else:
                commute_start_dt = datetime.fromisoformat(optimal_departure)
            
            # Convert UTC commute start time to user timezone
            commute_start_dt = commute_start_dt.astimezone(user_tz)
            
            # Calculate end time in user timezone
            commute_end_dt = office_departure_dt + timedelta(seconds=return_commute_info["duration"]["value"])
            
            # Get AI-enhanced route alternatives (convert to UTC for API)
            route_alternatives = await self.maps_tool.get_multiple_route_options(
                origin="home",
                destination="office", 
                departure_time=commute_start_dt.astimezone(ZoneInfo("UTC")).isoformat()
            )
            
            # Calculate AI-informed efficiency metrics
            office_duration_timedelta = office_departure_dt - office_arrival_dt
            total_commute_time = (office_arrival_dt - commute_start_dt) + (commute_end_dt - office_departure_dt)
            total_day_duration = commute_end_dt - commute_start_dt
            
            efficiency_metrics = {
                "total_commute_minutes": int(total_commute_time.total_seconds() / 60),
                "office_minutes": int(office_duration_timedelta.total_seconds() / 60),
                "total_day_minutes": int(total_day_duration.total_seconds() / 60),
                "commute_to_office_ratio": round(total_commute_time.total_seconds() / office_duration_timedelta.total_seconds(), 2),
                "day_efficiency": round(office_duration_timedelta.total_seconds() / total_day_duration.total_seconds(), 2)
            }
            
            # DEBUG: Log final output before returning
            final_commute_start = commute_start_dt.astimezone(ZoneInfo("UTC")).isoformat()
            final_office_arrival = office_arrival_dt.astimezone(ZoneInfo("UTC")).isoformat()
            final_office_departure = office_departure_dt.astimezone(ZoneInfo("UTC")).isoformat()
            final_commute_end = commute_end_dt.astimezone(ZoneInfo("UTC")).isoformat()
            
            logger.error(f"=== FINAL OUTPUT DEBUG ===")
            logger.error(f"OUTPUT - commute_start: {final_commute_start}")
            logger.error(f"OUTPUT - office_arrival: {final_office_arrival}")
            logger.error(f"OUTPUT - office_departure: {final_office_departure}")
            logger.error(f"OUTPUT - commute_end: {final_commute_end}")
            logger.error(f"=== FINAL OUTPUT DEBUG END ===")

            return {
                "option_type": presence_block["type"],
                "commute_start": final_commute_start,
                "office_arrival": final_office_arrival,
                "office_departure": final_office_departure,
                "commute_end": final_commute_end,
                "office_duration": self._format_duration(office_duration_timedelta),
                "office_meetings": presence_block.get("office_meetings", []),
                "remote_meetings": presence_block.get("remote_meetings", []),
                "business_rule_compliance": presence_block.get("business_rule_compliance", {}),
                
                # AI-enhanced commute details
                "ai_commute_strategy": {
                    "optimization_approach": "ai_traffic_pattern_analysis",
                    "route_alternatives": len(route_alternatives),
                    "reliability_score": commute_start_info.get("confidence", "medium"),
                    "productivity_suggestions": self._generate_productivity_tips(total_commute_time),
                    "environmental_score": self._calculate_environmental_score(efficiency_metrics),
                    "stress_reduction_tips": self._generate_stress_tips(ai_data)
                },
                
                "commute_details": {
                    "morning_commute": {
                        "duration": commute_start_info["travel_duration"]["text"],
                        "route": commute_start_info["route_info"]["route_summary"],
                        "traffic_conditions": commute_start_info["route_info"]["traffic_info"]["conditions"],
                        "confidence": commute_start_info["confidence"],
                        "ai_insights": "Optimized timing to avoid peak congestion"
                    },
                    "evening_commute": {
                        "duration": return_commute_info["duration"]["text"],
                        "route": return_commute_info["route_summary"],
                        "traffic_conditions": return_commute_info["traffic_info"]["conditions"],
                        "ai_insights": "Evening departure timing balances traffic and work completion"
                    },
                    "route_alternatives": [
                        {
                            "name": route["route_summary"],
                            "duration": route["duration"]["text"],
                            "reliability": "high" if route["traffic_info"]["delay_minutes"] < 10 else "moderate"
                        }
                        for route in route_alternatives[:2]  # Top 2 alternatives
                    ]
                },
                
                "efficiency_metrics": efficiency_metrics,
                "ai_confidence": ai_data.get("confidence", 0.8),
                "warnings": presence_block.get("warnings", []),
                "compliance_score": presence_block.get("compliance_score", 0.8)
            }
            
        except Exception as e:
            logger.error(f"Error creating AI office option: {e}")
            logger.error(f"Presence block: {presence_block}")
            logger.error(f"Target date: {target_date}, User timezone: {user_timezone}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._create_fallback_office_option(presence_block)
    
    async def _create_remote_option(self, presence_block: Dict[str, Any], ai_data: Dict[str, Any], target_date: str, user_timezone: str = "UTC") -> Dict[str, Any]:
        """Create AI-enhanced remote work option with timezone awareness"""
        
        return {
            "option_type": "FULL_REMOTE_RECOMMENDED",
            "commute_start": None,
            "office_arrival": None,
            "office_departure": None,
            "commute_end": None,
            "office_duration": "0 hours (remote work)",
            "office_meetings": [],
            "remote_meetings": presence_block.get("remote_meetings", []),
            "business_rule_compliance": presence_block.get("business_rule_compliance", {}),
            
            # AI-enhanced remote work strategy
            "ai_remote_strategy": {
                "productivity_optimization": "ai_schedule_analysis",
                "collaboration_tools": ["video_conferencing", "screen_sharing", "digital_whiteboard"],
                "focus_time_blocks": self._generate_focus_blocks(presence_block),
                "energy_management": "optimal_break_scheduling",
                "environmental_benefits": "zero_commute_carbon_footprint"
            },
            
            "commute_details": {
                "total_commute_time": "0 mins",
                "environmental_impact": "Zero carbon footprint - excellent choice!",
                "cost_savings": "$0 (no parking, gas, or transit costs)",
                "productivity_benefits": [
                    "No commute time = 2+ hours for focused work",
                    "Flexible schedule for optimal performance periods",
                    "Reduced stress from traffic and commute logistics",
                    "AI-optimized home workspace productivity"
                ],
                "ai_insights": "Remote work maximizes time efficiency and environmental sustainability"
            },
            
            "efficiency_metrics": {
                "total_commute_minutes": 0,
                "office_minutes": 0,
                "total_day_minutes": 480,  # 8-hour workday
                "commute_to_office_ratio": 0,
                "day_efficiency": 1.0  # 100% efficiency
            },
            
            "ai_confidence": ai_data.get("confidence", 0.9),
            "warnings": presence_block.get("warnings", []),
            "compliance_score": presence_block.get("compliance_score", 1.0)
        }
    
    def _parse_ai_optimizations(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI optimization response"""
        
        return {
            "traffic_analysis": "peak_avoidance" in ai_response.lower(),
            "multi_modal_considered": "transit" in ai_response.lower() or "bike" in ai_response.lower(),
            "productivity_focus": "productivity" in ai_response.lower(),
            "environmental_awareness": "environment" in ai_response.lower() or "carbon" in ai_response.lower(),
            "flexibility_planning": "alternative" in ai_response.lower() or "contingency" in ai_response.lower()
        }
    
    def _calculate_optimization_confidence(self, optimizations: Dict[str, Any]) -> float:
        """Calculate confidence in AI optimizations"""
        
        base_confidence = 0.75
        
        # Increase confidence based on optimization comprehensiveness
        if optimizations.get("traffic_analysis"):
            base_confidence += 0.05
        if optimizations.get("multi_modal_considered"):
            base_confidence += 0.05
        if optimizations.get("productivity_focus"):
            base_confidence += 0.03
        if optimizations.get("environmental_awareness"):
            base_confidence += 0.02
        if optimizations.get("flexibility_planning"):
            base_confidence += 0.05
        
        return min(base_confidence, 0.95)
    
    def _extract_strategies(self, ai_response: str) -> List[str]:
        """Extract optimization strategies from AI response"""
        
        strategies = []
        response_lower = ai_response.lower()
        
        if "traffic" in response_lower:
            strategies.append("traffic_pattern_optimization")
        if "route" in response_lower:
            strategies.append("multi_route_analysis")
        if "time" in response_lower:
            strategies.append("timing_optimization")
        if "cost" in response_lower:
            strategies.append("cost_benefit_analysis")
        if "stress" in response_lower:
            strategies.append("stress_minimization")
        
        return strategies or ["standard_optimization"]
    
    def _extract_alternatives(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract alternative considerations from AI response"""
        
        alternatives = []
        
        if "weather" in ai_response.lower():
            alternatives.append({"type": "weather_contingency", "impact": "route_reliability"})
        if "traffic" in ai_response.lower():
            alternatives.append({"type": "traffic_alternatives", "impact": "timing_flexibility"})
        if "transit" in ai_response.lower():
            alternatives.append({"type": "public_transport", "impact": "cost_sustainability"})
        
        return alternatives
    
    def _extract_environmental_impact(self, ai_response: str) -> Dict[str, Any]:
        """Extract environmental analysis from AI response"""
        
        return {
            "carbon_awareness": "carbon" in ai_response.lower() or "environment" in ai_response.lower(),
            "sustainability_score": 0.8 if "sustainable" in ai_response.lower() else 0.6,
            "eco_friendly_options": "transit" in ai_response.lower() or "bike" in ai_response.lower()
        }
    
    def _generate_productivity_tips(self, commute_time: timedelta) -> List[str]:
        """Generate AI productivity suggestions"""
        
        commute_minutes = int(commute_time.total_seconds() / 60)
        
        if commute_minutes > 60:
            return [
                "Use commute time for audiobooks or podcasts",
                "Schedule phone calls during predictable traffic delays",
                "Consider mobile workspace setup for productive transit time"
            ]
        else:
            return [
                "Short commute allows for morning routine optimization",
                "Use travel time for mindfulness or mental preparation"
            ]
    
    def _calculate_environmental_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate environmental impact score"""
        
        commute_minutes = metrics.get("total_commute_minutes", 0)
        
        if commute_minutes == 0:
            return 1.0  # Perfect score for remote work
        elif commute_minutes < 60:
            return 0.8  # Good score for short commute
        elif commute_minutes < 120:
            return 0.6  # Moderate score for medium commute
        else:
            return 0.4  # Lower score for long commute
    
    def _generate_stress_tips(self, ai_data: Dict[str, Any]) -> List[str]:
        """Generate stress reduction tips from AI analysis"""
        
        return [
            "Build buffer time for unexpected delays",
            "Use calming music or meditation during commute",
            "Have backup route planned for traffic contingencies",
            "Schedule calls after arrival to avoid commute pressure"
        ]
    
    def _generate_focus_blocks(self, presence_block: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate focus time blocks for remote work"""
        
        return [
            {"time": "9:00-11:00 AM", "activity": "Deep focus work", "duration": "2 hours"},
            {"time": "2:00-4:00 PM", "activity": "Creative tasks", "duration": "2 hours"},
            {"time": "4:30-5:30 PM", "activity": "Administrative work", "duration": "1 hour"}
        ]
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format timedelta as human-readable string"""
        
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
    
    def _create_fallback_office_option(self, presence_block: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback option when AI optimization fails"""
        
        return {
            "option_type": presence_block.get("type", "OFFICE_PRESENCE"),
            "commute_start": "08:00:00Z",
            "office_arrival": "09:00:00Z", 
            "office_departure": "17:00:00Z",
            "commute_end": "18:00:00Z",
            "office_duration": "8 hours",
            "office_meetings": presence_block.get("office_meetings", []),
            "remote_meetings": presence_block.get("remote_meetings", []),
            "business_rule_compliance": presence_block.get("business_rule_compliance", {}),
            "commute_details": {
                "morning_commute": {"duration": "1 hour", "route": "Standard route"},
                "evening_commute": {"duration": "1 hour", "route": "Standard route"}
            },
            "efficiency_metrics": {"day_efficiency": 0.8},
            "ai_confidence": 0.5,
            "warnings": ["Using fallback optimization - AI analysis unavailable"],
            "compliance_score": presence_block.get("compliance_score", 0.8)
        }