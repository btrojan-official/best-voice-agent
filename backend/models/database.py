import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from pathlib import Path

from .schemas import (
    Call, CallStatus, Settings, SystemStats, InformationToGather,
    UsageStats, CostStats, Message, ToolCall, ModelLatencyStats
)


class Database:
    """
    Simple JSON-based database for storing calls, settings, and statistics.
    Thread-safe with asyncio locks.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.calls_file = self.data_dir / "calls.json"
        self.settings_file = self.data_dir / "settings.json"
        self.stats_file = self.data_dir / "stats.json"
        
        self.lock = asyncio.Lock()
        
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize JSON files if they don't exist."""
        if not self.calls_file.exists():
            self._write_json(self.calls_file, [])
        
        if not self.settings_file.exists():
            default_model = os.getenv("DEFAULT_MODEL", "openai/gpt-oss-120b")
            default_token_length = int(os.getenv("ESTIMATED_TOKEN_LENGTH", "4"))
            default_settings = Settings(
                model_name=default_model,
                temperature=0.7,
                price_per_million_input_tokens=3.0,
                price_per_million_output_tokens=15.0,
                price_per_5s_transcription=0.03,
                price_per_10k_tts_chars=0.30,
                estimated_token_length=default_token_length,
                information_to_gather=[
                    InformationToGather(
                        id=str(uuid.uuid4()),
                        title="Customer Identification",
                        description="Verify the customer's full name and contact information for security purposes",
                        created_at=datetime.now().isoformat()
                    ),
                    InformationToGather(
                        id=str(uuid.uuid4()),
                        title="Order Number",
                        description="Ask for the order number or reference ID related to their inquiry",
                        created_at=datetime.now().isoformat()
                    ),
                    InformationToGather(
                        id=str(uuid.uuid4()),
                        title="Purchase Date",
                        description="Determine when the customer made their purchase or when the issue occurred",
                        created_at=datetime.now().isoformat()
                    )
                ]
            )
            self._write_json(self.settings_file, default_settings.model_dump())
        
        if not self.stats_file.exists():
            self._write_json(self.stats_file, SystemStats().model_dump())
    
    def _read_json(self, file_path: Path) -> Any:
        """Read and parse JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def _write_json(self, file_path: Path, data: Any):
        """Write data to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def create_call(self, model_name: str = "openai/gpt-oss-120b") -> Call:
        """Create a new call."""
        async with self.lock:
            call = Call(
                id=str(uuid.uuid4()),
                start_time=datetime.now().isoformat(),
                status=CallStatus.PENDING,
                model_name=model_name
            )
            
            calls = self._read_json(self.calls_file)
            calls.append(call.model_dump())
            self._write_json(self.calls_file, calls)
            
            await self._increment_stat("total_calls")
            await self._increment_stat("pending_calls")
            
            return call
    
    async def get_call(self, call_id: str) -> Optional[Call]:
        """Get a call by ID."""
        async with self.lock:
            calls = self._read_json(self.calls_file)
            for call_data in calls:
                if call_data["id"] == call_id:
                    return Call(**call_data)
            return None
    
    async def get_all_calls(self) -> List[Call]:
        """Get all calls."""
        async with self.lock:
            calls = self._read_json(self.calls_file)
            return [Call(**call_data) for call_data in calls]
    
    async def update_call(self, call: Call) -> Call:
        """Update an existing call."""
        async with self.lock:
            calls = self._read_json(self.calls_file)
            for i, call_data in enumerate(calls):
                if call_data["id"] == call.id:
                    calls[i] = call.model_dump()
                    self._write_json(self.calls_file, calls)
                    return call
            raise ValueError(f"Call {call.id} not found")
    
    async def update_call_status(
        self, 
        call_id: str, 
        status: CallStatus,
        error_message: Optional[str] = None
    ) -> Call:
        """Update call status."""
        call = await self.get_call(call_id)
        if not call:
            raise ValueError(f"Call {call_id} not found")
        
        old_status = call.status
        call.status = status
        
        if status == CallStatus.COMPLETED:
            call.end_time = datetime.now().isoformat()
        
        if error_message:
            call.error_message = error_message
        
        await self.update_call(call)
        
        if old_status == CallStatus.PENDING:
            await self._increment_stat("pending_calls", -1)
        
        if status == CallStatus.COMPLETED:
            await self._increment_stat("completed_calls")
        elif status == CallStatus.ERROR:
            await self._increment_stat("error_calls")
        
        return call
    
    async def add_message_to_call(self, call_id: str, message: Message):
        """Add a message to a call."""
        call = await self.get_call(call_id)
        if not call:
            raise ValueError(f"Call {call_id} not found")
        
        call.messages.append(message)
        await self.update_call(call)
    
    async def add_tool_call(self, call_id: str, tool_call: ToolCall):
        """Add a tool call to a call."""
        call = await self.get_call(call_id)
        if not call:
            raise ValueError(f"Call {call_id} not found")
        
        call.tool_calls.append(tool_call)
        await self.update_call(call)
    
    async def get_settings(self) -> Settings:
        """Get current settings."""
        async with self.lock:
            settings_data = self._read_json(self.settings_file)
            return Settings(**settings_data)
    
    async def update_settings(self, settings: Settings) -> Settings:
        """Update settings."""
        async with self.lock:
            self._write_json(self.settings_file, settings.model_dump())
            return settings
    
    async def add_information_to_gather(
        self, 
        title: str, 
        description: str
    ) -> InformationToGather:
        """Add new information to gather."""
        settings = await self.get_settings()
        
        info = InformationToGather(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            created_at=datetime.now().isoformat()
        )
        
        settings.information_to_gather.append(info)
        await self.update_settings(settings)
        
        return info
    
    async def remove_information_to_gather(self, info_id: str) -> bool:
        """Remove information to gather."""
        settings = await self.get_settings()
        
        original_length = len(settings.information_to_gather)
        settings.information_to_gather = [
            info for info in settings.information_to_gather
            if info.id != info_id
        ]
        
        if len(settings.information_to_gather) < original_length:
            await self.update_settings(settings)
            return True
        
        return False
    
    async def get_stats(self) -> SystemStats:
        """Get system statistics."""
        async with self.lock:
            stats_data = self._read_json(self.stats_file)
            return SystemStats(**stats_data)
    
    async def update_stats(
        self,
        usage_delta: Optional[UsageStats] = None,
        cost_delta: Optional[CostStats] = None,
        model_name: Optional[str] = None,
        call_tokens: Optional[int] = None,
        call_latency_ms: Optional[float] = None
    ):
        """Update system statistics."""
        async with self.lock:
            stats = SystemStats(**self._read_json(self.stats_file))
            
            if usage_delta:
                stats.total_usage.input_tokens += usage_delta.input_tokens
                stats.total_usage.output_tokens += usage_delta.output_tokens
                stats.total_usage.input_characters += usage_delta.input_characters
                stats.total_usage.output_characters += usage_delta.output_characters
                stats.total_usage.transcription_seconds += usage_delta.transcription_seconds
                stats.total_usage.tts_characters += usage_delta.tts_characters
                stats.total_usage.llm_calls += usage_delta.llm_calls
                stats.total_usage.llm_latency_ms += usage_delta.llm_latency_ms
            
            if cost_delta:
                stats.total_costs.llm_input_cost += cost_delta.llm_input_cost
                stats.total_costs.llm_output_cost += cost_delta.llm_output_cost
                stats.total_costs.transcription_cost += cost_delta.transcription_cost
                stats.total_costs.tts_cost += cost_delta.tts_cost
                stats.total_costs.total_cost += cost_delta.total_cost
            
            # Update model-specific latency stats
            if model_name and call_tokens and call_latency_ms:
                if model_name not in stats.model_latencies:
                    stats.model_latencies[model_name] = ModelLatencyStats(
                        model_name=model_name
                    )
                
                model_stats = stats.model_latencies[model_name]
                model_stats.total_calls += 1
                model_stats.total_tokens += call_tokens
                model_stats.total_latency_ms += call_latency_ms
                
                # Calculate average latency per 100 tokens
                if model_stats.total_tokens > 0:
                    model_stats.avg_latency_per_100_tokens = (
                        model_stats.total_latency_ms / model_stats.total_tokens
                    ) * 100
            
            stats.last_updated = datetime.now().isoformat()
            
            self._write_json(self.stats_file, stats.model_dump())
    
    async def _increment_stat(self, stat_name: str, value: int = 1):
        """Increment a specific statistic."""
        stats = SystemStats(**self._read_json(self.stats_file))
        
        if hasattr(stats, stat_name):
            current_value = getattr(stats, stat_name)
            setattr(stats, stat_name, current_value + value)
            stats.last_updated = datetime.now().isoformat()
            self._write_json(self.stats_file, stats.model_dump())


db = Database()
