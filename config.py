import os
import logging
from dotenv import load_dotenv
from typing import Optional, List

# Load environment variables
load_dotenv()

class Config:
    """Application configuration for database query system."""
    
    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
    
    # LLM Configuration
    MODEL_NAME: str = os.getenv('MODEL_NAME', 'claude-3-5-sonnet-20241022')
    MAX_TOKENS: int = int(os.getenv('MAX_TOKENS', '1000'))
    
    # Application Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT: int = int(os.getenv('PORT', '8000'))
    HOST: str = os.getenv('HOST', '127.0.0.1')
    
    # Database Configuration
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/pagila')
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'pagila')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'password')
    
    # Performance Settings
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    TIMEOUT_SECONDS: int = int(os.getenv('TIMEOUT_SECONDS', '30'))
    
    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    CORS_ORIGINS: List[str] = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else ["*"]
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        missing_keys = []
        
        if not cls.ANTHROPIC_API_KEY:
            missing_keys.append('ANTHROPIC_API_KEY')
        
        if missing_keys:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_keys)}\n"
                f"Please check your .env file and ensure all required keys are set."
            )
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL for connections."""
        return cls.DATABASE_URL

 