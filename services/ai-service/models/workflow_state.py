"""
LangGraph workflow state definitions
"""

from typing import List, Dict, Any, Optional, TypedDict


class CommuteState(TypedDict):
    """State for commute planning workflow"""
    
    # Input data
    job_id: str
    user_id: str
    target_date: str
    input_data: Dict[str, Any]
    
    # Workflow progress
    progress_step: str
    progress_percentage: float
    
    # Calendar analysis
    calendar_events: List[Dict[str, Any]]
    
    # Meeting classification
    meeting_classifications: List[Dict[str, Any]]  # remote vs office decisions
    
    # Office presence analysis
    office_presence_blocks: List[Dict[str, Any]]   # valid office time windows
    
    # Commute optimization
    commute_options: List[Dict[str, Any]]          # travel time calculations
    
    # Final output
    recommendations: List[Dict[str, Any]]          # final ranked recommendations
    
    # Error handling
    error_message: Optional[str]