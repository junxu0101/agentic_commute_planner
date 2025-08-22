"""
LangGraph Multi-Agent Commute Planning Workflow
"""

import logging
from datetime import datetime
from typing import Dict, Any

from models.workflow_state import CommuteState
from agents.schedule_analyzer_agent import ScheduleAnalyzerAgent
from agents.meeting_classifier_agent import MeetingClassifierAgent
from agents.office_presence_validator_agent import OfficePresenceValidatorAgent
from agents.commute_optimizer_agent import CommuteOptimizerAgent
from agents.option_presenter_agent import OptionPresenterAgent
from services.redis_service import RedisService
from services.backend_service import backend_service
from config.settings import get_settings

logger = logging.getLogger(__name__)


class CommuteWorkflow:
    """LangGraph workflow orchestrating multi-agent commute planning"""
    
    def __init__(self, redis_service: RedisService, backend_service):
        self.redis_service = redis_service
        self.backend_service = backend_service
        self.settings = get_settings()
        
        # Initialize agents
        self.schedule_analyzer = ScheduleAnalyzerAgent(backend_service)
        self.meeting_classifier = MeetingClassifierAgent()
        self.presence_validator = OfficePresenceValidatorAgent()
        self.option_presenter = OptionPresenterAgent()
        
    async def execute(self, workflow_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete multi-agent workflow
        
        Workflow Steps:
        1. Schedule Analysis - Analyze calendar events
        2. Meeting Classification - Determine office vs remote requirements
        3. Office Presence Validation - Apply 4+ hour business rules
        4. Commute Optimization - Calculate travel times and routes
        5. Option Presentation - Format and rank recommendations
        """
        
        job_id = workflow_input["job_id"]
        user_id = workflow_input["user_id"]
        target_date = workflow_input["target_date"]
        
        # DEBUG: Log complete workflow input to trace timezone data flow
        logger.error(f"=== WORKFLOW INPUT DEBUG ===")
        logger.error(f"WORKFLOW INPUT - Complete input: {workflow_input}")
        logger.error(f"WORKFLOW INPUT - job_id: {job_id}")
        logger.error(f"WORKFLOW INPUT - user_id: {user_id}")
        logger.error(f"WORKFLOW INPUT - target_date: {target_date}")
        logger.error(f"WORKFLOW INPUT - input_data: {workflow_input.get('input_data', {})}")
        logger.error(f"=== WORKFLOW INPUT DEBUG END ===")
        
        logger.info(f"Starting commute workflow for job {job_id}")
        
        # Initialize workflow state
        state: CommuteState = {
            "job_id": job_id,
            "user_id": user_id,
            "target_date": target_date,
            "input_data": workflow_input.get("input_data", {}),
            "progress_step": "Initializing workflow",
            "progress_percentage": 0.0,
            "calendar_events": [],
            "meeting_classifications": [],
            "office_presence_blocks": [],
            "commute_options": [],
            "recommendations": [],
            "error_message": None
        }
        
        try:
            # Step 1: Schedule Analysis
            await self._publish_progress(state)
            state = await self.schedule_analyzer.analyze_schedule(state)
            
            if state.get("error_message"):
                return self._create_error_result(state)
                
            # Step 2: Meeting Classification
            await self._publish_progress(state)
            await self._update_job_status(state)
            state = await self.meeting_classifier.classify_meetings(state)
            
            if state.get("error_message"):
                return self._create_error_result(state)
                
            # Step 3: Office Presence Validation
            await self._publish_progress(state)
            await self._update_job_status(state)
            state = await self.presence_validator.validate_office_presence(state)
            
            if state.get("error_message"):
                return self._create_error_result(state)
                
            # Step 4: Commute Optimization
            await self._publish_progress(state)
            await self._update_job_status(state)
            commute_optimizer = CommuteOptimizerAgent(user_id)
            state = await commute_optimizer.optimize_commute(state)
            
            if state.get("error_message"):
                return self._create_error_result(state)
                
            # Step 5: Option Presentation
            await self._publish_progress(state)
            await self._update_job_status(state)
            state = await self.option_presenter.present_recommendations(state)
            
            if state.get("error_message"):
                return self._create_error_result(state)
                
            # Save recommendations to database
            await self.backend_service.save_commute_recommendations(
                job_id,
                state["recommendations"]
            )
            
            # Final progress update
            await self._publish_progress(state)
            await self._update_job_status(state)
            
            # Return final result
            result = self._create_success_result(state)
            logger.info(f"Workflow completed successfully for job {job_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow error for job {job_id}: {e}")
            state["error_message"] = str(e)
            return self._create_error_result(state)
            
    async def _publish_progress(self, state: CommuteState) -> None:
        """Publish real-time progress update via Redis pub/sub"""
        
        progress_data = {
            "jobId": state["job_id"],
            "status": "IN_PROGRESS",
            "progress": state["progress_percentage"],
            "currentStep": state["progress_step"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": {
                "calendar_events_count": len(state.get("calendar_events", [])),
                "meeting_classifications_count": len(state.get("meeting_classifications", [])),
                "office_presence_blocks_count": len(state.get("office_presence_blocks", [])),
                "commute_options_count": len(state.get("commute_options", [])),
                "recommendations_count": len(state.get("recommendations", []))
            }
        }
        
        if state.get("error_message"):
            progress_data["error"] = state["error_message"]
            
        await self.redis_service.publish_progress(
            self.settings.redis_progress_channel,
            progress_data
        )
        
    async def _update_job_status(self, state: CommuteState) -> None:
        """Update job status in database"""
        
        await self.backend_service.update_job_status(
            state["job_id"],
            status="IN_PROGRESS",
            progress=state["progress_percentage"],
            current_step=state["progress_step"]
        )
        
    def _create_success_result(self, state: CommuteState) -> Dict[str, Any]:
        """Create successful workflow result"""
        
        return {
            "status": "success",
            "job_id": state["job_id"],
            "user_id": state["user_id"],
            "target_date": state["target_date"],
            "recommendations": state["recommendations"],
            "workflow_summary": {
                "calendar_events_analyzed": len(state["calendar_events"]),
                "meetings_classified": len(state["meeting_classifications"]),
                "office_options_evaluated": len([b for b in state["office_presence_blocks"] 
                                               if b["type"] != "FULL_REMOTE_RECOMMENDED"]),
                "total_options_generated": len(state["commute_options"]),
                "final_recommendations": len(state["recommendations"])
            },
            "execution_time": datetime.utcnow().isoformat(),
            "workflow_version": "1.0"
        }
        
    def _create_error_result(self, state: CommuteState) -> Dict[str, Any]:
        """Create error workflow result"""
        
        return {
            "status": "error",
            "job_id": state["job_id"],
            "user_id": state["user_id"],
            "target_date": state["target_date"],
            "error_message": state.get("error_message", "Unknown workflow error"),
            "failed_at_step": state.get("progress_step", "Unknown step"),
            "progress_when_failed": state.get("progress_percentage", 0),
            "partial_results": {
                "calendar_events": len(state.get("calendar_events", [])),
                "meeting_classifications": len(state.get("meeting_classifications", [])),
                "office_presence_blocks": len(state.get("office_presence_blocks", [])),
                "commute_options": len(state.get("commute_options", []))
            },
            "execution_time": datetime.utcnow().isoformat()
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """Check workflow health and dependencies"""
        
        health_status = {
            "workflow": "healthy",
            "agents": {
                "schedule_analyzer": "initialized",
                "meeting_classifier": "initialized", 
                "presence_validator": "initialized",
                "option_presenter": "initialized"
            },
            "services": {
                "redis": await self.redis_service.health_check(),
                "database": await self.backend_service.health_check()
            }
        }
        
        # Overall health
        all_healthy = (
            health_status["services"]["redis"] and 
            health_status["services"]["database"]
        )
        
        health_status["overall_status"] = "healthy" if all_healthy else "degraded"
        
        return health_status