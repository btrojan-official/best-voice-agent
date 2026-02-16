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
    llm_latency_ms: float = 0.0  # Total latency for all LLM calls in milliseconds


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
    model_name: str = "anthropic/claude-3.5-sonnet"  # Track which model was used


class InformationToGather(BaseModel):
    id: str
    title: str
    description: str
    created_at: str


class Settings(BaseModel):
    model_name: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.7
    information_to_gather: List[InformationToGather] = Field(default_factory=list)
    # Pricing configuration
    price_per_million_input_tokens: float = 3.0  # $ per 1M input tokens
    price_per_million_output_tokens: float = 15.0  # $ per 1M output tokens
    price_per_5s_transcription: float = 0.03  # $ per 5 seconds
    price_per_10k_tts_chars: float = 0.30  # $ per 10k characters
    # Token estimation
    estimated_token_length: int = 4  # Average characters per token (default: 4)


class ModelLatencyStats(BaseModel):
    model_name: str
    total_calls: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    avg_latency_per_100_tokens: float = 0.0  # milliseconds per 100 tokens


class SystemStats(BaseModel):
    total_calls: int = 0
    completed_calls: int = 0
    pending_calls: int = 0
    error_calls: int = 0
    total_usage: UsageStats = Field(default_factory=UsageStats)
    total_costs: CostStats = Field(default_factory=CostStats)
    model_latencies: Dict[str, ModelLatencyStats] = Field(default_factory=dict)
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
