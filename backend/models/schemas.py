from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CallStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: str
    content: str
    timestamp: str
    audio_duration: Optional[float] = None


class UsageStats(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    input_characters: int = 0
    output_characters: int = 0
    transcription_seconds: float = 0.0
    tts_characters: int = 0
    llm_calls: int = 0


class CostStats(BaseModel):
    llm_input_cost: float = 0.0
    llm_output_cost: float = 0.0
    transcription_cost: float = 0.0
    tts_cost: float = 0.0
    total_cost: float = 0.0


class ToolCall(BaseModel):
    timestamp: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None


class Call(BaseModel):
    id: str
    title: str = "New Call"
    status: CallStatus = CallStatus.PENDING
    start_time: str
    end_time: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    summary: Optional[str] = None
    usage_stats: UsageStats = Field(default_factory=UsageStats)
    cost_stats: CostStats = Field(default_factory=CostStats)
    error_message: Optional[str] = None


class InformationToGather(BaseModel):
    id: str
    title: str
    description: str
    created_at: str


class Settings(BaseModel):
    model_name: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.7
    information_to_gather: List[InformationToGather] = Field(default_factory=list)


class SystemStats(BaseModel):
    total_calls: int = 0
    completed_calls: int = 0
    pending_calls: int = 0
    error_calls: int = 0
    total_usage: UsageStats = Field(default_factory=UsageStats)
    total_costs: CostStats = Field(default_factory=CostStats)
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class AdminCredentials(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: Optional[str] = None


class CallCreateRequest(BaseModel):
    pass


class CallResponse(BaseModel):
    call_id: str
    status: CallStatus


class AudioChunk(BaseModel):
    audio_data: str
    timestamp: str


class TranscriptionResponse(BaseModel):
    text: str
    timestamp: str


class TTSRequest(BaseModel):
    text: str
    call_id: str


class SettingsUpdateRequest(BaseModel):
    model_name: Optional[str] = None
    temperature: Optional[float] = None


class InformationToGatherRequest(BaseModel):
    title: str
    description: str
