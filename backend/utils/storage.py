"""S3/MinIO storage integration for file uploads."""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, BinaryIO
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class StorageService:
    """Unified storage service supporting S3, MinIO, and local filesystem."""
    
    def __init__(self):
        self.provider = os.environ.get('STORAGE_PROVIDER', 'local').lower()
        self.bucket = os.environ.get('STORAGE_BUCKET', 'sipsetu-uploads')
        self.region = os.environ.get('STORAGE_REGION', 'us-east-1')
        self.endpoint_url = os.environ.get('STORAGE_ENDPOINT_URL')  # For MinIO
        self.local_path = os.environ.get('LOCAL_STORAGE_PATH', '/tmp/sipsetu-uploads')
        
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize storage client based on provider."""
        if self.provider in ('s3', 'minio'):
            try:
                self._client = boto3.client(
                    's3',
                    region_name=self.region,
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=os.environ.get('STORAGE_ACCESS_KEY'),
                    aws_secret_access_key=os.environ.get('STORAGE_SECRET_KEY'),
                )
                # Test connection
                self._client.head_bucket(Bucket=self.bucket)
            except (ClientError, NoCredentialsError) as e:
                print(f"Warning: S3/MinIO init failed, falling back to local: {e}")
                self.provider = 'local'
        
        if self.provider == 'local':
            os.makedirs(self.local_path, exist_ok=True)
    
    def upload_file(
        self,
        file_obj,
        filename: str,
        content_type: str = 'application/octet-stream',
        prefix: str = 'uploads'
    ) -> dict:
        """Upload a file and return metadata. Accepts bytes or file-like object."""
        from io import BytesIO
        
        # Convert bytes to file-like object if needed
        if isinstance(file_obj, bytes):
            file_obj = BytesIO(file_obj)
        
        # Generate unique key
        ext = os.path.splitext(filename)[1]
        key = f"{prefix}/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}{ext}"
        
        if self.provider in ('s3', 'minio') and self._client:
            return self._upload_s3(file_obj, key, content_type)
        else:
            return self._upload_local(file_obj, key, filename)
    
    def _upload_s3(self, file_obj: BinaryIO, key: str, content_type: str) -> dict:
        """Upload to S3/MinIO."""
        file_obj.seek(0)
        self._client.upload_fileobj(
            file_obj,
            self.bucket,
            key,
            ExtraArgs={'ContentType': content_type}
        )
        return {
            'key': key,
            'url': self.get_url(key),
            'provider': self.provider,
            'bucket': self.bucket,
        }
    
    def _upload_local(self, file_obj: BinaryIO, key: str, original_filename: str) -> dict:
        """Save to local filesystem."""
        # Use a simpler path for local storage
        local_key = os.path.join(self.local_path, key)
        os.makedirs(os.path.dirname(local_key), exist_ok=True)
        
        file_obj.seek(0)
        with open(local_key, 'wb') as f:
            f.write(file_obj.read())
        
        return {
            'key': key,
            'url': f"/uploads/{key}",  # Served by nginx or Flask static
            'provider': 'local',
            'path': local_key,
        }
    
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Get presigned URL for private files or public URL."""
        if self.provider in ('s3', 'minio') and self._client:
            try:
                # For MinIO, we can use presigned URLs
                if self.endpoint_url:
                    return self._client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': self.bucket, 'Key': key},
                        ExpiresIn=expires_in
                    )
                # For S3, check if public or generate presigned
                return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
            except ClientError:
                pass
        # Local fallback
        return f"/uploads/{key}"
    
    def delete_file(self, key: str) -> bool:
        """Delete a file."""
        if self.provider in ('s3', 'minio') and self._client:
            try:
                self._client.delete_object(Bucket=self.bucket, Key=key)
                return True
            except ClientError:
                return False
        else:
            try:
                path = os.path.join(self.local_path, key)
                if os.path.exists(path):
                    os.remove(path)
                return True
            except OSError:
                return False
    
    def file_exists(self, key: str) -> bool:
        """Check if file exists."""
        if self.provider in ('s3', 'minio') and self._client:
            try:
                self._client.head_object(Bucket=self.bucket, Key=key)
                return True
            except ClientError:
                return False
        else:
            return os.path.exists(os.path.join(self.local_path, key))
    
    def get_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        expires_in: int = 3600
    ) -> dict:
        """Generate presigned URL for direct client upload."""
        if self.provider in ('s3', 'minio') and self._client:
            try:
                url = self._client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': self.bucket,
                        'Key': key,
                        'ContentType': content_type,
                    },
                    ExpiresIn=expires_in
                )
                return {
                    'url': url,
                    'key': key,
                    'method': 'PUT',
                    'headers': {'Content-Type': content_type},
                    'expires_in': expires_in,
                }
            except ClientError as e:
                return {'error': str(e)}
        return {'error': 'Presigned upload not available for local storage'}


# Global instance
_storage_service: Optional[StorageService] = None


def get_storage() -> StorageService:
    """Get or create the global storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


def init_storage(app=None) -> StorageService:
    """Initialize storage service."""
    global _storage_service
    _storage_service = StorageService()
    return _storage_service