"""
Error Handling and Retry Strategies

Comprehensive error handling for SharePoint operations with sophisticated retry
mechanisms using exponential backoff and error classification.
"""

from tenacity import (
    retry, stop_after_attempt, wait_exponential, 
    retry_if_exception_type, before_sleep_log
)
import logging
from typing import Dict, Any, List, Tuple
import requests

logger = logging.getLogger(__name__)


class SharePointErrorHandler:
    """Comprehensive error handling for SharePoint operations."""
    
    # Define retriable vs non-retriable exceptions
    RETRIABLE_EXCEPTIONS = (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.ReadTimeout
    )
    
    AUTHENTICATION_EXCEPTIONS = (
        requests.exceptions.HTTPError,  # 401, 403 errors
    )
    
    @staticmethod
    def is_retriable_http_error(exception: Exception) -> bool:
        """
        Determine if HTTP error is retriable.
        
        Args:
            exception: Exception to check
            
        Returns:
            True if error is retriable, False otherwise
        """
        if isinstance(exception, requests.exceptions.HTTPError):
            if hasattr(exception, 'response') and exception.response:
                status_code = exception.response.status_code
                # Retry on server errors and rate limiting
                return status_code >= 500 or status_code == 429
        return False
    
    @classmethod
    def create_retry_decorator(cls, operation_type: str = "general"):
        """
        Create appropriate retry decorator for operation type.
        
        Args:
            operation_type: Type of operation (authentication, file_download, general)
            
        Returns:
            Configured retry decorator
        """
        if operation_type == "authentication":
            return retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=30),
                retry=retry_if_exception_type(cls.AUTHENTICATION_EXCEPTIONS),
                before_sleep=before_sleep_log(logger, logging.WARNING)
            )
        elif operation_type == "file_download":
            return retry(
                stop=stop_after_attempt(5),
                wait=wait_exponential(multiplier=1, min=4, max=60),
                retry=retry_if_exception_type(cls.RETRIABLE_EXCEPTIONS),
                before_sleep=before_sleep_log(logger, logging.WARNING)
            )
        else:
            return retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=20),
                retry=retry_if_exception_type(cls.RETRIABLE_EXCEPTIONS)
            )


class ResilientSharePointClient:
    """SharePoint client with comprehensive error handling."""
    
    def __init__(self, sharepoint_client):
        """
        Initialize resilient client wrapper.
        
        Args:
            sharepoint_client: SharePointAPIClient instance
        """
        self.client = sharepoint_client
        self.error_handler = SharePointErrorHandler()
    
    @SharePointErrorHandler.create_retry_decorator("file_download")
    def download_file_resilient(self, file_url: str) -> bytes:
        """
        Download file with comprehensive retry logic.
        
        Args:
            file_url: Server-relative URL of the file
            
        Returns:
            File content as bytes
        """
        try:
            return self.client.download_file(file_url)
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                # Force token refresh for authentication errors
                self.client.authenticator.clear_cache()
                return self.client.download_file(file_url)
            raise
    
    @SharePointErrorHandler.create_retry_decorator("general")
    def list_files_resilient(self, library_name: str, folder_path: str = None) -> List[Dict]:
        """
        List files with error handling.
        
        Args:
            library_name: Name of the SharePoint document library
            folder_path: Optional folder path within the library
            
        Returns:
            List of file metadata dictionaries
        """
        return self.client.list_files(library_name, folder_path)
    
    def process_files_with_error_collection(self, file_list: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Process files and collect errors separately.
        
        Args:
            file_list: List of file metadata dictionaries
            
        Returns:
            Tuple of (successful_files, failed_files)
        """
        successful_files = []
        failed_files = []
        
        for file_info in file_list:
            try:
                content = self.download_file_resilient(file_info['FileRef'])
                file_info['content'] = content
                file_info['status'] = 'success'
                successful_files.append(file_info)
                
            except Exception as e:
                error_info = {
                    'file_info': file_info,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'status': 'failed'
                }
                failed_files.append(error_info)
                logger.error(f"Failed to process file {file_info.get('FileRef')}: {e}")
        
        return successful_files, failed_files