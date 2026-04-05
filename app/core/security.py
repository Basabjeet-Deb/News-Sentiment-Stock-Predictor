"""
Security utilities and input validation
"""

import re
from typing import Optional
from fastapi import HTTPException, Header
from pydantic import BaseModel, validator, Field


class TickerValidator(BaseModel):
    """Validate stock ticker format"""
    ticker: str = Field(..., min_length=1, max_length=10)
    
    @validator('ticker')
    def validate_ticker(cls, v):
        """Ensure ticker is alphanumeric and uppercase"""
        if not v:
            raise ValueError("Ticker cannot be empty")
        
        # Remove whitespace
        v = v.strip().upper()
        
        # Allow only alphanumeric characters, dots, and hyphens
        if not re.match(r'^[A-Z0-9.\-]+$', v):
            raise ValueError("Ticker must contain only letters, numbers, dots, and hyphens")
        
        return v


class QueryValidator(BaseModel):
    """Validate search query strings"""
    query: str = Field(..., min_length=1, max_length=200)
    
    @validator('query')
    def validate_query(cls, v):
        """Sanitize query string"""
        if not v:
            raise ValueError("Query cannot be empty")
        
        # Remove potentially dangerous characters
        v = v.strip()
        
        # Block SQL injection patterns
        dangerous_patterns = [
            r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',
            r'(--|;|\/\*|\*\/)',
            r'(\bOR\b.*=.*|1=1)',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Query contains invalid characters or patterns")
        
        return v


class PaginationValidator(BaseModel):
    """Validate pagination parameters"""
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    
    @validator('limit')
    def validate_limit(cls, v):
        """Ensure reasonable limit"""
        if v > 500:
            raise ValueError("Limit cannot exceed 500")
        return v


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize user input string
    
    Args:
        value: Input string
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Truncate to max length
    value = value[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Remove control characters except newlines and tabs
    value = ''.join(char for char in value if char.isprintable() or char in '\n\t')
    
    return value.strip()


def validate_ticker_format(ticker: str) -> str:
    """
    Validate and sanitize stock ticker
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Validated ticker in uppercase
        
    Raises:
        HTTPException: If ticker is invalid
    """
    try:
        validated = TickerValidator(ticker=ticker)
        return validated.ticker
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid ticker: {str(e)}")


def validate_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """
    Validate API key from header (optional for now)
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        API key if valid, None if not required
    """
    # For now, API key is optional
    # In production, implement proper API key validation
    return x_api_key


def validate_numeric_range(
    value: Optional[float],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    field_name: str = "value"
) -> Optional[float]:
    """
    Validate numeric value is within range
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Name of field for error messages
        
    Returns:
        Validated value
        
    Raises:
        HTTPException: If value is out of range
    """
    if value is None:
        return None
    
    if min_val is not None and value < min_val:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be >= {min_val}"
        )
    
    if max_val is not None and value > max_val:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be <= {max_val}"
        )
    
    return value


def validate_sort_field(field: str, allowed_fields: list) -> str:
    """
    Validate sort field is in allowed list
    
    Args:
        field: Sort field name
        allowed_fields: List of allowed field names
        
    Returns:
        Validated field name
        
    Raises:
        HTTPException: If field is not allowed
    """
    if field not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field. Allowed: {', '.join(allowed_fields)}"
        )
    
    return field
