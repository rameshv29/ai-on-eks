"""
S3 utilities for uploading generated travel plans and creating presigned URLs
Uses AWS Profile instead of access keys for better security
"""
import boto3
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# S3 configuration
def get_default_bucket_name():
    """Generate unique bucket name with account ID"""
    try:
        # Get AWS account ID
        session = boto3.Session(profile_name=os.getenv('AWS_PROFILE', 'default'))
        sts_client = session.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        return f"citymapper-travel-plans-{account_id}"
    except Exception:
        # Fallback to timestamp-based unique name
        import time
        return f"citymapper-travel-plans-{int(time.time())}"

# Use user-provided bucket name if set, otherwise generate default
DEFAULT_BUCKET_NAME = os.getenv('S3_BUCKET_NAME') or get_default_bucket_name()
DEFAULT_AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')
DEFAULT_REGION = os.getenv('AWS_REGION', 'us-east-1')

class S3Manager:
    """Manages S3 operations for travel plan files"""
    
    def __init__(self, bucket_name: str = None, aws_profile: str = None, region: str = None):
        self.bucket_name = bucket_name or DEFAULT_BUCKET_NAME
        self.aws_profile = aws_profile or DEFAULT_AWS_PROFILE
        self.region = region or DEFAULT_REGION
        self.s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3 client using AWS profile"""
        try:
            # Create session with specified profile
            session = boto3.Session(profile_name=self.aws_profile)
            self.s3_client = session.client('s3', region_name=self.region)
            logger.info(f"✅ S3 client initialized with profile: {self.aws_profile}")
            
            # Test connection by listing buckets
            self.s3_client.list_buckets()
            logger.info("✅ S3 connection verified")
            
        except ProfileNotFound:
            logger.error(f"❌ AWS profile '{self.aws_profile}' not found")
            logger.info("💡 Configure AWS profile with: aws configure --profile {self.aws_profile}")
            raise
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found")
            logger.info("💡 Configure AWS credentials with: aws configure")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 client: {e}")
            raise
    
    def ensure_bucket_exists(self) -> bool:
        """Ensure the S3 bucket exists, create if it doesn't"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ Bucket '{self.bucket_name}' exists")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.region == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    
                    logger.info(f"✅ Created bucket '{self.bucket_name}'")
                    return True
                    
                except ClientError as create_error:
                    logger.error(f"❌ Failed to create bucket: {create_error}")
                    return False
            else:
                logger.error(f"❌ Error checking bucket: {e}")
                return False
    
    def upload_file(self, file_path: str, s3_key: str = None) -> Optional[str]:
        """
        Upload a file to S3 and return the S3 key
        
        Args:
            file_path: Local path to the file
            s3_key: S3 key (path) for the file. If None, uses filename with timestamp
            
        Returns:
            S3 key if successful, None if failed
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ File not found: {file_path}")
                return None
            
            # Generate S3 key if not provided
            if not s3_key:
                filename = os.path.basename(file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                s3_key = f"travel-plans/{timestamp}_{filename}"
            
            # Ensure bucket exists
            if not self.ensure_bucket_exists():
                return None
            
            # Upload file
            logger.info(f"📤 Uploading {file_path} to s3://{self.bucket_name}/{s3_key}")
            
            # Set content type for HTML files
            extra_args = {}
            if file_path.endswith('.html'):
                extra_args['ContentType'] = 'text/html'
                extra_args['ContentDisposition'] = 'inline'
            
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"✅ File uploaded successfully to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"❌ Failed to upload file: {e}")
            return None
    
    def generate_presigned_url(self, s3_key: str, expiration_minutes: int = 30) -> Optional[str]:
        """
        Generate a presigned URL for downloading the file
        
        Args:
            s3_key: S3 key of the file
            expiration_minutes: URL expiration time in minutes (default: 30)
            
        Returns:
            Presigned URL if successful, None if failed
        """
        try:
            expiration_seconds = expiration_minutes * 60
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration_seconds
            )
            
            logger.info(f"✅ Generated presigned URL (expires in {expiration_minutes} minutes)")
            return presigned_url
            
        except Exception as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            return None
    
    def upload_and_get_url(self, file_path: str, expiration_minutes: int = 30) -> Optional[Dict[str, Any]]:
        """
        Upload file to S3 and return presigned URL with metadata
        
        Args:
            file_path: Local path to the file
            expiration_minutes: URL expiration time in minutes
            
        Returns:
            Dictionary with upload info and presigned URL, None if failed
        """
        try:
            # Upload file
            s3_key = self.upload_file(file_path)
            if not s3_key:
                return None
            
            # Generate presigned URL
            presigned_url = self.generate_presigned_url(s3_key, expiration_minutes)
            if not presigned_url:
                return None
            
            # Get file info
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            # Calculate expiration time
            expiration_time = datetime.now() + timedelta(minutes=expiration_minutes)
            
            return {
                'filename': filename,
                'file_size': file_size,
                's3_key': s3_key,
                's3_bucket': self.bucket_name,
                'presigned_url': presigned_url,
                'expiration_minutes': expiration_minutes,
                'expires_at': expiration_time.isoformat(),
                'upload_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload and get URL: {e}")
            return None

def health_check() -> bool:
    """Check if S3 service is accessible"""
    try:
        s3_manager = S3Manager()
        return s3_manager.s3_client is not None
    except Exception:
        return False

# Convenience functions
def upload_travel_plan(file_path: str, expiration_minutes: int = 30) -> Optional[Dict[str, Any]]:
    """
    Upload a travel plan file to S3 and get presigned URL
    
    Args:
        file_path: Path to the HTML travel plan file
        expiration_minutes: URL expiration time in minutes
        
    Returns:
        Dictionary with upload info and presigned URL
    """
    s3_manager = S3Manager()
    return s3_manager.upload_and_get_url(file_path, expiration_minutes)

def format_upload_info(upload_info: Dict[str, Any]) -> str:
    """Format upload information for display"""
    if not upload_info:
        return "❌ Upload failed"
    
    file_size_mb = upload_info['file_size'] / (1024 * 1024)
    
    return f"""
📤 TRAVEL PLAN UPLOADED TO S3:
   📄 File: {upload_info['filename']} ({file_size_mb:.2f} MB)
   🪣 Bucket: {upload_info['s3_bucket']}
   🔑 S3 Key: {upload_info['s3_key']}
   ⏰ Uploaded: {upload_info['upload_time']}
   
🔗 DOWNLOAD LINK (Valid for {upload_info['expiration_minutes']} minutes):
   {upload_info['presigned_url']}
   
⏰ Link expires at: {upload_info['expires_at']}
   
💡 Save this link to download your interactive travel plan!
"""
