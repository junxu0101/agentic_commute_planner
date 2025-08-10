"""
User Context utilities for demo vs real user handling
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class UserContext:
    """Utilities for handling demo vs real user context"""
    
    # Demo user patterns (can be expanded)
    DEMO_USER_PATTERNS = [
        "demo",
        "test",
        "example",
        "sample"
    ]
    
    # Demo user IDs (specific demo accounts)
    DEMO_USER_IDS = {
        "demo-user-123",
        "test-user-456", 
        "sample-user-789"
    }
    
    @classmethod
    def is_demo_user(cls, user_id: str) -> bool:
        """Determine if a user is a demo user"""
        
        if not user_id:
            return False
        
        user_id_lower = user_id.lower()
        
        # Check explicit demo user IDs
        if user_id in cls.DEMO_USER_IDS:
            return True
        
        # Check demo patterns in user ID
        for pattern in cls.DEMO_USER_PATTERNS:
            if pattern in user_id_lower:
                return True
        
        return False
    
    @classmethod
    def get_fallback_strategy(cls, user_id: str) -> str:
        """Get appropriate fallback strategy for user type"""
        
        if cls.is_demo_user(user_id):
            return "demo_data_fallback"
        else:
            return "fail_fast"
    
    @classmethod
    def should_use_mock_data(cls, user_id: str) -> bool:
        """Determine if mock data should be used for this user"""
        
        return cls.is_demo_user(user_id)
    
    @classmethod
    def get_error_message_for_user(cls, user_id: str, error: str) -> str:
        """Get appropriate error message based on user type"""
        
        if cls.is_demo_user(user_id):
            return "Demo mode: Using sample recommendations. Real users would see actual AI analysis."
        else:
            return f"AI service temporarily unavailable: {error}. Please try again later."
    
    @classmethod
    def create_user_aware_config(cls, user_id: str) -> Dict[str, Any]:
        """Create configuration based on user type"""
        
        is_demo = cls.is_demo_user(user_id)
        
        return {
            "is_demo_user": is_demo,
            "fallback_strategy": cls.get_fallback_strategy(user_id),
            "use_mock_data": is_demo,
            "allow_mock_recommendations": is_demo,
            "require_real_ai": not is_demo,
            "error_handling": "graceful" if is_demo else "strict"
        }


def get_user_context(user_id: str) -> Dict[str, Any]:
    """Factory function to get user context configuration"""
    return UserContext.create_user_aware_config(user_id)