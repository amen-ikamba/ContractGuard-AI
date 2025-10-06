"""
AWS Textract helper utilities
"""

import boto3
import time
from typing import Dict, Any
from .logger import get_logger

logger = get_logger(__name__)


class TextractHelper:
    """Helper class for AWS Textract operations"""
    
    def __init__(self):
        self.textract = boto3.client('textract')
    
    def extract_text_from_s3(
        self,
        bucket: str,
        key: str,
        feature_types: list = None
    ) -> Dict[str, Any]:
        """
        Extract text from document in S3 using Textract.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            feature_types: List of features to extract (TABLES, FORMS)
        
        Returns:
            Dict with extracted text and structure
        """
        
        if feature_types is None:
            feature_types = ['TABLES', 'FORMS']
        
        try:
            # Start async job
            response = self.textract.start_document_analysis(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                FeatureTypes=feature_types
            )
            
            job_id = response['JobId']
            logger.info(f"Started Textract job: {job_id}")
            
            # Wait for completion
            result = self._wait_for_job_completion(job_id)
            
            # Parse results
            parsed = self._parse_textract_results(result)
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error with Textract: {str(e)}")
            raise
    
    def _wait_for_job_completion(
        self,
        job_id: str,
        max_wait: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for Textract job to complete.
        
        Args:
            job_id: Textract job ID
            max_wait: Maximum wait time in seconds
            poll_interval: Time between status checks
        
        Returns:
            Complete Textract results
        """
        
        waited = 0
        while waited < max_wait:
            response = self.textract.get_document_analysis(JobId=job_id)
            status = response['JobStatus']
            
            if status == 'SUCCEEDED':
                logger.info(f"Textract job {job_id} completed successfully")
                
                # Get all pages
                blocks = response['Blocks']
                next_token = response.get('NextToken')
                
                while next_token:
                    response = self.textract.get_document_analysis(
                        JobId=job_id,
                        NextToken=next_token
                    )
                    blocks.extend(response['Blocks'])
                    next_token = response.get('NextToken')
                
                return {'Blocks': blocks, 'JobStatus': 'SUCCEEDED'}
            
            elif status == 'FAILED':
                error_msg = response.get('StatusMessage', 'Unknown error')
                logger.error(f"Textract job {job_id} failed: {error_msg}")
                raise Exception(f"Textract job failed: {error_msg}")
            
            elif status == 'IN_PROGRESS':
                time.sleep(poll_interval)
                waited += poll_interval
            
            else:
                logger.warning(f"Unknown Textract status: {status}")
                time.sleep(poll_interval)
                waited += poll_interval
        
        raise Exception(f"Textract job {job_id} timed out after {max_wait}s")
    
    def _parse_textract_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Textract results into structured format.
        
        Args:
            results: Raw Textract results
        
        Returns:
            Structured text and metadata
        """
        
        blocks = results.get('Blocks', [])
        
        # Extract text
        lines = []
        tables = []
        key_value_pairs = []
        
        for block in blocks:
            block_type = block['BlockType']
            
            if block_type == 'LINE':
                lines.append({
                    'text': block.get('Text', ''),
                    'confidence': block.get('Confidence', 0),
                    'id': block.get('Id')
                })
            
            elif block_type == 'TABLE':
                # Extract table structure
                table = self._extract_table(block, blocks)
                if table:
                    tables.append(table)
            
            elif block_type == 'KEY_VALUE_SET':
                # Extract key-value pairs from forms
                if block.get('EntityTypes', [None])[0] == 'KEY':
                    kv_pair = self._extract_key_value(block, blocks)
                    if kv_pair:
                        key_value_pairs.append(kv_pair)
        
        # Combine all text
        full_text = '\n'.join([line['text'] for line in lines])
        
        return {
            'full_text': full_text,
            'lines': lines,
            'tables': tables,
            'key_value_pairs': key_value_pairs,
            'page_count': self._count_pages(blocks),
            'word_count': len(full_text.split())
        }
    
    def _extract_table(self, table_block: Dict, all_blocks: list) -> Dict:
        """Extract table structure from Textract blocks"""
        
        # This is simplified - full implementation would parse table cells
        return {
            'id': table_block.get('Id'),
            'confidence': table_block.get('Confidence', 0),
            'rows': table_block.get('RowCount', 0),
            'columns': table_block.get('ColumnCount', 0)
        }
    
    def _extract_key_value(self, key_block: Dict, all_blocks: list) -> Dict:
        """Extract key-value pair from form"""
        
        # Simplified extraction
        return {
            'key': key_block.get('Text', ''),
            'confidence': key_block.get('Confidence', 0)
        }
    
    def _count_pages(self, blocks: list) -> int:
        """Count number of pages in document"""
        
        pages = set()
        for block in blocks:
            if 'Page' in block:
                pages.add(block['Page'])
        
        return len(pages)