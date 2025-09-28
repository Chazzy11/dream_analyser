from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DreamInput(BaseModel):
    """Model for dream input from user."""

    dream_text: str = Field(..., min_length=10, description="The dream description")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")


class DreamAnalysis(BaseModel):
    """Model for dream analysis results."""

    upper_downer_score: float = Field(
        ..., ge=-1.0, le=1.0, description="Emotional valence (-1 = downer, 1 = upper)"
    )
    static_dynamic_score: float = Field(
        ..., ge=-1.0, le=1.0, description="Energy level (-1 = static, 1 = dynamic)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")
    keywords: List[str] = Field(default=[], description="Key dream elements")


class DreamRecord(BaseModel):
    """Complete dream record with analysis."""

    id: str
    dream_text: str
    user_id: str
    analysis: DreamAnalysis
    timestamp: datetime
    symbol_path: Optional[str] = None


class SymbolResponse(BaseModel):
    """Response model for symbol generation."""

    symbol_base64: str = Field(..., description="Base64 encoded symbol image")
    dream_count: int = Field(..., description="Total dreams analyzed for this user")
    coordinates: tuple = Field(..., description="(x, y) coordinates in dream space")
