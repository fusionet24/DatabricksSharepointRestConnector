# Spark SharePoint Connector

A custom Apache Spark data source that enables seamless integration with Microsoft SharePoint, allowing you to read and write files directly from SharePoint document libraries using familiar Spark DataFrame APIs.

## Features

- 🚀 **Simple Integration** - Read SharePoint files as Spark DataFrames with just a few lines of code
- 📁 **Multiple Formats** - Support for CSV, JSON, Parquet, and text files
- 🔐 **Secure Authentication** - Azure AD service principal authentication
- ⚡ **High Performance** - Parallel processing with intelligent partitioning
- 🔄 **Automatic Retries** - Built-in retry logic with exponential backoff
- 📊 **Batch Operations** - Efficient folder and library scanning

## Prerequisites

- Apache Spark 3.4+ (with Python Data Source API support)
- Python 3.8+
- Azure AD App Registration with SharePoint permissions

## Installation

```bash
pip install DatabricksSharepointRestConnector
```

Or install from source:

```bash
git clone https://github.com/fusionet24/DatabricksSharepointRestConnector
cd DatabricksSharepointRestConnector
pip install -e .
```

## Quick Start

### 1. Set up Azure AD App Registration

Before using the connector, you need to register an app in Azure AD:

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Click "New registration" and create your app
3. Under "Certificates & secrets", create a new client secret
4. Under "API permissions", add SharePoint permissions:
   - `Sites.Read.All` (for reading files)
   - `Sites.ReadWrite.All` (for reading and writing files)
5. Grant admin consent for the permissions

### 2. Basic Usage

```python
from pyspark.sql import SparkSession


# Read files from SharePoint
df = spark.read.format("sharepoint") \
    .option("site_url", "https://contoso.sharepoint.com/sites/data") \
    .option("client_id", "your-client-id") \
    .option("client_secret", "your-client-secret") \
    .option("tenant_id", "your-tenant-id") \
    .option("library_name", "Documents") \
    .load()

# Show the files
df.show()

# Display schema
df.printSchema()
```

### 3. Reading from a Specific Folder

```python
# Read files from a specific folder
df = spark.read.format("sharepoint") \
    .option("site_url", "https://contoso.sharepoint.com/sites/data") \
    .option("client_id", "your-client-id") \
    .option("client_secret", "your-client-secret") \
    .option("tenant_id", "your-tenant-id") \
    .option("library_name", "Documents") \
    .option("folder_path", "/Reports/2024/Q1") \
    .load()

# Filter for CSV files only
csv_files = df.filter(df.file_name.endswith(".csv"))
csv_files.select("file_name", "file_size", "modified_date").show()
```

### 4. Processing File Content

```python
# Read and process file content
df = spark.read.format("sharepoint") \
    .option("site_url", "https://contoso.sharepoint.com/sites/data") \
    .option("client_id", "your-client-id") \
    .option("client_secret", "your-client-secret") \
    .option("tenant_id", "your-tenant-id") \
    .option("library_name", "Documents") \
    .option("process_file_content", "true") \
    .load()

# Find all JSON files and display their content
json_files = df.filter(df.file_name.endswith(".json"))
json_files.select("file_name", "content").show(truncate=False)
```

## Configuration Options

| Option | Description | Default | Required |
|--------|-------------|---------|----------|
| `site_url` | SharePoint site URL | - | Yes |
| `client_id` | Azure AD application ID | - | Yes |
| `client_secret` | Azure AD client secret | - | Yes |
| `tenant_id` | Azure AD tenant ID | - | Yes |
| `library_name` | Document library name | - | Yes |
| `folder_path` | Specific folder path within library | - | No |
| `batch_size` | Files per batch operation | 100 | No |
| `max_partitions` | Maximum Spark partitions | 100 | No |
| `process_file_content` | Read file content (not just metadata) | true | No |
| `max_retries` | Maximum retry attempts | 3 | No |

## Common Use Cases

### Export SharePoint Data to Data Lake

```python
# Read all reports from SharePoint
reports_df = spark.read.format("sharepoint") \
    .option("site_url", "https://contoso.sharepoint.com/sites/analytics") \
    .option("client_id", "your-client-id") \
    .option("client_secret", "your-client-secret") \
    .option("tenant_id", "your-tenant-id") \
    .option("library_name", "Reports") \
    .option("folder_path", "/monthly-reports") \
    .load()

# Save to data lake with partitioning
reports_df.write \
    .mode("overwrite") \
    .partitionBy("modified_date") \
    .parquet("s3://datalake/sharepoint-reports/")
```

## Troubleshooting

### Authentication Errors

If you get authentication errors:
1. Verify your client ID and secret are correct
2. Check that your app has proper SharePoint permissions
3. Ensure admin consent was granted for the permissions
4. Verify the tenant ID matches your SharePoint tenant

### Connection Timeouts

For slow networks or large files:
```python
spark.conf.set("spark.network.timeout", "800s")
spark.conf.set("spark.executor.heartbeatInterval", "60s")
```

### Rate Limiting

The connector automatically handles SharePoint rate limiting with exponential backoff. If you still experience issues:
```python
.option("max_retries", "5") \
.option("retry_backoff_multiplier", "2.0")
```

