from agents import TResponseInputItem
from mypy_boto3_dynamodb.client import DynamoDBClient
from typing import Any, TypedDict

import json
import boto3
import os
import asyncio

from services.agents.qna_agent import qna_agent, QnaAgentContext
from services.agents.stream_run import stream_run
from services.websocket.streamer import WebSocketStream


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from dotenv import load_dotenv
load_dotenv()

REGION = os.environ.get("REGION", '')
DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME", '')

ddb_client: DynamoDBClient = boto3.client("dynamodb", region_name=REGION)

class AsyncAgentRunner(TypedDict):
    agent_name: str
    agent_params: Any
    user_id: str

def handler(event, context) -> None:
    record = event['Records'][0]
    body = record.get('body')
    if body is None:
        raise KeyError('body')

    queue_data: AsyncAgentRunner = json.loads(body)

    try:
        if queue_data['agent_name'] == 'qna_agent':
            ws = WebSocketStream('reader-qna', queue_data['user_id'])

            curr_conversation: list[TResponseInputItem] = queue_data['agent_params']['curr_conversation']
            query: str = queue_data['agent_params']['query']
            highlighted_text: str = queue_data['agent_params']['highlighted_text']
            page_content: str = queue_data['agent_params']['page_content']

            async def run_agent():
                await ws.send_chunk(None, "turn-start")
                stream_res = await stream_run(
                    agent=qna_agent,
                    input_items=curr_conversation,
                    stream_callback=ws.send_chunk,
                    context=QnaAgentContext(
                        query=query,
                        highlighted_text=highlighted_text,
                        page_content=page_content,
                    ),
                )
                conversation = stream_res.to_input_list()
                await ws.send_chunk(conversation, "turn-over")

            asyncio.run(run_agent())

    except Exception as e:
        logger.error(e)
    
