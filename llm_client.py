import anthropic
import logging
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Custom exception for LLM-related errors."""
    pass

class AnthropicClient:
    """Simple Anthropic API client for database query system."""
    
    def __init__(self):
        """Initialize the Anthropic client."""
        Config.validate()
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.model = Config.MODEL_NAME
        self.max_tokens = Config.MAX_TOKENS
        
        logger.info(f"Initialized Anthropic client with model: {self.model}")
    
    async def get_response(
        self,
        messages: list,
        max_tokens: Optional[int] = None,
        temperature: float = 0.1
    ) -> str:
        """
        Get a response from the LLM based on a conversation history.
        
        Args:
            messages: A list of messages forming the conversation history.
            max_tokens: Maximum tokens to generate.
            temperature: Randomness in response (0.0-1.0).
            
        Returns:
            Generated text response.
            
        Raises:
            LLMError: For API or processing errors.
        """
        try:
            if not messages:
                raise LLMError("Messages list cannot be empty")
            
            # The system prompt is now expected to be the first message if present
            system_prompt = None
            if messages[0]['role'] == 'system':
                system_prompt = messages[0]['content']
                messages = messages[1:]

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            if not response.content or len(response.content) == 0:
                raise LLMError("Empty response from API")
            
            content = response.content[0].text
            
            logger.info(f"Generated response: {len(content)} chars")
            
            return content
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMError(f"API error: {str(e)}")
                
        except Exception as e:
            logger.error(f"Unexpected error in get_response: {e}")
            raise LLMError(f"Unexpected error: {str(e)}") 