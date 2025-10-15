from mypy_boto3_s3.client import S3Client

import requests
import boto3
import os

from services.library.get_s3_presigned_url import get_s3_presigned_url

from dotenv import load_dotenv
load_dotenv()

REGION = os.getenv("REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME") or ''
MODAL_PROCESS = os.getenv("MODAL_PROCESS")

s3_client: S3Client = boto3.client("s3", region_name=REGION)

def mineru_pdf_extract(s3_key: str):
    """
    Run inference using MinerU models on external GPU to extract
    layout, text, images from PDF.
    """
    s3_url = get_s3_presigned_url(s3_key)

    # Run inference on external GPU, takes 1~10mins dep. on doc length.
    res = requests.post(
        f"https://{MODAL_PROCESS}.modal.run", 
        json={"pdf_url": s3_url}
    )

    data = res.json()
    
    markdown = data.get("markdown", "")
    metadata = data.get("metadata", {})
    assets = data.get("assets", [])


    return {
        "markdown": markdown,
        "metadata": metadata,
        "assets": assets
    }

