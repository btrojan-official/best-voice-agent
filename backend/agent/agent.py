import os
import json
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from datetime import datetime
import logging

from llama_index.core import Settings
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.openrouter import OpenRouter

from .prompts import SYSTEM_PROMPT, GREETING_PROMPT, SUMMARY_PROMPT, CALL_TITLE_PROMPT
from .tools import CustomerSupportTools, get_available_tools

logger = logging.getLogger(__name__)


class CustomerSupportAgent:
    """
    Async customer support agent optimized for real-time voice conversations.
    Uses LlamaIndex with OpenRouter for low-latency streaming responses.
    """
    
    def __init__(
        self,
        model: str = "anthropic/claude-3.5-sonnet",
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
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.llm = OpenRouter(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=512
        )
        
        Settings.llm = self.llm
        
        info_text = "\n".join([
            f"- {item['title']}: {item['description']}"
            for item in self.information_to_gather
        ]) if self.information_to_gather else "- Understand customer's needs and issues"
        
        system_prompt = SYSTEM_PROMPT.format(information_to_gather=info_text)
        self.conversation_history.append(
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)
        )
    
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
    
    async def process_message(self, user_message: str, acknowledgment: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Process user message and stream response.
        
        Args:
            user_message: User's transcribed message
            acknowledgment: Optional acknowledgment phrase that was played (e.g., "Hmm...")
        
        Yields:
            Response text chunks
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
            
            response_stream = await self.llm.astream_chat(self.conversation_history)
            
            full_response = ""
            async for chunk in response_stream:
                if chunk.delta:
                    full_response += chunk.delta
                    yield chunk.delta
            
            # Update the last assistant message with full response
            # Remove the acknowledgment-only message if it exists
            if acknowledgment:
                self.conversation_history.pop()  # Remove acknowledgment
            
            self.conversation_history.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=full_response)
            )
            
            logger.info(f"Generated response: {full_response}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = "I apologize, but I'm having trouble processing that. Could you please repeat?"
            self.conversation_history.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=error_response)
            )
            yield error_response
    
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
