import os
import json
import asyncio
import time
from typing import List, Dict, Any, AsyncGenerator, Optional, Tuple
from datetime import datetime
import logging

from llama_index.core import Settings
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.openrouter import OpenRouter
from llama_index.llms.groq import Groq

from .prompts import SYSTEM_PROMPT, GREETING_PROMPT, SUMMARY_PROMPT, CALL_TITLE_PROMPT
from .tools import CustomerSupportTools, get_available_tools

logger = logging.getLogger(__name__)


class CustomerSupportAgent:
    """
    Async customer support agent optimized for real-time voice conversations.
    Supports both OpenRouter and Groq for low-latency streaming responses.
    """
    
    # Known Groq models for auto-detection
    GROQ_MODELS = {
        "llama-3.3-70b-versatile",
        "moonshotai/kimi-k2-instruct-0905",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3.2-1b-preview",
        "llama-3.2-3b-preview",
        "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-preview",
        "mixtral-8x7b-32768",
        "gemma-7b-it",
        "gemma2-9b-it",
        "openai/gpt-oss-120b",
    }
    
    def __init__(
        self,
        model: str = "moonshotai/kimi-k2-instruct-0905",
        temperature: float = 0.7,
        information_to_gather: Optional[List[Dict[str, str]]] = None
    ):
        self.model = model
        self.temperature = temperature
        self.information_to_gather = information_to_gather or []
        self.conversation_history: List[ChatMessage] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.gathered_information: Dict[str, Any] = {}
        self.tools = CustomerSupportTools()
        
        # Long-short term memory management
        self.conversation_summary: Optional[str] = None
        self.messages_since_last_summary: int = 0
        self.summary_threshold: int = 20  # Start summarizing after 20 messages
        self.summary_update_interval: int = 4  # Update summary every 4 messages
        self.keep_recent_messages: int = 4  # Keep last 4 messages in full
        
        # Determine which provider to use based on model name
        use_groq = self._is_groq_model(model)
        
        if use_groq:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            
            self.llm = Groq(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=512
            )
            logger.info(f"Initialized Groq LLM with model: {model}")
        else:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            
            self.llm = OpenRouter(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=512
            )
            logger.info(f"Initialized OpenRouter LLM with model: {model}")
        
        Settings.llm = self.llm
        
        info_text = "\n".join([
            f"- {item['title']}: {item['description']}"
            for item in self.information_to_gather
        ]) if self.information_to_gather else "- Understand customer's needs and issues"
        
        system_prompt = SYSTEM_PROMPT.format(information_to_gather=info_text)
        self.conversation_history.append(
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)
        )
    
    def _is_groq_model(self, model: str) -> bool:
        """
        Determine if the model should use Groq provider.
        
        Args:
            model: Model name
            
        Returns:
            True if model should use Groq, False for OpenRouter
        """
        return model in self.GROQ_MODELS
    
    async def get_greeting(self) -> str:
        """
        Generate initial greeting for the customer.
        
        Returns:
            Greeting message
        """
        try:
            response = await self.llm.acomplete(GREETING_PROMPT)
            greeting = response.text.strip()
            
            self.conversation_history.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=greeting)
            )
            
            logger.info(f"Generated greeting: {greeting}")
            return greeting
        
        except Exception as e:
            logger.error(f"Error generating greeting: {e}")
            fallback = "Hello! Thank you for contacting customer support. How can I help you today?"
            self.conversation_history.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=fallback)
            )
            return fallback
    
    async def process_message(self, user_message: str, acknowledgment: Optional[str] = None) -> AsyncGenerator[Tuple[str, Optional[float], Optional[float]], None]:
        """
        Process user message and stream response.
        
        Args:
            user_message: User's transcribed message
            acknowledgment: Optional acknowledgment phrase that was played (e.g., "Hmm...")
        
        Yields:
            Tuple of (response text chunk, first_chunk_latency_ms, total_latency_ms)
            - first_chunk_latency_ms: only returned on first chunk (time to first token)
            - total_latency_ms: only returned on last chunk (total generation time)
        """
        try:
            self.conversation_history.append(
                ChatMessage(role=MessageRole.USER, content=user_message)
            )
            
            # If an acknowledgment was used, add it as assistant message for context
            if acknowledgment:
                self.conversation_history.append(
                    ChatMessage(role=MessageRole.ASSISTANT, content=acknowledgment)
                )
            
            logger.info(f"Processing user message: {user_message}")
            if acknowledgment:
                logger.info(f"With acknowledgment: {acknowledgment}")
            
            # Update memory management (summarize if needed)
            await self._update_memory()
            
            # Use condensed history for LLM to save tokens and improve context management
            condensed_history = self._get_condensed_history()
            
            logger.info(f"Using {len(condensed_history)} messages (condensed from {len(self.conversation_history)})")
            
            start_time = time.time()
            response_stream = await self.llm.astream_chat(condensed_history)
            
            full_response = ""
            chunk_count = 0
            first_chunk_time = None
            
            async for chunk in response_stream:
                if chunk.delta:
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                    full_response += chunk.delta
                    chunk_count += 1
                    # Only send first chunk latency with first chunk
                    if chunk_count == 1 and first_chunk_time:
                        yield chunk.delta, (first_chunk_time - start_time) * 1000, None
                    else:
                        yield chunk.delta, None, None
            
            end_time = time.time()
            total_latency_ms = (end_time - start_time) * 1000
            
            # Log the complete response received from OpenRouter
            logger.info(f"OpenRouter Response - {chunk_count} chunks in {total_latency_ms:.0f}ms")
            logger.info(f"Full output: {full_response}")
            
            # Update the last assistant message with full response
            # Remove the acknowledgment-only message if it exists
            if acknowledgment:
                self.conversation_history.pop()  # Remove acknowledgment
            
            self.conversation_history.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=full_response)
            )
            
            # Track messages since last summary update
            self.messages_since_last_summary += 2  # User message + assistant response
            
            # Send final marker with total latency
            yield "", None, total_latency_ms
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = "I apologize, but I'm having trouble processing that. Could you please repeat?"
            self.conversation_history.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=error_response)
            )
            yield error_response, None, None
    
    async def generate_summary(self) -> str:
        """
        Generate conversation summary.
        
        Returns:
            Summary of the conversation
        """
        try:
            conversation_text = "\n".join([
                f"{msg.role.value}: {msg.content}"
                for msg in self.conversation_history
                if msg.role != MessageRole.SYSTEM
            ])
            
            prompt = SUMMARY_PROMPT.format(conversation=conversation_text)
            response = await self.llm.acomplete(prompt)
            summary = response.text.strip()
            
            logger.info("Generated conversation summary")
            return summary
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Error generating summary"
    
    async def _generate_conversation_summary(self) -> str:
        """
        Generate a running summary of the conversation for long-short term memory.
        This is called when conversation exceeds threshold or needs updating.
        
        Returns:
            Summary of the conversation context
        """
        try:
            # Get messages excluding system and recent ones
            messages_to_summarize = self.conversation_history[1:-self.keep_recent_messages]  # Skip system prompt
            
            if not messages_to_summarize:
                return ""
            
            # If we already have a summary, include it in the context
            summary_prompt = ""
            if self.conversation_summary:
                summary_prompt = f"Previous conversation summary:\n{self.conversation_summary}\n\nContinuation of the conversation:\n"
            else:
                summary_prompt = "Conversation to summarize:\n"
            
            conversation_text = "\n".join([
                f"{msg.role.value}: {msg.content}"
                for msg in messages_to_summarize
                if msg.role != MessageRole.SYSTEM
            ])
            
            prompt = f"""{summary_prompt}{conversation_text}

Please provide a concise summary of the key points, customer issues, and resolution status from the above conversation. Focus on actionable information and important context."""
            
            response = await self.llm.acomplete(prompt)
            summary = response.text.strip()
            
            logger.info(f"Generated running conversation summary ({len(messages_to_summarize)} messages)")
            return summary
        
        except Exception as e:
            logger.error(f"Error generating running summary: {e}")
            return self.conversation_summary or ""
    
    def _get_condensed_history(self) -> List[ChatMessage]:
        """
        Get condensed conversation history using long-short term memory.
        Returns: system prompt + summary message + last N messages
        
        Returns:
            Condensed list of ChatMessages
        """
        # Always include system prompt
        condensed = [self.conversation_history[0]]
        
        # If we have a summary, add it as a system-like message
        if self.conversation_summary:
            condensed.append(
                ChatMessage(
                    role=MessageRole.SYSTEM, 
                    content=f"[Previous conversation summary: {self.conversation_summary}]"
                )
            )
        
        # Add recent messages
        if len(self.conversation_history) > 1:
            recent_messages = self.conversation_history[-self.keep_recent_messages:]
            condensed.extend(recent_messages)
        
        return condensed
    
    async def _update_memory(self) -> None:
        """
        Update long-short term memory if needed.
        Checks if summary needs to be created or updated based on message count.
        """
        # Count actual conversation messages (user + assistant only)
        non_system_count = len([
            msg for msg in self.conversation_history
            if msg.role in [MessageRole.USER, MessageRole.ASSISTANT]
        ])
        
        # Check if we need to create or update summary
        should_summarize = False
        
        if non_system_count >= self.summary_threshold and self.conversation_summary is None:
            # First time reaching threshold - create initial summary
            should_summarize = True
            logger.info(f"Reached {non_system_count} messages, creating initial summary")
        elif self.conversation_summary is not None and self.messages_since_last_summary >= self.summary_update_interval:
            # Update existing summary
            should_summarize = True
            logger.info(f"Updating summary after {self.messages_since_last_summary} new messages")
        
        if should_summarize:
            self.conversation_summary = await self._generate_conversation_summary()
            self.messages_since_last_summary = 0
    
    async def generate_call_title(self) -> str:
        """
        Generate a short title for the call.
        
        Returns:
            Call title
        """
        try:
            conversation_text = "\n".join([
                f"{msg.role.value}: {msg.content}"
                for msg in self.conversation_history
                if msg.role != MessageRole.SYSTEM
            ])[:500]
            
            prompt = CALL_TITLE_PROMPT.format(conversation=conversation_text)
            response = await self.llm.acomplete(prompt)
            title = response.text.strip().strip('"').strip("'")
            
            logger.info(f"Generated call title: {title}")
            return title
        
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "Customer Support Call"
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history in serializable format.
        
        Returns:
            List of message dictionaries
        """
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": datetime.now().isoformat()
            }
            for msg in self.conversation_history
            if msg.role != MessageRole.SYSTEM
        ]
    
    def get_conversation_summary(self) -> Optional[str]:
        """
        Get the current running conversation summary for long-short term memory.
        
        Returns:
            Current conversation summary or None
        """
        return self.conversation_summary
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get conversation statistics.
        
        Returns:
            Statistics dictionary
        """
        total_messages = len([
            msg for msg in self.conversation_history
            if msg.role != MessageRole.SYSTEM
        ])
        
        user_messages = len([
            msg for msg in self.conversation_history
            if msg.role == MessageRole.USER
        ])
        
        assistant_messages = len([
            msg for msg in self.conversation_history
            if msg.role == MessageRole.ASSISTANT
        ])
        
        total_chars = sum([
            len(msg.content)
            for msg in self.conversation_history
            if msg.role != MessageRole.SYSTEM
        ])
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "total_characters": total_chars,
            "tool_calls": len(self.tool_calls)
        }
