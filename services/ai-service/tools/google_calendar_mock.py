"""
Mock Google Calendar tool with realistic varied scenarios
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MockGoogleCalendarTool:
    """Mock Google Calendar API tool returning realistic varied scenarios"""
    
    # Meeting templates for realistic scenarios
    MEETING_TEMPLATES = [
        # Must be in-office meetings
        {
            "summary": "Q4 Client Presentation - Acme Corp",
            "meeting_type": "CLIENT_MEETING",
            "attendance_mode": "MUST_BE_IN_OFFICE",
            "duration_hours": 2,
            "attendees": 8,
            "description": "Quarterly business review with Acme Corp leadership team"
        },
        {
            "summary": "Product Demo - Enterprise Customer",
            "meeting_type": "PRESENTATION",
            "attendance_mode": "MUST_BE_IN_OFFICE",
            "duration_hours": 1.5,
            "attendees": 6,
            "description": "Live product demonstration for potential enterprise customer"
        },
        {
            "summary": "Team Workshop - Sprint Planning",
            "meeting_type": "TEAM_WORKSHOP",
            "attendance_mode": "MUST_BE_IN_OFFICE",
            "duration_hours": 3,
            "attendees": 12,
            "description": "In-person collaborative sprint planning session"
        },
        {
            "summary": "Senior Engineer Interview",
            "meeting_type": "INTERVIEW",
            "attendance_mode": "MUST_BE_IN_OFFICE",
            "duration_hours": 4,
            "attendees": 4,
            "description": "On-site technical interview with candidate"
        },
        
        # Can be remote meetings
        {
            "summary": "1:1 with Sarah (Manager)",
            "meeting_type": "ONE_ON_ONE",
            "attendance_mode": "CAN_BE_REMOTE",
            "duration_hours": 0.5,
            "attendees": 2,
            "description": "Weekly check-in with direct manager"
        },
        {
            "summary": "Daily Standup - Dev Team",
            "meeting_type": "STATUS_UPDATE",
            "attendance_mode": "CAN_BE_REMOTE",
            "duration_hours": 0.25,
            "attendees": 8,
            "description": "Daily team sync and status update"
        },
        {
            "summary": "Code Review Session",
            "meeting_type": "REVIEW",
            "attendance_mode": "CAN_BE_REMOTE",
            "duration_hours": 1,
            "attendees": 4,
            "description": "Review pull requests from current sprint"
        },
        {
            "summary": "Feature Brainstorming Call",
            "meeting_type": "BRAINSTORMING",
            "attendance_mode": "CAN_BE_REMOTE",
            "duration_hours": 1,
            "attendees": 6,
            "description": "Collaborative brainstorming for new feature ideas"
        },
        {
            "summary": "Weekly Check-in - Product Team",
            "meeting_type": "CHECK_IN",
            "attendance_mode": "CAN_BE_REMOTE",
            "duration_hours": 0.5,
            "attendees": 5,
            "description": "Regular product team sync"
        }
    ]
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
    async def get_calendar_events(self, target_date: str) -> List[Dict[str, Any]]:
        """Get mock calendar events for target date with varied realistic scenarios"""
        
        # Create different scenarios based on user_id for variety
        scenario_seed = hash(f"{self.user_id}_{target_date}") % 5
        
        # Generate 2-6 meetings for the day
        num_meetings = random.Random(scenario_seed).randint(2, 6)
        
        events = []
        used_times = set()
        
        # Parse target date and ensure proper timezone handling
        if target_date.endswith('Z'):
            target_dt = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
        else:
            target_dt = datetime.fromisoformat(target_date)
        
        # Create base date in UTC without timezone info to avoid double timezone
        base_date = target_dt.replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=None)
        
        for i in range(num_meetings):
            template = random.Random(scenario_seed + i).choice(self.MEETING_TEMPLATES)
            
            # Generate meeting time (8 AM to 6 PM)
            start_hour = random.Random(scenario_seed + i * 2).randint(8, 17)
            start_minute = random.Random(scenario_seed + i * 3).choice([0, 15, 30, 45])
            
            # Avoid conflicts
            time_key = f"{start_hour}:{start_minute:02d}"
            if time_key in used_times:
                continue
                
            used_times.add(time_key)
            
            start_time = base_date.replace(hour=start_hour, minute=start_minute)
            end_time = start_time + timedelta(hours=template["duration_hours"])
            
            event = {
                "id": f"mock_event_{self.user_id}_{i}_{scenario_seed}",
                "summary": template["summary"],
                "description": template["description"],
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
                "location": "Conference Room A" if template["attendance_mode"] == "MUST_BE_IN_OFFICE" else "Zoom",
                "attendees": [
                    {"email": f"attendee{j}@company.com", "name": f"Attendee {j}"}
                    for j in range(template["attendees"])
                ],
                "meeting_type": template["meeting_type"],
                "attendance_mode": template["attendance_mode"],
                "is_all_day": False,
                "is_recurring": random.Random(scenario_seed + i * 4).choice([True, False])
            }
            
            events.append(event)
            
        # Sort by start time
        events.sort(key=lambda x: x["start_time"])
        
        logger.info(f"Generated {len(events)} mock calendar events for user {self.user_id}")
        
        return events
        
    async def get_availability(self, target_date: str) -> Dict[str, Any]:
        """Get mock availability information"""
        return {
            "busy_periods": [],  # Simplified for mock
            "working_hours": {
                "start": "09:00",
                "end": "17:00"
            },
            "timezone": "America/New_York"
        }