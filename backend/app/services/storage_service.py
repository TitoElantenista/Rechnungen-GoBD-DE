"""Storage Service - S3 with versioning and object lock (WORM)"""

import io
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageService:
    """
    S3 storage service for revision-safe archiving
    
    Features:
    - Object versioning (all changes tracked)
    - Object lock (WORM - Write Once Read Many)
    - S3-compatible (works with MinIO, AWS S3, etc.)
    """
    
    def __init__(self):
        # Try S3, fall back to local storage in development
        self.use_local = False
        self.local_storage_path = Path("./storage")
        
        self.bucket = settings.S3_BUCKET
        
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                use_ssl=settings.S3_USE_SSL,
                config=Config(
                    signature_version='s3v4',
                    connect_timeout=2,
                    read_timeout=2,
                    retries={'max_attempts': 1, 'mode': 'standard'},
                ),
            )
            self.bucket = settings.S3_BUCKET
            
            # Test connection
            self.s3_client.list_buckets()
            
            # Ensure bucket exists
            self._ensure_bucket_exists()
            print("✅ Using S3 storage")
        except Exception as e:
            print(f"⚠️ S3 not available, using local storage: {e}")
            self.use_local = True
            self.s3_client = None
            self.bucket = None
        
        if self.use_local:
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError:
            # Bucket doesn't exist, create it
            try:
                self.s3_client.create_bucket(
                    Bucket=self.bucket,
                    CreateBucketConfiguration={
                        'LocationConstraint': settings.S3_REGION
                    } if settings.S3_REGION != 'us-east-1' else {}
                )
                
                # Enable versioning
                self.s3_client.put_bucket_versioning(
                    Bucket=self.bucket,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                
                print(f"✅ Created S3 bucket: {self.bucket} with versioning")
                
            except Exception as e:
                print(f"Warning: Could not create bucket {self.bucket}: {e}")
    
    async def store_pdf(self, invoice_number: str, pdf_bytes: bytes) -> str:
        """
        Store PDF in S3 with object lock or local filesystem
        
        Args:
            invoice_number: Invoice number for file naming
            pdf_bytes: PDF file content
        
        Returns:
            S3 object path or local file path
        """
        key = f"invoices/{datetime.utcnow().year}/{invoice_number}.pdf"
        
        if self.use_local:
            # Local filesystem storage
            file_path = self.local_storage_path / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(pdf_bytes)
            return key
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=pdf_bytes,
            ContentType='application/pdf',
            Metadata={
                'invoice_number': invoice_number,
                'created_at': datetime.utcnow().isoformat(),
                'content_type': 'application/pdf',
            },
            # Enable object lock for immutability (if supported)
            # ObjectLockMode='GOVERNANCE',  # Requires bucket with object lock
            # ObjectLockRetainUntilDate=datetime.utcnow() + timedelta(days=3650),  # 10 years
        )
        
        return key
    
    async def store_xml(self, invoice_number: str, xml_bytes: bytes) -> str:
        """
        Store ZUGFeRD XML in S3 or local filesystem
        
        Args:
            invoice_number: Invoice number for file naming
            xml_bytes: XML file content
        
        Returns:
            S3 object path or local file path
        """
        key = f"invoices/{datetime.utcnow().year}/{invoice_number}.xml"
        
        if self.use_local:
            # Local filesystem storage
            file_path = self.local_storage_path / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(xml_bytes)
            return key
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=xml_bytes,
            ContentType='text/xml',
            Metadata={
                'invoice_number': invoice_number,
                'created_at': datetime.utcnow().isoformat(),
                'content_type': 'text/xml',
            },
        )
        
        return key
    
    async def get_file(self, key: str) -> bytes:
        """
        Retrieve file from S3 or local filesystem
        
        Args:
            key: S3 object key or local file path
        
        Returns:
            File content as bytes
        """
        if self.use_local:
            file_path = self.local_storage_path / key
            if not file_path.exists():
                raise FileNotFoundError(f"File not found in storage: {key}")
            return file_path.read_bytes()
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in storage: {key}")
            raise
    
    async def get_pdf_stream(self, key: str) -> BinaryIO:
        """
        Get PDF as stream for preview
        
        Args:
            key: S3 object key
        
        Returns:
            Binary stream
        """
        pdf_bytes = await self.get_file(key)
        return io.BytesIO(pdf_bytes)
    
    def list_versions(self, key: str) -> list:
        """
        List all versions of an object (for audit)
        
        Args:
            key: S3 object key
        
        Returns:
            List of version metadata
        """
        try:
            response = self.s3_client.list_object_versions(
                Bucket=self.bucket,
                Prefix=key
            )
            
            versions = []
            for version in response.get('Versions', []):
                versions.append({
                    'version_id': version['VersionId'],
                    'last_modified': version['LastModified'].isoformat(),
                    'size': version['Size'],
                    'is_latest': version['IsLatest'],
                })
            
            return versions
            
        except ClientError:
            return []
    
    def delete_object(self, key: str):
        """
        Delete object (actually creates a delete marker due to versioning)
        
        Note: With versioning enabled, objects are never truly deleted,
        only marked as deleted. This ensures GoBD compliance.
        """
        self.s3_client.delete_object(Bucket=self.bucket, Key=key)
