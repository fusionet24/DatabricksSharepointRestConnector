"""
SharePoint REST API Client

Provides comprehensive access to SharePoint document libraries, files, and metadata
through structured REST API endpoints with batch operations support.
"""

import requests
from typing import List, Dict, Iterator, Optional
import json
from urllib.parse import quote
from datetime import datetime
import logging

from .sharepoint_auth import SharePointAuthenticator

logger = logging.getLogger(__name__)


class SharePointAPIClient:
    """
    SharePoint REST API client with comprehensive file and folder operations.
    
    Provides structured access to SharePoint content with support for batch operations
    and automatic error handling.
    """
    
    def __init__(self, site_url: str, authenticator: SharePointAuthenticator):
        """
        Initialize SharePoint API client.
        
        Args:
            site_url: SharePoint site URL
            authenticator: SharePoint authenticator instance
        """
        self.site_url = site_url.rstrip('/')
        self.authenticator = authenticator
        self.api_base = f"{self.site_url}/_api"
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get authenticated request headers.
        
        Returns:
            Dictionary of HTTP headers with authentication
        """
        token = self.authenticator.get_access_token(self.site_url)
        return {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose'
        }
    
    def list_files(self, library_name: str, folder_path: str = None) -> List[Dict]:
        """
        List files in SharePoint library or folder.
        
        Args:
            library_name: Name of the SharePoint document library
            folder_path: Optional folder path within the library
            
        Returns:
            List of file metadata dictionaries
            
        Raises:
            requests.HTTPError: If API request fails
        """
        if folder_path:
            encoded_path = quote(folder_path, safe='')
            endpoint = f"{self.api_base}/web/GetFolderByServerRelativeUrl('{encoded_path}')/Files"
            endpoint += "?$expand=ListItemAllFields"
        else:
            endpoint = f"{self.api_base}/web/lists/getbytitle('{library_name}')/items"
            endpoint += "?$select=Title,Modified,Author/Title,FileRef,FileLeafRef,File/Length"
            endpoint += "&$expand=Author,File"
        
        logger.debug(f"Listing files from endpoint: {endpoint}")
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('d', {}).get('results', [])
            
            logger.info(f"Retrieved {len(results)} files from {library_name}")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list files from {library_name}: {e}")
            raise
    
    def download_file(self, file_url: str) -> bytes:
        """
        Download file content from SharePoint.
        
        Args:
            file_url: Server-relative URL of the file
            
        Returns:
            File content as bytes
            
        Raises:
            requests.HTTPError: If download fails
        """
        encoded_url = quote(file_url, safe='')
        endpoint = f"{self.api_base}/web/GetFileByServerRelativeUrl('{encoded_url}')/$value"
        
        logger.debug(f"Downloading file: {file_url}")
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), timeout=60)
            response.raise_for_status()
            
            content = response.content
            logger.info(f"Downloaded file {file_url}, size: {len(content)} bytes")
            return content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download file {file_url}: {e}")
            raise
    
    def upload_file(self, library_name: str, file_name: str, content: bytes) -> Dict:
        """
        Upload file to SharePoint library.
        
        Args:
            library_name: Name of the SharePoint document library
            file_name: Name for the uploaded file
            content: File content as bytes
            
        Returns:
            Upload result metadata
            
        Raises:
            requests.HTTPError: If upload fails
        """
        endpoint = f"{self.api_base}/web/lists/getbytitle('{library_name}')/RootFolder/Files"
        endpoint += f"/add(url='{quote(file_name)}',overwrite=true)"
        
        headers = self._get_headers()
        headers['Content-Length'] = str(len(content))
        
        logger.debug(f"Uploading file {file_name} to {library_name}")
        
        try:
            response = requests.post(endpoint, headers=headers, data=content, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully uploaded file {file_name}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload file {file_name}: {e}")
            raise
    
    def batch_operations(self, operations: List[Dict]) -> List[Dict]:
        """
        Execute multiple operations in a single batch request.
        
        Args:
            operations: List of operation dictionaries
            
        Returns:
            List of operation results
            
        Raises:
            requests.HTTPError: If batch request fails
        """
        boundary = f"batch_{datetime.now().isoformat()}"
        batch_body = self._build_batch_body(operations, boundary)
        
        headers = self._get_headers()
        headers['Content-Type'] = f'multipart/mixed; boundary={boundary}'
        
        logger.debug(f"Executing batch with {len(operations)} operations")
        
        try:
            response = requests.post(
                f"{self.api_base}/$batch",
                headers=headers,
                data=batch_body,
                timeout=180
            )
            response.raise_for_status()
            
            results = self._parse_batch_response(response.text)
            logger.info(f"Batch completed successfully, {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Batch operation failed: {e}")
            raise
    
    def _build_batch_body(self, operations: List[Dict], boundary: str) -> str:
        """
        Build the batch request body.
        
        Args:
            operations: List of operations
            boundary: Batch boundary string
            
        Returns:
            Batch request body as string
        """
        body_parts = []
        
        for i, operation in enumerate(operations):
            body_parts.append(f"--{boundary}")
            body_parts.append("Content-Type: application/http")
            body_parts.append("Content-Transfer-Encoding: binary")
            body_parts.append("")
            
            method = operation.get('method', 'GET')
            url = operation.get('url', '')
            body_parts.append(f"{method} {url} HTTP/1.1")
            body_parts.append("Accept: application/json;odata=verbose")
            body_parts.append("")
            
            if operation.get('body'):
                body_parts.append(operation['body'])
            
            body_parts.append("")
        
        body_parts.append(f"--{boundary}--")
        return "\r\n".join(body_parts)
    
    def _parse_batch_response(self, response_text: str) -> List[Dict]:
        """
        Parse batch response text into structured results.
        
        Args:
            response_text: Raw batch response text
            
        Returns:
            List of parsed results
        """
        # Simple batch response parsing - in production, you'd want more robust parsing
        results = []
        parts = response_text.split('--batch')
        
        for part in parts:
            if 'HTTP/1.1 200 OK' in part and '{' in part:
                try:
                    json_start = part.find('{')
                    json_part = part[json_start:]
                    result = json.loads(json_part)
                    results.append(result)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return results