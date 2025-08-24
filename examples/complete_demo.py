"""
Complete Working Example with Real SharePoint Configuration

This example shows how to use the SharePoint connector with actual credentials.
Replace the placeholder values with your real SharePoint configuration.
"""

import os
from databricks_sharepoint_connector import (
    SharePointConnectorConfig,
    SharePointAuthenticator,
    SharePointAPIClient,
    configure_logging
)

def create_spark_dataframe_example():
    """Example of reading SharePoint data as a Spark DataFrame."""
    
    try:
        from pyspark.sql import SparkSession
        
        # Create Spark session
        spark = SparkSession.builder \
            .appName("SharePoint Connector Demo") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.network.timeout", "800s") \
            .config("spark.executor.heartbeatInterval", "60s") \
            .getOrCreate()
        
        print("✅ Spark session created successfully!")
        
        # Read data from SharePoint
        df = spark.read.format("sharepoint") \
            .option("site_url", "https://YOUR_TENANT.sharepoint.com/sites/YOUR_SITE") \
            .option("client_id", "YOUR_CLIENT_ID") \
            .option("client_secret", "YOUR_CLIENT_SECRET") \
            .option("tenant_id", "YOUR_TENANT_ID") \
            .option("library_name", "Documents") \
            .option("folder_path", "/Reports") \
            .option("batch_size", "100") \
            .option("max_partitions", "20") \
            .option("process_file_content", "true") \
            .option("log_level", "INFO") \
            .load()
        
        print("✅ SharePoint DataFrame created successfully!")
        
        # Show schema
        print("\nDataFrame Schema:")
        df.printSchema()
        
        # Show sample data
        print("\nSample Data (first 5 rows):")
        df.show(5, truncate=False)
        
        # Filter for specific file types
        csv_files = df.filter(df.file_name.endswith(".csv"))
        print(f"\nFound {csv_files.count()} CSV files")
        
        # Save to data lake (example)
        output_path = "/tmp/sharepoint_data"
        df.write.mode("overwrite").parquet(output_path)
        print(f"✅ Data saved to {output_path}")
        
        spark.stop()
        
    except ImportError:
        print("❌ PySpark is not available. Install with: pip install pyspark>=3.4.0")
    except Exception as e:
        print(f"❌ Error: {e}")


def direct_api_example():
    """Example of using the SharePoint API directly."""
    
    # Configure logging
    configure_logging("INFO")
    
    try:
        # Create configuration
        config = SharePointConnectorConfig(
            site_url="https://YOUR_TENANT.sharepoint.com/sites/YOUR_SITE",
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET",
            tenant_id="YOUR_TENANT_ID",
            library_name="Documents"
        )
        
        print("✅ Configuration created successfully!")
        
        # Validate configuration
        errors = config.validate()
        if errors:
            print(f"❌ Configuration errors: {errors}")
            return
        
        # Initialize authenticator and client
        authenticator = SharePointAuthenticator(
            config.client_id, 
            config.client_secret, 
            config.tenant_id
        )
        
        client = SharePointAPIClient(config.site_url, authenticator)
        
        print("✅ SharePoint client initialized successfully!")
        
        # List files in the library
        print(f"📁 Listing files in library: {config.library_name}")
        files = client.list_files(config.library_name)
        
        print(f"✅ Found {len(files)} files!")
        
        # Display first few files
        for i, file_info in enumerate(files[:5]):
            file_name = file_info.get('FileLeafRef', 'Unknown')
            file_size = file_info.get('File', {}).get('Length', 0) if isinstance(file_info.get('File'), dict) else 0
            modified = file_info.get('Modified', 'Unknown')
            print(f"  {i+1}. {file_name} ({file_size:,} bytes) - Modified: {modified}")
        
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more files")
        
        # Download first file (if available)
        if files:
            first_file = files[0]
            file_path = first_file.get('FileRef')
            file_name = first_file.get('FileLeafRef')
            
            if file_path:
                print(f"\n📥 Downloading file: {file_name}")
                content = client.download_file(file_path)
                print(f"✅ Downloaded {len(content):,} bytes")
                
                # Save to local file
                local_path = f"/tmp/{file_name}"
                with open(local_path, 'wb') as f:
                    f.write(content)
                print(f"✅ Saved to: {local_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def environment_variables_example():
    """Example using environment variables for configuration."""
    
    print("🔧 Environment Variables Example")
    print("=" * 50)
    
    # Show required environment variables
    required_vars = [
        "SHAREPOINT_SITE_URL",
        "SHAREPOINT_CLIENT_ID", 
        "SHAREPOINT_CLIENT_SECRET",
        "SHAREPOINT_TENANT_ID",
        "SHAREPOINT_LIBRARY_NAME"
    ]
    
    print("Required environment variables:")
    for var in required_vars:
        value = os.getenv(var, "NOT SET")
        masked_value = "***" if "SECRET" in var and value != "NOT SET" else value
        print(f"  {var}: {masked_value}")
    
    # Try to create config from environment
    try:
        config = SharePointConnectorConfig.from_environment()
        errors = config.validate()
        
        if not errors:
            print("✅ Environment configuration is valid!")
            print(f"Site URL: {config.site_url}")
            print(f"Library: {config.library_name}")
        else:
            print(f"❌ Environment configuration errors: {errors}")
            
    except Exception as e:
        print(f"❌ Failed to load from environment: {e}")


def main():
    """Run all examples."""
    
    print("SharePoint Connector - Complete Working Example")
    print("=" * 60)
    print()
    
    print("🔑 IMPORTANT: Replace placeholder values with your actual SharePoint configuration:")
    print("  - YOUR_TENANT: Your SharePoint tenant name")
    print("  - YOUR_SITE: Your SharePoint site name") 
    print("  - YOUR_CLIENT_ID: Azure AD app client ID")
    print("  - YOUR_CLIENT_SECRET: Azure AD app client secret")
    print("  - YOUR_TENANT_ID: Azure AD tenant ID")
    print()
    
    print("📋 Example 1: Direct API Usage")
    print("-" * 30)
    direct_api_example()
    print()
    
    print("📋 Example 2: Environment Variables")
    print("-" * 30)
    environment_variables_example()
    print()
    
    print("📋 Example 3: Spark DataFrame")
    print("-" * 30)
    create_spark_dataframe_example()
    print()
    
    print("✅ Examples completed!")
    print()
    print("🔒 Security Notes:")
    print("  - Never hardcode credentials in source code")
    print("  - Use Azure Key Vault or environment variables for production")
    print("  - Rotate client secrets regularly")
    print("  - Follow principle of least privilege for SharePoint permissions")


if __name__ == "__main__":
    main()