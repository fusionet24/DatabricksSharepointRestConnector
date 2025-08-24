"""
Command Line Interface for SharePoint Connector

Provides command-line utilities for testing and managing the SharePoint connector.
"""

import argparse
import sys
import os
import logging
from typing import Optional

from .config import SharePointConnectorConfig, configure_logging
from .sharepoint_auth import SharePointAuthenticator
from .sharepoint_client import SharePointAPIClient


def test_connection(config: SharePointConnectorConfig) -> bool:
    """
    Test SharePoint connection with provided configuration.
    
    Args:
        config: SharePoint connector configuration
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        print(f"Testing connection to {config.site_url}...")
        
        # Test authentication
        authenticator = SharePointAuthenticator(
            config.client_id, config.client_secret, config.tenant_id
        )
        
        # Test API access
        client = SharePointAPIClient(config.site_url, authenticator)
        files = client.list_files(config.library_name, config.folder_path)
        
        print(f"✅ Connection successful! Found {len(files)} files in library '{config.library_name}'")
        
        # Show first few files
        if files:
            print("\nFirst few files:")
            for i, file_info in enumerate(files[:5]):
                file_name = file_info.get('FileLeafRef', 'Unknown')
                file_size = file_info.get('File', {}).get('Length', 0) if isinstance(file_info.get('File'), dict) else 0
                print(f"  {i+1}. {file_name} ({file_size} bytes)")
            
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SharePoint Connector CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection using environment variables
  sharepoint-connector-test test-connection
  
  # Test connection with explicit parameters
  sharepoint-connector-test test-connection \\
    --site-url https://contoso.sharepoint.com/sites/data \\
    --client-id your-client-id \\
    --client-secret your-client-secret \\
    --tenant-id your-tenant-id \\
    --library-name Documents
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test connection command
    test_parser = subparsers.add_parser('test-connection', help='Test SharePoint connection')
    test_parser.add_argument('--site-url', help='SharePoint site URL')
    test_parser.add_argument('--client-id', help='Azure AD client ID')
    test_parser.add_argument('--client-secret', help='Azure AD client secret')
    test_parser.add_argument('--tenant-id', help='Azure AD tenant ID')
    test_parser.add_argument('--library-name', help='SharePoint library name')
    test_parser.add_argument('--folder-path', help='Optional folder path')
    test_parser.add_argument('--log-level', default='INFO', 
                           choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                           help='Logging level')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configure logging
    configure_logging(args.log_level if hasattr(args, 'log_level') else 'INFO')
    
    if args.command == 'test-connection':
        try:
            # Create configuration from args or environment
            if args.site_url and args.client_id and args.client_secret and args.tenant_id and args.library_name:
                config = SharePointConnectorConfig(
                    site_url=args.site_url,
                    client_id=args.client_id,
                    client_secret=args.client_secret,
                    tenant_id=args.tenant_id,
                    library_name=args.library_name,
                    folder_path=args.folder_path
                )
            else:
                print("Using configuration from environment variables...")
                config = SharePointConnectorConfig.from_environment()
            
            # Validate configuration
            validation_errors = config.validate()
            if validation_errors:
                print(f"Configuration validation failed:")
                for error in validation_errors:
                    print(f"  - {error}")
                return 1
            
            # Test connection
            success = test_connection(config)
            return 0 if success else 1
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())