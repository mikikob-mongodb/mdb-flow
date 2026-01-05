"""LLM service using Claude API (Anthropic)."""

from typing import List, Dict, Any, Optional
from anthropic import Anthropic

from shared.config import settings
from shared.logger import get_logger

logger = get_logger("llm")


class LLMService:
    """Service for interacting with Claude API."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize the LLM service.

        Args:
            model: Claude model to use (default: claude-sonnet-4-5-20250929)
        """
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = model

    def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """
        Generate a response from Claude.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters to pass to the API

        Returns:
            Generated text response
        """
        logger.debug(f"LLM generate: {len(messages)} message(s), max_tokens={max_tokens}, temp={temperature}")
        if messages:
            logger.debug(f"Last message preview: {messages[-1]['content'][:100]}...")

        # Strip non-API fields from messages (e.g., input_type)
        clean_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

        params = {
            "model": self.model,
            "messages": clean_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        if system:
            params["system"] = system

        logger.debug(f"Calling Anthropic API with model={self.model}")
        response = self.client.messages.create(**params)
        response_text = response.content[0].text
        logger.debug(f"LLM response preview: {response_text[:200]}...")
        return response_text

    def chat(
        self,
        user_message: str,
        system: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """
        Send a chat message and get a response.

        Args:
            user_message: User's message
            system: Optional system prompt
            conversation_history: Optional conversation history
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters to pass to the API

        Returns:
            Claude's response
        """
        messages = conversation_history.copy() if conversation_history else []
        messages.append({"role": "user", "content": user_message})

        return self.generate(
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

    def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        cache_prompts: bool = True,
        **kwargs
    ) -> Any:
        """
        Generate a response with tool use support.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: List of tool definitions
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            cache_prompts: Enable prompt caching for system and tools (default: True)
            **kwargs: Additional parameters to pass to the API

        Returns:
            Full API response object with tool calls
        """
        # Strip non-API fields from messages (e.g., input_type)
        clean_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

        params = {
            "model": self.model,
            "messages": clean_messages,
            "tools": tools,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        if system:
            if cache_prompts:
                # Use prompt caching - structure system as list with cache control
                params["system"] = [
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
                # Add beta header for prompt caching API
                params["extra_headers"] = {"anthropic-beta": "prompt-caching-2024-07-31"}
            else:
                params["system"] = system

        response = self.client.messages.create(**params)

        # Log cache performance
        if cache_prompts and system and hasattr(response, 'usage'):
            cache_read = getattr(response.usage, 'cache_read_input_tokens', 0)
            cache_creation = getattr(response.usage, 'cache_creation_input_tokens', 0)
            if cache_read > 0:
                logger.info(f"💾 Cache HIT: {cache_read} tokens from cache")
            elif cache_creation > 0:
                logger.info(f"💾 Cache MISS: {cache_creation} tokens cached for next call")

        return response


# Global LLM service instance
llm_service = LLMService()


def generate(
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    **kwargs
) -> str:
    """
    Generate a response from Claude.

    Args:
        messages: List of message dicts with 'role' and 'content'
        system: Optional system prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        **kwargs: Additional parameters to pass to the API

    Returns:
        Generated text response
    """
    return llm_service.generate(
        messages=messages,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )


def chat(
    user_message: str,
    system: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    **kwargs
) -> str:
    """
    Send a chat message and get a response.

    Args:
        user_message: User's message
        system: Optional system prompt
        conversation_history: Optional conversation history
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        **kwargs: Additional parameters to pass to the API

    Returns:
        Claude's response
    """
    return llm_service.chat(
        user_message=user_message,
        system=system,
        conversation_history=conversation_history,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )
