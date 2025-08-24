"""
Basic tests for SharePoint Connector

Tests core functionality without requiring actual SharePoint credentials.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the modules to test
from databricks_sharepoint_connector.config import SharePointConnectorConfig
from databricks_sharepoint_connector.sharepoint_auth import SharePointAuthenticator
from databricks_sharepoint_connector.sharepoint_client import SharePointAPIClient
from databricks_sharepoint_connector.file_processing import FileContentProcessor
from databricks_sharepoint_connector.partitioning import SharePointPartitionStrategy
from databricks_sharepoint_connector.error_handling import SharePointErrorHandler


class TestSharePointConnectorConfig:
    """Test SharePoint connector configuration."""
    
    def test_from_spark_options(self):
        """Test configuration creation from Spark options."""
        options = {
            "site_url": "https://test.sharepoint.com/sites/test",
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "tenant_id": "test-tenant-id",
            "library_name": "Documents",
            "batch_size": "200",
            "max_partitions": "50"
        }
        
        config = SharePointConnectorConfig.from_spark_options(options)
        
        assert config.site_url == "https://test.sharepoint.com/sites/test"
        assert config.client_id == "test-client-id"
        assert config.library_name == "Documents"
        assert config.batch_size == 200
        assert config.max_partitions == 50
    
    def test_validation_required_fields(self):
        """Test configuration validation for required fields."""
        config = SharePointConnectorConfig(
            site_url="",
            client_id="",
            client_secret="",
            tenant_id="",
            library_name=""
        )
        
        errors = config.validate()
        assert len(errors) == 5  # All required fields missing
        assert "site_url" in str(errors)
        assert "client_id" in str(errors)
    
    def test_validation_numeric_fields(self):
        """Test configuration validation for numeric fields."""
        config = SharePointConnectorConfig(
            site_url="https://test.sharepoint.com",
            client_id="test-id",
            client_secret="test-secret",
            tenant_id="test-tenant",
            library_name="Documents",
            batch_size=-1,
            max_partitions=0,
            max_retries=-1
        )
        
        errors = config.validate()
        assert len(errors) == 3  # Three numeric validation errors
        assert "batch_size must be positive" in errors
        assert "max_partitions must be positive" in errors
        assert "max_retries must be non-negative" in errors


class TestFileContentProcessor:
    """Test file content processing."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.processor = FileContentProcessor()
    
    def test_csv_processing(self):
        """Test CSV file processing."""
        csv_content = b"name,age,city\nJohn,30,NYC\nJane,25,LA\n"
        result = self.processor._process_csv_content(csv_content)
        
        assert "CSV file: 3 rows" in result
        assert "3 columns" in result
        assert "name, age, city" in result
    
    def test_json_processing_small(self):
        """Test JSON file processing for small files."""
        json_content = b'{"name": "John", "age": 30, "city": "NYC"}'
        result = self.processor._process_json_content(json_content)
        
        # Should return formatted JSON for small files
        assert "John" in result
        assert "age" in result
    
    def test_text_processing(self):
        """Test text file processing."""
        text_content = b"This is a test file\nWith multiple lines\nFor testing"
        result = self.processor._process_text_content(text_content)
        
        assert "This is a test file" in result
        assert "multiple lines" in result
    
    def test_binary_content_handling(self):
        """Test handling of binary content."""
        # Create some binary content that can't be decoded as text
        binary_content = bytes([0x00, 0x01, 0x02, 0xFF, 0xFE])
        result = self.processor._process_text_content(binary_content)
        
        assert "Binary content" in result or "bytes" in result


