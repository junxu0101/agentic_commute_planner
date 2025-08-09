"""
Option Presenter Agent - Formats and ranks recommendations according to ARCHITECTURE.md
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

from models.workflow_state import CommuteState

logger = logging.getLogger(__name__)


class OptionPresenterAgent:
    """Agent responsible for formatting and ranking final recommendations"""
    
    def __init__(self):
        pass
        
    async def present_recommendations(self, state: CommuteState) -> CommuteState:
        """
        Format and rank final commute recommendations following ARCHITECTURE.md format
        
        Output format matches exact JSON structure from ARCHITECTURE.md:
        - option_rank, type, commute timing
        - business_rule_compliance with PASS/FAIL/WARNING
        - perception_analysis with professional impact
        - detailed reasoning and trade-offs
        """
        
        logger.info("Formatting and ranking final recommendations")
        
        try:
            # Update progress
            state["progress_step"] = "Finalizing recommendations"
            state["progress_percentage"] = 0.9
            
            commute_options = state.get("commute_options", [])
            
            # Rank options by overall score
            ranked_options = self._rank_options(commute_options)
            
            # Format each option according to ARCHITECTURE.md specification
            formatted_recommendations = []
            for rank, option in enumerate(ranked_options, 1):
                formatted_rec = self._format_recommendation(option, rank)
                formatted_recommendations.append(formatted_rec)
                
            # Update state
            state["recommendations"] = formatted_recommendations
            state["progress_percentage"] = 1.0
            state["progress_step"] = "Recommendations complete"
            
            logger.info(f"Generated {len(formatted_recommendations)} ranked recommendations")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in option presentation: {e}")
            state["error_message"] = f"Option presentation failed: {str(e)}"
            return state
            
    def _rank_options(self, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank options by overall score considering multiple factors"""
        
        scored_options = []
        
        for option in options:
            total_score = 0
            
            # Base compliance score (0-100)
            compliance_score = option.get("compliance_score", 0)
            total_score += compliance_score
            
            # Efficiency bonus (0-20 points)
            efficiency = option.get("efficiency_metrics", {})
            if efficiency.get("day_efficiency", 0) > 0.8:
                total_score += 20
            elif efficiency.get("day_efficiency", 0) > 0.6:
                total_score += 10
                
            # Remote work bonus for flexibility (0-15 points)
            if option["option_type"] == "FULL_REMOTE_RECOMMENDED":
                if not option.get("warnings", []):
                    total_score += 15
                    
            # Meeting coverage bonus (0-15 points)
            office_meetings = option.get("office_meetings", [])
            high_confidence_meetings = [m for m in office_meetings if m.get("confidence") == "high"]
            if office_meetings and len(high_confidence_meetings) == len(office_meetings):
                total_score += 15
                
            # Penalty for warnings (-5 points per warning)
            warnings = option.get("warnings", [])
            total_score -= len(warnings) * 5
            
            # Penalty for high commute ratio (-10 points if ratio > 0.5)
            commute_ratio = efficiency.get("commute_to_office_ratio", 0)
            if commute_ratio > 0.5:
                total_score -= 10
                
            scored_options.append({
                **option,
                "total_score": max(0, total_score)  # Don't allow negative scores
            })
            
        # Sort by total score (highest first)
        return sorted(scored_options, key=lambda x: x["total_score"], reverse=True)
        
    def _format_recommendation(self, option: Dict[str, Any], rank: int) -> Dict[str, Any]:
        """Format single recommendation according to ARCHITECTURE.md JSON format"""
        
        # Extract meeting IDs
        office_meeting_ids = [m["meeting_id"] for m in option.get("office_meetings", [])]
        remote_meeting_ids = [m["meeting_id"] for m in option.get("remote_meetings", [])]
        
        # Format business rule compliance
        compliance = option.get("business_rule_compliance", {})
        formatted_compliance = {}
        
        for rule, result in compliance.items():
            status = result.get("status", "UNKNOWN")
            message = result.get("message", "")
            
            if status == "PASS":
                formatted_compliance[rule] = f"✅ PASS ({message})"
            elif status == "FAIL":
                formatted_compliance[rule] = f"❌ FAIL ({message})"
            elif status == "WARNING":
                formatted_compliance[rule] = f"⚠️ WARNING ({message})"
            else:
                formatted_compliance[rule] = f"❓ {status} ({message})"
                
        # Generate perception analysis
        perception = self._analyze_professional_perception(option)
        
        # Generate detailed reasoning
        reasoning = self._generate_reasoning(option, rank)
        
        # Generate trade-offs analysis
        trade_offs = self._analyze_trade_offs(option)
        
        return {
            "option_rank": rank,
            "type": option["option_type"],
            "commute_start": option.get("commute_start"),
            "office_arrival": option.get("office_arrival"),
            "office_departure": option.get("office_departure"),
            "commute_end": option.get("commute_end"),
            "office_duration": option.get("office_duration"),
            "office_meetings": office_meeting_ids,
            "remote_meetings": remote_meeting_ids,
            "business_rule_compliance": formatted_compliance,
            "perception_analysis": perception,
            "reasoning": reasoning,
            "trade_offs": trade_offs
        }
        
    def _analyze_professional_perception(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze professional impact and team visibility"""
        
        option_type = option["option_type"]
        compliance_score = option.get("compliance_score", 0)
        office_meetings = option.get("office_meetings", [])
        efficiency = option.get("efficiency_metrics", {})
        
        # Determine professional impact
        if option_type == "FULL_REMOTE_RECOMMENDED":
            if not option.get("warnings", []):
                impact = "NEUTRAL_TO_POSITIVE"
                reasoning = "Efficient remote work with no critical office meetings missed"
                visibility = "MEDIUM"
            else:
                impact = "NEUTRAL"
                reasoning = "Remote work with some trade-offs in meeting attendance"
                visibility = "LOW"
                
        elif compliance_score >= 80:
            impact = "VERY_POSITIVE"
            reasoning = "Strong office presence demonstrating commitment and professionalism"
            visibility = "HIGH"
            
        elif compliance_score >= 60:
            impact = "NEUTRAL_TO_POSITIVE"
            reasoning = "Good balance of office presence and meeting requirements"
            visibility = "MEDIUM"
            
        else:
            impact = "NEUTRAL"
            reasoning = "Office presence meets basic requirements but may have perception risks"
            visibility = "LOW"
            
        # Enhance reasoning based on specific factors
        if option_type == "FULL_DAY_OFFICE":
            enhanced_reasoning = "Extended office presence maximizes face-time and collaboration opportunities"
        elif option_type == "STRATEGIC_AFTERNOON":
            enhanced_reasoning = "Strategic afternoon presence for key meetings while maintaining flexibility"
        elif option_type == "STRATEGIC_MORNING":
            enhanced_reasoning = "Early arrival demonstrates dedication and ensures availability for morning priorities"
        elif option_type == "CORE_HOURS_PRESENCE":
            enhanced_reasoning = "Core hours presence ensures availability during peak collaboration time"
        else:
            enhanced_reasoning = reasoning
            
        return {
            "professional_impact": impact,
            "reasoning": enhanced_reasoning,
            "team_visibility": visibility
        }
        
    def _generate_reasoning(self, option: Dict[str, Any], rank: int) -> str:
        """Generate detailed reasoning for recommendation ranking"""
        
        option_type = option["option_type"]
        office_meetings = option.get("office_meetings", [])
        remote_meetings = option.get("remote_meetings", [])
        efficiency = option.get("efficiency_metrics", {})
        warnings = option.get("warnings", [])
        
        reasoning_parts = []
        
        # Rank-based opening
        if rank == 1:
            reasoning_parts.append("🥇 RECOMMENDED OPTION:")
        elif rank == 2:
            reasoning_parts.append("🥈 STRONG ALTERNATIVE:")
        else:
            reasoning_parts.append(f"Option #{rank}:")
            
        # Type-specific reasoning
        if option_type == "FULL_REMOTE_RECOMMENDED":
            reasoning_parts.append(
                f"Full remote work maximizes flexibility and productivity. "
                f"All {len(remote_meetings)} meetings can be handled effectively remotely. "
                f"Zero commute time saves approximately {efficiency.get('total_commute_minutes', 0)} minutes, "
                f"providing more time for deep work and better work-life balance."
            )
            
        elif option_type == "FULL_DAY_OFFICE":
            reasoning_parts.append(
                f"Full day office presence provides maximum visibility and collaboration opportunities. "
                f"Covers all {len(office_meetings)} office-required meetings with strong professional presence. "
                f"Office duration of {option.get('office_duration')} demonstrates commitment and availability."
            )
            
        elif option_type == "STRATEGIC_AFTERNOON":
            reasoning_parts.append(
                f"Strategic afternoon presence optimally balances meeting requirements with flexibility. "
                f"Covers {len(office_meetings)} key office meetings while allowing remote work for "
                f"{len(remote_meetings)} other commitments. Efficient use of office time."
            )
            
        else:
            reasoning_parts.append(
                f"This option covers {len(office_meetings)} office meetings while maintaining "
                f"flexibility for {len(remote_meetings)} remote interactions."
            )
            
        # Efficiency commentary
        if efficiency:
            day_eff = efficiency.get("day_efficiency", 0)
            commute_ratio = efficiency.get("commute_to_office_ratio", 0)
            
            if day_eff > 0.8:
                reasoning_parts.append("Excellent time efficiency with minimal commute overhead.")
            elif commute_ratio > 0.4:
                reasoning_parts.append(
                    f"Moderate efficiency with {int(commute_ratio * 100)}% of office time spent commuting."
                )
                
        # Address warnings if present
        if warnings:
            reasoning_parts.append(f"Note: {len(warnings)} considerations including {warnings[0].lower()}.")
            
        return " ".join(reasoning_parts)
        
    def _analyze_trade_offs(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trade-offs for each recommendation"""
        
        option_type = option["option_type"]
        efficiency = option.get("efficiency_metrics", {})
        office_meetings = option.get("office_meetings", [])
        remote_meetings = option.get("remote_meetings", [])
        
        trade_offs = {}
        
        if option_type == "FULL_REMOTE_RECOMMENDED":
            trade_offs.update({
                "pros": [
                    "Zero commute time and costs",
                    "Maximum flexibility and comfort",
                    "Optimal work-life balance",
                    "Environmental benefits (no travel)"
                ],
                "cons": [
                    "Limited face-to-face interaction",
                    "Potential visibility concerns with management",
                    "May miss spontaneous collaboration opportunities"
                ],
                "cost_impact": "Saves ~$40-60/day in commute costs"
            })
            
        else:
            # Office presence options
            commute_time = efficiency.get("total_commute_minutes", 0)
            office_time = efficiency.get("office_minutes", 0)
            
            trade_offs.update({
                "pros": [
                    f"Direct engagement in {len(office_meetings)} key meetings",
                    "High visibility and professional presence",
                    "Spontaneous collaboration opportunities",
                    "Access to office resources and environment"
                ],
                "cons": [
                    f"{commute_time} minutes total commute time",
                    f"Commute costs (parking, gas, time value)",
                    f"Less flexibility for personal schedule"
                ],
                "cost_impact": f"~$40-60/day in commute expenses",
                "time_investment": f"{commute_time} min commute for {office_time} min office time"
            })
            
            if option_type == "FULL_DAY_OFFICE":
                trade_offs["pros"].append("Maximum in-person collaboration time")
                trade_offs["cons"].append("Longest day with commute overhead")
                
            elif option_type in ["STRATEGIC_AFTERNOON", "STRATEGIC_MORNING"]:
                trade_offs["pros"].append("Optimal balance of presence and flexibility")
                trade_offs["cons"].append("Split attention between office and remote work")
                
        # Add efficiency metrics
        if efficiency:
            trade_offs["efficiency_score"] = f"{efficiency.get('day_efficiency', 0):.1%}"
            
        return trade_offs