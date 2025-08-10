"""
AI-Powered Calendar Analyzer Agent using LLMs for intelligent event understanding
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain.prompts import ChatPromptTemplate

from tools.google_calendar_mock import MockGoogleCalendarTool
from services.backend_service import BackendService
from utils.event_normalizer import EventNormalizer

logger = logging.getLogger(__name__)


class AICalendarAnalyzer:
    """AI-powered agent for intelligent calendar analysis"""
    
    def __init__(self, llm: BaseLanguageModel, backend_service: BackendService):
        self.llm = llm
        self.backend_service = backend_service
        self.calendar_tool = None  # Will be set per user
        
        # Define the AI prompt for calendar analysis
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert calendar analyst AI. Your job is to analyze calendar events and extract meaningful insights for commute planning decisions.

For each calendar event, analyze:
1. Meeting importance and priority level
2. Required attendance mode (in-person vs remote viable)
3. Meeting context and relationships between events
4. Time constraints and scheduling patterns
5. Stakeholder involvement and business impact

Provide structured analysis that will help determine optimal work location decisions."""),
            ("human", """Analyze these calendar events for {date}:

CALENDAR EVENTS:
{events_json}

Please provide:
1. Overall day structure analysis
2. Key insights about meeting patterns
3. Recommendations for work location optimization
4. Confidence assessment of your analysis

Format your response as structured analysis, not just a list.""")
        ])
    
    async def analyze_schedule(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered calendar analysis using LLMs for intelligent understanding
        """
        
        user_id = state["user_id"]
        target_date = state["target_date"]
        
        logger.info(f"AI analyzing schedule for user {user_id} on {target_date}")
        
        try:
            # Initialize calendar tool for this user
            self.calendar_tool = MockGoogleCalendarTool(user_id)
            
            # Update progress
            state["progress_step"] = "AI retrieving and analyzing calendar events"
            state["progress_percentage"] = 0.1
            
            # First, try to get events from database
            db_events = await self.backend_service.get_user_calendar_events(user_id, target_date)
            
            calendar_events = []
            
            if db_events:
                logger.info(f"Found {len(db_events)} events in database")
                calendar_events = self._normalize_db_events(db_events)
            else:
                logger.info("No database events found, generating mock calendar data")
                calendar_events = await self.calendar_tool.get_calendar_events(target_date)
            
            if not calendar_events:
                logger.warning("No calendar events found")
                state["calendar_events"] = []
                state["ai_insights"]["calendar_analysis"] = "No events found for analysis"
                return state
            
            # AI-POWERED ANALYSIS: Use LLM to understand the events
            ai_analysis = await self._analyze_events_with_ai(calendar_events, target_date)
            
            # Update state with both events and AI insights
            state["calendar_events"] = calendar_events
            state["llm_reasoning"]["calendar_analysis"] = ai_analysis["reasoning"]
            state["confidence_scores"]["calendar_analysis"] = ai_analysis["confidence"]
            state["ai_insights"]["calendar_patterns"] = ai_analysis["patterns"]
            state["ai_insights"]["work_location_hints"] = ai_analysis["location_hints"]
            
            state["progress_percentage"] = 0.25
            
            logger.info(f"AI calendar analysis complete: {len(calendar_events)} events analyzed")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in AI calendar analysis: {e}")
            state["error_message"] = f"AI calendar analysis failed: {str(e)}"
            return state
    
    def _normalize_db_events(self, db_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize database events from backend GraphQL (camelCase) to AI service format (snake_case)
        
        This method was missing and causing the empty timestamp issue!
        """
        logger.info(f"Normalizing {len(db_events)} database events")
        
        try:
            normalized_events = EventNormalizer.normalize_event_list(db_events, source="backend")
            
            # Log normalization results
            events_with_times = [e for e in normalized_events if e.get("start_time") and e.get("end_time")]
            events_without_times = [e for e in normalized_events if not e.get("start_time") or not e.get("end_time")]
            
            logger.info(f"Normalization complete: {len(events_with_times)} events with timestamps, "
                       f"{len(events_without_times)} events missing timestamps")
            
            if events_without_times:
                logger.warning(f"Events without proper timestamps: {[e.get('summary', 'Unknown') for e in events_without_times]}")
            
            return normalized_events
            
        except Exception as e:
            logger.error(f"Error normalizing database events: {e}")
            # Return empty list rather than crash
            return []
    
    async def _analyze_events_with_ai(self, events: List[Dict[str, Any]], target_date: str) -> Dict[str, Any]:
        """Use LLM to analyze calendar events intelligently"""
        
        try:
            # Format events for AI analysis
            events_json = json.dumps(events, indent=2)
            
            # Create the prompt
            messages = self.analysis_prompt.format_messages(
                date=target_date,
                events_json=events_json
            )
            
            # Get AI analysis
            response = await self.llm.agenerate([messages])
            ai_analysis_text = response.generations[0][0].text
            
            # Extract structured insights from AI response
            insights = self._parse_ai_analysis(ai_analysis_text)
            
            return {
                "reasoning": ai_analysis_text,
                "confidence": self._calculate_confidence_score(events, ai_analysis_text),
                "patterns": insights.get("patterns", []),
                "location_hints": insights.get("location_hints", {})
            }
            
        except Exception as e:
            logger.error(f"Error in AI event analysis: {e}")
            return {
                "reasoning": f"AI analysis failed: {str(e)}",
                "confidence": 0.0,
                "patterns": [],
                "location_hints": {}
            }
    
    def _parse_ai_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Extract structured insights from AI analysis text"""
        
        insights = {
            "patterns": [],
            "location_hints": {}
        }
        
        try:
            # Look for key patterns in the AI response
            analysis_lower = analysis_text.lower()
            
            # Identify meeting patterns
            if "client" in analysis_lower or "presentation" in analysis_lower:
                insights["patterns"].append("client_facing_meetings")
            
            if "standup" in analysis_lower or "sync" in analysis_lower:
                insights["patterns"].append("routine_team_meetings")
                
            if "1:1" in analysis_lower or "one-on-one" in analysis_lower:
                insights["patterns"].append("personal_meetings")
            
            # Extract location hints
            if "office" in analysis_lower and "required" in analysis_lower:
                insights["location_hints"]["office_preference"] = "high"
            elif "remote" in analysis_lower and ("viable" in analysis_lower or "suitable" in analysis_lower):
                insights["location_hints"]["remote_viability"] = "high"
            else:
                insights["location_hints"]["flexibility"] = "moderate"
                
        except Exception as e:
            logger.warning(f"Could not parse AI analysis insights: {e}")
        
        return insights
    
    def _calculate_confidence_score(self, events: List[Dict[str, Any]], analysis: str) -> float:
        """Calculate confidence score for AI analysis"""
        
        base_confidence = 0.7  # Base confidence for AI analysis
        
        # Increase confidence based on event richness
        if events:
            # More events = more data = higher confidence
            event_factor = min(len(events) * 0.05, 0.2)
            base_confidence += event_factor
            
            # Rich event descriptions increase confidence
            for event in events:
                if event.get("description") and len(event["description"]) > 50:
                    base_confidence += 0.02
                    
                if event.get("attendees") and len(event["attendees"]) > 2:
                    base_confidence += 0.02
        
        # Analysis quality affects confidence
        if analysis:
            if len(analysis) > 300:  # Detailed analysis
                base_confidence += 0.05
            if "confidence" in analysis.lower():  # AI expressed confidence
                base_confidence += 0.05
        
        return min(base_confidence, 0.95)  # Cap at 95%
    
