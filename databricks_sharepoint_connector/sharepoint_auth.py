"""
SharePoint Authentication Module

Handles Azure AD service principal authentication for SharePoint access using MSAL.
Provides secure token acquisition, caching, and automatic refresh capabilities.
"""

from msal import ConfidentialClientApplication
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SharePointAuthenticator:
    """
    Azure AD service principal authenticator for SharePoint resources.
    
    Provides secure, scalable access to SharePoint resources with automatic
    token refresh and caching to minimize API calls.
    """
    
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        """
        Initialize the SharePoint authenticator.
        
        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=self.authority
        )
        
        self._token_cache = {}
        self._token_lock = threading.Lock()
    
    def get_access_token(self, resource_url: str) -> str:
        """
        Get valid access token for SharePoint resource.
        
        Args:
            resource_url: SharePoint site URL to get token for
            
        Returns:
            Valid access token string
            
        Raises:
            Exception: If authentication fails
        """
        scope = f"{resource_url}/.default"
        
        with self._token_lock:
            # Check cached token validity
            if self._is_token_valid(scope):
                logger.debug(f"Using cached token for scope: {scope}")
                return self._token_cache[scope]['token']
            
            # Acquire new token
            logger.info(f"Acquiring new token for scope: {scope}")
            result = self.app.acquire_token_for_client(scopes=[scope])
            
            if 'access_token' in result:
                self._cache_token(scope, result)
                return result['access_token']
            else:
                error_msg = result.get('error_description', 'Unknown authentication error')
                logger.error(f"Authentication failed: {error_msg}")
                raise Exception(f"Authentication failed: {error_msg}")
    
    def _is_token_valid(self, scope: str) -> bool:
        """
        Check if cached token is still valid.
        
        Args:
            scope: Token scope to check
            
        Returns:
            True if token is valid, False otherwise
        """
        if scope not in self._token_cache:
            return False
        
        token_info = self._token_cache[scope]
        buffer_time = timedelta(minutes=5)  # 5-minute buffer before expiration
        return datetime.now() + buffer_time < token_info['expires_at']
    
    def _cache_token(self, scope: str, token_result: Dict):
        """
        Cache token with expiration info.
        
        Args:
            scope: Token scope
            token_result: Token result from MSAL
        """
        expires_in = token_result.get('expires_in', 3600)
        self._token_cache[scope] = {
            'token': token_result['access_token'],
            'expires_at': datetime.now() + timedelta(seconds=expires_in)
        }
        logger.debug(f"Cached token for scope {scope}, expires at {self._token_cache[scope]['expires_at']}")
    
    def clear_cache(self):
        """Clear the token cache (useful for testing or forcing re-authentication)."""
        with self._token_lock:
            self._token_cache.clear()
            logger.info("Token cache cleared")