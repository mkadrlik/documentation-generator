"""AI client for generating documentation"""

import asyncio
from typing import Optional
import openai
import anthropic

from utils.logger import setup_logger
from utils.metrics import get_metrics

logger = setup_logger(__name__)

class AIClient:
    """Client for AI providers"""
    
    def __init__(self, config):
        self.config = config
        self._openai_client = None
        self._anthropic_client = None
        self._openrouter_client = None
        self.metrics = get_metrics(config)
    
    def _get_openai_client(self):
        """Get OpenAI client"""
        if not self._openai_client:
            if not self.config.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self._openai_client = openai.AsyncOpenAI(api_key=self.config.openai_api_key)
        return self._openai_client
    
    def _get_anthropic_client(self):
        """Get Anthropic client"""
        if not self._anthropic_client:
            if not self.config.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self._anthropic_client = anthropic.AsyncAnthropic(api_key=self.config.anthropic_api_key)
        return self._anthropic_client
    
    def _get_openrouter_client(self):
        """Get OpenRouter client (uses OpenAI-compatible API)"""
        if not self._openrouter_client:
            if not self.config.openrouter_api_key:
                raise ValueError("OpenRouter API key not configured")
            self._openrouter_client = openai.AsyncOpenAI(
                api_key=self.config.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        return self._openrouter_client
    
    async def generate_text(
        self,
        prompt: str,
        provider: str = None,
        model: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> str:
        """Generate text using specified AI provider"""
        
        # Use config defaults if not provided
        provider = provider or self.config.default_ai_provider
        model = model or self.config.default_model
        max_tokens = max_tokens or self.config.default_max_tokens
        temperature = temperature or self.config.default_temperature
        
        if provider.lower() == "openai":
            return await self._generate_openai(prompt, model, max_tokens, temperature)
        elif provider.lower() == "anthropic":
            return await self._generate_anthropic(prompt, model, max_tokens, temperature)
        elif provider.lower() == "openrouter":
            return await self._generate_openrouter(prompt, model, max_tokens, temperature)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    async def _generate_openai(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Generate text using OpenAI"""
        try:
            client = self._get_openai_client()
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical writer who creates clear, comprehensive documentation. Always respond with well-structured markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content.strip()
            self.metrics.record_ai_request(provider="openai", model=model, success=True)
            return content
            
        except Exception as e:
            self.metrics.record_ai_request(provider="openai", model=model, success=False)
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def _generate_anthropic(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Generate text using Anthropic"""
        try:
            client = self._get_anthropic_client()
            
            # Map model names if needed
            if model == "gpt-4o-mini":
                model = "claude-3-haiku-20240307"
            elif model == "gpt-4":
                model = "claude-3-sonnet-20240229"
            
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are an expert technical writer who creates clear, comprehensive documentation. Always respond with well-structured markdown.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = response.content[0].text.strip()
            self.metrics.record_ai_request(provider="anthropic", model=model, success=True)
            return content
            
        except Exception as e:
            self.metrics.record_ai_request(provider="anthropic", model=model, success=False)
            logger.error(f"Anthropic generation error: {e}")
            raise
    
    async def _generate_openrouter(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Generate text using OpenRouter"""
        try:
            client = self._get_openrouter_client()
            
            # OpenRouter supports many models - use the model name as provided
            # Popular OpenRouter models:
            # - anthropic/claude-3-sonnet
            # - anthropic/claude-3-haiku
            # - openai/gpt-4o-mini
            # - openai/gpt-4o
            # - meta-llama/llama-3.1-8b-instruct
            # - google/gemini-pro
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical writer who creates clear, comprehensive documentation. Always respond with well-structured markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                extra_headers={
                    "HTTP-Referer": "https://github.com/mkadrlik/documentation-generator",
                    "X-Title": "Documentation Generator MCP Server"
                }
            )
            
            content = response.choices[0].message.content.strip()
            self.metrics.record_ai_request(provider="openrouter", model=model, success=True)
            return content
            
        except Exception as e:
            self.metrics.record_ai_request(provider="openrouter", model=model, success=False)
            logger.error(f"OpenRouter generation error: {e}")
            raise