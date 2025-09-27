from fastapi import APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
import os
import boto3
from jose import jwt
from src.services.library.main import upload_to_s3
from datetime import datetime

load_dotenv()
router = APIRouter()

REGION = os.getenv("REGION")
POOL_ID = os.getenv("POOL_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
BUCKET_NAME = os.getenv("BUCKET_NAME")
SUB = os.getenv("SUB")

#Take DynamoDB query result and extract important information
def format_entry(book_entry):
    return {
        "date_downloaded": book_entry["date_downloaded"]["S"],
        "pdf_link": book_entry["pdf_link"]["S"],
        "pages": book_entry["num_of_pages"]["N"],
        "date_published": book_entry["date_published"]["S"],
        "author": book_entry["author"]["S"],
        "title": book_entry["title"]["S"],
        "notes": [
            {
                "comment": note["M"]["comment"]["S"],
                "page_num": int(note["M"]["page_num"]["N"]),
                "book_title": note["M"]["book_title"]["S"],
            }
            for note in book_entry.get("notes", {}).get("L", [])
        ],
    }

TABLE = os.getenv("DDB_TABLE_NAME")
ddb = boto3.client("dynamodb", region_name=REGION)

#Uploads PDF to S3, parse text using OCR  
@router.post("/post-title")
async def post_title(title: str, author: str = "N/A", date_published: str = "", file: UploadFile = File(...), pages=0):
    s3_client = boto3.client("s3", region_name=REGION)
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE)
    sub = SUB
    pk = f"USER#{sub}"
    pdf_bytes = await file.read()
    url_link = upload_to_s3(client=s3_client, pdf_bytes=pdf_bytes, filename=title, bucket=BUCKET_NAME)["s3_uri"]

    item = {
            "PK": pk,
            "SK": f"BOOK#{title}",
            "title": title,
            "author": author,
            "date_published": date_published or "unknown",
            "date_downloaded": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "pdf_link": url_link,
            "num_of_pages": pages,
            "notes": [],
        }

    table.put_item(
        TableName=TABLE,
        Item=item,
        ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)"
    )
    
    return {"ok": True}
    


# Returns all titles in library
@router.get("/get-titles-all/")
async def get_titles_all():
    sub = SUB
    pk = f"USER#{sub}"
    #Make query to DynamoDB table to search for all books for user
    out = ddb.query(
        TableName=TABLE,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        ExpressionAttributeValues={":pk": {"S":pk}, ":sk": {"S": "BOOK#"}},
    )
    #Result to store all book objects
    result = []
    for item in out["Items"]:
        result.append(format_entry(item))
    return result


@router.get("/get-title/")
async def get_title(title_name: str):
    sub = SUB
    pk = f"USER#{sub}"
    #Make query to DynamoDB table to search for all books for user
    out = ddb.query(
        TableName=TABLE,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        FilterExpression = "title = :title",
        ExpressionAttributeValues={":pk": {"S":pk}, ":sk": {"S": "BOOK#"}, ":title": {"S":title_name }},

    )
    return{"book" : format_entry(out["Items"][0])}

@router.delete("/delete-title/")
async def delete_title(title_name: str):
    sub = SUB 
    pk = f"USER#{sub}"
    #Make query to DynamoDB table to search for all books for user
    out = ddb.query(
        TableName=TABLE,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        FilterExpression = "title = :title",
        ExpressionAttributeValues={":pk": {"S":pk}, ":sk": {"S": "BOOK#"}, ":title": {"S":title_name }},
    )

    # Determine if a match was found
    if out["Count"] == 0:
        return {"error": f"No book found with title {title_name}"}
    
    book = out["Items"][0]
    sk = book["SK"]["S"]

    ddb.delete_item(
        TableName=TABLE,
        Key={"PK": {"S": pk}, "SK": {"S": sk}}
    )
    return {"success": f"Deleted book {title_name}"}

#Append new note to list of notes for a user's book    
@router.patch("/post-note")
async def post_note(text: str, page_num: int, book_title: str):
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE)
    sub = SUB
    pk = f"USER#{sub}"
    sk = f"BOOK#{book_title}"
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

@router.get("/get-notes")
async def get_notes(book_title:str):
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE)
    sub = SUB
    pk = f"USER#{sub}"
    sk = f"BOOK#{book_title}"
    resp = table.get_item(
        Key={"PK": pk, "SK": sk},
        ProjectionExpression="notes"
    )

    if "Item" not in resp:
        raise HTTPException(status_code=404, detail=f"Book not found: {book_title}")

    notes = resp["Item"].get("notes", [])
    return {"book_title": book_title, "count": len(notes), "notes": notes}




