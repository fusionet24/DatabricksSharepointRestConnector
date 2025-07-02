"""
Example Usage of SharePoint Connector

Demonstrates how to use the SharePoint Spark connector in various scenarios.
"""

import os
from typing import Optional

try:
    from pyspark.sql import SparkSession
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    print("Warning: PySpark is not available. Examples will show configuration only.")

from databricks_sharepoint_connector import (
    SharePointDataSource, 
    SharePointConnectorConfig,
    SharePointAuthenticator,
    SharePointAPIClient
)


def create_spark_session() -> Optional['SparkSession']:
    """Create Spark session for examples."""
    if not PYSPARK_AVAILABLE:
        return None
    
    return SparkSession.builder \
        .appName("SharePoint Connector Example") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()


def example_basic_usage():
    """Example 1: Basic usage with minimal configuration."""
    print("=== Example 1: Basic Usage ===")
    
    spark = create_spark_session()
    if not spark:
        print("Skipping Spark example - PySpark not available")
        return
    
    # Basic configuration - replace with your actual values
    df = spark.read.format("sharepoint") \
        .option("site_url", "https://contoso.sharepoint.com/sites/data") \
        .option("client_id", "your-client-id") \
        .option("client_secret", "your-client-secret") \
        .option("tenant_id", "your-tenant-id") \
        .option("library_name", "Documents") \
        .load()
    
    print("Schema:")
    df.printSchema()
    
    print("Sample data:")
    df.show(5, truncate=False)


def example_folder_specific():
    """Example 2: Reading from a specific folder with filtering."""
    print("\n=== Example 2: Folder-Specific Reading ===")
    
    spark = create_spark_session()
    if not spark:
        print("Skipping Spark example - PySpark not available")
        return
    
    # Read from specific folder
    df = spark.read.format("sharepoint") \
        .option("site_url", "https://contoso.sharepoint.com/sites/data") \
        .option("client_id", "your-client-id") \
        .option("client_secret", "your-client-secret") \
        .option("tenant_id", "your-tenant-id") \
        .option("library_name", "Documents") \
        .option("folder_path", "/Reports/2024/Q1") \
        .option("process_file_content", "true") \
        .load()
    
    # Filter for specific file types
    csv_files = df.filter(df.file_name.endswith(".csv"))
    
    print("CSV files found:")
    csv_files.select("file_name", "file_size", "modified_date").show()


def example_performance_tuning():
    """Example 3: Performance tuning for large datasets."""
    print("\n=== Example 3: Performance Tuning ===")
    
    spark = create_spark_session()
    if not spark:
        print("Skipping Spark example - PySpark not available")
        return
    
    # Configure Spark for better performance
    spark.conf.set("spark.network.timeout", "800s")
    spark.conf.set("spark.executor.heartbeatInterval", "60s")
    
    # Optimized configuration for large datasets
    df = spark.read.format("sharepoint") \
        .option("site_url", "https://contoso.sharepoint.com/sites/analytics") \
        .option("client_id", "your-client-id") \
        .option("client_secret", "your-client-secret") \
        .option("tenant_id", "your-tenant-id") \
        .option("library_name", "Reports") \
        .option("batch_size", "200") \
        .option("max_partitions", "50") \
        .option("target_partition_size_mb", "200") \
        .option("max_retries", "5") \
        .option("retry_backoff_multiplier", "2.0") \
        .load()
    
    # Process and save to data lake
    df.write \
        .mode("overwrite") \
        .partitionBy("modified_date") \
        .parquet("s3://datalake/sharepoint-reports/")


def example_direct_api_usage():
    """Example 4: Direct API usage without Spark."""
    print("\n=== Example 4: Direct API Usage ===")
    
    # Configuration from environment or direct values
    config = SharePointConnectorConfig(
        site_url="https://contoso.sharepoint.com/sites/data",
        client_id="your-client-id",
        client_secret="your-client-secret", 
        tenant_id="your-tenant-id",
        library_name="Documents"
    )
    
    try:
        # Initialize authenticator and client
        authenticator = SharePointAuthenticator(
            config.client_id, config.client_secret, config.tenant_id
        )
        client = SharePointAPIClient(config.site_url, authenticator)
        
        # List files
        files = client.list_files(config.library_name)
        print(f"Found {len(files)} files")
        
        # Download a specific file (if any exist)
        if files:
            first_file = files[0]
            file_path = first_file.get('FileRef')
            if file_path:
                content = client.download_file(file_path)
                print(f"Downloaded {len(content)} bytes from {first_file.get('FileLeafRef')}")
        
    except Exception as e:
        print(f"API usage example failed: {e}")


def example_environment_config():
    """Example 5: Using environment variables for configuration."""
    print("\n=== Example 5: Environment Configuration ===")
    
    # Set environment variables (in practice, these would be set externally)
    env_vars = {
        "SHAREPOINT_SITE_URL": "https://contoso.sharepoint.com/sites/data",
        "SHAREPOINT_CLIENT_ID": "your-client-id",
        "SHAREPOINT_CLIENT_SECRET": "your-client-secret",
        "SHAREPOINT_TENANT_ID": "your-tenant-id",
        "SHAREPOINT_LIBRARY_NAME": "Documents",
        "SHAREPOINT_BATCH_SIZE": "150",
        "SHAREPOINT_MAX_PARTITIONS": "20"
    }
    
    # Temporarily set environment variables for demo
    original_values = {}
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        # Create configuration from environment
        config = SharePointConnectorConfig.from_environment()
        print(f"Loaded configuration for site: {config.site_url}")
        print(f"Library: {config.library_name}")
        print(f"Batch size: {config.batch_size}")
        print(f"Max partitions: {config.max_partitions}")
        
        # Validate configuration
        validation_errors = config.validate()
        if validation_errors:
            print("Configuration validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print("Configuration is valid!")
    
    finally:
        # Restore original environment variables
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def main():
    """Run all examples."""
    print("SharePoint Connector Examples")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_folder_specific()
        example_performance_tuning()
        example_direct_api_usage()
        example_environment_config()
        
        print("\n" + "=" * 50)
        print("Examples completed!")
        print("\nNote: Replace placeholder values with your actual SharePoint configuration.")
        print("For production use, store credentials securely (e.g., Azure Key Vault).")
        
    except Exception as e:
        print(f"Example execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()