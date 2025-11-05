from fastapi import APIRouter, Request
from agents import TResponseInputItem
from pydantic import BaseModel
from typing import List

from util.tokens.verifyIdToken import verify_token

from services.agents.stream_run import stream_run
from services.agents.qna_agent import qna_agent, QnaAgentContext
from services.websocket.streamer import WebSocketStream

router = APIRouter()

class PostQnaRequest(BaseModel):
    query: str
    highlighted_text: str
    page_content: str
    curr_conversation: List[TResponseInputItem]

@router.post("/post-qna")
async def post_qna_message(request: Request, body: PostQnaRequest):
    auth_header = request.headers.get("authorization")

    user_id = verify_token(auth_header)

    websocket_streamer = WebSocketStream("reader-qna", user_id)

    stream_res = await stream_run(
        agent=qna_agent,
        input_items=body.curr_conversation,
        stream_callback=websocket_streamer.send_chunk,
        context=QnaAgentContext(
            query=body.query,
            highlighted_text=body.highlighted_text,
            page_content=body.page_content,
        ),
    )

    conversation = stream_res.to_input_list()

    await websocket_streamer.send_chunk(conversation, "turn-over")

    return {"conversation": conversation}