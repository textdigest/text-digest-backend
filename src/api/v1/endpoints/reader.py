from fastapi import APIRouter, Request, HTTPException
from agents import TResponseInputItem
from pydantic import BaseModel
from typing import List
from mypy_boto3_sqs.client import SQSClient
from mypy_boto3_dynamodb.client import DynamoDBClient

import boto3
import os
import json

from services.agents.transcribe_audio import transcribe_audio_from_base64
from util.tokens.verifyIdToken import verify_token

from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

REGION = os.getenv("REGION") or ''
ASYNC_AGENT_RUNNER_QUEUE_URL = os.getenv("ASYNC_AGENT_RUNNER_QUEUE_URL") or ''
DDB_TABLE_NAME = os.getenv("DDB_TABLE_NAME") or ''

sqs_client: SQSClient = boto3.client("sqs", region_name=REGION)
ddb_client: DynamoDBClient = boto3.client("dynamodb", region_name=REGION)

class PostQnaRequest(BaseModel):
    query: str
    highlighted_text: str
    page_content: str
    curr_conversation: List[TResponseInputItem]
    conversation_id: str

@router.post("/post-qna")
async def post_qna_message(request: Request, body: PostQnaRequest):
    auth_header = request.headers.get("authorization")

    user_id = verify_token(auth_header)

    sqs_client.send_message(
        QueueUrl=ASYNC_AGENT_RUNNER_QUEUE_URL,
        MessageBody=json.dumps({
            "agent_name": "qna_agent",
            "agent_params": {
                "curr_conversation": body.curr_conversation,
                "query": body.query,
                "highlighted_text": body.highlighted_text,
                "page_content": body.page_content,
            },
            "user_id": user_id,
            "conversation_id": body.conversation_id
        }),
        MessageGroupId=user_id,
        MessageDeduplicationId=f"{user_id}-{body.conversation_id}-{hash(json.dumps(body.dict()))}"
    )

    return {"ok": True}

class PostVerbalQnaRequest(BaseModel):
    audio_base64: str
    highlighted_text: str
    page_content: str
    curr_conversation: List[TResponseInputItem]
    conversation_id: str
    file_extension: str = "webm"

@router.post("/post-verbal-qna")
async def post_verbal_qna_message(request: Request, body: PostVerbalQnaRequest):
    auth_header = request.headers.get("authorization")

    user_id = verify_token(auth_header)

    query_text = transcribe_audio_from_base64(body.audio_base64, body.file_extension)

    user_message: TResponseInputItem = {
        "role": "user",
        "content": query_text
    }
    
    updated_conversation = body.curr_conversation + [user_message]

    qna_body = PostQnaRequest(
        query=query_text,
        highlighted_text=body.highlighted_text,
        page_content=body.page_content,
        curr_conversation=updated_conversation,
        conversation_id=body.conversation_id,
    )

    sqs_client.send_message(
        QueueUrl=ASYNC_AGENT_RUNNER_QUEUE_URL,
        MessageBody=json.dumps({
            "agent_name": "qna_agent",
            "agent_params": {
                "curr_conversation": qna_body.curr_conversation,
                "query": qna_body.query,
                "highlighted_text": qna_body.highlighted_text,
                "page_content": qna_body.page_content,
            },
            "user_id": user_id,
            "conversation_id": qna_body.conversation_id
        }),
        MessageGroupId=user_id,
        MessageDeduplicationId=f"{user_id}-{qna_body.conversation_id}-{hash(json.dumps(qna_body.dict()))}"
    )

    return {"ok": True, "transcribed": query_text}


class PostPageNumberRequest(BaseModel):
    title_id: str
    page_number: int

@router.post("/page-number")
async def post_page_number(request: Request, body: PostPageNumberRequest):
    auth_header = request.headers.get("authorization")

    user_id = verify_token(auth_header)

    pk = f"USER#{user_id}"
    sk = f"PAGE#{body.title_id}"

    ddb_client.put_item(
        TableName=DDB_TABLE_NAME,
        Item={
            "PK": {"S": pk},
            "SK": {"S": sk},
            "page_number": {"N": str(body.page_number)}
        }
    )

    return {"ok": True}

@router.get("/page-number")
async def get_page_number(request: Request, title_id: str):
    auth_header = request.headers.get("authorization")

    user_id = verify_token(auth_header)

    pk = f"USER#{user_id}"
    sk = f"PAGE#{title_id}"

    response = ddb_client.get_item(
        TableName=DDB_TABLE_NAME,
        Key={
            "PK": {"S": pk},
            "SK": {"S": sk}
        }
    )

    if "Item" not in response:
        return {"pageNumber": 0}

    page_number_attr = response["Item"].get("page_number")
    if page_number_attr and "N" in page_number_attr:
        page_number = int(page_number_attr["N"])
    else:
        page_number = 0

    return {"pageNumber": page_number}