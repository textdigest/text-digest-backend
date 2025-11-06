from fastapi import APIRouter, Request
from agents import TResponseInputItem
from pydantic import BaseModel
from typing import List
from mypy_boto3_sqs.client import SQSClient

import boto3
import os
import json

from util.tokens.verifyIdToken import verify_token

from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

REGION = os.getenv("REGION") or ''
ASYNC_AGENT_RUNNER_QUEUE_URL = os.getenv("ASYNC_AGENT_RUNNER_QUEUE_URL") or ''

sqs_client: SQSClient = boto3.client("sqs", region_name=REGION)

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