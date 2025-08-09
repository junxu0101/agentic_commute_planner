"""
Backend service client for GraphQL API communication
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from config.settings import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class BackendService:
    """Client for communicating with the Go backend GraphQL API"""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def make_graphql_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GraphQL request to the backend service"""
        try:
            response = await self.client.post(
                self.backend_url,
                json={
                    "query": query,
                    "variables": variables or {}
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("errors"):
                logger.error(f"Backend GraphQL errors: {result['errors']}")
                raise Exception(f"Backend GraphQL error: {result['errors'][0].get('message', 'Unknown error')}")
            
            return result.get("data", {})
            
        except Exception as error:
            logger.error(f"Error calling backend service: {error}")
            raise
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: str, 
        progress: float,
        current_step: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update job status via backend API"""
        
        mutation = """
        mutation UpdateJob($id: ID!, $input: UpdateJobInput!) {
            updateJob(id: $id, input: $input) {
                id
                userId
                status
                progress
                currentStep
                targetDate
                result
                errorMessage
                updatedAt
            }
        }
        """
        
        variables = {
            "id": job_id,
            "input": {
                "status": status,
                "progress": progress
            }
        }
        
        if current_step is not None:
            variables["input"]["currentStep"] = current_step
            
        if result is not None:
            variables["input"]["result"] = json.dumps(result)
            
        if error_message is not None:
            variables["input"]["errorMessage"] = error_message
        
        try:
            data = await self.make_graphql_request(mutation, variables)
            return data.get("updateJob")
        except Exception as error:
            logger.error(f"Failed to update job {job_id}: {error}")
            return None
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details from backend"""
        
        query = """
        query GetJob($id: ID!) {
            job(id: $id) {
                id
                userId
                status
                progress
                currentStep
                targetDate
                inputData
                result
                errorMessage
                createdAt
                updatedAt
            }
        }
        """
        
        try:
            data = await self.make_graphql_request(query, {"id": job_id})
            return data.get("job")
        except Exception as error:
            logger.error(f"Failed to get job {job_id}: {error}")
            return None
    
    async def get_user_calendar_events(self, user_id: str, target_date: str) -> List[Dict[str, Any]]:
        """Get user calendar events from backend"""
        
        query = """
        query GetCalendarEvents($userId: ID!) {
            calendarEvents(userId: $userId) {
                id
                summary
                description
                startTime
                endTime
                location
                attendees
                meetingType
                attendanceMode
                isAllDay
                isRecurring
            }
        }
        """
        
        try:
            data = await self.make_graphql_request(query, {"userId": user_id})
            return data.get("calendarEvents", [])
        except Exception as error:
            logger.error(f"Failed to get calendar events for user {user_id}: {error}")
            return []
    
    async def save_commute_recommendations(self, job_id: str, recommendations: List[Dict[str, Any]]) -> bool:
        """Save commute recommendations to job result"""
        try:
            # Update the job with the final recommendations as the result
            result = await self.update_job_status(
                job_id=job_id,
                status="COMPLETED",
                progress=1.0,
                current_step="Recommendations complete",
                result={
                    "recommendations": recommendations,
                    "total_options": len(recommendations),
                    "analysis_complete": True
                }
            )
            
            if result:
                logger.info(f"Successfully saved {len(recommendations)} commute recommendations for job {job_id}")
                return True
            else:
                logger.error(f"Failed to save commute recommendations for job {job_id}")
                return False
                
        except Exception as error:
            logger.error(f"Error saving commute recommendations for job {job_id}: {error}")
            return False
    
    async def health_check(self) -> bool:
        """Check if backend service is healthy"""
        try:
            query = "query { __typename }"
            await self.make_graphql_request(query)
            return True
        except Exception:
            return False


# Global backend service instance
backend_service = BackendService(settings.backend_service_url)