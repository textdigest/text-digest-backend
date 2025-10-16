import json
import boto3
import os

from typing import Dict, Any, Optional
import time

from mypy_boto3_dynamodb.client import DynamoDBClient
from boto3.dynamodb.conditions import Key, Attr

from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.getenv("REGION") or ''
WEBSOCKET_API_GATEWAY: str = os.getenv("WEBSOCKET_API_GATEWAY") or ''
DDB_TABLE_NAME = os.getenv("DDB_TABLE_NAME") or ''

ddb_client: DynamoDBClient = boto3.client("dynamodb", region_name=REGION)

class WebSocketStream:
    def __init__(self,  service_name: str, user_id: str):
        self.connection_id = get_user_connection(user_id)
        self.user_id = user_id
        self.service_name = service_name

        endpoint_url = WEBSOCKET_API_GATEWAY.replace("wss://", "https://")

        logger.info(f"WebSocket endpoint URL: {endpoint_url}")
        logger.info(f"Connection ID: {self.connection_id}")

        self.apigw_client = boto3.client('apigatewaymanagementapi',
            endpoint_url=endpoint_url
        )
        self.is_connected = True
    
    async def send_chunk(self, content: str, event: str):
        if not self.is_connected:
            connection_id = get_user_connection(self.user_id)
            if connection_id:
                self.connection_id = connection_id
                self.is_connected = True
            else:
                return

        try:
            message = {
                'service': self.service_name,
                'event': event,
                'body': content,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
            self.apigw_client.post_to_connection(
                ConnectionId=self.connection_id,
                Data=json.dumps(message)
            )

        except Exception as e:
            if 'GoneException' in str(e):
                print(f"Connection {self.connection_id} is gone")
                self.is_connected = False
            else:
                print(f"Failed to send message: {e}")


def get_user_connection(user_id: str, attempts: int = 3) -> Optional[str]:
    backoff = 1
    
    for _ in range(attempts):
        try:
            response = ddb_client.get_item(
                TableName=DDB_TABLE_NAME,
                Key={
                    "PK": {"S": f"USER#{user_id}"},
                    "SK": {"S": "WS_CONNECTION"}
                }
            )

            if response and "Item" in response and "connection_id" in response["Item"]:
                return response["Item"]["connection_id"].get("S")
        
        except Exception as e:
            print(f"Failed to get connection for user {user_id}: {e}")
        
        time.sleep(backoff)

        backoff *= 2

    return None