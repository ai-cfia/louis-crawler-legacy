#!/usr/bin/env python3
"""
Test script to verify that the pipeline selection works correctly 
based on the STORAGE_MODE environment variable.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from louis.crawler.spiders.goldie_playwright_parallel import get_pipeline_config_for_storage_mode
import louis.db as db


def test_pipeline_selection():
    """Test pipeline selection with different STORAGE_MODE values."""
    
    # Save original value
    original_storage_mode = os.environ.get('STORAGE_MODE')
    
    test_cases = [
        ('database', 'louis.crawler.pipelines.LouisPipeline'),
        ('disk', 'louis.crawler.pipelines.DiskPipeline'),
        ('s3', 'louis.crawler.pipelines.S3Pipeline'),
        ('invalid', 'louis.crawler.pipelines.LouisPipeline'),  # Should fallback
        (None, 'louis.crawler.pipelines.LouisPipeline'),  # Default
    ]
    
    print("Testing pipeline selection based on STORAGE_MODE:")
    print("=" * 60)
    
    for storage_mode, expected_pipeline in test_cases:
        # Set environment variable
        if storage_mode is None:
            if 'STORAGE_MODE' in os.environ:
                del os.environ['STORAGE_MODE']
            mode_display = 'None (default)'
        else:
            os.environ['STORAGE_MODE'] = storage_mode
            mode_display = storage_mode
        
        # Get storage mode from db module
        actual_storage_mode = db.get_storage_mode()
        
        # Get pipeline configuration
        pipeline_config = get_pipeline_config_for_storage_mode()
        
        # Check if expected pipeline is in the configuration
        pipeline_found = expected_pipeline in pipeline_config
        actual_pipeline = list(pipeline_config.keys())[0] if pipeline_config else 'None'
        
        # Print results
        status = "✅ PASS" if pipeline_found else "❌ FAIL"
        print(f"{status} STORAGE_MODE={mode_display}")
        print(f"   Resolved to: {actual_storage_mode}")
        print(f"   Expected pipeline: {expected_pipeline}")
        print(f"   Actual pipeline: {actual_pipeline}")
        print(f"   Pipeline config: {pipeline_config}")
        print()
    
    # Restore original value
    if original_storage_mode is not None:
        os.environ['STORAGE_MODE'] = original_storage_mode
    elif 'STORAGE_MODE' in os.environ:
        del os.environ['STORAGE_MODE']
    
    print("Test completed!")


if __name__ == '__main__':
    test_pipeline_selection() 