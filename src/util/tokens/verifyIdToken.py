import os
import json
import urllib.request
import time
from jose import jwk, jwt
from jose.utils import base64url_decode
from dotenv import load_dotenv

load_dotenv()
REGION = os.getenv("REGION")
POOL_ID = os.getenv("POOL_ID")
CLIENT_ID = os.getenv("CLIENT_ID")


import logging #Cant use print for cloudwatch logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

keys_url = f'https://cognito-idp.us-east-1.amazonaws.com/{POOL_ID}/.well-known/jwks.json'
with urllib.request.urlopen(keys_url) as f:
    response = f.read()
keys = json.loads(response.decode('utf-8'))['keys']


def verify_token(id_token: str | None) -> str:
    """
    Verifies a cognito-issued id token. Throws an error if token is invalid or dne.
    
    Args:
        token (str): Cognito-issued ID Token.

    Returns:
        str: The user id extracted from the token claims if valid.

    ```python
    # Example usage:
    @router.get("/")
    async def fastapi_route(request: Request):
        auth_header = request.headers.get("authorization")
        user_id = verify_token(auth_header)
    ```
    """
    if not id_token:
        raise Exception("Unauthorized")


    if id_token.startswith("Bearer "):
        id_token = id_token.split(" ", 1)[1]

    try:
        headers = jwt.get_unverified_headers(id_token)
        kid = headers['kid']

        key = next((k for k in keys if k['kid'] == kid), None)
        if not key:
            raise ValueError('Public key not found in jwks.json')
        public_key = jwk.construct(key)

        message, encoded_signature = id_token.rsplit('.', 1)
        decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
        if not public_key.verify(message.encode('utf-8'), decoded_signature):
            raise ValueError('Signature verification failed')

        claims = jwt.get_unverified_claims(id_token)

        if time.time() > claims['exp']:
            raise ValueError('Token has expired')

        if claims['iss'] != f'https://cognito-idp.us-east-1.amazonaws.com/{POOL_ID}':
            raise ValueError('Invalid issuer')

        user_id = claims['sub']

        return user_id

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise ValueError("Error processing token")