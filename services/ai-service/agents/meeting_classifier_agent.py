"""
Meeting Classifier Agent - Determines remote vs in-office requirements
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, List

from models.workflow_state import CommuteState

logger = logging.getLogger(__name__)


class MeetingClassifierAgent:
    """Agent responsible for classifying meetings as office vs remote"""
    
    # Meeting classification rules based on ARCHITECTURE.md
    OFFICE_REQUIRED_KEYWORDS = [
        "client", "presentation", "demo", "interview", "workshop", "stakeholder",
        "board", "executive", "pitch", "contract", "signing", "negotiation",
        "training", "onboarding", "all-hands", "town hall", "offsite"
    ]
    
    REMOTE_FRIENDLY_KEYWORDS = [
        "1:1", "one-on-one", "standup", "sync", "check-in", "retrospective",
        "brainstorm", "code review", "planning", "backlog", "refinement"
    ]
    
    OFFICE_REQUIRED_TYPES = {
        "CLIENT_MEETING", "PRESENTATION", "TEAM_WORKSHOP", "INTERVIEW", "STAKEHOLDER_MEETING"
    }
    
    REMOTE_FRIENDLY_TYPES = {
        "ONE_ON_ONE", "STATUS_UPDATE", "REVIEW", "BRAINSTORMING", "CHECK_IN"
    }
    
    def __init__(self):
        pass
        
    async def classify_meetings(self, state: CommuteState) -> CommuteState:
        """
        Classify each meeting as requiring office presence or allowing remote attendance
        
        Classification logic:
        - CLIENT_MEETING, PRESENTATION, TEAM_WORKSHOP, INTERVIEW → MUST_BE_IN_OFFICE
        - ONE_ON_ONE, STATUS_UPDATE, REVIEW, BRAINSTORMING, CHECK_IN → CAN_BE_REMOTE
        - Unknown meetings → analyze by keywords and attendee count
        """
        
        logger.info(f"Classifying {len(state['calendar_events'])} meetings for office vs remote")
        
        try:
            # Update progress
            state["progress_step"] = "Classifying meeting requirements"
            state["progress_percentage"] = 0.3
            
            meeting_classifications = []
            
            for event in state["calendar_events"]:
                classification = self._classify_single_meeting(event)
                meeting_classifications.append(classification)
                
            # Analyze overall meeting distribution
            office_meetings = [m for m in meeting_classifications if m["requires_office"]]
            remote_meetings = [m for m in meeting_classifications if not m["requires_office"]]
            
            # Update state
            state["meeting_classifications"] = meeting_classifications
            state["progress_percentage"] = 0.4
            
            logger.info(
                f"Meeting classification complete: {len(office_meetings)} office-required, "
                f"{len(remote_meetings)} remote-friendly"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in meeting classification: {e}")
            state["error_message"] = f"Meeting classification failed: {str(e)}"
            return state
            
    def _classify_single_meeting(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a single meeting for office vs remote attendance"""
        
        meeting_id = event["id"]
        summary = event["summary"].lower()
        description = event.get("description", "").lower()
        meeting_type = event.get("meeting_type", "UNKNOWN")
        attendance_mode = event.get("attendance_mode", "FLEXIBLE")
        attendees = event.get("attendees", [])
        location = event.get("location", "").lower()
        
        # Start with explicit attendance mode if set
        if attendance_mode == "MUST_BE_IN_OFFICE":
            requires_office = True
            confidence = "high"
            reason = "Explicitly marked as office-required"
        elif attendance_mode == "CAN_BE_REMOTE":
            requires_office = False
            confidence = "high"
            reason = "Explicitly marked as remote-friendly"
        else:
            # Classify based on meeting type
            if meeting_type in self.OFFICE_REQUIRED_TYPES:
                requires_office = True
                confidence = "high"
                reason = f"Meeting type '{meeting_type}' requires office presence"
            elif meeting_type in self.REMOTE_FRIENDLY_TYPES:
                requires_office = False
                confidence = "high"
                reason = f"Meeting type '{meeting_type}' can be remote"
            else:
                # Analyze by keywords and context
                office_score = 0
                remote_score = 0
                reasons = []
                
                # Check for office-required keywords
                for keyword in self.OFFICE_REQUIRED_KEYWORDS:
                    if keyword in summary or keyword in description:
                        office_score += 2
                        reasons.append(f"Contains keyword '{keyword}'")
                        
                # Check for remote-friendly keywords
                for keyword in self.REMOTE_FRIENDLY_KEYWORDS:
                    if keyword in summary or keyword in description:
                        remote_score += 2
                        reasons.append(f"Contains remote-friendly keyword '{keyword}'")
                        
                # Attendee count analysis
                attendee_count = len(attendees) if attendees else 0
                if attendee_count >= 8:
                    office_score += 1
                    reasons.append(f"Large meeting ({attendee_count} attendees)")
                elif attendee_count <= 2:
                    remote_score += 1
                    reasons.append(f"Small meeting ({attendee_count} attendees)")
                    
                # Location analysis
                if "conference" in location or "room" in location:
                    office_score += 1
                    reasons.append("Conference room booked")
                elif "zoom" in location or "meet" in location or "teams" in location:
                    remote_score += 1
                    reasons.append("Virtual meeting platform specified")
                    
                # Duration analysis (very long meetings often need office presence)
                start_dt = datetime.fromisoformat(event["start_time"].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(event["end_time"].replace('Z', '+00:00'))
                duration_hours = (end_dt - start_dt).total_seconds() / 3600
                
                if duration_hours >= 3:
                    office_score += 1
                    reasons.append(f"Long meeting ({duration_hours:.1f} hours)")
                    
                # Make final decision
                if office_score > remote_score:
                    requires_office = True
                    confidence = "medium" if office_score - remote_score >= 2 else "low"
                    reason = "; ".join(reasons[:3])  # Top 3 reasons
                else:
                    requires_office = False
                    confidence = "medium" if remote_score > office_score else "low"
                    reason = "; ".join(reasons[:3]) if reasons else "Default to remote-friendly"
                    
        return {
            "meeting_id": meeting_id,
            "summary": event["summary"],
            "start_time": event["start_time"],
            "end_time": event["end_time"],
            "requires_office": requires_office,
            "confidence": confidence,
            "reason": reason,
            "meeting_type": meeting_type,
            "original_attendance_mode": attendance_mode,
            "attendee_count": len(attendees) if attendees else 0,
            "duration_minutes": int((datetime.fromisoformat(event["end_time"].replace('Z', '+00:00')) - 
                                   datetime.fromisoformat(event["start_time"].replace('Z', '+00:00'))).total_seconds() / 60)
        }
        
    def get_classification_summary(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of meeting classifications"""
        
        total_meetings = len(classifications)
        office_required = sum(1 for c in classifications if c["requires_office"])
        remote_friendly = total_meetings - office_required
        
        high_confidence = sum(1 for c in classifications if c["confidence"] == "high")
        
        office_duration = sum(c["duration_minutes"] for c in classifications if c["requires_office"])
        remote_duration = sum(c["duration_minutes"] for c in classifications if not c["requires_office"])
        
        return {
            "total_meetings": total_meetings,
            "office_required_count": office_required,
            "remote_friendly_count": remote_friendly,
            "high_confidence_classifications": high_confidence,
            "classification_accuracy": (high_confidence / total_meetings) if total_meetings > 0 else 0,
            "office_meeting_minutes": office_duration,
            "remote_meeting_minutes": remote_duration,
            "office_percentage": (office_required / total_meetings * 100) if total_meetings > 0 else 0
        }