class TestSharePointPartitionStrategy:
    """Test partition strategy."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.strategy = SharePointPartitionStrategy(target_partition_size_mb=100, max_partitions=10)
    
    def test_empty_file_list(self):
        """Test partitioning with empty file list."""
        result = self.strategy.calculate_optimal_partitions([], cluster_cores=4)
        assert result == []
    
    def test_single_file(self):
        """Test partitioning with single file."""
        files = [{"File": {"Length": 1024}, "FileRef": "test.txt"}]
        result = self.strategy.calculate_optimal_partitions(files, cluster_cores=4)
        
        assert len(result) == 1
        assert len(result[0]) == 1
        assert result[0][0]["FileRef"] == "test.txt"
    
    def test_multiple_files_balancing(self):
        """Test file balancing across partitions."""
        # Create files that would exceed the target partition size (100MB)
        files = [
            {"File": {"Length": 100000000}, "FileRef": "large1.txt"},  # 100MB
            {"File": {"Length": 80000000}, "FileRef": "large2.txt"},   # 80MB  
            {"File": {"Length": 60000000}, "FileRef": "medium1.txt"},  # 60MB
            {"File": {"Length": 40000000}, "FileRef": "medium2.txt"},  # 40MB
            {"File": {"Length": 20000000}, "FileRef": "small1.txt"},   # 20MB
            {"File": {"Length": 10000000}, "FileRef": "small2.txt"}    # 10MB
        ]
        
        result = self.strategy.calculate_optimal_partitions(files, cluster_cores=4)
        
        # Should create multiple partitions for large dataset
        assert len(result) >= 1  # At least one partition
        
        # Total files should be preserved
        total_files = sum(len(partition) for partition in result)
        assert total_files == 6
    
    def test_get_file_size_different_formats(self):
        """Test file size extraction from different API response formats."""
        # Format 1: File object with Length
        file1 = {"File": {"Length": 1024}}
        assert self.strategy._get_file_size(file1) == 1024
        
        # Format 2: Direct Length field
        file2 = {"Length": 2048}
        assert self.strategy._get_file_size(file2) == 2048
        
        # Format 3: No size information
        file3 = {"FileRef": "test.txt"}
        assert self.strategy._get_file_size(file3) == 0


class TestSharePointErrorHandler:
    """Test error handling functionality."""
    
    def test_retriable_http_error_detection(self):
        """Test detection of retriable HTTP errors."""
        import requests
        
        # Create mock responses
        server_error_response = Mock()
        server_error_response.status_code = 500
        
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        
        auth_error_response = Mock()
        auth_error_response.status_code = 401
        
        # Test server error (should be retriable)
        server_error = requests.exceptions.HTTPError()
        server_error.response = server_error_response
        assert SharePointErrorHandler.is_retriable_http_error(server_error)
        
        # Test rate limiting (should be retriable)
        rate_limit_error = requests.exceptions.HTTPError()
        rate_limit_error.response = rate_limit_response
        assert SharePointErrorHandler.is_retriable_http_error(rate_limit_error)
        
        # Test auth error (should not be retriable)
        auth_error = requests.exceptions.HTTPError()
        auth_error.response = auth_error_response
        assert not SharePointErrorHandler.is_retriable_http_error(auth_error)
    
    def test_create_retry_decorator(self):
        """Test retry decorator creation."""
        # Test different operation types
        auth_decorator = SharePointErrorHandler.create_retry_decorator("authentication")
        download_decorator = SharePointErrorHandler.create_retry_decorator("file_download")
        general_decorator = SharePointErrorHandler.create_retry_decorator("general")
        
        # All should be callable decorators
        assert callable(auth_decorator)
        assert callable(download_decorator)
        assert callable(general_decorator)


@patch('databricks_sharepoint_connector.sharepoint_auth.ConfidentialClientApplication')
class TestSharePointAuthenticator:
    """Test SharePoint authenticator."""
    
    def test_initialization(self, mock_msal):
        """Test authenticator initialization."""
        auth = SharePointAuthenticator("client-id", "client-secret", "tenant-id")
        
        assert auth.client_id == "client-id"
        assert auth.client_secret == "client-secret"
        assert auth.tenant_id == "tenant-id"
        assert "tenant-id" in auth.authority
        
        # Verify MSAL app was created
        mock_msal.assert_called_once()
    
    def test_token_caching(self, mock_msal):
        """Test token caching functionality."""
        # Mock MSAL app
        mock_app = Mock()
        mock_app.acquire_token_for_client.return_value = {
            'access_token': 'test-token',
            'expires_in': 3600
        }
        mock_msal.return_value = mock_app
        
        auth = SharePointAuthenticator("client-id", "client-secret", "tenant-id")
        
        # First call should acquire token
        token1 = auth.get_access_token("https://test.sharepoint.com")
        assert token1 == "test-token"
        
        # Second call should use cached token
        token2 = auth.get_access_token("https://test.sharepoint.com")
        assert token2 == "test-token"
        
        # Should only call MSAL once due to caching
        assert mock_app.acquire_token_for_client.call_count == 1
    
    def test_authentication_failure(self, mock_msal):
        """Test handling of authentication failures."""
        # Mock MSAL app to return error
        mock_app = Mock()
        mock_app.acquire_token_for_client.return_value = {
            'error': 'invalid_client',
            'error_description': 'Invalid client credentials'
        }
        mock_msal.return_value = mock_app
        
        auth = SharePointAuthenticator("client-id", "client-secret", "tenant-id")
        
        with pytest.raises(Exception) as excinfo:
            auth.get_access_token("https://test.sharepoint.com")
        
        assert "Authentication failed" in str(excinfo.value)
        assert "Invalid client credentials" in str(excinfo.value)


def test_basic_import():
    """Test that all modules can be imported successfully."""
    from databricks_sharepoint_connector import (
        SharePointDataSource,
        SharePointAuthenticator,
        SharePointAPIClient,
        SharePointConnectorConfig
    )
    
    # Basic smoke test - ensure classes can be imported
    assert SharePointDataSource is not None
    assert SharePointAuthenticator is not None
    assert SharePointAPIClient is not None
    assert SharePointConnectorConfig is not None


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])