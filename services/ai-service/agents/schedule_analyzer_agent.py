"""
Schedule Analyzer Agent - Analyzes calendar events for commute planning
"""

import logging
from datetime import datetime
from typing import Dict, Any

from models.workflow_state import CommuteState
from tools.google_calendar_mock import MockGoogleCalendarTool
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class ScheduleAnalyzerAgent:
    """Agent responsible for analyzing calendar events"""
    
    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        
    async def analyze_schedule(self, state: CommuteState) -> CommuteState:
        """
        Analyze user's calendar for the target date
        
        Steps:
        1. Retrieve calendar events from database and/or external API
        2. Parse and normalize event data
        3. Identify meeting patterns and time blocks
        4. Update workflow state with calendar analysis
        """
        
        logger.info(f"Analyzing schedule for user {state['user_id']} on {state['target_date']}")
        
        try:
            # Update progress
            state["progress_step"] = "Analyzing calendar schedule"
            state["progress_percentage"] = 0.1
            
            # First, try to get events from database
            db_events = await self.database_service.get_user_calendar_events(
                state["user_id"],
                state["target_date"]
            )
            
            calendar_events = []
            
            if db_events:
                logger.info(f"Found {len(db_events)} events in database")
                calendar_events = self._normalize_db_events(db_events)
            else:
                # Use mock tool for demonstration
                logger.info("No events in database, using mock calendar data")
                calendar_tool = MockGoogleCalendarTool(state["user_id"])
                mock_events = await calendar_tool.get_calendar_events(state["target_date"])
                calendar_events = self._normalize_mock_events(mock_events)
            
            # Analyze calendar patterns
            analysis = self._analyze_calendar_patterns(calendar_events, state["target_date"])
            
            # Update state
            state["calendar_events"] = calendar_events
            state["progress_percentage"] = 0.2
            
            logger.info(
                f"Schedule analysis complete: {len(calendar_events)} events, "
                f"{analysis['total_meeting_time']} minutes of meetings"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in schedule analysis: {e}")
            state["error_message"] = f"Schedule analysis failed: {str(e)}"
            return state
            
    def _normalize_db_events(self, db_events):
        """Normalize database events to consistent format using shared utility"""
        from utils.event_normalizer import EventNormalizer
        
        logger.info(f"Normalizing {len(db_events)} database events (legacy method)")
        return EventNormalizer.normalize_event_list(db_events, source="backend")
        
    def _normalize_mock_events(self, mock_events):
        """Normalize mock events to consistent format (already in correct format)"""
        return mock_events
        
    def _analyze_calendar_patterns(self, events, target_date):
        """Analyze calendar patterns and meeting distribution"""
        
        total_meeting_time = 0
        meeting_blocks = []
        earliest_meeting = None
        latest_meeting = None
        
        for event in events:
            if event["is_all_day"]:
                continue
                
            start_dt = datetime.fromisoformat(event["start_time"].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(event["end_time"].replace('Z', '+00:00'))
            
            duration_minutes = (end_dt - start_dt).total_seconds() / 60
            total_meeting_time += duration_minutes
            
            meeting_blocks.append({
                "start": start_dt.hour + start_dt.minute / 60,
                "end": end_dt.hour + end_dt.minute / 60,
                "duration_minutes": duration_minutes,
                "meeting_type": event["meeting_type"],
                "attendance_mode": event["attendance_mode"]
            })
            
            if earliest_meeting is None or start_dt.hour < earliest_meeting:
                earliest_meeting = start_dt.hour
                
            if latest_meeting is None or end_dt.hour > latest_meeting:
                latest_meeting = end_dt.hour
                
        # Identify free time blocks (simplified)
        free_blocks = self._identify_free_blocks(meeting_blocks)
        
        return {
            "total_meeting_time": int(total_meeting_time),
            "meeting_blocks": meeting_blocks,
            "free_blocks": free_blocks,
            "earliest_meeting_hour": earliest_meeting,
            "latest_meeting_hour": latest_meeting,
            "meeting_density": len(events) / 10 if len(events) > 0 else 0  # meetings per 10-hour workday
        }
        
    def _identify_free_blocks(self, meeting_blocks):
        """Identify free time blocks between meetings"""
        if not meeting_blocks:
            return [{"start": 8, "end": 18, "duration_hours": 10}]
            
        # Sort meetings by start time
        sorted_meetings = sorted(meeting_blocks, key=lambda x: x["start"])
        
        free_blocks = []
        current_time = 8.0  # 8 AM
        
        for meeting in sorted_meetings:
            if meeting["start"] > current_time:
                # Free block before this meeting
                free_blocks.append({
                    "start": current_time,
                    "end": meeting["start"],
                    "duration_hours": meeting["start"] - current_time
                })
            current_time = max(current_time, meeting["end"])
            
        # Free block after last meeting (if before 6 PM)
        if current_time < 18:
            free_blocks.append({
                "start": current_time,
                "end": 18,
                "duration_hours": 18 - current_time
            })
            
        return free_blocks