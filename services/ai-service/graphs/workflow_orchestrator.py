"""
Workflow Orchestrator - Manages both rule-based and AI-powered workflows
"""

import logging
import os
from typing import Dict, Any

from graphs.commute_workflow import CommuteWorkflow
from graphs.langgraph_workflow import LangGraphCommuteWorkflow
from services.redis_service import RedisService
from services.backend_service import backend_service
from config.settings import get_settings
from utils.user_context import get_user_context

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates between rule-based and AI-powered workflows"""
    
    def __init__(self, redis_service: RedisService, backend_service):
        self.redis_service = redis_service
        self.backend_service = backend_service
        self.settings = get_settings()
        
        # Initialize both workflow types
        self.rule_based_workflow = CommuteWorkflow(redis_service, backend_service)
        self.ai_workflow = LangGraphCommuteWorkflow(redis_service, backend_service)
        
        # Determine which workflow to use
        self.use_ai_workflow = self._should_use_ai_workflow()
        
        logger.info(f"Workflow orchestrator initialized - Using {'AI-powered' if self.use_ai_workflow else 'rule-based'} workflow")
    
    def _should_use_ai_workflow(self) -> bool:
        """Determine whether to use AI-powered or rule-based workflow"""
        
        # Check for AI workflow enablement flag
        ai_enabled = os.getenv("USE_AI_WORKFLOW", "true").lower() == "true"
        
        # Check for API keys availability
        has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))
        has_ai_keys = has_openai_key or has_anthropic_key
        
        # Use AI workflow if enabled and keys are available
        use_ai = ai_enabled and has_ai_keys
        
        if ai_enabled and not has_ai_keys:
            logger.warning("AI workflow enabled but no API keys found - falling back to rule-based workflow")
        
        return use_ai
    
    async def execute(self, workflow_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the appropriate workflow based on configuration and user type"""
        
        job_id = workflow_input.get("job_id", "unknown")
        user_id = workflow_input.get("user_id", "unknown")
        
        # Get user context to determine fallback strategy
        user_context = get_user_context(user_id)
        is_demo_user = user_context["is_demo_user"]
        fallback_strategy = user_context["fallback_strategy"]
        
        logger.info(f"Executing workflow for job {job_id}, user {user_id} (demo: {is_demo_user})")
        
        if self.use_ai_workflow:
            logger.info(f"Attempting AI-powered workflow for job {job_id}")
            try:
                result = await self.ai_workflow.execute(workflow_input)
                
                # Mark result as AI-powered
                if isinstance(result, dict):
                    result["workflow_type"] = "ai_powered_langgraph"
                    result["ai_enabled"] = True
                    result["user_context"] = user_context
                
                return result
                
            except Exception as e:
                logger.error(f"AI workflow failed for job {job_id}: {e}")
                
                # Apply user-aware fallback strategy
                if fallback_strategy == "fail_fast":
                    # Real users: Fail fast with clear error
                    logger.info(f"Real user {user_id}: Failing fast, no fallback to mock data")
                    return {
                        "status": "error",
                        "job_id": job_id,
                        "user_id": user_id,
                        "error_message": f"AI service temporarily unavailable. Please try again later.",
                        "workflow_type": "ai_required_failed",
                        "ai_enabled": False,
                        "user_context": user_context,
                        "technical_error": str(e)
                    }
                
                elif fallback_strategy == "demo_data_fallback":
                    # Demo users: Fall back to rule-based with demo data
                    logger.info(f"Demo user {user_id}: Falling back to rule-based workflow with demo data")
                    result = await self.rule_based_workflow.execute(workflow_input)
                    
                    if isinstance(result, dict):
                        result["workflow_type"] = "demo_fallback"
                        result["ai_enabled"] = False
                        result["fallback_reason"] = "Demo mode: Using sample data due to AI service unavailability"
                        result["user_context"] = user_context
                        result["is_demo_data"] = True
                    
                    return result
        else:
            logger.info(f"Executing rule-based workflow for job {job_id}")
            result = await self.rule_based_workflow.execute(workflow_input)
            
            if isinstance(result, dict):
                result["workflow_type"] = "rule_based"
                result["ai_enabled"] = False
                result["user_context"] = user_context
                result["is_demo_data"] = is_demo_user
            
            return result
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of both workflow types"""
        
        health_status = {
            "orchestrator": "healthy",
            "ai_workflow_available": self.use_ai_workflow,
            "workflows": {}
        }
        
        # Check rule-based workflow health
        try:
            rule_health = await self.rule_based_workflow.health_check()
            health_status["workflows"]["rule_based"] = rule_health
        except Exception as e:
            health_status["workflows"]["rule_based"] = {"status": "error", "error": str(e)}
        
        # Check AI workflow health if enabled
        if self.use_ai_workflow:
            try:
                # AI workflow health check would be implemented in LangGraphCommuteWorkflow
                health_status["workflows"]["ai_powered"] = {
                    "status": "healthy",
                    "llm_keys_available": {
                        "openai": bool(os.getenv("OPENAI_API_KEY")),
                        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY"))
                    }
                }
            except Exception as e:
                health_status["workflows"]["ai_powered"] = {"status": "error", "error": str(e)}
        
        # Overall health
        workflow_errors = [
            w for w in health_status["workflows"].values() 
            if isinstance(w, dict) and w.get("status") == "error"
        ]
        
        health_status["overall_status"] = "healthy" if not workflow_errors else "degraded"
        
        return health_status


# Global workflow orchestrator instance
def create_workflow_orchestrator(redis_service: RedisService) -> WorkflowOrchestrator:
    """Factory function to create workflow orchestrator"""
    return WorkflowOrchestrator(redis_service, backend_service)