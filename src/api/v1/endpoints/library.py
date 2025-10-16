from fastapi import APIRouter, HTTPException, Request, Form, File, UploadFile
from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_s3.client import S3Client
from mypy_boto3_sqs.client import SQSClient
from typing import List

from datetime import datetime
from uuid import uuid4
import boto3
import os
import json

from services.library.format_ddb_entry import deserialize_ddb_title_item, serialize_title, Title, DdbTitleItem
from services.library.upload_to_s3 import upload_pdf_to_s3, upload_parsed_pdf_to_s3

from util.tokens.verifyIdToken import verify_token

from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

REGION = os.getenv("REGION") or ''
POOL_ID = os.getenv("POOL_ID") or ''
CLIENT_ID = os.getenv("CLIENT_ID") or ''
BUCKET_NAME = os.getenv("BUCKET_NAME") or ''
DDB_TABLE_NAME = os.getenv("DDB_TABLE_NAME") or ''
ASYNC_PDF_EXTRACT_QUEUE_URL = os.getenv("ASYNC_PDF_EXTRACT_QUEUE_URL") or ''

s3_client: S3Client = boto3.client("s3", region_name=REGION)
ddb_client: DynamoDBClient = boto3.client("dynamodb", region_name=REGION)
sqs_client: SQSClient = boto3.client("sqs", region_name=REGION)

# region post-title
@router.post("/post-title")
async def post_title(
    request: Request, 
    title: str = Form(...),
    author: str = Form("Unknown"),
    date_published: str = Form(""),
    file: UploadFile = File(...),
    pages: int = Form(0)
):
    auth_header = request.headers.get("authorization")
    sub = verify_token(auth_header)

    pdf_bytes = await file.read()
    upload_pdf_s3_res = upload_pdf_to_s3(file_bytes=pdf_bytes, filename=title, path='uploads')

    title_id = str(uuid4())
    title_obj = Title(
        id=title_id,
        #
        title=title,
        author=author,
        date_published=date_published or "unknown",
        date_downloaded=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        pages=pages,
        #
        is_public=False,
        is_processing=True,
        #
        notes=[]
    )

    sqs_client.send_message(
        QueueUrl=ASYNC_PDF_EXTRACT_QUEUE_URL,
        MessageBody=json.dumps({
            "user_id": sub,
            "s3_uri": upload_pdf_s3_res["s3_uri"],
            "title_id": title_id
        }),
        MessageGroupId=sub,
        MessageDeduplicationId=title_id
    )

    serialized_title = serialize_title(title_obj, sub, upload_pdf_s3_res["s3_uri"])
    ddb_client.put_item(
        TableName=DDB_TABLE_NAME,
        Item=serialized_title,
        ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)"
    )
        
    return {"ok": True}

# region get-titles-all
@router.get("/get-titles-all/")
async def get_titles_all(request: Request):
    auth_header = request.headers.get("authorization")
    sub = verify_token(auth_header)

    pk = f"USER#{sub}"

    user_titles = ddb_client.query(
        TableName=DDB_TABLE_NAME,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        ExpressionAttributeValues={":pk": {"S":pk}, ":sk": {"S": "TITLE#"}},
    )

    public_titles = ddb_client.query(
        TableName= DDB_TABLE_NAME,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        ExpressionAttributeValues={":pk": {"S":"PUBLIC"}, ":sk": {"S": "TITLE#"}},
    )

    result: List[Title] = []
    for item in user_titles["Items"]:
        title_obj, ddb_item = deserialize_ddb_title_item(item)
        result.append(title_obj)
    
    for item in public_titles["Items"]:
        title_obj, ddb_item = deserialize_ddb_title_item(item)
        result.append(title_obj)
        
    return result

# region get-title
@router.get("/get-title/")
async def get_title(request: Request, title_id: str, is_public: bool):
    auth_header = request.headers.get("authorization")
    sub = verify_token(auth_header)

    pk = "PUBLIC" if is_public else f"USER#{sub}"
    sk = f"TITLE#{title_id}"

    out = ddb_client.get_item(
        TableName=DDB_TABLE_NAME,
        Key={"PK": {"S": pk}, "SK": {"S": sk}}
    )

    if "Item" not in out:
        raise HTTPException(status_code=404, detail=f"Title with id {title_id} not found")

    title, ddb_title_item = deserialize_ddb_title_item(out["Item"])
    
    return {"title": title}

# region delete-title
@router.delete("/delete-title/")
async def delete_title(id: str, request: Request):
    auth_header = request.headers.get("authorization")
    sub = verify_token(auth_header)

    pk = f"USER#{sub}"
    sk = f"TITLE#{id}"

    title_item_resp = ddb_client.get_item(
        TableName=DDB_TABLE_NAME,
        Key={"PK": {"S": pk}, "SK": {"S": sk}}
    )

    if "Item" not in title_item_resp:
        raise HTTPException(status_code=404, detail=f"Title with id {id} not found")

    title_obj, ddb_title = deserialize_ddb_title_item(title_item_resp["Item"])
    ddb_client.delete_item(
        TableName=DDB_TABLE_NAME,
        Key={"PK": {"S": pk}, "SK": {"S": sk}}
    )

    pdf_link = ddb_title.pdf_link
    s3_key = pdf_link.split('/', 3)[-1]
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)

    return {"success": f"Deleted title {id}"}

# region post-note
@router.patch("/post-note")
async def post_note(request: Request, text: str, page_num: int, book_title: str):
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(DDB_TABLE_NAME)

    auth_header = request.headers.get("authorization")
    sub = verify_token(auth_header)

    pk = f"USER#{sub}"
    sk = f"TITLE#{book_title}"

    new_note = {
            "comment": text,
            "page_num": page_num,
            "book_title": book_title, 
    }

    try:
        response = table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression="SET notes = list_append(if_not_exists(notes, :empty), :new)",
            ExpressionAttributeValues={
                ":empty": [],
                ":new": [new_note],
            },
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            ReturnValues="UPDATED_NEW",
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"ok": True, "updated_notes": response["Attributes"]["notes"]}

# region get-notes
@router.get("/get-notes")
async def get_notes(request: Request, book_title:str):
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(DDB_TABLE_NAME)

    auth_header = request.headers.get("authorization")
    sub = verify_token(auth_header)

    pk = f"USER#{sub}"
    sk = f"TITLE#{book_title}"

    resp = table.get_item(
        Key={"PK": pk, "SK": sk},
        ProjectionExpression="notes"
    )

    if "Item" not in resp:
        raise HTTPException(status_code=404, detail=f"Title not found: {book_title}")

    notes = resp["Item"].get("notes", [])
    
    return {"book_title": book_title, "count": len(notes), "notes": notes} # type: ignore