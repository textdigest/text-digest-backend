from agents import Runner, TResponseInputItem, RunResultStreaming
from typing import Any, List

async def stream_run(
    agent: Any,
    input_items: List[TResponseInputItem],
    *,
    stream_callback=None,
    event_name: str = "chunk",
    **kwargs,
) -> RunResultStreaming:
    streamed = Runner.run_streamed(agent, input_items, **kwargs)

    text_parts: list[str] = []
    try:
        async for event in streamed.stream_events():       
            if getattr(event, "type", "") == "raw_response_event":
                data = getattr(event, "data", {})
                delta_str = None
                if hasattr(data, "delta"):
                    delta_str = getattr(data, "delta")
                elif isinstance(data, dict):
                    delta_str = (
                        data.get("delta")
                        or data.get("content")
                        or (
                            data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                            if "choices" in data
                            else ""
                        )
                    )
                if delta_str:
                    if stream_callback:
                        await stream_callback(delta_str, event_name)
                    else:
                        print(delta_str, end="", flush=True)
                    text_parts.append(str(delta_str))

        full_text = "".join(text_parts)
        setattr(streamed, "streamed_text", full_text)
        return streamed
    
    except Exception as e:
        print("\n[Streaming disabled due to error, falling back]\n", e, flush=True)
        result = await Runner.run(agent, input_items, **kwargs)
        print(result.final_output)
        raise e