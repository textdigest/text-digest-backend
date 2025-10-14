from mypy_boto3_s3.client import S3Client
import boto3
import os

from dotenv import load_dotenv
load_dotenv()

REGION = os.getenv("REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

s3_client: S3Client = boto3.client("s3", region_name=REGION)

def get_s3_presigned_url(s3_key: str, expiration: int = 3600) -> str:
    """For s3 GET requests"""
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': BUCKET_NAME,
            'Key': s3_key,
            'ResponseContentDisposition': 'inline'
            },
        ExpiresIn=expiration
    )
    return url