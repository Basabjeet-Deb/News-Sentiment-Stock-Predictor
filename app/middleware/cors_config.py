"""
CORS configuration with environment-based origins
"""

import os
from typing import List


def get_cors_origins() -> List[str]:
    """
    Get CORS origins based on environment
    
    Returns:
        List of allowed origins
    """
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        # Production: Only allow specific domains
        allowed_origins = os.getenv(
            "ALLOWED_ORIGINS",
            "https://yourdomain.com,https://www.yourdomain.com"
        ).split(",")
        
        return [origin.strip() for origin in allowed_origins]
    
    elif env == "staging":
        # Staging: Allow staging domains
        return [
            "https://staging.yourdomain.com",
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    
    else:
        # Development: Allow localhost
        return [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]


def get_cors_config() -> dict:
    """
    Get CORS middleware configuration
    
    Returns:
        Dictionary with CORS settings
    """
    env = os.getenv("ENVIRONMENT", "development")
    
    return {
        "allow_origins": get_cors_origins(),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Request-ID",
        ],
        "expose_headers": [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        "max_age": 600 if env == "production" else 300,
    }
