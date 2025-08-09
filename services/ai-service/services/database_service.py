"""
Database service for PostgreSQL operations
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for job and result management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[Pool] = None
        
    async def connect(self) -> None:
        """Connect to PostgreSQL database"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Connected to PostgreSQL database")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from database"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from database")
            
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: float = None,
        current_step: str = None,
        result: Dict[str, Any] = None,
        error_message: str = None
    ) -> bool:
        """Update job status and progress"""
        if not self.pool:
            raise RuntimeError("Database not connected")
            
        try:
            async with self.pool.acquire() as connection:
                query = """
                    UPDATE jobs 
                    SET 
                        status = $1,
                        progress = COALESCE($2, progress),
                        current_step = COALESCE($3, current_step),
                        result = COALESCE($4, result),
                        error_message = COALESCE($5, error_message),
                        updated_at = NOW()
                    WHERE id = $6
                    RETURNING id
                """
                
                result_json = json.dumps(result) if result else None
                row = await connection.fetchrow(
                    query,
                    status,
                    progress,
                    current_step,
                    result_json,
                    error_message,
                    job_id
                )
                
                if row:
                    logger.info(f"Updated job {job_id} status to {status}")
                    return True
                else:
                    logger.warning(f"Job {job_id} not found for update")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False
            
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details"""
        if not self.pool:
            raise RuntimeError("Database not connected")
            
        try:
            async with self.pool.acquire() as connection:
                query = """
                    SELECT 
                        id, user_id, status, progress, current_step,
                        target_date, input_data, result, error_message,
                        created_at, updated_at
                    FROM jobs 
                    WHERE id = $1
                """
                
                row = await connection.fetchrow(query, job_id)
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
            
    async def get_user_calendar_events(
        self,
        user_id: str,
        target_date: str
    ) -> List[Dict[str, Any]]:
        """Get user's calendar events for target date"""
        if not self.pool:
            raise RuntimeError("Database not connected")
            
        try:
            async with self.pool.acquire() as connection:
                query = """
                    SELECT 
                        id, summary, description, start_time, end_time,
                        location, attendees, meeting_type, attendance_mode,
                        is_all_day, is_recurring
                    FROM calendar_events 
                    WHERE user_id = $1 
                    AND DATE(start_time) = DATE($2)
                    ORDER BY start_time
                """
                
                rows = await connection.fetch(query, user_id, target_date)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting calendar events for user {user_id}: {e}")
            return []
            
    async def save_commute_recommendations(
        self,
        job_id: str,
        recommendations: List[Dict[str, Any]]
    ) -> bool:
        """Save commute recommendations to database"""
        if not self.pool:
            raise RuntimeError("Database not connected")
            
        try:
            async with self.pool.acquire() as connection:
                # Delete existing recommendations for this job
                await connection.execute(
                    "DELETE FROM commute_recommendations WHERE job_id = $1",
                    job_id
                )
                
                # Insert new recommendations
                for rank, rec in enumerate(recommendations, 1):
                    rec_id = str(uuid.uuid4())
                    
                    query = """
                        INSERT INTO commute_recommendations (
                            id, job_id, option_rank, option_type,
                            commute_start, office_arrival, office_departure, commute_end,
                            office_duration, office_meetings, remote_meetings,
                            business_rule_compliance, perception_analysis,
                            reasoning, trade_offs, created_at
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW()
                        )
                    """
                    
                    await connection.execute(
                        query,
                        rec_id,
                        job_id,
                        rank,
                        rec.get("option_type"),
                        rec.get("commute_start"),
                        rec.get("office_arrival"),
                        rec.get("office_departure"),
                        rec.get("commute_end"),
                        rec.get("office_duration"),
                        json.dumps(rec.get("office_meetings", [])),
                        json.dumps(rec.get("remote_meetings", [])),
                        json.dumps(rec.get("business_rule_compliance", {})),
                        json.dumps(rec.get("perception_analysis", {})),
                        rec.get("reasoning"),
                        json.dumps(rec.get("trade_offs", {}))
                    )
                    
                logger.info(f"Saved {len(recommendations)} recommendations for job {job_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving recommendations for job {job_id}: {e}")
            return False
            
    async def health_check(self) -> bool:
        """Check database connection health"""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False