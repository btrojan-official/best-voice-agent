import os
import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Header

logger = logging.getLogger(__name__)


class AuthService:
    """Simple authentication service using environment variables."""
    
    @staticmethod
    def verify_credentials(username: str, password: str) -> bool:
        """
        Verify admin credentials against environment variables.
        
        Args:
            username: Provided username
            password: Provided password
        
        Returns:
            True if credentials match, False otherwise
        """
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        return username == admin_username and password == admin_password
    
    @staticmethod
    def create_token(username: str) -> str:
        """
        Create a simple token (in production, use JWT).
        
        Args:
            username: Username to create token for
        
        Returns:
            Simple token string
        """
        timestamp = datetime.now().isoformat()
        return f"{username}:{timestamp}"
    
    @staticmethod
    def verify_token(token: Optional[str]) -> bool:
        """
        Verify authentication token.
        
        Args:
            token: Token to verify
        
        Returns:
            True if valid, False otherwise
        """
        if not token:
            logger.warning("Token is None or empty")
            return False
        
        try:
            # Split only on the first colon since timestamp contains colons
            parts = token.split(":", 1)
            logger.info(f"Token parts after split: {len(parts)} parts")
            if len(parts) != 2:
                logger.warning(f"Invalid token format, expected 2 parts, got {len(parts)}")
                return False
            
            username = parts[0]
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            
            result = username == admin_username
            logger.info(f"Token verification: username={username}, expected={admin_username}, result={result}")
            return result
        
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return False


def require_auth(authorization: Optional[str] = Header(None)) -> str:
    """
    Dependency to require authentication.
    
    Args:
        authorization: Authorization header
    
    Returns:
        Token if valid
    
    Raises:
        HTTPException: If authentication fails
    """
    logger.info(f"Authorization header: {authorization}")
    
    if not authorization:
        logger.warning("Authorization header missing")
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        logger.warning(f"Invalid authorization format: {authorization}")
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    logger.info(f"Extracted token: {token[:20]}..." if len(token) > 20 else f"Extracted token: {token}")
    
    if not AuthService.verify_token(token):
        logger.warning(f"Token verification failed")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    logger.info("Authentication successful")
    return token
