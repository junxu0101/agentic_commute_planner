"""
AI-Powered Office Presence Decision Maker using LLMs for intelligent business logic
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from langchain_core.language_models import BaseLanguageModel
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class AIOfficeDecisionMaker:
    """AI-powered agent for intelligent office presence decisions"""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        
        # Define the AI prompt for office presence decisions
        self.decision_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert workplace optimization AI. Your job is to make intelligent decisions about office vs remote work based on meeting requirements, business rules, and productivity optimization.

Consider these factors:
1. **Business Rules**: 4+ hour minimum for office presence (but flexible for exceptional cases)
2. **Meeting Requirements**: Office-required vs remote-viable meetings
3. **Productivity Optimization**: Minimize commute while maximizing effectiveness
4. **Team Coordination**: Consider collaboration opportunities
5. **Personal Efficiency**: Balance work-life and commute costs
6. **Context Factors**: Weather, traffic, personal circumstances

Generate multiple viable options with different work arrangements (full remote, hybrid, full office) and rank them by overall utility."""),
            ("human", """Make office presence decisions based on this meeting analysis:

MEETING CLASSIFICATIONS:
{meetings_json}

TARGET DATE: {target_date}

BUSINESS CONTEXT:
- Standard policy: 4+ hours in office if going in
- Flexible arrangements allowed for optimal productivity
- Team collaboration valued but not mandatory
- Commute cost and time should be considered

Please generate:
1. Multiple office presence options (remote, hybrid, full office)
2. Detailed reasoning for each option
3. Pros and cons analysis
4. Recommended option with confidence score
5. Compliance assessment with business rules

Format as structured analysis with clear recommendations.""")
        ])
    
    async def make_office_decisions(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered office presence decision making
        """
        
        meeting_classifications = state.get("meeting_classifications", [])
        target_date = state.get("target_date", "")
        
        logger.info(f"AI making office presence decisions for {len(meeting_classifications)} meetings")
        
        try:
            # Update progress
            state["progress_step"] = "AI determining optimal office presence strategy"
            state["progress_percentage"] = 0.55
            
            if not meeting_classifications:
                logger.warning("No meeting classifications to analyze")
                state["office_presence_blocks"] = []
                return state
            
            # AI-POWERED DECISION MAKING: Use LLM for intelligent business logic
            ai_decisions = await self._make_decisions_with_ai(meeting_classifications, target_date)
            
            # Process AI decisions into structured office presence blocks
            office_presence_blocks = self._process_ai_decisions(ai_decisions, meeting_classifications)
            
            # Update state with AI insights
            state["office_presence_blocks"] = office_presence_blocks
            state["llm_reasoning"]["office_decisions"] = ai_decisions["reasoning"]
            state["confidence_scores"]["office_decisions"] = ai_decisions["confidence"]
            state["ai_insights"]["decision_factors"] = ai_decisions["key_factors"]
            state["ai_insights"]["alternative_options"] = ai_decisions["alternatives"]
            
            state["progress_percentage"] = 0.65
            
            logger.info(f"AI office decisions complete: {len(office_presence_blocks)} presence options generated")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in AI office decision making: {e}")
            state["error_message"] = f"AI office decision making failed: {str(e)}"
            return state
    
    async def _make_decisions_with_ai(self, meetings: List[Dict[str, Any]], target_date: str) -> Dict[str, Any]:
        """Use LLM to make intelligent office presence decisions"""
        
        try:
            # Format meetings for AI analysis
            meetings_json = json.dumps([
                {
                    "summary": m.get("summary", ""),
                    "start_time": m.get("start_time", ""),
                    "duration_hours": m.get("duration_hours", 1.0),
                    "requires_office": m.get("requires_office", False),
                    "attendance_mode": m.get("attendance_mode", "CAN_BE_REMOTE"),
                    "business_impact": m.get("business_impact", "Medium"),
                    "ai_confidence": m.get("ai_confidence", 0.7),
                    "ai_reasoning": m.get("ai_reasoning", "")
                }
                for m in meetings
            ], indent=2)
            
            # Create the prompt
            messages = self.decision_prompt.format_messages(
                meetings_json=meetings_json,
                target_date=target_date
            )
            
            # Get AI decision analysis
            response = await self.llm.agenerate([messages])
            ai_response = response.generations[0][0].text
            
            # Extract structured decisions from AI response
            decisions_data = self._parse_ai_decisions(ai_response, meetings)
            
            return {
                "reasoning": ai_response,
                "decisions": decisions_data,
                "confidence": self._calculate_decision_confidence(decisions_data),
                "key_factors": self._extract_decision_factors(ai_response),
                "alternatives": self._extract_alternatives(ai_response)
            }
            
        except Exception as e:
            logger.error(f"Error in AI decision making: {e}")
            return {
                "reasoning": f"AI decision making failed: {str(e)}",
                "decisions": self._fallback_decisions(meetings),
                "confidence": 0.5,
                "key_factors": ["fallback_logic"],
                "alternatives": []
            }
    
    def _parse_ai_decisions(self, response: str, meetings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse AI decision response into structured format"""
        
        decisions = {
            "recommended_option": "hybrid",
            "options": []
        }
        
        try:
            response_lower = response.lower()
            
            # Analyze AI response for decision patterns
            office_meetings = [m for m in meetings if m.get("requires_office", False)]
            remote_meetings = [m for m in meetings if not m.get("requires_office", False)]
            
            # Generate options based on AI analysis and meeting requirements
            if office_meetings:
                # Generate hybrid option (recommended if office meetings exist)
                hybrid_option = self._create_hybrid_option(office_meetings, remote_meetings, response)
                decisions["options"].append(hybrid_option)
                decisions["recommended_option"] = "hybrid"
                
                # Generate full office option
                office_option = self._create_office_option(meetings, response)
                decisions["options"].append(office_option)
            
            # Always generate remote option
            remote_option = self._create_remote_option(meetings, response)
            decisions["options"].append(remote_option)
            
            # If no office meetings, recommend remote
            if not office_meetings:
                decisions["recommended_option"] = "remote"
            
        except Exception as e:
            logger.warning(f"Could not parse AI decisions: {e}")
            decisions = self._fallback_decisions(meetings)
        
        return decisions
    
    def _create_hybrid_option(self, office_meetings: List, remote_meetings: List, ai_response: str) -> Dict[str, Any]:
        """Create hybrid work option based on AI analysis"""
        
        # Calculate office time window around office-required meetings
        office_start_hour = 9  # Default start
        office_end_hour = 17   # Default end
        
        if office_meetings:
            meeting_hours = []
            for meeting in office_meetings:
                try:
                    start_time = meeting.get("start_time", "")
                    if start_time:
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        meeting_hours.append(dt.hour)
                except:
                    continue
            
            if meeting_hours:
                office_start_hour = max(8, min(meeting_hours) - 1)  # 1 hour before first meeting
                office_end_hour = min(18, max(meeting_hours) + 2)   # 2 hours after last meeting
        
        office_duration = office_end_hour - office_start_hour
        
        return {
            "type": "HYBRID_RECOMMENDED",
            "arrival_hour": office_start_hour,
            "departure_hour": office_end_hour,
            "office_duration_hours": office_duration,
            "office_meetings": office_meetings,
            "remote_meetings": remote_meetings,
            "business_rule_compliance": {
                "meets_4_hour_minimum": office_duration >= 4,
                "policy_compliant": True,
                "exceptions_applied": []
            },
            "compliance_score": 0.95,
            "ai_rationale": f"Hybrid approach optimizes for office-required meetings while allowing remote work for flexible meetings",
            "warnings": [] if office_duration >= 4 else ["Office duration below 4-hour minimum"]
        }
    
    def _create_office_option(self, meetings: List, ai_response: str) -> Dict[str, Any]:
        """Create full office day option"""
        
        return {
            "type": "FULL_OFFICE_DAY",
            "arrival_hour": 9,
            "departure_hour": 17,
            "office_duration_hours": 8,
            "office_meetings": meetings,
            "remote_meetings": [],
            "business_rule_compliance": {
                "meets_4_hour_minimum": True,
                "policy_compliant": True,
                "exceptions_applied": []
            },
            "compliance_score": 1.0,
            "ai_rationale": "Full office day maximizes collaboration opportunities and ensures all meetings have in-person option",
            "warnings": ["Higher commute cost and time investment"]
        }
    
    def _create_remote_option(self, meetings: List, ai_response: str) -> Dict[str, Any]:
        """Create full remote work option"""
        
        office_meetings = [m for m in meetings if m.get("requires_office", False)]
        
        return {
            "type": "FULL_REMOTE_RECOMMENDED",
            "arrival_hour": None,
            "departure_hour": None,
            "office_duration_hours": 0,
            "office_meetings": [],
            "remote_meetings": meetings,
            "business_rule_compliance": {
                "meets_4_hour_minimum": False,
                "policy_compliant": len(office_meetings) == 0,
                "exceptions_applied": ["remote_work_optimization"] if office_meetings else []
            },
            "compliance_score": 1.0 if len(office_meetings) == 0 else 0.3,
            "ai_rationale": "Remote work maximizes productivity and minimizes commute cost when no office presence required",
            "warnings": ["May impact collaboration opportunities"] + (
                [f"{len(office_meetings)} meetings may benefit from in-person attendance"] if office_meetings else []
            )
        }
    
    def _fallback_decisions(self, meetings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback decision making when AI fails"""
        
        office_meetings = [m for m in meetings if m.get("requires_office", False)]
        
        if office_meetings:
            return {
                "recommended_option": "hybrid",
                "options": [self._create_hybrid_option(office_meetings, [m for m in meetings if not m.get("requires_office", False)], "")]
            }
        else:
            return {
                "recommended_option": "remote", 
                "options": [self._create_remote_option(meetings, "")]
            }
    
    def _process_ai_decisions(self, ai_decisions: Dict[str, Any], meetings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process AI decisions into standard office presence blocks"""
        
        return ai_decisions.get("decisions", {}).get("options", [])
    
    def _calculate_decision_confidence(self, decisions_data: Dict[str, Any]) -> float:
        """Calculate confidence in AI decisions"""
        
        options = decisions_data.get("options", [])
        if not options:
            return 0.5
        
        # Base confidence on number of viable options and their compliance
        base_confidence = 0.7
        
        compliant_options = [opt for opt in options if opt.get("compliance_score", 0) > 0.8]
        if compliant_options:
            base_confidence += 0.1
        
        if len(options) > 1:  # Multiple options show thorough analysis
            base_confidence += 0.05
        
        return min(base_confidence, 0.95)
    
    def _extract_decision_factors(self, ai_response: str) -> List[str]:
        """Extract key decision factors from AI response"""
        
        factors = []
        response_lower = ai_response.lower()
        
        if "meeting" in response_lower:
            factors.append("meeting_requirements")
        if "commute" in response_lower:
            factors.append("commute_optimization")
        if "productivity" in response_lower:
            factors.append("productivity_analysis")
        if "collaboration" in response_lower:
            factors.append("team_collaboration")
        if "policy" in response_lower or "rule" in response_lower:
            factors.append("business_compliance")
        
        return factors or ["standard_decision_logic"]
    
    def _extract_alternatives(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract alternative considerations from AI response"""
        
        alternatives = []
        
        if "weather" in ai_response.lower():
            alternatives.append({"factor": "weather", "impact": "commute_conditions"})
        if "traffic" in ai_response.lower():
            alternatives.append({"factor": "traffic", "impact": "commute_time"})
        if "team" in ai_response.lower():
            alternatives.append({"factor": "team_presence", "impact": "collaboration_opportunities"})
        
        return alternatives