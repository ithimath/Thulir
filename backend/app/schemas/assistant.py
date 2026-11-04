"""Pydantic schemas for the Grounded AI Assistant (Stretch 2)."""
from typing import List, Optional
from pydantic import BaseModel, Field

class AssistantQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Question about school policy, rules, or interventions")
    language: Optional[str] = Field("en", description="Preferred response language ('en' or 'ta')")

class AssistantQueryResponse(BaseModel):
    response: str
    title: Optional[str] = None
    grounded_sources: List[str]
    confidence_type: str
    is_refusal: bool = False
    disclaimer: str

