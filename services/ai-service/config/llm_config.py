"""
LLM Configuration and Factory for Multi-Agent System
"""

import os
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseLanguageModel
import logging

logger = logging.getLogger(__name__)


class LLMConfig:
    """Configuration and factory for LLM instances"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.openai_api_key and not self.anthropic_api_key:
            logger.warning("No LLM API keys found. Using mock responses.")
    
    def get_calendar_analyzer_llm(self) -> BaseLanguageModel:
        """Get LLM for calendar analysis (OpenAI first - using free credits)"""
        if self.openai_api_key:
            return ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model="gpt-4o-mini",
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=2000
            )
        elif self.anthropic_api_key:
            return ChatAnthropic(
                anthropic_api_key=self.anthropic_api_key,
                model="claude-3-sonnet-20240229",
                temperature=0.1,
                max_tokens=2000
            )
        else:
            return self._get_mock_llm()
    
    def get_meeting_classifier_llm(self) -> BaseLanguageModel:
        """Get LLM for meeting classification (GPT-4 - strong reasoning)"""
        if self.openai_api_key:
            return ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model="gpt-4o-mini",
                temperature=0.2,  # Slightly higher for creative classification
                max_tokens=1500
            )
        elif self.anthropic_api_key:
            return ChatAnthropic(
                anthropic_api_key=self.anthropic_api_key,
                model="claude-3-sonnet-20240229",
                temperature=0.2,
                max_tokens=1500
            )
        else:
            return self._get_mock_llm()
    
    def get_office_decision_llm(self) -> BaseLanguageModel:
        """Get LLM for office presence decisions (OpenAI first - using free credits)"""
        if self.openai_api_key:
            return ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model="gpt-4o-mini",
                temperature=0.3,  # Moderate creativity for flexible reasoning
                max_tokens=2000
            )
        elif self.anthropic_api_key:
            return ChatAnthropic(
                anthropic_api_key=self.anthropic_api_key,
                model="claude-3-sonnet-20240229",
                temperature=0.3,
                max_tokens=2000
            )
        else:
            return self._get_mock_llm()
    
    def get_commute_optimizer_llm(self) -> BaseLanguageModel:
        """Get LLM for commute optimization (GPT-4 - mathematical reasoning)"""
        if self.openai_api_key:
            return ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model="gpt-4o-mini",
                temperature=0.1,  # Low temperature for consistent calculations
                max_tokens=2000
            )
        elif self.anthropic_api_key:
            return ChatAnthropic(
                anthropic_api_key=self.anthropic_api_key,
                model="claude-3-sonnet-20240229",
                temperature=0.1,
                max_tokens=2000
            )
        else:
            return self._get_mock_llm()
    
    def get_recommendation_llm(self) -> BaseLanguageModel:
        """Get LLM for recommendation presentation (OpenAI first - using free credits)"""
        if self.openai_api_key:
            return ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model="gpt-4o-mini",
                temperature=0.4,  # Higher creativity for engaging communication
                max_tokens=2500
            )
        elif self.anthropic_api_key:
            return ChatAnthropic(
                anthropic_api_key=self.anthropic_api_key,
                model="claude-3-sonnet-20240229",
                temperature=0.4,
                max_tokens=2500
            )
        else:
            return self._get_mock_llm()
    
    def _get_mock_llm(self) -> BaseLanguageModel:
        """Fallback mock LLM for development without API keys"""
        from .mock_llm import MockLLM
        return MockLLM()


# Global LLM configuration instance
llm_config = LLMConfig()