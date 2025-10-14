from fastapi import APIRouter, HTTPException, Request, Form, File, UploadFile
from datetime import datetime
from typing import List
from uuid import uuid4
import boto3
import os

from mypy_boto3_dynamodb.client import DynamoDBClient
from mypy_boto3_s3.client import S3Client

from services.library.format_ddb_entry import deserialize_ddb_title_item, serialize_title, Title, DdbTitleItem
from services.library.upload_to_s3 import upload_pdf_to_s3, upload_parsed_pdf_to_s3
from services.library.pdf_extract import pdf_extract

from util.tokens.verifyIdToken import verify_token

from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

REGION = os.getenv("REGION") or ''
POOL_ID = os.getenv("POOL_ID") or ''
CLIENT_ID = os.getenv("CLIENT_ID") or ''
USERNAME = os.getenv("USERNAME") or ''
PASSWORD = os.getenv("PASSWORD") or ''
BUCKET_NAME = os.getenv("BUCKET_NAME") or ''
TABLE = os.getenv("DDB_TABLE_NAME") or ''

s3_client: S3Client = boto3.client("s3", region_name=REGION)
ddb_client: DynamoDBClient = boto3.client("dynamodb", region_name=REGION)

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

    document_data = pdf_extract(upload_pdf_s3_res["key"])

    title_id = str(uuid4())

    upload_parsed_pdf_s3_res = upload_parsed_pdf_to_s3(dict(document_data), title_id, path='parsed-uploads')
    
    title_obj = Title(
        id=title_id,
        title=title,
        author=author,
        date_published=date_published or "unknown",
        date_downloaded=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        pages=pages,
        notes=[]
    )

    serialized_title = serialize_title(title_obj, sub, upload_pdf_s3_res["s3_uri"], upload_parsed_pdf_s3_res["s3_uri"])

    res = ddb_client.put_item(
        TableName=TABLE,
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

    out = ddb_client.query(
        TableName=TABLE,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        ExpressionAttributeValues={":pk": {"S":pk}, ":sk": {"S": "TITLE#"}},
    )

    result: List[Title] = []
    for item in out["Items"]:
        title_obj, ddb_item = deserialize_ddb_title_item(item)
        result.append(title_obj)
        
    return result

# region get-title
@router.get("/get-title/")
async def get_title(request: Request, title_id: str):
    auth_header = request.headers.get("authorization")
    sub = verify_token(auth_header)

    pk = f"USER#{sub}"
    sk = f"TITLE#{title_id}"

    out = ddb_client.get_item(
        TableName=TABLE,
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
        TableName=TABLE,
        Key={"PK": {"S": pk}, "SK": {"S": sk}}
    )

    if "Item" not in title_item_resp:
        raise HTTPException(status_code=404, detail=f"Title with id {id} not found")

    title_obj, ddb_title = deserialize_ddb_title_item(title_item_resp["Item"])
    ddb_client.delete_item(
        TableName=TABLE,
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
    table = dynamodb.Table(TABLE)

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
    table = dynamodb.Table(TABLE)

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