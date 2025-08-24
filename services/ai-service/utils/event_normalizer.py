"""
Event Data Normalization Utility

Provides consistent event data format conversion between:
- Backend GraphQL responses (camelCase)
- AI service processing (snake_case)
- Mock calendar data (snake_case)
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class EventNormalizer:
    """Handles consistent event data normalization across the AI service"""
    
    @staticmethod
    def normalize_backend_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize backend GraphQL event (camelCase) to AI service format (snake_case)
        
        Backend format: { startTime, endTime, meetingType, attendanceMode, isAllDay, isRecurring }
        AI format: { start_time, end_time, meeting_type, attendance_mode, is_all_day, is_recurring }
        """
        try:
            # Extract timestamps with proper fallback
            start_time = EventNormalizer._normalize_timestamp(
                event.get("startTime") or event.get("start_time")
            )
            end_time = EventNormalizer._normalize_timestamp(
                event.get("endTime") or event.get("end_time") 
            )
            
            # Log warning if timestamps are missing
            if not start_time or not end_time:
                logger.warning(f"Event {event.get('id', 'unknown')} missing timestamps: "
                             f"startTime={event.get('startTime')}, endTime={event.get('endTime')}")
            
            normalized = {
                # Basic fields
                "id": event.get("id", ""),
                "summary": event.get("summary", ""),
                "description": event.get("description", ""),
                
                # Timestamp fields (camelCase → snake_case)
                "start_time": start_time,
                "end_time": end_time,
                
                # Location and attendees
                "location": event.get("location", ""),
                "attendees": EventNormalizer._normalize_attendees(event.get("attendees")),
                
                # Enum fields (camelCase → snake_case)
                "meeting_type": event.get("meetingType") or event.get("meeting_type") or "UNKNOWN",
                "attendance_mode": event.get("attendanceMode") or event.get("attendance_mode") or "FLEXIBLE",
                
                # Boolean fields (camelCase → snake_case)
                "is_all_day": event.get("isAllDay") or event.get("is_all_day") or False,
                "is_recurring": event.get("isRecurring") or event.get("is_recurring") or False,
                
                # Optional fields
                "google_event_id": event.get("googleEventId") or event.get("google_event_id"),
            }
            
            logger.debug(f"Normalized event {normalized['id']}: {normalized['summary']} "
                        f"({normalized['start_time']} - {normalized['end_time']})")
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing backend event: {e}")
            logger.error(f"Event data: {event}")
            
            # Return safe fallback event
            return EventNormalizer._create_fallback_event(event)
    
    @staticmethod
    def normalize_mock_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize mock event data (already in snake_case, but validate format)
        """
        try:
            # Mock events should already be in correct format, but validate
            normalized = {
                "id": event.get("id", ""),
                "summary": event.get("summary", ""),
                "description": event.get("description", ""),
                "start_time": EventNormalizer._normalize_timestamp(event.get("start_time")),
                "end_time": EventNormalizer._normalize_timestamp(event.get("end_time")),
                "location": event.get("location", ""),
                "attendees": EventNormalizer._normalize_attendees(event.get("attendees")),
                "meeting_type": event.get("meeting_type", "UNKNOWN"),
                "attendance_mode": event.get("attendance_mode", "FLEXIBLE"),
                "is_all_day": event.get("is_all_day", False),
                "is_recurring": event.get("is_recurring", False),
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing mock event: {e}")
            return EventNormalizer._create_fallback_event(event)
    
    @staticmethod
    def normalize_event_list(events: List[Dict[str, Any]], source: str = "unknown") -> List[Dict[str, Any]]:
        """
        Normalize a list of events, detecting source format automatically
        
        Args:
            events: List of event dictionaries
            source: Source hint ("backend", "mock", or "unknown")
        """
        if not events:
            return []
        
        normalized_events = []
        
        for event in events:
            try:
                # Auto-detect source if not specified
                if source == "unknown":
                    detected_source = EventNormalizer._detect_event_source(event)
                else:
                    detected_source = source
                
                # Normalize based on detected source
                if detected_source == "backend":
                    normalized_event = EventNormalizer.normalize_backend_event(event)
                else:  # mock or unknown
                    normalized_event = EventNormalizer.normalize_mock_event(event)
                
                normalized_events.append(normalized_event)
                
            except Exception as e:
                logger.error(f"Error normalizing event in list: {e}")
                # Add fallback event to maintain list integrity
                normalized_events.append(EventNormalizer._create_fallback_event(event))
        
        logger.info(f"Normalized {len(normalized_events)} events from {source} source")
        return normalized_events
    
    @staticmethod
    def _normalize_timestamp(timestamp: Any) -> str:
        """
        Normalize various timestamp formats to ISO string
        
        Handles:
        - ISO strings
        - datetime objects  
        - None/empty values
        """
        if not timestamp:
            return ""
        
        if isinstance(timestamp, str):
            # Already a string, return as-is if it's a valid timestamp
            return timestamp
        
        if hasattr(timestamp, 'isoformat'):
            # datetime object
            iso_string = timestamp.isoformat()
            return iso_string + "Z" if not iso_string.endswith('Z') else iso_string
        
        # Try to convert to string
        return str(timestamp) if timestamp else ""
    
    @staticmethod
    def _normalize_attendees(attendees: Any) -> List[Dict[str, str]]:
        """Normalize attendees to consistent format"""
        if not attendees:
            return []
        
        if isinstance(attendees, str):
            # If it's a JSON string, try to parse it
            try:
                import json
                parsed = json.loads(attendees)
                if isinstance(parsed, list):
                    return parsed
            except:
                # If parsing fails, treat as single attendee email
                return [{"email": attendees, "name": attendees.split("@")[0]}]
        
        if isinstance(attendees, list):
            return attendees
        
        return []
    
    @staticmethod
    def _detect_event_source(event: Dict[str, Any]) -> str:
        """
        Detect event source based on field naming convention
        
        Backend: camelCase (startTime, endTime, meetingType)
        Mock: snake_case (start_time, end_time, meeting_type)
        """
        # Check for camelCase fields (backend)
        if "startTime" in event or "endTime" in event or "meetingType" in event:
            return "backend"
        
        # Check for snake_case fields (mock)
        if "start_time" in event or "end_time" in event or "meeting_type" in event:
            return "mock"
        
        return "unknown"
    
    @staticmethod
    def _create_fallback_event(original_event: Dict[str, Any]) -> Dict[str, Any]:
        """Create a safe fallback event when normalization fails"""
        return {
            "id": original_event.get("id", "fallback_event"),
            "summary": original_event.get("summary", "Event Processing Error"),
            "description": "This event could not be processed correctly",
            "start_time": "",
            "end_time": "",
            "location": "",
            "attendees": [],
            "meeting_type": "UNKNOWN",
            "attendance_mode": "FLEXIBLE", 
            "is_all_day": False,
            "is_recurring": False,
        }