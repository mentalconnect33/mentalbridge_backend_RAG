from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ChatMessage:
    role: str
    content: str

@dataclass
class ChatRequest:
    query: str
    chat_history: List[ChatMessage] = field(default_factory=list)

@dataclass
class ArticleInfo:
    id: int
    title: str
    category: str
    similarity: float
    read_time: Optional[str] = None

@dataclass
class ClinicInfo:
    clinic_id: int
    name: str
    location: str
    specialties: List[str]
    similarity: float

@dataclass
class ChatResponse:
    response: str
    articles: List[Dict[str, Any]] = field(default_factory=list)
    clinics: List[Dict[str, Any]] = field(default_factory=list)
