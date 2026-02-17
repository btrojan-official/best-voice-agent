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
        model: str = "openai/gpt-oss-120b",
        temperature: float = 0.7,
        information_to_gather: Optional[List[Dict[str, str]]] = None
    ):
        self.model = model
        self.temperature = temperature
        self.information_to_gather = information_to_gather or []
        self.conversation_history: List[ChatMessage] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.tools = CustomerSupportTools()
        
        # Long-short term memory management
        self.conversation_summary: Optional[str] = None
        self.last_summary_point: int = 0  # Index in history where last summary was created
        self.summary_threshold: int = 20  # Create/update summary every 20 non-summarized messages
        self.keep_recent_messages: int = 4  # Always keep last 4 messages in full
        
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
        
        # Build system prompt with information to gather and current status
        self._update_system_prompt()
    
    def _update_system_prompt(self):
        """Update the system prompt with current gathered data status."""
        info_text = "\n".join([
            f"- {item['title']}: {item['description']}"
            for item in self.information_to_gather
        ]) if self.information_to_gather else "- order_id, customer_name, customer_surname, issue_type, issue_description"
        
        # Build gathered data status
        gathered_data = self.tools.get_gathered_information()
        if gathered_data:
            status_lines = []
            for field in self.information_to_gather:
                field_title = field['title']
                if field_title in gathered_data:
                    status_lines.append(f"✓ {field_title}: {gathered_data[field_title]}")
                else:
                    status_lines.append(f"✗ {field_title}: NOT YET GATHERED")
            gathered_data_status = "\n".join(status_lines)
        else:
            gathered_data_status = "No data gathered yet. Start gathering information from the customer."
        
        # Get current date and time
        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        system_prompt = SYSTEM_PROMPT.format(
            current_datetime=current_datetime,
            information_to_gather=info_text,
            gathered_data_status=gathered_data_status
        )
        
        # Update or add system prompt
        if self.conversation_history and self.conversation_history[0].role == MessageRole.SYSTEM:
            self.conversation_history[0] = ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)
        else:
            self.conversation_history.insert(0, ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))
    
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
    
    async def process_message(self, user_message: str, acknowledgment: Optional[str] = None) -> AsyncGenerator[Tuple[str, Optional[float], Optional[float], Optional[Dict[str, int]]], None]:
        """
        Process user message and stream response.
        
        Args:
            user_message: User's transcribed message
            acknowledgment: Optional acknowledgment phrase that was played (e.g., "Hmm...")
        
        Yields:
            Tuple of (response text chunk, first_chunk_latency_ms, total_latency_ms, usage_dict)
            - first_chunk_latency_ms: only returned on first chunk (time to first token)
            - total_latency_ms: only returned on last chunk (total generation time)
            - usage_dict: only returned on last chunk, contains actual token counts {'prompt_tokens': int, 'completion_tokens': int, 'total_tokens': int}
        """
        try:
            self.conversation_history.append(
                ChatMessage(role=MessageRole.USER, content=user_message)
            )
            
            # Note: We do NOT add acknowledgment to history
            # Acknowledgments are just filler phrases while the model thinks
            # They should not influence the model's response
            
            logger.info(f"Processing user message: {user_message}")
            if acknowledgment:
                logger.info(f"Acknowledgment was played: {acknowledgment}")
            
            # Update memory management (summarize if needed)
            await self._update_memory()
            
            # Update system prompt with current gathered data status
            self._update_system_prompt()
            
            # Use condensed history for LLM to save tokens
            history_to_use = self._get_condensed_history()
            logger.info(f"Using {len(history_to_use)} messages (condensed from {len(self.conversation_history)})")
            
            start_time = time.time()
            
            # Track token usage
            usage_data = None
            
            # Use chat with tools for function calling
            try:
                response = await self.llm.achat(
                    messages=history_to_use,
                    tools=get_available_tools()
                )
                
                logger.info("Raw response:")
                logger.info(response.raw)
                
                if hasattr(response.raw, 'usage'):
                    usage = response.raw.usage
                    usage_data = {
                        'prompt_tokens': usage.prompt_tokens,
                        'completion_tokens': usage.completion_tokens,
                        'total_tokens': usage.total_tokens
                    }
                    logger.info(f"Token usage: {usage_data}")

                tool_calls_made = []
                logger.info(response.raw.choices[0].message.tool_calls or [])
                if hasattr(response.raw.choices[0].message, 'tool_calls') and response.raw.choices[0].message.tool_calls:
                    logger.info(f"Tool call!!!!!!!!!!!")
                    tool_calls = response.raw.choices[0].message.tool_calls
                    
                    for tool_call in tool_calls:
                        if tool_call.type == 'function':
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)
                            
                            logger.info(f"Tool call: {function_name} with args: {function_args}")
                            
                            # Execute the tool
                            if function_name == "save_gathered_data":
                                result = self.tools.save_gathered_data(function_args.get('data_fields', {}))
                                tool_calls_made.append({
                                    "tool": function_name,
                                    "args": function_args,
                                    "result": result,
                                    "timestamp": datetime.now().isoformat()
                                })
                                self.tool_calls.append(tool_calls_made[-1])
                
                full_response = response.message.content if hasattr(response, 'message') and response.message.content else ""
                
                if (not full_response or full_response.strip() == "") and tool_calls_made:
                    logger.info("Tool was used but model didn't provide a text response. Querying model again with tool results.")
                    
                    tool_results_summary = []
                    for tool_call in tool_calls_made:
                        tool_results_summary.append(f"Tool '{tool_call['tool']}' was executed successfully with data: {tool_call['args']}")
                    
                    tool_info_message = (
                        "You just used tools successfully: " + "; ".join(tool_results_summary) + 
                        ". Now continue the conversation naturally with the customer. "
                        "Acknowledge what was saved and ask for the next piece of information if needed."
                    )
                    
                    self.conversation_history.append(
                        ChatMessage(role=MessageRole.SYSTEM, content=tool_info_message)
                    )
                    
                    history_for_followup = self._get_condensed_history()
                    followup_response = await self.llm.achat(
                        messages=history_for_followup,
                        tools=get_available_tools()
                    )
                    
                    if hasattr(followup_response.raw, 'usage'):
                        followup_usage = followup_response.raw.usage
                        if usage_data:
                            usage_data['prompt_tokens'] += followup_usage.prompt_tokens
                            usage_data['completion_tokens'] += followup_usage.completion_tokens
                            usage_data['total_tokens'] += followup_usage.total_tokens
                        else:
                            usage_data = {
                                'prompt_tokens': followup_usage.prompt_tokens,
                                'completion_tokens': followup_usage.completion_tokens,
                                'total_tokens': followup_usage.total_tokens
                            }
                        logger.info(f"Updated token usage after followup: {usage_data}")
                    
                    full_response = followup_response.message.content if hasattr(followup_response, 'message') and followup_response.message.content else ""
                    
                    self.conversation_history.pop()
                    
                    if not full_response or full_response.strip() == "":
                        logger.warning("Model still didn't provide a message after followup query.")
                        full_response = "I've recorded that information. What else can I help you with?"
                
            except Exception as e:
                logger.warning(f"Tool calling not supported or error: {e}, falling back to streaming")
                # Fallback to streaming without tools
                response_stream = await self.llm.astream_chat(history_to_use)
                
                full_response = ""
                chunk_count = 0
                first_chunk_time = None
                
                async for chunk in response_stream:
                    if chunk.delta:
                        if first_chunk_time is None:
                            first_chunk_time = time.time()
                        full_response += chunk.delta
                        chunk_count += 1
                        if chunk_count == 1 and first_chunk_time:
                            yield chunk.delta, (first_chunk_time - start_time) * 1000, None, None
                        else:
                            yield chunk.delta, None, None, None
            
            end_time = time.time()
            total_latency_ms = (end_time - start_time) * 1000
            
            if full_response:
                first_chunk_latency_ms = total_latency_ms
                yield full_response, first_chunk_latency_ms, None, None
            
            logger.info(f"Response generated in {total_latency_ms:.0f}ms")
            logger.info(f"Full output: {full_response}")
            if tool_calls_made:
                logger.info(f"Tool calls made: {len(tool_calls_made)}")
            
            self.conversation_history.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=full_response)
            )
            
            yield "", None, total_latency_ms, usage_data
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = "I apologize, but I'm having trouble processing that. Could you please repeat?"
            self.conversation_history.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=error_response)
            )
            yield error_response, None, None, None
    
    async def _generate_conversation_summary(self, messages_to_summarize: List[ChatMessage]) -> str:
        """
        Generate summary of specific messages for long-short term memory.
        
        Args:
            messages_to_summarize: Messages to include in summary
            
        Returns:
            Summary text
        """
        try:
            # If we have a previous summary, include it in the prompt
            summary_context = ""
            if self.conversation_summary:
                summary_context = f"Previous conversation summary:\n{self.conversation_summary}\n\nContinuation of the conversation:\n"
            else:
                summary_context = "Conversation to summarize:\n"
            
            conversation_text = "\n".join([
                f"{msg.role.value}: {msg.content}"
                for msg in messages_to_summarize
                if msg.role != MessageRole.SYSTEM
            ])
            
            prompt = f"""{summary_context}{conversation_text}

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
        Returns: system prompt + summary (if exists) + last N messages
        
        Returns:
            Condensed list of ChatMessages
        """
        condensed = [self.conversation_history[0]]
        
        if self.conversation_summary:
            condensed.append(
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=f"[Previous conversation summary: {self.conversation_summary}]"
                )
            )
        
        all_messages_except_system = self.conversation_history[1:]
        if all_messages_except_system:
            recent_messages = all_messages_except_system[-self.keep_recent_messages:]
            condensed.extend(recent_messages)
        
        return condensed
    
    async def _update_memory(self) -> None:
        """
        Update long-short term memory if needed.
        Every 20 non-summarized messages, summarize oldest 16 and keep last 4.
        """
        all_messages_except_system = self.conversation_history[1:]
        non_summarized_messages = all_messages_except_system[self.last_summary_point:]
        
        non_summarized_count = len(non_summarized_messages)
        
        if non_summarized_count >= self.summary_threshold:
            logger.info(f"Reached {non_summarized_count} non-summarized messages, creating/updating summary")
            
            messages_to_summarize_count = non_summarized_count - self.keep_recent_messages
            
            if messages_to_summarize_count > 0:
                start_idx = 1 + self.last_summary_point
                end_idx = start_idx + messages_to_summarize_count
                messages_to_summarize = self.conversation_history[start_idx:end_idx]
                
                self.conversation_summary = await self._generate_conversation_summary(messages_to_summarize)
                
                self.last_summary_point += messages_to_summarize_count
                
                logger.info(f"Summarized {messages_to_summarize_count} messages, new summary point at index {self.last_summary_point}")
    
    def get_conversation_summary(self) -> Optional[str]:
        """
        Get the current running conversation summary.
        
        Returns:
            Current conversation summary or None
        """
        return self.conversation_summary
    
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
    
    def get_gathered_information(self) -> Dict[str, str]:
        """
        Get all gathered information from customer.
        
        Returns:
            Dictionary of gathered information
        """
        return self.tools.get_gathered_information()
