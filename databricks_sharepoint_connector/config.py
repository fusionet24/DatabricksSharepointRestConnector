"""
Configuration Management for SharePoint Connector

Provides comprehensive configuration management, environment-specific settings,
and operational procedures for production deployments.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import os
import logging


@dataclass
class SharePointConnectorConfig:
    """Configuration class for SharePoint Spark connector."""
    
    # Authentication settings
    site_url: str
    client_id: str
    client_secret: str
    tenant_id: str
    
    # SharePoint settings
    library_name: str
    folder_path: Optional[str] = None
    
    # Performance settings
    batch_size: int = 100
    max_partitions: int = 100
    target_partition_size_mb: int = 150
    cluster_cores: int = 50
    
    # Error handling settings
    max_retries: int = 3
    retry_backoff_multiplier: float = 1.0
    retry_max_wait_seconds: int = 60
    
    # Processing settings
    enable_caching: bool = True
    process_file_content: bool = True
    supported_formats: Optional[List[str]] = None
    
    # Monitoring settings
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['csv', 'json', 'parquet', 'txt']
    
    @classmethod
    def from_spark_options(cls, options: Dict[str, str]) -> 'SharePointConnectorConfig':
        """
        Create configuration from Spark DataFrame options.
        
        Args:
            options: Dictionary of Spark DataFrame options
            
        Returns:
            SharePointConnectorConfig instance
        """
        return cls(
            site_url=options.get("site_url"),
            client_id=options.get("client_id"),
            client_secret=options.get("client_secret"),
            tenant_id=options.get("tenant_id"),
            library_name=options.get("library_name"),
            folder_path=options.get("folder_path"),
            batch_size=int(options.get("batch_size", "100")),
            max_partitions=int(options.get("max_partitions", "100")),
            target_partition_size_mb=int(options.get("target_partition_size_mb", "150")),
            cluster_cores=int(options.get("cluster_cores", "50")),
            max_retries=int(options.get("max_retries", "3")),
            retry_backoff_multiplier=float(options.get("retry_backoff_multiplier", "1.0")),
            retry_max_wait_seconds=int(options.get("retry_max_wait_seconds", "60")),
            enable_caching=options.get("enable_caching", "true").lower() == "true",
            process_file_content=options.get("process_file_content", "true").lower() == "true",
            enable_metrics=options.get("enable_metrics", "true").lower() == "true",
            log_level=options.get("log_level", "INFO")
        )
    
    @classmethod
    def from_environment(cls) -> 'SharePointConnectorConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            SharePointConnectorConfig instance
        """
        return cls(
            site_url=os.getenv("SHAREPOINT_SITE_URL"),
            client_id=os.getenv("SHAREPOINT_CLIENT_ID"),
            client_secret=os.getenv("SHAREPOINT_CLIENT_SECRET"),
            tenant_id=os.getenv("SHAREPOINT_TENANT_ID"),
            library_name=os.getenv("SHAREPOINT_LIBRARY_NAME"),
            folder_path=os.getenv("SHAREPOINT_FOLDER_PATH"),
            batch_size=int(os.getenv("SHAREPOINT_BATCH_SIZE", "100")),
            max_partitions=int(os.getenv("SHAREPOINT_MAX_PARTITIONS", "100")),
            target_partition_size_mb=int(os.getenv("SHAREPOINT_TARGET_PARTITION_SIZE_MB", "150")),
            cluster_cores=int(os.getenv("SHAREPOINT_CLUSTER_CORES", "50")),
            max_retries=int(os.getenv("SHAREPOINT_MAX_RETRIES", "3")),
            enable_caching=os.getenv("SHAREPOINT_ENABLE_CACHING", "true").lower() == "true",
            process_file_content=os.getenv("SHAREPOINT_PROCESS_FILE_CONTENT", "true").lower() == "true",
            enable_metrics=os.getenv("SHAREPOINT_ENABLE_METRICS", "true").lower() == "true",
            log_level=os.getenv("SHAREPOINT_LOG_LEVEL", "INFO")
        )
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of validation errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Required fields
        required_fields = ["site_url", "client_id", "client_secret", "tenant_id", "library_name"]
        for field in required_fields:
            if not getattr(self, field):
                errors.append(f"Missing required field: {field}")
        
        # Validate numeric fields
        if self.batch_size <= 0:
            errors.append("batch_size must be positive")
        if self.max_partitions <= 0:
            errors.append("max_partitions must be positive")
        if self.target_partition_size_mb <= 0:
            errors.append("target_partition_size_mb must be positive")
        if self.max_retries < 0:
            errors.append("max_retries must be non-negative")
        
        return errors


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for SharePoint connector.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger('databricks_sharepoint_connector').setLevel(getattr(logging, log_level.upper()))
    logging.getLogger('msal').setLevel(logging.WARNING)  # Reduce MSAL verbosity
    logging.getLogger('urllib3').setLevel(logging.WARNING)  # Reduce urllib3 verbosity