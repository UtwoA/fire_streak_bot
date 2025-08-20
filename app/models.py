from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Member:
    user_id: int
    username: Optional[str]
    first_name: Optional[str]

@dataclass
class ChatState:
    chat_id: int
    streak: int = 0
    max_streak: int = 0
    status: str = 'inactive'  # inactive | active | frozen | reset
    last_active_date: Optional[date] = None
    frozen_type: Optional[str] = None
    thaw_required: int = 0
    thaw_count: int = 0
    pre_freeze_streak: int = 0
