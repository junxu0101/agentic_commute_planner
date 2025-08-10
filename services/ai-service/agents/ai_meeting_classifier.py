"""
AI-Powered Meeting Classifier using LLMs for intelligent meeting analysis
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List

from langchain_core.language_models import BaseLanguageModel
from langchain.prompts import ChatPromptTemplate
from utils.event_normalizer import EventNormalizer

logger = logging.getLogger(__name__)


class AIMeetingClassifier:
    """AI-powered agent for intelligent meeting classification"""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        
        # Define the AI prompt for meeting classification
        self.classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert meeting analyst AI. Your job is to classify meetings for optimal work location decisions.

For each meeting, determine:
1. **Office Requirement Level**: 
   - MUST_BE_IN_OFFICE: Client meetings, presentations, interviews, workshops requiring in-person presence
   - CAN_BE_REMOTE: 1:1s, standups, reviews, brainstorming that work well remotely  
   - FLEXIBLE: Could work either way depending on context

2. **Business Impact**: High/Medium/Low importance for business outcomes
3. **Collaboration Intensity**: How much interactive collaboration is needed
4. **Stakeholder Sensitivity**: External clients vs internal team
5. **Technology Requirements**: Specialized equipment, whiteboards, etc.

Provide detailed reasoning for each classification."""),
            ("human", """Classify these meetings for work location optimization:

MEETINGS TO CLASSIFY:
{meetings_json}

For each meeting, provide:
1. Recommended attendance mode (MUST_BE_IN_OFFICE/CAN_BE_REMOTE/FLEXIBLE)
2. Confidence level (0.0-1.0) 
3. Detailed reasoning
4. Key factors that influenced the decision
5. Alternative considerations

Return a structured JSON response with classifications.""")
        ])
    
    async def classify_meetings(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered meeting classification using LLMs
        """
        
        calendar_events = state.get("calendar_events", [])
        
        logger.info(f"AI classifying {len(calendar_events)} meetings")
        
        try:
            # Update progress
            state["progress_step"] = "AI analyzing meeting requirements"
            state["progress_percentage"] = 0.35
            
            if not calendar_events:
                logger.warning("No calendar events to classify")
                state["meeting_classifications"] = []
                return state
            
            # AI-POWERED CLASSIFICATION: Use LLM to understand meeting requirements
            ai_classifications = await self._classify_meetings_with_ai(calendar_events)
            
            # Process AI classifications into standard format
            meeting_classifications = self._process_ai_classifications(calendar_events, ai_classifications)
            
            # Update state with AI insights
            state["meeting_classifications"] = meeting_classifications
            state["llm_reasoning"]["meeting_classification"] = ai_classifications["reasoning"]
            state["confidence_scores"]["meeting_classification"] = ai_classifications["overall_confidence"]
            state["ai_insights"]["classification_factors"] = ai_classifications["key_factors"]
            
            # Analyze overall meeting distribution
            office_meetings = [m for m in meeting_classifications if m["requires_office"]]
            remote_meetings = [m for m in meeting_classifications if not m["requires_office"]]
            
            state["ai_insights"]["meeting_distribution"] = {
                "office_required": len(office_meetings),
                "remote_viable": len(remote_meetings),
                "total_meetings": len(meeting_classifications)
            }
            
            state["progress_percentage"] = 0.45
            
            logger.info(
                f"AI meeting classification complete: {len(office_meetings)} office-required, "
                f"{len(remote_meetings)} remote-viable"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error in AI meeting classification: {e}")
            state["error_message"] = f"AI meeting classification failed: {str(e)}"
            return state
    
    async def _classify_meetings_with_ai(self, meetings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to classify meetings intelligently"""
        
        try:
            # Format meetings for AI analysis
            meetings_json = json.dumps([
                {
                    "id": m.get("id"),
                    "summary": m.get("summary", ""),
                    "description": m.get("description", ""), 
                    "attendees_count": len(m.get("attendees", [])),
                    "duration_hours": self._calculate_duration_hours(m),
                    "location": m.get("location", ""),
                    "meeting_type": m.get("meeting_type", "UNKNOWN")
                }
                for m in meetings
            ], indent=2)
            
            # Create the prompt
            messages = self.classification_prompt.format_messages(
                meetings_json=meetings_json
            )
            
            # Get AI classification
            response = await self.llm.agenerate([messages])
            ai_response = response.generations[0][0].text
            
            # Try to parse as JSON, fallback to text analysis
            try:
                classifications_data = json.loads(ai_response)
            except json.JSONDecodeError:
                classifications_data = self._parse_text_response(ai_response, meetings)
            
            return {
                "reasoning": ai_response,
                "classifications": classifications_data,
                "overall_confidence": self._calculate_overall_confidence(classifications_data),
                "key_factors": self._extract_key_factors(ai_response)
            }
            
        except Exception as e:
            logger.error(f"Error in AI meeting classification: {e}")
            return {
                "reasoning": f"AI classification failed: {str(e)}",
                "classifications": {},
                "overall_confidence": 0.0,
                "key_factors": []
            }
    
    def _parse_text_response(self, response: str, meetings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse AI text response when JSON parsing fails"""
        
        classifications = {}
        
        for i, meeting in enumerate(meetings):
            meeting_id = meeting.get("id", f"meeting_{i}")
            
            # Extract classification from text (simple heuristics)
            response_lower = response.lower()
            meeting_summary = meeting.get("summary", "").lower()
            
            if any(keyword in meeting_summary for keyword in ["client", "presentation", "demo", "interview"]):
                requires_office = True
                confidence = 0.8
                reasoning = "Client-facing or high-stakes meeting requiring in-person presence"
            elif any(keyword in meeting_summary for keyword in ["standup", "1:1", "sync", "review"]):
                requires_office = False
                confidence = 0.7
                reasoning = "Routine meeting suitable for remote attendance"
            else:
                requires_office = "office" in response_lower and meeting_summary in response_lower
                confidence = 0.6
                reasoning = "Classification based on AI text analysis"
            
            classifications[meeting_id] = {
                "requires_office": requires_office,
                "confidence": confidence,
                "reasoning": reasoning,
                "attendance_mode": "MUST_BE_IN_OFFICE" if requires_office else "CAN_BE_REMOTE"
            }
        
        return classifications
    
    def _process_ai_classifications(self, meetings: List[Dict[str, Any]], ai_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process AI classifications into standard format"""
        
        classifications = []
        ai_classifications = ai_data.get("classifications", {})
        
        for i, meeting in enumerate(meetings):
            meeting_id = meeting.get("id", f"meeting_{i}")
            
            # Get AI classification or fallback
            ai_result = ai_classifications.get(meeting_id, {})
            
            # Ensure meeting is properly normalized before processing
            normalized_meeting = self._ensure_normalized_meeting(meeting)
            
            classification = {
                "meeting_id": meeting_id,
                "summary": normalized_meeting.get("summary", ""),
                "start_time": normalized_meeting.get("start_time", ""),
                "end_time": normalized_meeting.get("end_time", ""),
                "duration_hours": self._calculate_duration_hours(normalized_meeting),
                "attendee_count": len(normalized_meeting.get("attendees", [])),
                
                # AI-powered decisions
                "requires_office": ai_result.get("requires_office", False),
                "attendance_mode": ai_result.get("attendance_mode", "CAN_BE_REMOTE"),
                "business_impact": ai_result.get("business_impact", "Medium"),
                "collaboration_intensity": ai_result.get("collaboration_intensity", "Medium"),
                
                # AI metadata
                "ai_confidence": ai_result.get("confidence", 0.7),
                "ai_reasoning": ai_result.get("reasoning", "Standard classification applied"),
                "classification_method": "ai_llm_powered"
            }
            
            classifications.append(classification)
        
        return classifications
    
    def _ensure_normalized_meeting(self, meeting: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure meeting data is properly normalized, handling both camelCase and snake_case
        
        This prevents the empty timestamp issue by checking both naming conventions
        """
        try:
            # If meeting already has proper snake_case timestamps, return as-is
            if meeting.get("start_time") and meeting.get("end_time"):
                return meeting
            
            # If meeting has camelCase fields, normalize it
            if meeting.get("startTime") or meeting.get("endTime"):
                logger.debug("Normalizing meeting with camelCase fields")
                return EventNormalizer.normalize_backend_event(meeting)
            
            # If no timestamp fields found at all, log warning and return with empty times
            logger.warning(f"Meeting {meeting.get('id', 'unknown')} has no timestamp fields: {list(meeting.keys())}")
            meeting_copy = meeting.copy()
            meeting_copy.update({
                "start_time": "",
                "end_time": ""
            })
            return meeting_copy
            
        except Exception as e:
            logger.error(f"Error normalizing meeting {meeting.get('id', 'unknown')}: {e}")
            return meeting
    
    def _calculate_duration_hours(self, meeting: Dict[str, Any]) -> float:
        """Calculate meeting duration in hours"""
        
        try:
            start_time = meeting.get("start_time", "")
            end_time = meeting.get("end_time", "")
            
            if not start_time or not end_time:
                return 1.0  # Default 1 hour
            
            # Parse ISO format times
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration = end_dt - start_dt
            return duration.total_seconds() / 3600
            
        except Exception:
            return 1.0  # Fallback to 1 hour
    
    def _calculate_overall_confidence(self, classifications_data: Dict[str, Any]) -> float:
        """Calculate overall confidence for all classifications"""
        
        if not classifications_data:
            return 0.0
            
        confidences = []
        for classification in classifications_data.values():
            if isinstance(classification, dict):
                confidences.append(classification.get("confidence", 0.7))
        
        return sum(confidences) / len(confidences) if confidences else 0.7
    
    def _extract_key_factors(self, ai_response: str) -> List[str]:
        """Extract key decision factors from AI response"""
        
        factors = []
        response_lower = ai_response.lower()
        
        if "client" in response_lower:
            factors.append("client_involvement")
        if "presentation" in response_lower:
            factors.append("presentation_requirements")
        if "collaboration" in response_lower:
            factors.append("collaborative_work")
        if "stakeholder" in response_lower:
            factors.append("stakeholder_engagement")
        if "technology" in response_lower or "equipment" in response_lower:
            factors.append("technical_requirements")
        
        return factors or ["standard_business_logic"]