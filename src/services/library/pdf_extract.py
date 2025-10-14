from typing import TypedDict
import logging
import requests
import boto3
import os
from mypy_boto3_s3.client import S3Client
from services.library.get_s3_presigned_url import get_s3_presigned_url

import base64
import zipfile
import io
import json

from dotenv import load_dotenv
load_dotenv()

REGION = os.getenv("REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME") or ''
MODAL_PROCESS = os.getenv("MODAL_PROCESS")

s3_client: S3Client = boto3.client("s3", region_name=REGION)


import time

def pdf_extract(s3_key: str):
    """
    Runs inference on the provided PDF URL and returns the extracted markdown and image binaries.
    Times the process.
    """
    start_time = time.time()
    s3_url = get_s3_presigned_url(s3_key)

    print(s3_url)
    print(MODAL_PROCESS)

    res = requests.post(
        f"https://{MODAL_PROCESS}.modal.run",
        json={"pdf_url": s3_url}
    )

    data = res.json()
    
    markdown = data.get("markdown", "")
    metadata = data.get("metadata", {})
    assets = data.get("assets", [])

    end_time = time.time()
    print(f"PDF extraction took {end_time - start_time:.2f} seconds")
    
    return {
        "markdown": markdown,
        "metadata": metadata,
        "assets": assets
    }

