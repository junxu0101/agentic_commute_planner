"""
LangGraph Multi-Agent Commute Planning Workflow
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from models.workflow_state import CommuteState
from config.llm_config import llm_config
from agents.ai_calendar_analyzer import AICalendarAnalyzer
from agents.ai_meeting_classifier import AIMeetingClassifier  
from agents.ai_office_decision_maker import AIOfficeDecisionMaker
from agents.ai_commute_optimizer import AICommuteOptimizer
from agents.ai_recommendation_presenter import AIRecommendationPresenter
from services.redis_service import RedisService
from services.backend_service import backend_service
from config.settings import get_settings

logger = logging.getLogger(__name__)


class AICommuteState(BaseModel):
    """Enhanced state model for AI-powered workflow"""
    
    # Core workflow data
    job_id: str
    user_id: str
    target_date: str
    user_timezone: str = "UTC"
    input_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Progress tracking
    progress_step: str = "Initializing AI workflow"
    progress_percentage: float = 0.0
    
    # Data through pipeline
    calendar_events: List[Dict[str, Any]] = Field(default_factory=list)
    meeting_classifications: List[Dict[str, Any]] = Field(default_factory=list)
    office_presence_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    commute_options: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # AI-specific metadata
    llm_reasoning: Dict[str, str] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    ai_insights: Dict[str, Any] = Field(default_factory=dict)
    
    # Error handling
    error_message: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class LangGraphCommuteWorkflow:
    """LangGraph-powered AI commute planning workflow"""
    
    def __init__(self, redis_service: RedisService, backend_service):
        self.redis_service = redis_service
        self.backend_service = backend_service
        self.settings = get_settings()
        
        # Initialize AI agents with LLMs
        self.calendar_analyzer = AICalendarAnalyzer(
            llm=llm_config.get_calendar_analyzer_llm(),
            backend_service=backend_service
        )
        
        self.meeting_classifier = AIMeetingClassifier(
            llm=llm_config.get_meeting_classifier_llm()
        )
        
        self.office_decision_maker = AIOfficeDecisionMaker(
            llm=llm_config.get_office_decision_llm()
        )
        
        self.commute_optimizer = AICommuteOptimizer(
            llm=llm_config.get_commute_optimizer_llm(),
            user_id=None  # Will be set per workflow
        )
        
        self.recommendation_presenter = AIRecommendationPresenter(
            llm=llm_config.get_recommendation_llm()
        )
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph state machine"""
        
        workflow = StateGraph(AICommuteState)
        
        # Add nodes (agents)
        workflow.add_node("calendar_analysis", self._calendar_analysis_node)
        workflow.add_node("meeting_classification", self._meeting_classification_node) 
        workflow.add_node("office_decision", self._office_decision_node)
        workflow.add_node("commute_optimization", self._commute_optimization_node)
        workflow.add_node("recommendation_presentation", self._recommendation_presentation_node)
        
        # Define the workflow edges
        workflow.set_entry_point("calendar_analysis")
        workflow.add_edge("calendar_analysis", "meeting_classification")
        workflow.add_edge("meeting_classification", "office_decision")
        workflow.add_edge("office_decision", "commute_optimization")
        workflow.add_edge("commute_optimization", "recommendation_presentation")
        workflow.add_edge("recommendation_presentation", END)
        
        return workflow.compile()
    
    async def execute(self, workflow_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the AI-powered workflow"""
        
        job_id = workflow_input["job_id"]
        user_id = workflow_input["user_id"]
        target_date = workflow_input["target_date"]
        
        logger.info(f"Starting AI commute workflow for job {job_id}")
        
        # Extract user timezone - job_worker already extracted it from context
        input_data = workflow_input.get("input_data", {})
        user_timezone = workflow_input.get("user_timezone")
        
        # Fail fast if timezone is missing - don't silently corrupt data with UTC fallback
        if not user_timezone or user_timezone == "UTC":
            error_msg = f"Missing or invalid user_timezone in workflow_input. Got: {user_timezone}. This is required for timezone-aware processing."
            logger.error(f"CRITICAL ERROR: {error_msg}")
            logger.error(f"workflow_input keys: {list(workflow_input.keys())}")
            raise ValueError(error_msg)
        
        # DEBUG: Log LangGraph workflow input
        logger.error(f"=== LANGGRAPH WORKFLOW INPUT DEBUG ===")
        logger.error(f"LANGGRAPH - Complete workflow_input: {workflow_input}")
        logger.error(f"LANGGRAPH - job_id: {job_id}")
        logger.error(f"LANGGRAPH - user_id: {user_id}")
        logger.error(f"LANGGRAPH - target_date: {target_date}")
        logger.error(f"LANGGRAPH - input_data: {input_data}")
        logger.error(f"LANGGRAPH - user_timezone: {user_timezone}")
        logger.error(f"=== LANGGRAPH WORKFLOW INPUT DEBUG END ===")
        
        # Initialize AI state
        initial_state = AICommuteState(
            job_id=job_id,
            user_id=user_id,
            target_date=target_date,
            user_timezone=user_timezone,
            input_data=input_data,
        )
        
        try:
            # Set user_id for commute optimizer
            self.commute_optimizer.user_id = user_id
            
            # Execute the LangGraph workflow
            final_state = await self.workflow.ainvoke(initial_state.dict())
            
            # Convert back to AICommuteState for final processing
            if isinstance(final_state, dict):
                result_state = AICommuteState(**final_state)
            else:
                # If final_state is already an AICommuteState object, use it directly
                result_state = final_state
            
            # Save AI recommendations to database
            await self.backend_service.save_commute_recommendations(
                job_id,
                result_state.recommendations
            )
            
            # Final progress update
            await self._publish_progress(result_state)
            
            # Return success result with AI insights
            result = self._create_ai_success_result(result_state)
            logger.info(f"AI workflow completed successfully for job {job_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"AI workflow error for job {job_id}: {e}")
            error_state = initial_state.copy()
            error_state.error_message = str(e)
            return self._create_error_result(error_state.dict())
    
    async def _calendar_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node for AI calendar analysis"""
        logger.info("Executing calendar analysis with AI")
        
        ai_state = AICommuteState(**state) if isinstance(state, dict) else state
        ai_state.progress_step = "AI analyzing calendar events"
        ai_state.progress_percentage = 0.2
        
        await self._publish_progress(ai_state)
        
        # Execute AI calendar analysis
        result = await self.calendar_analyzer.analyze_schedule(ai_state.dict())
        return result
    
    async def _meeting_classification_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node for AI meeting classification"""
        logger.info("Executing meeting classification with AI")
        
        ai_state = AICommuteState(**state) if isinstance(state, dict) else state
        ai_state.progress_step = "AI classifying meeting requirements"
        ai_state.progress_percentage = 0.4
        
        await self._publish_progress(ai_state)
        
        # Execute AI meeting classification
        result = await self.meeting_classifier.classify_meetings(ai_state.dict())
        return result
    
    async def _office_decision_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node for AI office presence decisions"""
        logger.info("Executing office decision making with AI")
        
        ai_state = AICommuteState(**state) if isinstance(state, dict) else state
        ai_state.progress_step = "AI determining optimal office presence"
        ai_state.progress_percentage = 0.6
        
        await self._publish_progress(ai_state)
        
        # Execute AI office decision making
        result = await self.office_decision_maker.make_office_decisions(ai_state.dict())
        return result
    
    async def _commute_optimization_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node for AI commute optimization"""
        logger.info("Executing commute optimization with AI")
        
        ai_state = AICommuteState(**state) if isinstance(state, dict) else state
        ai_state.progress_step = "AI optimizing commute routes and timing"
        ai_state.progress_percentage = 0.8
        
        await self._publish_progress(ai_state)
        
        # Execute AI commute optimization
        result = await self.commute_optimizer.optimize_commute(ai_state.dict())
        return result
    
    async def _recommendation_presentation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node for AI recommendation presentation"""
        logger.info("Executing recommendation presentation with AI")
        
        ai_state = AICommuteState(**state) if isinstance(state, dict) else state
        ai_state.progress_step = "AI generating personalized recommendations"
        ai_state.progress_percentage = 0.95
        
        await self._publish_progress(ai_state)
        
        # Execute AI recommendation presentation
        result = await self.recommendation_presenter.present_recommendations(ai_state.dict())
        
        # Update final state
        final_state = AICommuteState(**result) if isinstance(result, dict) else result
        final_state.progress_percentage = 1.0
        final_state.progress_step = "AI analysis complete"
        
        return final_state.dict()
    
    async def _publish_progress(self, state: AICommuteState) -> None:
        """Publish AI workflow progress with reasoning insights"""
        
        progress_data = {
            "jobId": state.job_id,
            "status": "IN_PROGRESS",
            "progress": state.progress_percentage,
            "currentStep": state.progress_step,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ai_insights": {
                "confidence_scores": state.confidence_scores,
                "reasoning_available": bool(state.llm_reasoning),
                "events_analyzed": len(state.calendar_events),
                "classifications_made": len(state.meeting_classifications)
            }
        }
        
        if state.error_message:
            progress_data["error"] = state.error_message
            
        await self.redis_service.publish_progress(
            self.settings.redis_progress_channel,
            progress_data
        )
    
    def _create_ai_success_result(self, state: AICommuteState) -> Dict[str, Any]:
        """Create AI-enhanced success result"""
        
        return {
            "status": "success",
            "job_id": state.job_id,
            "user_id": state.user_id,
            "target_date": state.target_date,
            "recommendations": state.recommendations,
            "ai_metadata": {
                "llm_reasoning": state.llm_reasoning,
                "confidence_scores": state.confidence_scores,
                "ai_insights": state.ai_insights,
                "workflow_type": "langgraph_ai_powered"
            },
            "workflow_summary": {
                "calendar_events_analyzed": len(state.calendar_events),
                "meetings_classified": len(state.meeting_classifications), 
                "office_options_evaluated": len(state.office_presence_blocks),
                "total_options_generated": len(state.commute_options),
                "final_recommendations": len(state.recommendations)
            },
            "execution_time": datetime.utcnow().isoformat(),
            "workflow_version": "2.0-ai"
        }
    
    def _create_error_result(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create AI workflow error result"""
        
        return {
            "status": "error",
            "job_id": state["job_id"],
            "user_id": state["user_id"], 
            "target_date": state["target_date"],
            "error_message": state.get("error_message", "Unknown AI workflow error"),
            "failed_at_step": state.get("progress_step", "Unknown step"),
            "progress_when_failed": state.get("progress_percentage", 0),
            "ai_metadata": {
                "llm_reasoning": state.get("llm_reasoning", {}),
                "confidence_scores": state.get("confidence_scores", {}),
                "workflow_type": "langgraph_ai_powered"
            },
            "execution_time": datetime.utcnow().isoformat()
        }