import os
from typing import Optional, List, Dict

from dotenv import load_dotenv
load_dotenv()

from llama_index.core import Settings
from llama_index.core.schema import BaseNode
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterOperator, VectorStoreQuery
from .nvidia_embedding import NvidiaEmbedding

Settings.llm = None  # type: ignore

def query_text_embedding(query_text: str, top_k: int, doc_name: Optional[str]) -> dict:
    print({"query_text": query_text, "top_k": top_k, "doc_name": doc_name})
    """This tool will retrieve chunks of industry standards documentation related to the query text.

    Args:
        query_text (str): Grammatically valid English that will be used to find related industry standards documentation.
        top_k (int): Number of relevant chunks to retrieve. Must be less than 5.
        doc_name (Optional[str]): Specific document name to filter by (e.g., "OSHA", "TPI", "ISO"). Use None for no filter.
        
    Returns:
        str: Industry standards documentation.
    """

    vector_store = PineconeVectorStore(
        api_key=os.environ["PINECONE_API_KEY"],
        environment=os.environ["PINECONE_ENVIRONMENT"],
        index_name=os.environ["PINECONE_INDEX_NAME"],
        namespace="global",
    )

    embed_model = NvidiaEmbedding(api_key=os.environ["NVIDIA_API_KEY"])
    query_embedding = embed_model.get_query_embedding(query_text)

    filters = None
    if doc_name:
        filters = MetadataFilters(filters=[
            MetadataFilter(
                key="doc_name", 
                value=doc_name, 
                operator=FilterOperator.EQ
            )
        ])

    query_obj = VectorStoreQuery(
        query_embedding=query_embedding,
        similarity_top_k=top_k,
        filters=filters
    )

    response = vector_store.query(query_obj)
    
    pages: Dict[int, List[BaseNode]] = {}
    if response.nodes:
        for node in response.nodes:
            page_num = node.metadata.get("page_number", None)
            if page_num is None:
                continue
            pages.setdefault(page_num, []).append(node)

    page_objects = []
    for page_num, node_list in pages.items():
        sorted_nodes = sorted(node_list, key=lambda n: getattr(n, "start_char_idx", 0) or 0)
        seen = set()
        chunks: List[str] = []
        for n in sorted_nodes:
            txt = n.get_content()
            if txt not in seen:
                chunks.append(txt)
                seen.add(txt)
        content = " ".join(chunks)
        page_objects.append({"page_number": page_num, "content": content})

    return {"standards_retrieved": page_objects}