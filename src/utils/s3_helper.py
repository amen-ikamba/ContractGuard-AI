"""
S3 helper utilities for document storage
"""

import boto3
import os
from typing import Optional, BinaryIO
from botocore.exceptions import ClientError
from .logger import get_logger

logger = get_logger(__name__)


class S3Helper:
    """Helper class for S3 operations"""
    
    def __init__(self, bucket_name: Optional[str] = None):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name or os.getenv('CONTRACTS_BUCKET')
        
        if not self.bucket_name:
            logger.warning("S3 bucket name not configured")
    
    def upload_file(
        self,
        file_path: str,
        s3_key: str,
        bucket: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload file to S3.
        
        Args:
            file_path: Local file path
            s3_key: S3 key (path in bucket)
            bucket: Bucket name (optional, uses default)
            metadata: Additional metadata
        
        Returns:
            S3 URI (s3://bucket/key)
        """
        bucket = bucket or self.bucket_name
        
        try:
            extra_args = {'ServerSideEncryption': 'AES256'}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_file(
                file_path,
                bucket,
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded file to s3://{bucket}/{s3_key}")
            return f"s3://{bucket}/{s3_key}"
            
        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise
    
    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        s3_key: str,
        bucket: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file object to S3.
        
        Args:
            file_obj: File-like object
            s3_key: S3 key
            bucket: Bucket name
            content_type: MIME type
        
        Returns:
            S3 URI
        """
        bucket = bucket or self.bucket_name
        
        try:
            extra_args = {'ServerSideEncryption': 'AES256'}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_fileobj(
                file_obj,
                bucket,
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded file object to s3://{bucket}/{s3_key}")
            return f"s3://{bucket}/{s3_key}"
            
        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise
    
    def download_file(
        self,
        s3_key: str,
        local_path: str,
        bucket: Optional[str] = None
    ) -> str:
        """
        Download file from S3.
        
        Args:
            s3_key: S3 key
            local_path: Local destination path
            bucket: Bucket name
        
        Returns:
            Local file path
        """
        bucket = bucket or self.bucket_name
        
        try:
            self.s3_client.download_file(bucket, s3_key, local_path)
            logger.info(f"Downloaded s3://{bucket}/{s3_key} to {local_path}")
            return local_path
            
        except ClientError as e:
            logger.error(f"Error downloading from S3: {str(e)}")
            raise
    
    def get_object(self, s3_key: str, bucket: Optional[str] = None) -> bytes:
        """
        Get object content from S3.
        
        Args:
            s3_key: S3 key
            bucket: Bucket name
        
        Returns:
            File content as bytes
        """
        bucket = bucket or self.bucket_name
        
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=s3_key)
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Error getting object from S3: {str(e)}")
            raise
    
    def generate_presigned_url(
        self,
        s3_key: str,
        bucket: Optional[str] = None,
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for temporary access.
        
        Args:
            s3_key: S3 key
            bucket: Bucket name
            expiration: URL validity in seconds
        
        Returns:
            Presigned URL
        """
        bucket = bucket or self.bucket_name
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise
    
    def delete_object(self, s3_key: str, bucket: Optional[str] = None):
        """Delete object from S3"""
        bucket = bucket or self.bucket_name
        
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=s3_key)
            logger.info(f"Deleted s3://{bucket}/{s3_key}")
            
        except ClientError as e:
            logger.error(f"Error deleting from S3: {str(e)}")
            raise
    
    def list_objects(
        self,
        prefix: str = "",
        bucket: Optional[str] = None
    ) -> list:
        """
        List objects in bucket with prefix.
        
        Args:
            prefix: S3 key prefix
            bucket: Bucket name
        
        Returns:
            List of object keys
        """
        bucket = bucket or self.bucket_name
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
            
        except ClientError as e:
            logger.error(f"Error listing S3 objects: {str(e)}")
            raise