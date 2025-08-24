"""
Databricks SharePoint REST Connector

A custom Apache Spark data source for Microsoft SharePoint using Python Data Source API v2.
Provides secure, scalable access to SharePoint resources with comprehensive error handling
and performance optimization.
"""

__version__ = "1.0.0"
__author__ = "FusionNet24"

from .sharepoint_auth import SharePointAuthenticator
from .sharepoint_client import SharePointAPIClient
from .config import SharePointConnectorConfig, configure_logging
from .file_processing import FileContentProcessor
from .partitioning import SharePointPartitionStrategy
from .error_handling import SharePointErrorHandler, ResilientSharePointClient

# Import Spark components conditionally
try:
    from .sharepoint_datasource import SharePointDataSource, SharePointDataSourceReader, SharePointInputPartition
    _SPARK_AVAILABLE = True
except ImportError:
    _SPARK_AVAILABLE = False
    # Create placeholder classes for documentation
    class SharePointDataSource:
        def __init__(self):
            raise ImportError("PySpark is required for SharePoint data source functionality")
    
    class SharePointDataSourceReader:
        def __init__(self):
            raise ImportError("PySpark is required for SharePoint data source functionality")
    
    class SharePointInputPartition:
        def __init__(self):
            raise ImportError("PySpark is required for SharePoint data source functionality")

__all__ = [
    "SharePointDataSource",
    "SharePointDataSourceReader", 
    "SharePointInputPartition",
    "SharePointAuthenticator", 
    "SharePointAPIClient",
    "SharePointConnectorConfig",
    "configure_logging",
    "FileContentProcessor",
    "SharePointPartitionStrategy",
    "SharePointErrorHandler",
    "ResilientSharePointClient"
]

# Expose availability flag
__spark_available__ = _SPARK_AVAILABLE