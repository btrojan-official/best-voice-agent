import asyncio
import base64
import json
import logging
from typing import Dict
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse

from models import db, CallStatus, Message, UsageStats, CostStats
from agent import CustomerSupportAgent
from utils.transcription import transcribe_audio_stream
from utils.tts import text_to_speech_stream
from utils.precomputed_audio import precomputed_audio_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections for active calls."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_agents: Dict[str, CustomerSupportAgent] = {}
    
    async def connect(self, call_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        self.active_connections[call_id] = websocket
        logger.info(f"WebSocket connected for call {call_id}")
    
    def disconnect(self, call_id: str):
        """Remove WebSocket connection."""
        if call_id in self.active_connections:
            del self.active_connections[call_id]
        if call_id in self.active_agents:
            del self.active_agents[call_id]
        logger.info(f"WebSocket disconnected for call {call_id}")
    
    async def send_message(self, call_id: str, message: dict):
        """Send message through WebSocket."""
        if call_id in self.active_connections:
            await self.active_connections[call_id].send_json(message)
    
    def get_agent(self, call_id: str) -> CustomerSupportAgent:
        """Get or create agent for call."""
        return self.active_agents.get(call_id)
    
    def set_agent(self, call_id: str, agent: CustomerSupportAgent):
        """Store agent for call."""
        self.active_agents[call_id] = agent


manager = ConnectionManager()


@router.post("/call/start")
async def start_call():
    """
    Start a new customer support call.
    
    Returns:
        Call information including ID and WebSocket URL
    """
    try:
        settings = await db.get_settings()
        call = await db.create_call(model_name=settings.model_name)
        logger.info(f"Started new call: {call.id} with model {settings.model_name}")
        
        return {
            "call_id": call.id,
            "status": call.status,
            "websocket_url": f"/ws/call/{call.id}"
        }
    
    except Exception as e:
        logger.error(f"Error starting call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/call/{call_id}")
async def websocket_call_endpoint(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for real-time voice conversation.
    
    Message format:
    - Client -> Server: {"type": "audio", "data": "<base64_audio>"}
    - Server -> Client: {"type": "transcription", "text": "..."}
    - Server -> Client: {"type": "response", "text": "..."}
    - Server -> Client: {"type": "audio", "data": "<base64_audio>"}
    - Server -> Client: {"type": "error", "message": "..."}
    """
    await manager.connect(call_id, websocket)
    
    websocket_disconnected = False
    
    try:
        call = await db.get_call(call_id)
        if not call:
            await websocket.send_json({
                "type": "error",
                "message": f"Call {call_id} not found"
            })
            await websocket.close()
            return
        
        settings = await db.get_settings()
        
        # Update call with model name
        call.model_name = settings.model_name
        await db.update_call(call)
        
        agent = CustomerSupportAgent(
            model=settings.model_name,
            temperature=settings.temperature,
            information_to_gather=[
                {"title": info.title, "description": info.description}
                for info in settings.information_to_gather
            ]
        )
        manager.set_agent(call_id, agent)
        
        # Try to use precomputed greeting first
        greeting_data = precomputed_audio_manager.get_greeting()
        
        if greeting_data:
            # Use precomputed greeting
            greeting = greeting_data["text"]
            audio_data = greeting_data["audio"]
            
            message = Message(
                role="assistant",
                content=greeting,
                timestamp=datetime.now().isoformat()
            )
            await db.add_message_to_call(call_id, message)
            
            await websocket.send_json({
                "type": "response",
                "text": greeting
            })
            
            # Send precomputed audio
            await websocket.send_json({
                "type": "audio",
                "data": base64.b64encode(audio_data).decode('utf-8')
            })
            
            call.usage_stats.tts_characters += len(greeting)
            # Calculate TTS cost: (chars / 10000) * price_per_10k
            call.cost_stats.tts_cost += (len(greeting) / 10000) * settings.price_per_10k_tts_chars
            await db.update_call(call)
            
            logger.info(f"Used precomputed greeting for call {call_id}")
        else:
            # Fallback to generating greeting
            greeting = await agent.get_greeting()
            
            message = Message(
                role="assistant",
                content=greeting,
                timestamp=datetime.now().isoformat()
            )
            await db.add_message_to_call(call_id, message)
            
            await websocket.send_json({
                "type": "response",
                "text": greeting
            })
            
            try:
                audio_data = await text_to_speech_stream(greeting)
                await websocket.send_json({
                    "type": "audio",
                    "data": base64.b64encode(audio_data).decode('utf-8')
                })
                
                call.usage_stats.tts_characters += len(greeting)
                call.cost_stats.tts_cost += len(greeting) * 0.00003
                await db.update_call(call)
            
            except Exception as e:
                logger.error(f"TTS error for greeting: {e}")
        
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "audio":
                    audio_base64 = data.get("data")
                    if not audio_base64:
                        continue
                    
                    try:
                        audio_bytes = base64.b64decode(audio_base64)
                        
                        transcription = await transcribe_audio_stream(audio_bytes)
                        
                        if not transcription or not transcription.strip():
                            continue
                        
                        await websocket.send_json({
                            "type": "transcription",
                            "text": transcription
                        })
                        
                        user_message = Message(
                            role="user",
                            content=transcription,
                            timestamp=datetime.now().isoformat()
                        )
                        await db.add_message_to_call(call_id, user_message)
                        
                        call = await db.get_call(call_id)
                        call.usage_stats.input_characters += len(transcription)
                        call.usage_stats.transcription_seconds += len(audio_bytes) / 16000
                        # Calculate transcription cost: (seconds / 5) * price_per_5s
                        call.cost_stats.transcription_cost += ((len(audio_bytes) / 16000) / 5) * settings.price_per_5s_transcription
                        await db.update_call(call)
                        
                        # Get random acknowledgment and wait 1 second before sending
                        ack_data = precomputed_audio_manager.get_random_acknowledgment()
                        
                        # Wait 1 second for a more natural conversation flow
                        await asyncio.sleep(1.0)
                        
                        # Send acknowledgment audio after delay
                        if ack_data["audio"]:
                            await websocket.send_json({
                                "type": "acknowledgment",
                                "text": ack_data["text"],
                                "data": base64.b64encode(ack_data["audio"]).decode('utf-8')
                            })
                            logger.info(f"Sent precomputed acknowledgment: {ack_data['text']}")
                        else:
                            # Generate acknowledgment audio on-the-fly
                            try:
                                ack_audio = await text_to_speech_stream(ack_data["text"])
                                if ack_audio:
                                    await websocket.send_json({
                                        "type": "acknowledgment",
                                        "text": ack_data["text"],
                                        "data": base64.b64encode(ack_audio).decode('utf-8')
                                    })
                                    # Save for future use
                                    precomputed_audio_manager.save_acknowledgment_audio(ack_data["text"], ack_audio)
                                    logger.info(f"Generated and sent acknowledgment: {ack_data['text']}")
                            except Exception as e:
                                logger.error(f"Error generating acknowledgment: {e}")
                        
                        # Process message with acknowledgment context
                        response_text = ""
                        first_chunk_latency_ms = None
                        total_latency_ms = None
                        async for chunk_data in agent.process_message(transcription, ack_data["text"]):
                            chunk, first_latency, total_latency = chunk_data
                            if first_latency is not None:
                                first_chunk_latency_ms = first_latency
                            if total_latency is not None:
                                total_latency_ms = total_latency
                            if chunk:  # Only send non-empty chunks
                                response_text += chunk
                                await websocket.send_json({
                                    "type": "response_chunk",
                                    "text": chunk
                                })
                        
                        await websocket.send_json({
                            "type": "response",
                            "text": response_text
                        })
                        
                        assistant_message = Message(
                            role="assistant",
                            content=response_text,
                            timestamp=datetime.now().isoformat()
                        )
                        await db.add_message_to_call(call_id, assistant_message)
                        
                        call = await db.get_call(call_id)
                        call.usage_stats.output_characters += len(response_text)
                        call.usage_stats.llm_calls += 1
                        
                        # Store latency for this call (use total latency for better accuracy)
                        if total_latency_ms:
                            call.usage_stats.llm_latency_ms += total_latency_ms
                        
                        # Use configured token estimation
                        estimated_output_tokens = len(response_text) // settings.estimated_token_length
                        call.usage_stats.output_tokens += estimated_output_tokens
                        
                        # Calculate LLM output cost: (tokens / 1M) * price_per_million
                        call.cost_stats.llm_output_cost += (estimated_output_tokens / 1_000_000) * settings.price_per_million_output_tokens
                        
                        # Also add input cost based on input characters
                        estimated_input_tokens = len(transcription) // settings.estimated_token_length
                        call.usage_stats.input_tokens += estimated_input_tokens
                        call.cost_stats.llm_input_cost += (estimated_input_tokens / 1_000_000) * settings.price_per_million_input_tokens
                        
                        # Update conversation summary if available (for long-short term memory)
                        conversation_summary = agent.get_conversation_summary()
                        if conversation_summary:
                            call.conversation_summary = conversation_summary
                        
                        await db.update_call(call)
                        
                        try:
                            audio_data = await text_to_speech_stream(response_text)
                            await websocket.send_json({
                                "type": "audio",
                                "data": base64.b64encode(audio_data).decode('utf-8')
                            })
                            
                            call = await db.get_call(call_id)
                            call.usage_stats.tts_characters += len(response_text)
                            # Calculate TTS cost: (chars / 10000) * price_per_10k
                            call.cost_stats.tts_cost += (len(response_text) / 10000) * settings.price_per_10k_tts_chars
                            await db.update_call(call)
                        
                        except Exception as e:
                            logger.error(f"TTS error: {e}")
                    
                    except Exception as e:
                        logger.error(f"Error processing audio: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Error processing audio"
                        })
                
                elif data.get("type") == "end_call":
                    logger.info(f"Call {call_id} ended by client")
                    break
            
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for call {call_id}")
                websocket_disconnected = True
                break
            
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except:
                    # Websocket already closed
                    websocket_disconnected = True
                    break
        
        agent = manager.get_agent(call_id)
        if agent:
            try:
                summary = await agent.generate_summary()
                title = await agent.generate_call_title()
                
                call = await db.get_call(call_id)
                call.summary = summary
                call.title = title
                await db.update_call(call)
            
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
        
        await db.update_call_status(call_id, CallStatus.COMPLETED)
        
        call = await db.get_call(call_id)
        call.cost_stats.total_cost = (
            call.cost_stats.llm_input_cost +
            call.cost_stats.llm_output_cost +
            call.cost_stats.transcription_cost +
            call.cost_stats.tts_cost
        )
        await db.update_call(call)
        
        await db.update_stats(
            usage_delta=call.usage_stats,
            cost_delta=call.cost_stats,
            model_name=call.model_name,
            call_tokens=call.usage_stats.input_tokens + call.usage_stats.output_tokens,
            call_latency_ms=call.usage_stats.llm_latency_ms
        )
    
    except WebSocketDisconnect:
        # User hung up - this is normal, not an error
        logger.info(f"User hung up call {call_id}")
        websocket_disconnected = True
    
    except Exception as e:
        logger.error(f"Fatal error in WebSocket: {e}")
        # Only mark as ERROR if websocket is still connected (real error, not user hangup)
        if not websocket_disconnected:
            await db.update_call_status(call_id, CallStatus.ERROR, str(e))
        else:
            logger.info(f"Error occurred after disconnect for call {call_id}, not marking as ERROR")
    
    finally:
        manager.disconnect(call_id)


@router.get("/call/{call_id}")
async def get_call(call_id: str):
    """
    Get call details.
    
    Args:
        call_id: Call ID
    
    Returns:
        Call information
    """
    try:
        call = await db.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return call
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call: {e}")
        raise HTTPException(status_code=500, detail=str(e))
