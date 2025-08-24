"""
Setup configuration for Databricks SharePoint REST Connector
"""

from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "A custom Apache Spark data source for Microsoft SharePoint integration"

# Read version from package
version = "1.0.0"

setup(
    name="DatabricksSharepointRestConnector",
    version=version,
    author="FusionNet24",
    author_email="contact@fusionet24.com",
    description="A custom Apache Spark data source for Microsoft SharePoint using Python Data Source API v2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fusionet24/DatabricksSharepointRestConnector",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Data Engineers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.8",
    install_requires=[
        "msal>=1.20.0",
        "requests>=2.25.0",
        "tenacity>=8.0.0",
    ],
    extras_require={
        "spark": [
            "pyspark>=3.4.0",
        ],
        "parquet": [
            "pyarrow>=10.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "all": [
            "pyspark>=3.4.0",
            "pyarrow>=10.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "sharepoint-connector-test=databricks_sharepoint_connector.cli:main",
        ],
    },
    keywords=[
        "spark", "sharepoint", "databricks", "data-source", "microsoft", 
        "azure", "rest-api", "connector", "etl", "data-engineering"
    ],
    project_urls={
        "Bug Reports": "https://github.com/fusionet24/DatabricksSharepointRestConnector/issues",
        "Source": "https://github.com/fusionet24/DatabricksSharepointRestConnector",
        "Documentation": "https://github.com/fusionet24/DatabricksSharepointRestConnector#readme",
    },
)