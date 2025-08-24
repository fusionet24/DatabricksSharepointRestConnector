"""
Spark Data Source API v2 Implementation for SharePoint

Main implementation of the SharePoint data source using Spark's Python Data Source API v2.
Provides distributed reading of SharePoint files with intelligent partitioning.
"""

try:
    from pyspark.sql.datasource import DataSource, DataSourceReader, InputPartition
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, LongType
except ImportError:
    # Fallback for environments without PySpark
    class DataSource:
        pass
    class DataSourceReader:
        pass
    class InputPartition:
        pass
    StructType = StructField = StringType = IntegerType = TimestampType = LongType = None

from typing import Iterator, List, Tuple, Dict
import logging
from datetime import datetime

from .sharepoint_auth import SharePointAuthenticator
from .sharepoint_client import SharePointAPIClient
from .error_handling import ResilientSharePointClient
from .partitioning import SharePointPartitionStrategy
from .file_processing import FileContentProcessor
from .config import SharePointConnectorConfig, configure_logging

logger = logging.getLogger(__name__)


class SharePointInputPartition(InputPartition):
    """Represents a partition of SharePoint files to process."""
    
    def __init__(self, partition_id: int, file_list: List[Dict], partition_params: Dict):
        """
        Initialize SharePoint input partition.
        
        Args:
            partition_id: Unique partition identifier
            file_list: List of files to process in this partition
            partition_params: Connection parameters for this partition
        """
        super().__init__()
        self.partition_id = partition_id
        self.file_list = file_list
        self.partition_params = partition_params


