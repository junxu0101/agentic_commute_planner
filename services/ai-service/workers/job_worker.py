"""
Event-driven job worker with Redis BRPOP and concurrency control
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import traceback

from config.settings import get_settings
from services.redis_service import RedisService
from services.backend_service import backend_service
from graphs.workflow_orchestrator import create_workflow_orchestrator

logger = logging.getLogger(__name__)


class JobWorker:
    """Event-driven job worker with concurrency control"""
    
    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service
        self.backend_service = backend_service
        self.settings = get_settings()
        
        # Concurrency control - max 5 concurrent jobs
        self.semaphore = asyncio.Semaphore(self.settings.max_concurrent_jobs)
        self.running = False
        self.active_jobs: Dict[str, asyncio.Task] = {}
        
        # Initialize workflow orchestrator (handles both rule-based and AI workflows)
        self.workflow_orchestrator = create_workflow_orchestrator(redis_service)
        
    async def start(self) -> None:
        """Start the job worker with event-driven processing"""
        self.running = True
        logger.info(
            f"Starting job worker with max {self.settings.max_concurrent_jobs} concurrent jobs"
        )
        
        while self.running:
            try:
                # Use blocking pop to wait for jobs - no polling!
                job_data = await self.redis_service.pop_job(
                    self.settings.redis_job_queue,
                    timeout=1  # 1 second timeout to allow checking self.running
                )
                
                if job_data:
                    # Process job immediately when received
                    await self._handle_job(job_data)
                    
            except Exception as e:
                logger.error(f"Error in job worker loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
                
        logger.info("Job worker stopped")
        
    async def stop(self) -> None:
        """Stop the job worker and wait for active jobs to complete"""
        logger.info("Stopping job worker...")
        self.running = False
        
        # Cancel all active jobs
        if self.active_jobs:
            logger.info(f"Cancelling {len(self.active_jobs)} active jobs")
            for job_id, task in self.active_jobs.items():
                task.cancel()
                
            # Wait for cancellation to complete
            await asyncio.gather(*self.active_jobs.values(), return_exceptions=True)
            
        logger.info("Job worker stopped successfully")
        
    async def _handle_job(self, job_data: Dict[str, Any]) -> None:
        """Handle incoming job with concurrency control"""
        job_id = job_data.get("job_id")
        if not job_id:
            logger.error("Received job without job_id")
            return
            
        # Check if we're already processing this job
        if job_id in self.active_jobs:
            logger.warning(f"Job {job_id} already being processed, skipping")
            return
            
        # Create task for job processing with concurrency control
        task = asyncio.create_task(self._process_job_with_semaphore(job_data))
        self.active_jobs[job_id] = task
        
        # Set up task completion callback
        task.add_done_callback(lambda t: self.active_jobs.pop(job_id, None))
        
        logger.info(
            f"Started processing job {job_id} "
            f"({len(self.active_jobs)}/{self.settings.max_concurrent_jobs} active)"
        )
        
    async def _process_job_with_semaphore(self, job_data: Dict[str, Any]) -> None:
        """Process job with semaphore-based concurrency control"""
        job_id = job_data.get("job_id")
        
        async with self.semaphore:
            try:
                await self._process_job(job_data)
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}")
                logger.error(traceback.format_exc())
                
                # Update job status to failed via backend service
                await self.backend_service.update_job_status(
                    job_id,
                    status="FAILED",
                    progress=0.0,
                    error_message=str(e)
                )
                
                # Publish failure notification
                await self.redis_service.publish_progress(
                    self.settings.redis_progress_channel,
                    {
                        "jobId": job_id,
                        "status": "FAILED",
                        "errorMessage": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                
    async def _process_job(self, job_data: Dict[str, Any]) -> None:
        """Process a single job using LangGraph workflow"""
        job_id = job_data.get("job_id")
        user_id = job_data.get("user_id")
        target_date = job_data.get("target_date")
        
        logger.info(f"Processing job {job_id} for user {user_id}, target date {target_date}")
        
        try:
            # Update job status to in progress via backend service
            await self.backend_service.update_job_status(
                job_id,
                status="IN_PROGRESS",
                progress=0.0,
                current_step="Starting workflow"
            )
            
            # Publish progress update
            await self.redis_service.publish_progress(
                self.settings.redis_progress_channel,
                {
                    "jobId": job_id,
                    "status": "IN_PROGRESS",
                    "progress": 0.0,
                    "currentStep": "Starting workflow",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Handle input_data (can be either dict or JSON string)
            raw_input_data = job_data.get("input_data", {})
            if isinstance(raw_input_data, str):
                try:
                    parsed_input_data = json.loads(raw_input_data)
                    logger.info(f"Parsed input_data from JSON string for job {job_id}")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse input_data as JSON, using as raw string: {raw_input_data}")
                    parsed_input_data = {"raw_input": raw_input_data}
            elif isinstance(raw_input_data, dict):
                parsed_input_data = raw_input_data
                logger.info(f"Using input_data as dict for job {job_id}")
            else:
                logger.warning(f"Unexpected input_data type for job {job_id}: {type(raw_input_data)}")
                parsed_input_data = {"raw_input": str(raw_input_data)}
            
            # Extract user timezone from input data for timezone-aware processing
            user_timezone = "UTC"  # Default fallback
            if isinstance(parsed_input_data, dict):
                context = parsed_input_data.get("context", {})
                if isinstance(context, dict):
                    user_timezone = context.get("user_timezone", "UTC")
            
            # Execute workflow via orchestrator (AI-powered or rule-based)
            workflow_input = {
                "job_id": job_id,
                "user_id": user_id,
                "target_date": target_date,
                "input_data": parsed_input_data,
                "user_timezone": user_timezone
            }
            
            result = await self.workflow_orchestrator.execute(workflow_input)
            
            # Update job status to completed
            await self.backend_service.update_job_status(
                job_id,
                status="COMPLETED",
                progress=1.0,
                current_step="Workflow completed",
                result=result
            )
            
            # Publish completion notification
            await self.redis_service.publish_progress(
                self.settings.redis_progress_channel,
                {
                    "jobId": job_id,
                    "status": "COMPLETED",
                    "progress": 1.0,
                    "currentStep": "Workflow completed",
                    "result": json.dumps(result) if result else None,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            logger.info(f"Successfully completed job {job_id}")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            raise  # Re-raise to be handled by _process_job_with_semaphore
            
    async def get_worker_stats(self) -> Dict[str, Any]:
        """Get current worker statistics"""
        queue_length = await self.redis_service.get_queue_length(
            self.settings.redis_job_queue
        )
        
        return {
            "running": self.running,
            "active_jobs": len(self.active_jobs),
            "max_concurrent_jobs": self.settings.max_concurrent_jobs,
            "queue_length": queue_length,
            "active_job_ids": list(self.active_jobs.keys())
        }