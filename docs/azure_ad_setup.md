# Azure AD Setup Guide

This guide walks you through setting up Azure AD app registration for the SharePoint connector.

## Prerequisites

- Access to Azure Active Directory admin portal
- SharePoint admin permissions (for granting consent)
- PowerShell (for verification steps)

## Step 1: Create Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **"New registration"**
4. Fill in the details:
   - **Name**: `SharePoint Connector App`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: Leave blank for now
5. Click **"Register"**

## Step 2: Note Important IDs

After registration, copy these values (you'll need them for the connector):

- **Application (client) ID**
- **Directory (tenant) ID**

## Step 3: Create Client Secret

1. In your app registration, go to **"Certificates & secrets"**
2. Click **"New client secret"**
3. Add description: `SharePoint Connector Secret`
4. Set expiration: `24 months` (recommended)
5. Click **"Add"**
6. **IMPORTANT**: Copy the secret value immediately (you won't see it again)

## Step 4: Configure API Permissions

1. Go to **"API permissions"**
2. Click **"Add a permission"**
3. Select **"SharePoint"**
4. Choose **"Application permissions"** (not delegated)
5. Add these permissions:
   - `Sites.Read.All` - Read items and lists in all site collections
   - `Sites.ReadWrite.All` - Read and write items and lists in all site collections (if you need write access)

## Step 5: Grant Admin Consent

1. In the **"API permissions"** section
2. Click **"Grant admin consent for [Your Organization]"**
3. Confirm by clicking **"Yes"**
4. Verify all permissions show **"Granted for [Your Organization]"**

## Step 6: Test the Configuration

Create a test script to verify your setup:

```python
from databricks_sharepoint_connector import SharePointConnectorConfig, SharePointAuthenticator, SharePointAPIClient

# Replace with your actual values
config = SharePointConnectorConfig(
    site_url="https://yourtenant.sharepoint.com/sites/yoursite",
    client_id="your-client-id",
    client_secret="your-client-secret", 
    tenant_id="your-tenant-id",
    library_name="Documents"  # or another library name
)

try:
    # Test authentication
    authenticator = SharePointAuthenticator(
        config.client_id, config.client_secret, config.tenant_id
    )
    
    # Test API access
    client = SharePointAPIClient(config.site_url, authenticator)
    files = client.list_files(config.library_name)
    
    print(f"✅ Success! Found {len(files)} files in {config.library_name}")
    
except Exception as e:
    print(f"❌ Error: {e}")
```

## Step 7: Use with Environment Variables (Recommended)

For production, use environment variables:

```bash
export SHAREPOINT_SITE_URL="https://yourtenant.sharepoint.com/sites/yoursite"
export SHAREPOINT_CLIENT_ID="your-client-id"
export SHAREPOINT_CLIENT_SECRET="your-client-secret"
export SHAREPOINT_TENANT_ID="your-tenant-id"
export SHAREPOINT_LIBRARY_NAME="Documents"
```

Then use:

```python
from databricks_sharepoint_connector import SharePointConnectorConfig

config = SharePointConnectorConfig.from_environment()
```

## Troubleshooting

### Authentication Errors

**Error**: `AADSTS70011: The provided value for the input parameter 'scope' is not valid`
- **Solution**: Check that your site URL is correct and accessible

**Error**: `AADSTS700016: Application with identifier 'xxx' was not found`
- **Solution**: Verify your client ID is correct

**Error**: `AADSTS7000215: Invalid client secret is provided`
- **Solution**: Check your client secret, may need to create a new one

### Permission Errors

**Error**: `403 Forbidden` when accessing SharePoint
- **Solution**: Ensure admin consent was granted for the required permissions
- **Check**: Verify the app has `Sites.Read.All` or `Sites.ReadWrite.All` permissions

**Error**: `404 Not Found` for site or library
- **Solution**: Verify the site URL and library name are correct
- **Check**: Ensure the service principal has access to the specific site

### Network/Connection Errors

**Error**: Connection timeouts
- **Solution**: Configure longer timeouts in Spark:
  ```python
  spark.conf.set("spark.network.timeout", "800s")
  spark.conf.set("spark.executor.heartbeatInterval", "60s")
  ```

## Security Best Practices

1. **Rotate secrets regularly** (every 6-12 months)
2. **Use Azure Key Vault** for storing secrets in production
3. **Principle of least privilege** - only grant necessary permissions
4. **Monitor app usage** through Azure AD logs
5. **Never commit secrets** to source code repositories

## PowerShell Verification

Use this PowerShell script to verify your setup:

```powershell
# Install required module
Install-Module -Name PnP.PowerShell -Force

# Connect using app registration
Connect-PnPOnline -Url "https://yourtenant.sharepoint.com/sites/yoursite" `
  -ClientId "your-client-id" `
  -ClientSecret "your-client-secret" `
  -Tenant "your-tenant-id"

# Test access
Get-PnPList
Get-PnPListItem -List "Documents" | Select-Object Title
```

## Next Steps

Once your Azure AD app is configured:

1. Install the SharePoint connector: `pip install DatabricksSharepointRestConnector`
2. Use the test CLI: `python -m databricks_sharepoint_connector.cli test-connection`
3. Try the examples in the `examples/` directory
4. Integrate with your Spark workflows

For more information, see the main README.md file.