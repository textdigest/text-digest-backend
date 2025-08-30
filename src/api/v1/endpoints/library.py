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

#Take DynamoDB query result and extract important information
def format_entry(book_entry):
    return {"date_downloaded": book_entry["date_downloaded"]["S"],  "pdf_link": book_entry["pdf_link"]["S"], "pages": book_entry["num_of_pages"]["N"], "date_published": book_entry["date_published"]["S"], "author": book_entry["author"]["S"], "title": book_entry["title"]["S"]} 

def retrieveToken():
    client = boto3.client("cognito-idp", region_name=REGION)
    print("LOOK HERE BOZO:", USERNAME, PASSWORD, REGION, POOL_ID, CLIENT_ID)
    resp = client.initiate_auth(
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": USERNAME, "PASSWORD": PASSWORD},
        ClientId=CLIENT_ID,
    )
    token = resp["AuthenticationResult"]["IdToken"]

    # decode without verification (just for dev!)
    claims = jwt.decode(token, key=None, options={"verify_signature": False, "verify_aud": False})
    sub = claims["sub"]
    return sub

TABLE = os.getenv("DDB_TABLE", "main-app-test")
ddb = boto3.client("dynamodb")

#Uploads PDF to S3, parse text using OCR  
@router.post("/post-title")
async def post_title(title: str, author: str = "N/A", date_published: str = "", file: UploadFile = File(...), pages=0):
    s3_client = boto3.client("s3", region_name=REGION)
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE)
    sub = retrieveToken()
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
    sub = retrieveToken()
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
    sub = retrieveToken()
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
    sub = retrieveToken()
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




