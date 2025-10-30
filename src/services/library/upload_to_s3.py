from mypy_boto3_s3.client import S3Client
from typing import TypedDict
import boto3
import os
import json

from dotenv import load_dotenv
load_dotenv()

REGION = os.getenv("REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME") or ''

s3_client: S3Client = boto3.client("s3", region_name=REGION)

class UploadToS3Result(TypedDict):
    key: str
    s3_uri: str

def upload_pdf_to_s3(file_bytes: bytes, filename: str, path: str | None = None) -> UploadToS3Result:
    try:
        base_name = filename.replace('.pdf', '')
        key = f'{path}/{base_name}.pdf' if path else f'{base_name}.pdf'
        s3_client.put_object(Bucket=BUCKET_NAME, Key=key, Body=file_bytes, ContentType="application/pdf")
        return {"key": key, "s3_uri": f"s3://{BUCKET_NAME}/{key}"}
    
    except Exception as e:
        raise Exception(f"Failed to upload_to_s3: {e}")

def get_presigned_put_url(s3_key: str, expiration: int = 3600) -> str:
    """Generate presigned PUT URL for direct S3 upload"""
    url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': BUCKET_NAME,
            'Key': s3_key,
            'ContentType': 'application/pdf'
        },
        ExpiresIn=expiration
    )
    return url

class UploadDocumentDataResult(TypedDict):
    key: str
    s3_uri: str

def upload_parsed_pdf_to_s3(data: dict, title_id: str, path: str | None = None) -> UploadDocumentDataResult:
    try:
        json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        key = f'{path}/{title_id}.json' if path else f'{title_id}.json'
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json_bytes,
            ContentType="application/json"
        )
        
        return {"key": key, "s3_uri": f"s3://{BUCKET_NAME}/{key}"}
    
    except Exception as e:
        raise Exception(f"Failed to upload document data to S3: {e}")