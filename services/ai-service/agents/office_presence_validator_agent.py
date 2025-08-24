"""
Office Presence Validator Agent - Applies 4+ hour business rules and validates office time blocks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

from models.workflow_state import CommuteState

logger = logging.getLogger(__name__)


class OfficePresenceValidatorAgent:
    """Agent responsible for validating office presence blocks against business rules"""
    
    # Business rule constants
    MINIMUM_OFFICE_HOURS = 4.0
    CORE_HOURS_START = 10  # 10 AM
    CORE_HOURS_END = 16    # 4 PM
    LUNCH_DASH_THRESHOLD = 1.5  # 1.5 hours or less is considered "lunch and dash"
    PROFESSIONAL_ARRIVAL_BEFORE = 10  # Arriving before 10 AM is professional
    PROFESSIONAL_DEPARTURE_AFTER = 16  # Staying past 4 PM is professional
    
    # Company policy configurations
    COMPANY_POLICIES = {
        "mandatory_office_days": ["Tuesday", "Thursday"],  # Example: Tuesdays and Thursdays required
        "minimum_office_days_per_week": 3,  # Example: At least 3 days per week
        "team_collaboration_days": {"Wednesday": "Engineering Team Sync"},
        "all_hands_days": {"first_tuesday": "Monthly All-Hands"}
    }
    
    def __init__(self):
        pass
        
    async def validate_office_presence(self, state: CommuteState) -> CommuteState:
        """
        Validate office presence blocks against business rules and generate viable options
        
        Business Rules:
        1. Minimum 4+ hours if going to office
        2. Professional arrival/departure patterns
        3. Core hours presence (10 AM - 4 PM)
        4. No "lunch and dash" patterns
        5. Buffer time for commute and transitions
        """
        
        logger.info("Validating office presence blocks against business rules")
        
        try:
            # Update progress
            state["progress_step"] = "Validating office presence rules"
            state["progress_percentage"] = 0.5
            
            meeting_classifications = state.get("meeting_classifications", [])
            target_date = state.get("target_date", "")
            
            # Check company policy requirements first
            policy_requirements = self._check_company_policy(target_date)
            
            # Generate possible office presence blocks (considering both meetings and policy)
            presence_blocks = self._generate_office_presence_options(meeting_classifications)
            
            # Apply company policy requirements
            presence_blocks = self._apply_policy_requirements(presence_blocks, policy_requirements)
            
            # Validate each block against business rules
            validated_blocks = []
            for block in presence_blocks:
                validation = self._validate_single_block(block, meeting_classifications)
                if validation["is_valid"] or validation["force_include"]:
                    validated_blocks.append(validation)
                    
            # Add full remote option
            remote_option = self._create_remote_option(meeting_classifications)
            validated_blocks.append(remote_option)
            
            # Rank blocks by compliance score
            validated_blocks.sort(key=lambda x: x["compliance_score"], reverse=True)
            
            # Update state
            state["office_presence_blocks"] = validated_blocks
            state["progress_percentage"] = 0.6
            
            logger.info(f"Generated {len(validated_blocks)} validated presence options")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in office presence validation: {e}")
            state["error_message"] = f"Office presence validation failed: {str(e)}"
            return state
            
    def _generate_office_presence_options(self, classifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate possible office presence blocks based on meetings"""
        
        office_meetings = [c for c in classifications if c["requires_office"]]
        
        if not office_meetings:
            return []  # No office meetings, only remote option will be generated
            
        options = []
        
        # Option 1: Full day office (8 AM - 6 PM)
        options.append({
            "type": "FULL_DAY_OFFICE",
            "arrival_hour": 8.0,
            "departure_hour": 18.0,
            "office_duration_hours": 10.0,
            "office_meetings": office_meetings,
            "remote_meetings": [c for c in classifications if not c["requires_office"]],
            "business_rule_compliance": {},
            "compliance_score": 80,
            "is_valid": True,
            "force_include": False,
            "warnings": []
        })
        
        # Option 2: Strategic morning (early arrival for morning meetings)
        morning_meetings = [m for m in office_meetings 
                          if datetime.fromisoformat(m["start_time"].replace('Z', '+00:00')).hour < 12]
        if morning_meetings:
            earliest_meeting_hour = min(
                datetime.fromisoformat(m["start_time"].replace('Z', '+00:00')).hour - 0.5  # 30 min buffer
                for m in morning_meetings
            )
            departure_hour = max(13.0, earliest_meeting_hour + self.MINIMUM_OFFICE_HOURS)
            options.append({
                "type": "STRATEGIC_MORNING",
                "arrival_hour": max(7.0, earliest_meeting_hour),
                "departure_hour": departure_hour,
                "office_duration_hours": departure_hour - max(7.0, earliest_meeting_hour),
                "office_meetings": morning_meetings,
                "remote_meetings": [c for c in classifications if not c["requires_office"] or c not in morning_meetings],
                "business_rule_compliance": {},
                "compliance_score": 75,
                "is_valid": True,
                "force_include": False,
                "warnings": []
            })
            
        # Option 3: Strategic afternoon (for afternoon meetings)
        afternoon_meetings = [m for m in office_meetings 
                            if datetime.fromisoformat(m["start_time"].replace('Z', '+00:00')).hour >= 12]
        if afternoon_meetings:
            latest_meeting_hour = max(
                datetime.fromisoformat(m["end_time"].replace('Z', '+00:00')).hour + 
                datetime.fromisoformat(m["end_time"].replace('Z', '+00:00')).minute / 60 + 0.5  # 30 min buffer
                for m in afternoon_meetings
            )
            arrival_hour = min(12.0, latest_meeting_hour - self.MINIMUM_OFFICE_HOURS)
            options.append({
                "type": "STRATEGIC_AFTERNOON", 
                "arrival_hour": arrival_hour,
                "departure_hour": latest_meeting_hour,
                "office_duration_hours": latest_meeting_hour - arrival_hour,
                "office_meetings": afternoon_meetings,
                "remote_meetings": [c for c in classifications if not c["requires_office"] or c not in afternoon_meetings],
                "business_rule_compliance": {},
                "compliance_score": 75,
                "is_valid": True,
                "force_include": False,
                "warnings": []
            })
            
        # Option 4: Core hours presence (10 AM - 4 PM minimum)
        core_meetings = [m for m in office_meetings 
                        if (datetime.fromisoformat(m["start_time"].replace('Z', '+00:00')).hour >= self.CORE_HOURS_START and
                            datetime.fromisoformat(m["end_time"].replace('Z', '+00:00')).hour <= self.CORE_HOURS_END)]
        if core_meetings:
            options.append({
                "type": "CORE_HOURS_PRESENCE",
                "arrival_hour": 9.5,  # 9:30 AM
                "departure_hour": 16.5,  # 4:30 PM
                "office_meetings": core_meetings,
                "remote_meetings": [c for c in classifications if not c["requires_office"] or c not in core_meetings]
            })
            
        return options
        
    def _validate_single_block(self, block: Dict[str, Any], all_classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a single office presence block against business rules"""
        
        arrival_hour = block["arrival_hour"]
        departure_hour = block["departure_hour"] 
        office_duration = departure_hour - arrival_hour
        
        validation_results = {}
        compliance_score = 0
        is_valid = True
        warnings = []
        
        # Rule 1: Minimum 4+ hours
        if office_duration >= self.MINIMUM_OFFICE_HOURS:
            validation_results["minimum_stay"] = {
                "status": "PASS",
                "message": f"{office_duration:.1f}h meets minimum {self.MINIMUM_OFFICE_HOURS}h requirement"
            }
            compliance_score += 25
        else:
            validation_results["minimum_stay"] = {
                "status": "FAIL", 
                "message": f"{office_duration:.1f}h below minimum {self.MINIMUM_OFFICE_HOURS}h requirement"
            }
            is_valid = False
            
        # Rule 2: Arrival pattern analysis
        if arrival_hour <= 8.5:  # Before 8:30 AM
            validation_results["arrival_pattern"] = {
                "status": "PASS",
                "message": f"Early arrival ({self._hour_to_time(arrival_hour)}) shows dedication"
            }
            compliance_score += 20
        elif arrival_hour <= self.PROFESSIONAL_ARRIVAL_BEFORE:  # Before 10 AM
            validation_results["arrival_pattern"] = {
                "status": "PASS",
                "message": f"Professional arrival time ({self._hour_to_time(arrival_hour)})"
            }
            compliance_score += 15
        elif arrival_hour >= 13:  # After 1 PM (afternoon arrival)
            validation_results["arrival_pattern"] = {
                "status": "PASS",
                "message": f"Strategic afternoon arrival ({self._hour_to_time(arrival_hour)}) acceptable"
            }
            compliance_score += 10
        else:
            validation_results["arrival_pattern"] = {
                "status": "WARNING",
                "message": f"Mid-morning arrival ({self._hour_to_time(arrival_hour)}) less optimal"
            }
            warnings.append("Mid-morning arrival may appear less dedicated")
            compliance_score += 5
            
        # Rule 3: Core hours presence (10 AM - 4 PM)
        core_overlap_start = max(arrival_hour, self.CORE_HOURS_START)
        core_overlap_end = min(departure_hour, self.CORE_HOURS_END)
        core_presence_hours = max(0, core_overlap_end - core_overlap_start)
        
        if core_presence_hours >= 4:  # Present for most/all core hours
            validation_results["core_hours_presence"] = {
                "status": "PASS",
                "message": f"Present during core collaboration hours ({core_presence_hours:.1f}h)"
            }
            compliance_score += 20
        elif core_presence_hours >= 2:  # Present for some core hours
            validation_results["core_hours_presence"] = {
                "status": "WARNING", 
                "message": f"Limited core hours presence ({core_presence_hours:.1f}h)"
            }
            compliance_score += 10
        else:
            validation_results["core_hours_presence"] = {
                "status": "FAIL",
                "message": "Minimal core hours presence may impact collaboration"
            }
            warnings.append("Limited availability during core collaboration hours")
            
        # Rule 4: Departure pattern analysis
        if departure_hour >= 17.5:  # After 5:30 PM
            validation_results["departure_pattern"] = {
                "status": "PASS",
                "message": f"Extended presence until {self._hour_to_time(departure_hour)}"
            }
            compliance_score += 15
        elif departure_hour >= self.PROFESSIONAL_DEPARTURE_AFTER:  # After 4 PM
            validation_results["departure_pattern"] = {
                "status": "PASS", 
                "message": f"Professional departure time ({self._hour_to_time(departure_hour)})"
            }
            compliance_score += 10
        else:
            validation_results["departure_pattern"] = {
                "status": "WARNING",
                "message": f"Early departure ({self._hour_to_time(departure_hour)}) may appear uncommitted"
            }
            compliance_score += 5
            
        # Rule 5: Lunch and dash detection
        if 11 <= arrival_hour <= 13 and 13 <= departure_hour <= 15 and office_duration <= self.LUNCH_DASH_THRESHOLD:
            validation_results["lunch_pattern"] = {
                "status": "FAIL",
                "message": "Pattern resembles 'lunch and dash' - appears unprofessional"
            }
            is_valid = False
        else:
            validation_results["lunch_pattern"] = {
                "status": "PASS",
                "message": "No lunch-and-dash pattern detected"
            }
            compliance_score += 10
            
        # Check if critical office meetings are covered
        office_meetings = block["office_meetings"]
        uncovered_critical_meetings = []
        
        for meeting in office_meetings:
            meeting_start_hour = datetime.fromisoformat(meeting["start_time"].replace('Z', '+00:00')).hour + \
                               datetime.fromisoformat(meeting["start_time"].replace('Z', '+00:00')).minute / 60
            meeting_end_hour = datetime.fromisoformat(meeting["end_time"].replace('Z', '+00:00')).hour + \
                             datetime.fromisoformat(meeting["end_time"].replace('Z', '+00:00')).minute / 60
                             
            if not (arrival_hour <= meeting_start_hour - 0.5 and departure_hour >= meeting_end_hour + 0.5):
                if meeting["confidence"] == "high":
                    uncovered_critical_meetings.append(meeting["summary"])
                    
        force_include = len(office_meetings) > 0 and len(uncovered_critical_meetings) == 0
        
        return {
            "type": block["type"],
            "arrival_hour": arrival_hour,
            "departure_hour": departure_hour,
            "office_duration_hours": office_duration,
            "office_meetings": office_meetings,
            "remote_meetings": block["remote_meetings"],
            "business_rule_compliance": validation_results,
            "compliance_score": compliance_score,
            "is_valid": is_valid,
            "force_include": force_include,
            "warnings": warnings,
            "uncovered_critical_meetings": uncovered_critical_meetings
        }
        
    def _create_remote_option(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create full remote work option"""
        
        # Check if any meetings absolutely require office presence
        critical_office_meetings = [c for c in classifications 
                                  if c.get("attendance_mode") == "MUST_BE_IN_PERSON" and (c.get("ai_confidence", 0) > 0.8 or c.get("confidence", "") == "high")]
        
        if critical_office_meetings:
            compliance_score = 0  # Low score if missing critical office meetings
            validation_status = "WARNING"
            message = f"Missing {len(critical_office_meetings)} critical office meetings"
        else:
            compliance_score = 85  # High base score for flexibility
            validation_status = "PASS"
            message = "All meetings can be handled remotely"
            
        return {
            "type": "FULL_REMOTE_RECOMMENDED",
            "arrival_hour": None,
            "departure_hour": None, 
            "office_duration_hours": 0,
            "office_meetings": [],
            "remote_meetings": classifications,
            "business_rule_compliance": {
                "flexible_work": {
                    "status": validation_status,
                    "message": message
                },
                "no_commute": {
                    "status": "PASS",
                    "message": "Zero commute time maximizes productivity"
                },
                "work_life_balance": {
                    "status": "PASS", 
                    "message": "Optimal work-life balance"
                }
            },
            "compliance_score": compliance_score,
            "is_valid": True,
            "force_include": True,
            "warnings": [message] if critical_office_meetings else [],
            "uncovered_critical_meetings": [m["summary"] for m in critical_office_meetings]
        }
        
    def _hour_to_time(self, hour: float) -> str:
        """Convert decimal hour to time string (e.g., 8.5 -> '8:30 AM')"""
        h = int(hour)
        m = int((hour - h) * 60)
        period = "AM" if h < 12 else "PM"
        display_hour = h if h <= 12 else h - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{m:02d} {period}"
    
    def _check_company_policy(self, target_date: str) -> Dict[str, Any]:
        """Check if company policy requires office presence on target date"""
        
        try:
            # Parse target date to get day of week
            if target_date.endswith('Z'):
                date_dt = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            else:
                date_dt = datetime.fromisoformat(target_date)
            
            day_name = date_dt.strftime('%A')  # Monday, Tuesday, etc.
            
            policy_requirements = {
                "requires_office_presence": False,
                "policy_reason": None,
                "flexibility_allowed": True,
                "minimum_hours_required": self.MINIMUM_OFFICE_HOURS
            }
            
            # Check mandatory office days
            if day_name in self.COMPANY_POLICIES["mandatory_office_days"]:
                policy_requirements.update({
                    "requires_office_presence": True,
                    "policy_reason": f"Company policy requires office presence on {day_name}s",
                    "flexibility_allowed": False,
                    "minimum_hours_required": 8.0  # Full day required
                })
                
            # Check team collaboration days
            if day_name in self.COMPANY_POLICIES["team_collaboration_days"]:
                collaboration_reason = self.COMPANY_POLICIES["team_collaboration_days"][day_name]
                policy_requirements.update({
                    "requires_office_presence": True,
                    "policy_reason": f"Team collaboration day: {collaboration_reason}",
                    "flexibility_allowed": True,  # Can leave early if no meetings
                    "minimum_hours_required": 6.0  # Partial day OK
                })
            
            logger.info(f"Policy check for {day_name}: {policy_requirements}")
            return policy_requirements
            
        except Exception as e:
            logger.error(f"Error checking company policy: {e}")
            return {
                "requires_office_presence": False,
                "policy_reason": None,
                "flexibility_allowed": True,
                "minimum_hours_required": self.MINIMUM_OFFICE_HOURS
            }
    
    def _apply_policy_requirements(self, presence_blocks: List[Dict[str, Any]], policy_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply company policy requirements to presence blocks"""
        
        if not policy_requirements["requires_office_presence"]:
            return presence_blocks  # No policy constraints
        
        # If policy requires office presence, ensure at least one office option exists
        has_office_option = any(block["type"] != "FULL_REMOTE_RECOMMENDED" for block in presence_blocks)
        
        if not has_office_option:
            # Create a policy-compliant office block
            policy_block = {
                "type": "POLICY_REQUIRED_OFFICE_PRESENCE",
                "arrival_hour": 9.0,
                "departure_hour": 17.0,
                "office_duration_hours": policy_requirements["minimum_hours_required"],
                "office_meetings": [],
                "remote_meetings": [],
                "business_rule_compliance": {
                    "company_policy": {
                        "status": "REQUIRED",
                        "message": policy_requirements["policy_reason"]
                    }
                },
                "compliance_score": 95,  # High score for policy compliance
                "is_valid": True,
                "force_include": True,
                "warnings": [],
                "policy_driven": True
            }
            presence_blocks.append(policy_block)
        
        # Adjust compliance scores based on policy requirements
        for block in presence_blocks:
            if block["type"] == "FULL_REMOTE_RECOMMENDED" and policy_requirements["requires_office_presence"]:
                # Lower score for remote work when policy requires office
                block["compliance_score"] = max(block["compliance_score"] - 30, 10)
                block["warnings"].append(f"Policy violation: {policy_requirements['policy_reason']}")
            elif block["type"] != "FULL_REMOTE_RECOMMENDED" and policy_requirements["requires_office_presence"]:
                # Boost score for office presence when required by policy
                block["compliance_score"] = min(block["compliance_score"] + 15, 100)
        
        return presence_blocks