class SharePointDataSourceReader(DataSourceReader):
    """Reads data from SharePoint with partitioning support."""
    
    def __init__(self, options: Dict[str, str], schema: StructType):
        """
        Initialize SharePoint data source reader.
        
        Args:
            options: Configuration options from Spark
            schema: Expected schema for the data
        """
        self.options = options
        self.schema = schema
        
        # Create configuration from options
        self.config = SharePointConnectorConfig.from_spark_options(options)
        
        # Configure logging
        configure_logging(self.config.log_level)
        
        # Validate configuration
        validation_errors = self.config.validate()
        if validation_errors:
            raise ValueError(f"Configuration validation failed: {validation_errors}")
        
        # Initialize partition strategy
        self.partition_strategy = SharePointPartitionStrategy(
            target_partition_size_mb=self.config.target_partition_size_mb,
            max_partitions=self.config.max_partitions
        )
        
        logger.info(f"Initialized SharePoint reader for {self.config.site_url}")
    
    def partitions(self) -> List[InputPartition]:
        """
        Plan input partitions for parallel processing.
        
        Returns:
            List of input partitions
        """
        try:
            # Initialize SharePoint client
            authenticator = SharePointAuthenticator(
                self.config.client_id, 
                self.config.client_secret, 
                self.config.tenant_id
            )
            client = SharePointAPIClient(self.config.site_url, authenticator)
            
            # Get all files from SharePoint
            logger.info(f"Listing files from library: {self.config.library_name}")
            all_files = client.list_files(self.config.library_name, self.config.folder_path)
            
            if not all_files:
                logger.warning("No files found in SharePoint library")
                return []
            
            # Create partitions based on file count and size
            balanced_partitions = self.partition_strategy.calculate_optimal_partitions(
                all_files, self.config.cluster_cores
            )
            
            # Create InputPartition objects
            partitions = []
            for i, file_batch in enumerate(balanced_partitions):
                partition = SharePointInputPartition(
                    partition_id=i,
                    file_list=file_batch,
                    partition_params={
                        "site_url": self.config.site_url,
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "tenant_id": self.config.tenant_id,
                        "process_file_content": self.config.process_file_content,
                        "max_retries": self.config.max_retries,
                        "log_level": self.config.log_level
                    }
                )
                partitions.append(partition)
            
            logger.info(f"Created {len(partitions)} partitions for {len(all_files)} files")
            return partitions
            
        except Exception as e:
            logger.error(f"Failed to create partitions: {e}")
            raise
    
    def read(self, partition: SharePointInputPartition) -> Iterator[Tuple]:
        """
        Read data from SharePoint partition with error handling.
        
        Args:
            partition: SharePoint input partition to read
            
        Yields:
            Tuples representing rows of data
        """
        # Configure logging for this partition
        configure_logging(partition.partition_params.get("log_level", "INFO"))
        
        logger.info(f"Processing partition {partition.partition_id} with {len(partition.file_list)} files")
        
        # Initialize clients within the executor
        authenticator = SharePointAuthenticator(
            partition.partition_params["client_id"],
            partition.partition_params["client_secret"],
            partition.partition_params["tenant_id"]
        )
        client = SharePointAPIClient(partition.partition_params["site_url"], authenticator)
        resilient_client = ResilientSharePointClient(client)
        
        # Initialize file processor
        file_processor = FileContentProcessor()
        
        # Process all files in the partition
        processed_count = 0
        for file_info in partition.file_list:
            try:
                row = self._process_file(file_info, resilient_client, file_processor, partition.partition_params)
                if row:
                    yield row
                    processed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to process file {file_info.get('FileRef', 'unknown')}: {e}")
                # Yield error row instead of failing completely
                yield self._create_error_row(file_info, str(e))
        
        logger.info(f"Partition {partition.partition_id} completed: {processed_count} files processed")
    
    def _process_file(self, file_info: Dict, resilient_client: ResilientSharePointClient, 
                     file_processor: FileContentProcessor, params: Dict) -> Tuple:
        """
        Process individual file with retry logic.
        
        Args:
            file_info: File metadata dictionary
            resilient_client: Resilient SharePoint client
            file_processor: File content processor
            params: Partition parameters
            
        Returns:
            Tuple representing the file data row
        """
        file_name = file_info.get('FileLeafRef', '')
        file_path = file_info.get('FileRef', '')
        file_size = self._get_file_size(file_info)
        modified_date = self._parse_date(file_info.get('Modified'))
        content_type = file_info.get('ContentType', '')
        
        # Download and process content if requested
        content = ""
        if params.get("process_file_content", True):
            try:
                file_content_bytes = resilient_client.download_file_resilient(file_path)
                content = file_processor.process_file_content(file_content_bytes, file_name)
            except Exception as e:
                logger.warning(f"Failed to download content for {file_name}: {e}")
                content = f"Download error: {str(e)}"
        
        return (
            file_name,
            file_path,
            file_size,
            modified_date,
            content_type,
            content
        )
    
    def _create_error_row(self, file_info: Dict, error_message: str) -> Tuple:
        """
        Create an error row for failed file processing.
        
        Args:
            file_info: File metadata dictionary
            error_message: Error message
            
        Returns:
            Tuple representing the error row
        """
        return (
            file_info.get('FileLeafRef', ''),
            file_info.get('FileRef', ''),
            0,
            None,
            "error",
            f"Processing error: {error_message}"
        )
    
    def _get_file_size(self, file_info: Dict) -> int:
        """Extract file size from file metadata."""
        if 'File' in file_info and isinstance(file_info['File'], dict):
            return file_info['File'].get('Length', 0)
        elif 'Length' in file_info:
            return file_info.get('Length', 0)
        else:
            return 0
    
    def _parse_date(self, date_str) -> datetime:
        """Parse SharePoint date string to datetime."""
        if not date_str:
            return None
        
        try:
            # Handle different SharePoint date formats
            if isinstance(date_str, str):
                # Remove timezone info if present
                if 'T' in date_str:
                    date_str = date_str.split('T')[0] + ' ' + date_str.split('T')[1].split('.')[0]
                return datetime.fromisoformat(date_str.replace('Z', ''))
            return date_str
        except (ValueError, AttributeError):
            return None


class SharePointDataSource(DataSource):
    """Custom Spark data source for SharePoint integration."""
    
    @classmethod
    def name(cls):
        """Return the name of this data source."""
        return "sharepoint"
    
    def schema(self):
        """
        Define the schema for SharePoint file data.
        
        Returns:
            StructType schema definition
        """
        if StructType is None:
            raise ImportError("PySpark is required for SharePoint data source")
            
        return StructType([
            StructField("file_name", StringType(), False),
            StructField("file_path", StringType(), False),
            StructField("file_size", LongType(), True),
            StructField("modified_date", TimestampType(), True),
            StructField("content_type", StringType(), True),
            StructField("content", StringType(), True)
        ])
    
    def reader(self, schema: StructType):
        """
        Create a data source reader.
        
        Args:
            schema: Schema for the data
            
        Returns:
            SharePointDataSourceReader instance
        """
        return SharePointDataSourceReader(self.options, schema)