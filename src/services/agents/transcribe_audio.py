import base64
import io
from openai import OpenAI

openai_client = OpenAI()

def transcribe_audio_from_base64(audio_base64: str, file_extension: str = "webm") -> str:
    data = base64.b64decode(audio_base64)
    buffer = io.BytesIO(data)
    buffer.name = f"audio.{file_extension}"
    result = openai_client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=buffer,
        language="en",
    )
    print(f"Transcription result: {result.text}")
    return result.text