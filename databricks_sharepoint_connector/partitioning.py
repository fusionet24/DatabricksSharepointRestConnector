"""
Advanced Partitioning and Performance Optimization

Intelligent partitioning strategies for SharePoint data to maximize performance
in large SharePoint environments with size-aware distribution.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class SharePointPartitionStrategy:
    """Advanced partitioning strategies for SharePoint data."""
    
    def __init__(self, target_partition_size_mb: int = 150, max_partitions: int = 1000):
        """
        Initialize partition strategy.
        
        Args:
            target_partition_size_mb: Target size per partition in MB
            max_partitions: Maximum number of partitions to create
        """
        self.target_partition_size_mb = target_partition_size_mb
        self.max_partitions = max_partitions
    
    def calculate_optimal_partitions(self, file_list: List[Dict], cluster_cores: int = 50) -> List[List[Dict]]:
        """
        Calculate optimal partitioning based on file sizes and cluster capacity.
        
        Args:
            file_list: List of file metadata dictionaries
            cluster_cores: Number of cores available in the cluster
            
        Returns:
            List of partitions, each containing a list of files
        """
        if not file_list:
            return []
        
        # Analyze file size distribution
        total_size_bytes = sum(self._get_file_size(f) for f in file_list)
        total_size_mb = total_size_bytes / (1024 * 1024)
        
        # Calculate partition count based on size
        size_based_partitions = max(1, int(total_size_mb / self.target_partition_size_mb))
        
        # Calculate partition count based on cluster capacity
        core_based_partitions = cluster_cores * 2  # 2 tasks per core
        
        # Use the smaller value to avoid over-partitioning
        optimal_partitions = min(size_based_partitions, core_based_partitions, self.max_partitions)
        
        logger.info(f"Partitioning {len(file_list)} files into {optimal_partitions} partitions "
                   f"(total size: {total_size_mb:.2f} MB)")
        
        # Group files into partitions
        if len(file_list) <= optimal_partitions:
            # One file per partition if we have more partitions than files
            return [[f] for f in file_list]
        
        # Distribute files across partitions considering size balance
        return self._balance_partitions_by_size(file_list, optimal_partitions)
    
    def _balance_partitions_by_size(self, file_list: List[Dict], num_partitions: int) -> List[List[Dict]]:
        """
        Balance partitions by file size to prevent data skew.
        
        Args:
            file_list: List of file metadata dictionaries
            num_partitions: Number of partitions to create
            
        Returns:
            List of balanced partitions
        """
        # Sort files by size (descending)
        sorted_files = sorted(
            file_list,
            key=self._get_file_size,
            reverse=True
        )
        
        # Initialize partitions with size tracking
        partitions = [[] for _ in range(num_partitions)]
        partition_sizes = [0] * num_partitions
        
        # Distribute files using greedy algorithm
        for file_info in sorted_files:
            file_size = self._get_file_size(file_info)
            
            # Find partition with smallest current size
            min_partition_idx = partition_sizes.index(min(partition_sizes))
            
            # Add file to that partition
            partitions[min_partition_idx].append(file_info)
            partition_sizes[min_partition_idx] += file_size
        
        # Remove empty partitions and log partition sizes
        non_empty_partitions = [p for p in partitions if p]
        for i, partition in enumerate(non_empty_partitions):
            size_mb = sum(self._get_file_size(f) for f in partition) / (1024 * 1024)
            logger.debug(f"Partition {i}: {len(partition)} files, {size_mb:.2f} MB")
        
        return non_empty_partitions
    
    def _get_file_size(self, file_info: Dict) -> int:
        """
        Extract file size from file metadata.
        
        Args:
            file_info: File metadata dictionary
            
        Returns:
            File size in bytes
        """
        # Handle different SharePoint API response formats
        if 'File' in file_info and isinstance(file_info['File'], dict):
            return file_info['File'].get('Length', 0)
        elif 'Length' in file_info:
            return file_info.get('Length', 0)
        else:
            return 0