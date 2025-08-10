"""
Mock LLM for development and testing without API keys
"""

from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult, Generation
from langchain.callbacks.manager import Callbacks
import logging
import json

logger = logging.getLogger(__name__)


class MockLLM(BaseLanguageModel):
    """Mock LLM that provides realistic responses for development"""
    
    def __init__(self):
        super().__init__()
        self.call_count = 0
    
    @property
    def _llm_type(self) -> str:
        return "mock"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate mock responses based on message content"""
        
        self.call_count += 1
        message_text = " ".join([msg.content for msg in messages if hasattr(msg, 'content')])
        
        # Generate response based on context
        response = self._generate_contextual_response(message_text)
        
        logger.info(f"Mock LLM call #{self.call_count}: {len(message_text)} chars in, {len(response)} chars out")
        
        return LLMResult(
            generations=[[Generation(text=response)]],
            llm_output={"token_usage": {"total_tokens": len(response.split())}}
        )
    
    def _generate_contextual_response(self, message_text: str) -> str:
        """Generate contextual mock responses"""
        
        message_lower = message_text.lower()
        
        # Calendar Analysis Responses
        if "analyze" in message_lower and "calendar" in message_lower:
            return """
Based on the calendar events, I can see several patterns:

**Meeting Analysis:**
- 3 meetings scheduled throughout the day
- Mix of client-facing and internal meetings
- Potential for hybrid work arrangement

**Key Insights:**
- Q4 Client Presentation requires in-person presence (high stakes, multiple attendees)
- Daily standup can be conducted remotely
- 1:1 with manager is flexible on location

**Recommendations:**
- Office presence recommended for client presentation
- Remote work viable for other meetings
- Consider commute timing around high-priority meetings
"""
        
        # Meeting Classification Responses  
        elif "classify" in message_lower and "meeting" in message_lower:
            return json.dumps({
                "office_required": [
                    {
                        "meeting": "Q4 Client Presentation",
                        "reason": "Client-facing, high-stakes presentation requiring in-person presence",
                        "confidence": 0.95
                    }
                ],
                "remote_friendly": [
                    {
                        "meeting": "Daily Standup", 
                        "reason": "Routine team sync, well-suited for video call",
                        "confidence": 0.90
                    },
                    {
                        "meeting": "1:1 with Manager",
                        "reason": "Personal discussion, effective via video call",
                        "confidence": 0.85
                    }
                ]
            })
        
        # Office Decision Responses
        elif "office" in message_lower and "decision" in message_lower:
            return """
**Office Presence Analysis:**

Given the meeting mix and business requirements:

**Recommendation: Hybrid Day (4-6 hours in office)**
- **Office presence required**: 2-4 PM for client presentation
- **Remote work viable**: Morning standup, afternoon 1:1
- **Optimal schedule**: Work from home morning, office afternoon, home evening

**Reasoning:**
- Client presentation is the anchor requiring office presence
- 4-hour minimum office presence met efficiently
- Minimizes commute while maintaining professional standards
- Allows focused preparation time at home

**Confidence Score: 88%**
"""
        
        # Commute Optimization Responses
        elif "commute" in message_lower and ("optimize" in message_lower or "route" in message_lower):
            return """
**Optimal Commute Strategy:**

**Recommended Schedule:**
- **Depart Home**: 12:30 PM
- **Arrive Office**: 1:15 PM (45 min commute)
- **Office Duration**: 1:15 PM - 5:00 PM (3h 45m)
- **Depart Office**: 5:00 PM  
- **Arrive Home**: 6:00 PM (1h evening commute)

**Route Analysis:**
- Morning avoided rush hour (7-10 AM)
- Midday departure: light traffic, reliable timing
- Evening departure: moderate traffic, acceptable delay

**Efficiency Metrics:**
- Total commute time: 1h 45m
- Office productivity time: 3h 45m
- Commute-to-work ratio: 0.47 (acceptable)

**Alternative Options:**
1. Earlier arrival (11 AM) - Longer office time, higher commute cost
2. Later departure (7 PM) - Avoid evening traffic, late return home
"""
        
        # Recommendation Presentation Responses
        elif "recommend" in message_lower or "present" in message_lower:
            return """
# 🎯 Smart Commute Recommendation for Tuesday, Aug 13th

## 📋 Executive Summary
**Recommendation**: Hybrid work day with strategic office presence for client presentation

## 🏢 Optimal Schedule
- **9:00 AM - 12:30 PM**: Work from home (standup, preparation)
- **12:30 PM - 1:15 PM**: Commute to office  
- **1:15 PM - 5:00 PM**: Office presence (client presentation + follow-up)
- **5:00 PM - 6:00 PM**: Return commute

## 🧠 AI Reasoning
- **Client presentation** identified as high-priority, requiring in-person presence
- **Morning meetings** (standup, 1:1) optimized for remote attendance
- **Traffic patterns** analyzed for minimal commute impact
- **Work-life balance** maintained with late-morning departure

## 📊 Key Metrics  
- **Office time**: 3h 45m (meets 4-hour policy with buffer)
- **Total commute**: 1h 45m (efficient for hybrid day)
- **Productivity score**: 92% (focused morning prep + effective office time)

## 💡 Pro Tips
- Use morning home time for focused client presentation preparation
- Schedule buffer time before client meeting for setup
- Consider staying slightly later if traffic is heavy at 5 PM

*This recommendation balances professional requirements with personal efficiency.*
"""
        
        # Default response
        else:
            return f"""
I understand you're asking about: {message_text[:100]}...

As an AI assistant, I'll analyze this request and provide a thoughtful response based on the context and requirements you've provided. Let me know if you need me to focus on any specific aspects or provide additional detail.
"""
    
    async def agenerate(
        self,
        messages: List[List[BaseMessage]],
        stop: Optional[List[str]] = None,
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Async version of generate"""
        # For simplicity, just call the sync version
        return self._generate(messages[0] if messages else [], stop, **kwargs)