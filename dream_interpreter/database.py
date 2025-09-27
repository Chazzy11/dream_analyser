from typing import Dict, List, Optional
from datetime import datetime
import uuid
from .models import DreamRecord


class DreamDatabase:
    """Simple in-memory database for storing dream records."""
    
    def __init__(self):
        self.dreams: Dict[str, DreamRecord] = {}
        self.user_dreams: Dict[str, List[str]] = {}  # user_id -> list of dream_ids
    
    def store_dream(self, dream_record: DreamRecord) -> str:
        """Store a dream record and return its ID."""
        dream_id = str(uuid.uuid4())
        dream_record.id = dream_id
        
        self.dreams[dream_id] = dream_record
        
        # Update user dreams index
        user_id = dream_record.user_id
        if user_id not in self.user_dreams:
            self.user_dreams[user_id] = []
        self.user_dreams[user_id].append(dream_id)
        
        return dream_id
    
    def get_user_dreams(self, user_id: str) -> List[DreamRecord]:
        """Get all dreams for a specific user."""
        dream_ids = self.user_dreams.get(user_id, [])
        return [self.dreams[dream_id] for dream_id in dream_ids if dream_id in self.dreams]
    
    def get_dream(self, dream_id: str) -> Optional[DreamRecord]:
        """Get a specific dream by ID."""
        return self.dreams.get(dream_id)
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get statistics for a user's dreams."""
        dreams = self.get_user_dreams(user_id)
        if not dreams:
            return {"total_dreams": 0}
        
        total = len(dreams)
        avg_upper_downer = sum(d.analysis.upper_downer_score for d in dreams) / total
        avg_static_dynamic = sum(d.analysis.static_dynamic_score for d in dreams) / total
        avg_confidence = sum(d.analysis.confidence for d in dreams) / total
        
        return {
            "total_dreams": total,
            "average_emotional_score": round(avg_upper_downer, 2),
            "average_dynamic_score": round(avg_static_dynamic, 2),
            "average_confidence": round(avg_confidence, 2),
            "dominant_quadrant": self._get_dominant_quadrant(avg_static_dynamic, avg_upper_downer)
        }
    
    def _get_dominant_quadrant(self, x: float, y: float) -> str:
        """Determine which quadrant the user's dreams predominantly fall into."""
        if y > 0 and x > 0:
            return "Dynamic Upper (Energetic Positive)"
        elif y > 0 and x <= 0:
            return "Static Upper (Peaceful Positive)"
        elif y <= 0 and x > 0:
            return "Dynamic Downer (Chaotic Negative)"
        else:
            return "Static Downer (Stagnant Negative)"