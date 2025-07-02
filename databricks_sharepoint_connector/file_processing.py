"""
File Content Processing

Handles processing of different file formats including CSV, JSON, Parquet, and text files
with format-specific validation and content extraction.
"""

import json
import csv
from io import StringIO, BytesIO
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FileContentProcessor:
    """Handles processing of different file formats."""
    
    def process_file_content(self, content: bytes, file_name: str) -> str:
        """
        Process file content based on format.
        
        Args:
            content: File content as bytes
            file_name: Name of the file to determine format
            
        Returns:
            Processed content as string
        """
        file_extension = file_name.lower().split('.')[-1] if '.' in file_name else ''
        
        try:
            if file_extension == 'csv':
                return self._process_csv_content(content)
            elif file_extension == 'json':
                return self._process_json_content(content)
            elif file_extension == 'parquet':
                return self._process_parquet_content(content)
            elif file_extension in ['txt', 'log']:
                return self._process_text_content(content)
            else:
                # Default text processing
                return self._process_text_content(content)
        except Exception as e:
            logger.warning(f"Failed to process {file_name} as {file_extension}: {e}")
            return f"Processing error: {str(e)}"
    
    def _process_csv_content(self, content: bytes) -> str:
        """
        Process CSV file content.
        
        Args:
            content: CSV file content as bytes
            
        Returns:
            CSV summary as string
        """
        try:
            text_content = content.decode('utf-8')
            # Validate CSV structure
            csv_reader = csv.reader(StringIO(text_content))
            rows = list(csv_reader)
            
            if not rows:
                return "Empty CSV file"
            
            headers = rows[0] if rows else []
            row_count = len(rows)
            col_count = len(headers) if headers else 0
            
            summary = f"CSV file: {row_count} rows, {col_count} columns"
            if headers:
                summary += f", Headers: {', '.join(headers[:5])}"
                if len(headers) > 5:
                    summary += f" (and {len(headers) - 5} more)"
            
            return summary
            
        except Exception as e:
            return f"CSV processing error: {e}"
    
    def _process_json_content(self, content: bytes) -> str:
        """
        Process JSON file content.
        
        Args:
            content: JSON file content as bytes
            
        Returns:
            JSON summary or formatted content
        """
        try:
            text_content = content.decode('utf-8')
            json_data = json.loads(text_content)
            
            # For small JSON files, return formatted content
            if len(text_content) < 10000:  # Less than 10KB
                return json.dumps(json_data, indent=2)
            else:
                # For large files, return summary
                data_type = type(json_data).__name__
                if isinstance(json_data, list):
                    return f"JSON array with {len(json_data)} items"
                elif isinstance(json_data, dict):
                    keys = list(json_data.keys())[:5]
                    summary = f"JSON object with {len(json_data)} keys: {keys}"
                    if len(json_data) > 5:
                        summary += f" (and {len(json_data) - 5} more)"
                    return summary
                else:
                    return f"JSON {data_type}: {str(json_data)[:100]}..."
                    
        except Exception as e:
            return f"JSON processing error: {e}"
    
    def _process_parquet_content(self, content: bytes) -> str:
        """
        Process Parquet file content.
        
        Args:
            content: Parquet file content as bytes
            
        Returns:
            Parquet metadata summary
        """
        try:
            # Try to import pyarrow
            import pyarrow.parquet as pq
            
            parquet_file = pq.ParquetFile(BytesIO(content))
            schema_info = str(parquet_file.schema)
            num_rows = parquet_file.metadata.num_rows
            num_cols = len(parquet_file.schema)
            
            summary = f"Parquet file: {num_rows} rows, {num_cols} columns"
            
            # Add column names
            column_names = [field.name for field in parquet_file.schema]
            if column_names:
                summary += f", Columns: {', '.join(column_names[:5])}"
                if len(column_names) > 5:
                    summary += f" (and {len(column_names) - 5} more)"
            
            return summary
            
        except ImportError:
            return "Parquet processing requires pyarrow library"
        except Exception as e:
            return f"Parquet processing error: {e}"
    
    def _process_text_content(self, content: bytes) -> str:
        """
        Process text file content.
        
        Args:
            content: Text file content as bytes
            
        Returns:
            Text content or summary for large files
        """
        try:
            text_content = content.decode('utf-8')
            
            # For small files, return full content
            if len(text_content) < 5000:  # Less than 5KB
                return text_content
            else:
                # For large files, return summary
                lines = text_content.split('\n')
                return f"Text file: {len(lines)} lines, {len(text_content)} characters"
                
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                try:
                    text_content = content.decode(encoding)
                    return f"Text file ({encoding}): {len(content)} bytes"
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, treat as binary
            return f"Binary content: {len(content)} bytes"