"""
models.py - Pydantic Data Models for PaasA Numerology AI
Author: Bhavya Sharma | Enrollment: 2450850380 | MCSP-232
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List
import re


class UserInput(BaseModel):
    """Model for user input data collected from the input form."""
    full_name: str
    dob: str          # Format: DD-MM-YYYY
    gender: str       # 'Male' or 'Female'

    @field_validator('full_name')
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 100:
            raise ValueError('Name must be between 2 and 100 characters')
        if not re.match(r'^[A-Za-z\s]+$', v):
            raise ValueError('Name must contain only letters and spaces')
        return v

    @field_validator('dob')
    @classmethod
    def validate_dob(cls, v):
        if not re.match(r'^\d{2}-\d{2}-\d{4}$', v):
            raise ValueError('Date must be in DD-MM-YYYY format')
        day, month, year = map(int, v.split('-'))
        if not (1 <= day <= 31):
            raise ValueError('Invalid day')
        if not (1 <= month <= 12):
            raise ValueError('Invalid month')
        if not (1900 <= year <= 2025):
            raise ValueError('Year must be between 1900 and 2025')
        return v

    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        if v not in ['Male', 'Female']:
            raise ValueError('Gender must be Male or Female')
        return v


class ChatMessage(BaseModel):
    """Model for chat messages sent to AI."""
    session_id: str
    message: str

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Message cannot be empty')
        if len(v) > 500:
            raise ValueError('Message must be 500 characters or less')
        v = re.sub(r'<[^>]+>', '', v)   # strip HTML tags
        return v


class LoShuGrid(BaseModel):
    """Model for Lo Shu Grid data."""
    grid: list
    present_numbers: list
    missing_numbers: list
    frequencies: dict


class Planes(BaseModel):
    """Model for plane analysis data."""
    mental: dict
    emotional: dict
    practical: dict
    thought: dict
    will: dict
    action: dict


class CoreNumbers(BaseModel):
    """Model for calculated core numerology numbers."""
    name_number: int
    mulank: int
    bhagyank: int
    kua_number: int


class Insights(BaseModel):
    """Model for AI-generated insights."""
    personality_snapshot: str
    strongest_plane: str
    strongest_plane_meaning: str
    key_strength: str
    key_challenge: str
    remedy_suggestion: str
    message: str


class NumerologyResult(BaseModel):
    """Complete numerology result for a session."""
    session_id: str
    user_name: str
    dob: str
    gender: str
    numbers: CoreNumbers
    loshu_grid: LoShuGrid
    planes: Planes
    insights: Insights


class SessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    response: str
    session_id: str


class HistoryItem(BaseModel):
    """Model for a single history item."""
    session_id: str
    user_name: str
    dob: str
    created_at: str


class HistoryResponse(BaseModel):
    """Response model for history retrieval."""
    sessions: List[HistoryItem]
    total: int
