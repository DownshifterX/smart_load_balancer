"""
app/config.py
--------------
Application settings loaded from environment variables / .env file.
Uses pydantic-settings for validation and type coercion.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration with sensible defaults."""

    # Server
    HOST: str = Field(default="0.0.0.0", description="Bind host")
    PORT: int = Field(default=8000, description="Bind port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Simulation
    SIMULATION_TICK_MS: int = Field(default=500, description="Simulation tick interval in ms")
    MAX_SERVERS: int = Field(default=20, description="Maximum number of simulated servers")
    DEFAULT_ALGORITHM: str = Field(default="round_robin", description="Default LB algorithm")
    DEFAULT_TRAFFIC_MODE: str = Field(default="normal", description="Default traffic mode")

    # Defaults for new servers
    DEFAULT_SERVER_MAX_CONNECTIONS: int = Field(default=100, description="Default max connections per server")
    DEFAULT_SERVER_WEIGHT: int = Field(default=1, description="Default server weight")

    # SMTP Configuration (For Feedback)
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP Server Host")
    SMTP_PORT: int = Field(default=587, description="SMTP Server Port")
    SMTP_USER: str = Field(default="", description="SMTP Username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP Password (App Password)")
    SMTP_TLS: bool = Field(default=True, description="Enable STARTTLS")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Singleton settings instance
settings = Settings()
