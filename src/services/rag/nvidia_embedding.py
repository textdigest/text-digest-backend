from typing import Any, List, Optional
from openai import OpenAI

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.bridge.pydantic import PrivateAttr


class NvidiaEmbedding(BaseEmbedding):
    _client: OpenAI = PrivateAttr()
    _model: str = PrivateAttr()
    _params: dict = PrivateAttr()

    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/llama-3.2-nv-embedqa-1b-v2",
        base_url: str = "https://integrate.api.nvidia.com/v1",
        model_params: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._params = model_params or {
            "encoding_format": "float",
            "extra_body": {"input_type": "query", "truncate": "NONE"},
        }

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    def _get_query_embedding(self, query: str) -> List[float]:
        r = self._client.embeddings.create(input=[query], model=self._model, **self._params)
        return r.data[0].embedding

    def _get_text_embedding(self, text: str) -> List[float]:
        r = self._client.embeddings.create(input=[text], model=self._model, **self._params)
        return r.data[0].embedding

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        r = self._client.embeddings.create(input=texts, model=self._model, **self._params)
        return [d.embedding for d in r.data] 