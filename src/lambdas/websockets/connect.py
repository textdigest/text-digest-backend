import os
import boto3

from aws_lambda_typing.events import APIGatewayProxyEventV2
from aws_lambda_typing.context import Context

from mypy_boto3_dynamodb.client import DynamoDBClient

from util.tokens.verifyIdToken import verify_token

REGION = os.environ["REGION"]
DDB_TABLE_NAME = os.environ["DDB_TABLE_NAME"]

ddb_client: DynamoDBClient = boto3.client("dynamodb", region_name=REGION)

def handler(event: APIGatewayProxyEventV2, context: Context):
    try:
        token = event.get("queryStringParameters", {}).get("token")
        
        if not token:
            return {"statusCode": 401, "body": "Unauthorized"}
        
        user_id = verify_token(token)
        connection_id = event.get("requestContext", {}).get("connectionId")
        if not connection_id:
            return {"statusCode": 400, "body": "Requires connectionId."}
        
        ddb_client.put_item(
            TableName=DDB_TABLE_NAME,
            Item={
                "PK": {"S": f"USER#{user_id}"},
                "SK": {"S": "WS_CONNECTION"},
                "connection_id": {"S": connection_id}
            }
        )
        
        return {"statusCode": 200, "body": "Connected"}
    
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        return {"statusCode": 401, "body": "Unauthorized"}

