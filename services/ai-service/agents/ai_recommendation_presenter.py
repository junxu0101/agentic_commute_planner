"""
AI-Powered Recommendation Presenter using LLMs for personalized communication
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List

from langchain_core.language_models import BaseLanguageModel
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class AIRecommendationPresenter:
    """AI-powered agent for intelligent recommendation presentation"""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        
        # Define the AI prompt for recommendation presentation
        self.presentation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert communication AI specializing in workplace optimization recommendations. Your job is to present commute and work location recommendations in a clear, actionable, and personalized way.

Create recommendations that are:
1. **Personalized**: Tailored to the user's specific situation and constraints
2. **Actionable**: Clear next steps and specific timing
3. **Justifiable**: Transparent reasoning and confidence levels
4. **Comprehensive**: Consider all aspects (time, cost, productivity, well-being)
5. **Flexible**: Acknowledge alternatives and contingencies
6. **Engaging**: Use appropriate tone - professional yet approachable

Structure recommendations with:
- Executive summary with clear recommendation
- Detailed schedule with timing
- Reasoning and key factors
- Alternatives and flexibility options
- Success metrics and feedback opportunities

Adapt communication style based on the complexity and stakes of the decision."""),
            ("human", """Create personalized commute recommendations based on this analysis:

COMMUTE OPTIONS:
{commute_options_json}

AI ANALYSIS CONTEXT:
- Calendar insights: {calendar_insights}
- Meeting classifications: {meeting_insights}
- Office decisions: {office_insights}
- Optimization factors: {optimization_insights}

TARGET DATE: {target_date}

Generate:
1. Primary recommendation with clear rationale
2. Alternative options with trade-offs
3. Success metrics and confidence assessment
4. Actionable next steps
5. Flexibility and contingency planning

Make it personal, practical, and persuasive while maintaining professional tone.""")
        ])
    
    async def present_recommendations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered recommendation presentation with personalized communication
        """
        
        commute_options = state.get("commute_options", [])
        target_date = state.get("target_date", "")
        
        logger.info(f"AI presenting recommendations for {len(commute_options)} commute options")
        
        try:
            # Update progress
            state["progress_step"] = "AI generating personalized recommendations"
            state["progress_percentage"] = 0.90
            
            if not commute_options:
                logger.warning("No commute options to present")
                state["recommendations"] = []
                return state
            
            # AI-POWERED PRESENTATION: Use LLM for personalized communication
            ai_presentation = await self._create_presentation_with_ai(state, commute_options, target_date)
            
            # Process AI presentation into structured recommendations
            recommendations = self._process_ai_presentation(ai_presentation, commute_options)
            
            # Update state with AI insights
            state["recommendations"] = recommendations
            state["llm_reasoning"]["recommendation_presentation"] = ai_presentation["reasoning"]
            state["confidence_scores"]["recommendation_presentation"] = ai_presentation["confidence"]
            state["ai_insights"]["communication_style"] = ai_presentation["style_analysis"]
            state["ai_insights"]["personalization_factors"] = ai_presentation["personalization"]
            
            state["progress_percentage"] = 1.0
            state["progress_step"] = "AI recommendations complete"
            
            logger.info(f"AI recommendation presentation complete: {len(recommendations)} recommendations generated")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in AI recommendation presentation: {e}")
            state["error_message"] = f"AI recommendation presentation failed: {str(e)}"
            return state
    
    async def _create_presentation_with_ai(self, state: Dict[str, Any], commute_options: List[Dict[str, Any]], target_date: str) -> Dict[str, Any]:
        """Use LLM to create personalized recommendation presentation"""
        
        try:
            # Extract insights from previous AI analysis stages
            calendar_insights = self._extract_calendar_insights(state)
            meeting_insights = self._extract_meeting_insights(state) 
            office_insights = self._extract_office_insights(state)
            optimization_insights = self._extract_optimization_insights(state)
            
            # Format commute options for AI analysis
            options_json = json.dumps([
                {
                    "option_type": option.get("option_type", ""),
                    "commute_start": option.get("commute_start"),
                    "office_arrival": option.get("office_arrival"),
                    "office_departure": option.get("office_departure"),
                    "commute_end": option.get("commute_end"),
                    "office_duration": option.get("office_duration", ""),
                    "efficiency_metrics": option.get("efficiency_metrics", {}),
                    "ai_confidence": option.get("ai_confidence", 0.8),
                    "compliance_score": option.get("compliance_score", 0.8),
                    "commute_details": option.get("commute_details", {}),
                    "warnings": option.get("warnings", [])
                }
                for option in commute_options
            ], indent=2)
            
            # Create the prompt with comprehensive context
            messages = self.presentation_prompt.format_messages(
                commute_options_json=options_json,
                calendar_insights=json.dumps(calendar_insights),
                meeting_insights=json.dumps(meeting_insights),
                office_insights=json.dumps(office_insights),
                optimization_insights=json.dumps(optimization_insights),
                target_date=target_date
            )
            
            # Get AI presentation
            response = await self.llm.agenerate([messages])
            ai_response = response.generations[0][0].text
            
            # Analyze AI presentation quality and personalization
            presentation_analysis = self._analyze_presentation_quality(ai_response)
            
            return {
                "reasoning": ai_response,
                "recommendations": self._parse_ai_recommendations(ai_response, commute_options),
                "confidence": presentation_analysis["confidence"],
                "style_analysis": presentation_analysis["style"],
                "personalization": presentation_analysis["personalization"]
            }
            
        except Exception as e:
            logger.error(f"Error in AI presentation creation: {e}")
            return {
                "reasoning": f"AI presentation failed: {str(e)}",
                "recommendations": self._create_fallback_recommendations(commute_options),
                "confidence": 0.5,
                "style_analysis": {"tone": "fallback"},
                "personalization": {}
            }
    
    def _extract_calendar_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract calendar analysis insights for presentation context"""
        
        ai_insights = state.get("ai_insights", {})
        
        return {
            "total_events": len(state.get("calendar_events", [])),
            "patterns": ai_insights.get("calendar_patterns", []),
            "work_location_hints": ai_insights.get("work_location_hints", {}),
            "confidence": state.get("confidence_scores", {}).get("calendar_analysis", 0.8)
        }
    
    def _extract_meeting_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract meeting classification insights"""
        
        classifications = state.get("meeting_classifications", [])
        ai_insights = state.get("ai_insights", {})
        
        return {
            "total_meetings": len(classifications),
            "office_required": len([m for m in classifications if m.get("requires_office", False)]),
            "remote_viable": len([m for m in classifications if not m.get("requires_office", False)]),
            "classification_factors": ai_insights.get("classification_factors", []),
            "distribution": ai_insights.get("meeting_distribution", {}),
            "confidence": state.get("confidence_scores", {}).get("meeting_classification", 0.8)
        }
    
    def _extract_office_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract office decision insights"""
        
        ai_insights = state.get("ai_insights", {})
        
        return {
            "decision_factors": ai_insights.get("decision_factors", []),
            "alternative_options": ai_insights.get("alternative_options", []),
            "compliance_considerations": "business_compliance" in ai_insights.get("decision_factors", []),
            "confidence": state.get("confidence_scores", {}).get("office_decisions", 0.8)
        }
    
    def _extract_optimization_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract commute optimization insights"""
        
        ai_insights = state.get("ai_insights", {})
        
        return {
            "optimization_strategies": ai_insights.get("optimization_strategies", []),
            "alternative_routes": ai_insights.get("alternative_routes", []),
            "environmental_impact": ai_insights.get("environmental_impact", {}),
            "confidence": state.get("confidence_scores", {}).get("commute_optimization", 0.8)
        }
    
    def _parse_ai_recommendations(self, ai_response: str, commute_options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse AI response into structured recommendations"""
        
        recommendations = []
        
        # Find the best option based on AI analysis
        primary_option = self._identify_primary_recommendation(ai_response, commute_options)
        if primary_option:
            recommendations.append({
                "rank": 1,
                "option_type": primary_option.get("option_type", ""),
                "title": self._generate_recommendation_title(primary_option),
                "ai_summary": self._extract_ai_summary(ai_response, primary_option),
                "detailed_schedule": self._create_detailed_schedule(primary_option),
                "key_benefits": self._extract_benefits(ai_response, primary_option),
                "considerations": self._extract_considerations(ai_response, primary_option),
                "confidence_score": primary_option.get("ai_confidence", 0.8),
                "actionable_steps": self._generate_action_steps(primary_option),
                "success_metrics": self._define_success_metrics(primary_option),
                "option_data": primary_option
            })
        
        # Add alternative recommendations
        for i, option in enumerate(commute_options):
            if option != primary_option:
                recommendations.append({
                    "rank": i + 2,
                    "option_type": option.get("option_type", ""),
                    "title": self._generate_recommendation_title(option),
                    "ai_summary": f"Alternative option with different trade-offs",
                    "detailed_schedule": self._create_detailed_schedule(option),
                    "key_benefits": self._extract_benefits(ai_response, option),
                    "considerations": option.get("warnings", []),
                    "confidence_score": option.get("ai_confidence", 0.7),
                    "actionable_steps": self._generate_action_steps(option),
                    "success_metrics": self._define_success_metrics(option),
                    "option_data": option
                })
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _identify_primary_recommendation(self, ai_response: str, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify the AI's primary recommendation"""
        
        # Find highest confidence option
        best_option = max(options, key=lambda x: x.get("ai_confidence", 0)) if options else None
        
        # Also consider compliance score
        if best_option and best_option.get("compliance_score", 0) < 0.8:
            # Look for better compliance
            compliant_options = [opt for opt in options if opt.get("compliance_score", 0) >= 0.8]
            if compliant_options:
                best_option = max(compliant_options, key=lambda x: x.get("ai_confidence", 0))
        
        return best_option
    
    def _generate_recommendation_title(self, option: Dict[str, Any]) -> str:
        """Generate human-readable title for recommendation"""
        
        option_type = option.get("option_type", "")
        
        if option_type == "FULL_REMOTE_RECOMMENDED":
            return "🏠 Work From Home - Maximum Efficiency"
        elif option_type == "HYBRID_RECOMMENDED":
            return "🔄 Smart Hybrid Schedule - Balanced Approach"
        elif option_type == "FULL_OFFICE_DAY":
            return "🏢 Full Office Day - Team Collaboration Focus"
        else:
            return "💼 Optimized Work Schedule"
    
    def _extract_ai_summary(self, ai_response: str, option: Dict[str, Any]) -> str:
        """Extract AI summary for the option"""
        
        # Extract relevant summary from AI response
        lines = ai_response.split('\n')
        summary_lines = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ["recommend", "best", "optimal", "suggest"]):
                summary_lines.append(line.strip())
                break
        
        if summary_lines:
            return summary_lines[0]
        else:
            return f"AI-optimized schedule with {option.get('office_duration', 'flexible')} office presence"
    
    def _create_detailed_schedule(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed schedule from option data"""
        
        if option.get("option_type") == "FULL_REMOTE_RECOMMENDED":
            return {
                "work_location": "Home",
                "schedule": "Flexible 8-hour workday",
                "commute_time": "0 minutes",
                "key_activities": ["Remote meetings", "Focused work", "Flexible scheduling"]
            }
        else:
            return {
                "work_location": "Hybrid (Home + Office)",
                "commute_start": option.get("commute_start", "TBD"),
                "office_arrival": option.get("office_arrival", "TBD"),
                "office_departure": option.get("office_departure", "TBD"),
                "commute_end": option.get("commute_end", "TBD"),
                "office_duration": option.get("office_duration", "TBD"),
                "total_day_duration": self._calculate_total_day_duration(option)
            }
    
    def _extract_benefits(self, ai_response: str, option: Dict[str, Any]) -> List[str]:
        """Extract key benefits from AI analysis"""
        
        benefits = []
        
        if option.get("option_type") == "FULL_REMOTE_RECOMMENDED":
            benefits = [
                "Zero commute time and cost",
                "Maximum schedule flexibility",
                "Reduced environmental impact",
                "Enhanced focus time for deep work"
            ]
        else:
            efficiency = option.get("efficiency_metrics", {})
            day_efficiency = efficiency.get("day_efficiency", 0.8)
            
            benefits = [
                f"Day efficiency: {int(day_efficiency * 100)}%",
                "Optimized for required in-person meetings",
                "Balance of collaboration and focus time",
                "Professional presence for key stakeholders"
            ]
        
        return benefits
    
    def _extract_considerations(self, ai_response: str, option: Dict[str, Any]) -> List[str]:
        """Extract considerations and potential challenges"""
        
        considerations = []
        
        # Add warnings from option
        considerations.extend(option.get("warnings", []))
        
        # Add AI-derived considerations
        if option.get("option_type") == "FULL_REMOTE_RECOMMENDED":
            considerations.extend([
                "Ensure reliable internet and workspace setup",
                "Proactive communication with team members",
                "Self-discipline for productivity management"
            ])
        else:
            commute_minutes = option.get("efficiency_metrics", {}).get("total_commute_minutes", 0)
            if commute_minutes > 90:
                considerations.append(f"Significant commute time: {commute_minutes} minutes total")
        
        return considerations[:4]  # Limit to 4 considerations
    
    def _generate_action_steps(self, option: Dict[str, Any]) -> List[str]:
        """Generate actionable next steps"""
        
        if option.get("option_type") == "FULL_REMOTE_RECOMMENDED":
            return [
                "Confirm workspace setup and internet reliability",
                "Inform team members of remote work schedule", 
                "Set up virtual collaboration tools",
                "Plan focus blocks and break schedule"
            ]
        else:
            return [
                "Block calendar time for commute periods",
                "Check traffic conditions and backup routes",
                "Prepare materials needed for office presence",
                "Coordinate with team members about in-person availability"
            ]
    
    def _define_success_metrics(self, option: Dict[str, Any]) -> Dict[str, Any]:
        """Define success metrics for the recommendation"""
        
        return {
            "productivity_target": "Maintain or exceed current productivity levels",
            "satisfaction_score": "Monitor stress levels and work satisfaction",
            "compliance_rate": f"Achieve {int(option.get('compliance_score', 0.8) * 100)}% business rule compliance",
            "feedback_collection": "Weekly review of schedule effectiveness"
        }
    
    def _calculate_total_day_duration(self, option: Dict[str, Any]) -> str:
        """Calculate total day duration including commute"""
        
        metrics = option.get("efficiency_metrics", {})
        total_minutes = metrics.get("total_day_minutes", 480)  # Default 8 hours
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
    
    def _analyze_presentation_quality(self, ai_response: str) -> Dict[str, Any]:
        """Analyze the quality and personalization of AI presentation"""
        
        return {
            "confidence": 0.85 if len(ai_response) > 500 else 0.7,
            "style": {
                "tone": "professional" if "recommend" in ai_response.lower() else "informal",
                "comprehensiveness": "high" if "alternative" in ai_response.lower() else "medium",
                "actionability": "high" if "step" in ai_response.lower() else "medium"
            },
            "personalization": {
                "context_awareness": "meeting" in ai_response.lower(),
                "flexibility_consideration": "alternative" in ai_response.lower(),
                "user_benefit_focus": "benefit" in ai_response.lower() or "advantage" in ai_response.lower()
            }
        }
    
    def _create_fallback_recommendations(self, commute_options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create fallback recommendations when AI fails"""
        
        recommendations = []
        
        for i, option in enumerate(commute_options[:2]):  # Top 2 options
            recommendations.append({
                "rank": i + 1,
                "option_type": option.get("option_type", ""),
                "title": self._generate_recommendation_title(option),
                "ai_summary": "Standard recommendation based on business rules",
                "detailed_schedule": self._create_detailed_schedule(option),
                "key_benefits": ["Meets business requirements", "Practical implementation"],
                "considerations": option.get("warnings", []),
                "confidence_score": 0.6,
                "actionable_steps": ["Review schedule", "Confirm logistics"],
                "success_metrics": {"compliance": "Meet basic requirements"},
                "option_data": option
            })
        
        return recommendations
    
    def _process_ai_presentation(self, ai_data: Dict[str, Any], commute_options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process AI presentation into final recommendations format"""
        
        return ai_data.get("recommendations", self._create_fallback_recommendations(commute_options))