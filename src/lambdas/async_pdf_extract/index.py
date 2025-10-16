from aws_lambda_typing import context as lambda_context, events
from mypy_boto3_dynamodb.client import DynamoDBClient
from typing import TypedDict

import json
import boto3
import os
import asyncio

from services.library.upload_to_s3 import upload_parsed_pdf_to_s3
from services.library.pdf_extract import mineru_pdf_extract
from services.websocket.streamer import WebSocketStream

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from dotenv import load_dotenv
load_dotenv()

REGION = os.environ.get("REGION", '')
DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME", '')

ddb_client: DynamoDBClient = boto3.client("dynamodb", region_name=REGION)

class AsyncPdfExtractQueueMessage(TypedDict):
    user_id: str
    s3_uri: str
    title_id: str

def handler(event: events.SQSEvent, context: lambda_context.LambdaContext) -> None:
    record = event['Records'][0]

    body = record.get('body')
    if body is None:
        raise KeyError('body')

    queue_data: AsyncPdfExtractQueueMessage = json.loads(body)
    ws = WebSocketStream('library', queue_data['user_id'])

    try:
        logger.info(f"Attempting to run inference on title: {queue_data['title_id']}")

        # MinerU Inference
        s3_key =  queue_data["s3_uri"].split('/', 3)[-1]
        document_data = mineru_pdf_extract(s3_key)
        upload_parsed_pdf_s3_res = upload_parsed_pdf_to_s3(dict(document_data), queue_data['title_id'], path='parsed-uploads')

        # Update DDB Entry on Completion
        ddb_client.update_item(
            TableName=DDB_TABLE_NAME,
            Key={
                "PK": {"S": f"USER#{queue_data['user_id']}"},
                "SK": {"S": f"TITLE#{queue_data['title_id']}"}
            },
            UpdateExpression="SET is_processing = :is_processing, parsed_pdf_link = :parsed_pdf_link",
            ExpressionAttributeValues={
                ":is_processing": {"BOOL": False},
                ":parsed_pdf_link": {"S": upload_parsed_pdf_s3_res['s3_uri']},
            }
        )

        # WS Notify Front-end
        asyncio.run(ws.send_chunk(queue_data['title_id'], 'PROCESSING_COMPLETE'))
    except Exception as e:
        asyncio.run(ws.send_chunk(queue_data['title_id'], 'PROCESSING_FAILED'))
    
