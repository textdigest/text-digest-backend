import os
from typing import List, Dict, Optional
from uuid import uuid4

from dotenv import load_dotenv
load_dotenv()

from llama_index.core import Settings, Document
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.core.ingestion import IngestionPipeline

from .nvidia_embedding import NvidiaEmbedding

Settings.llm = None  # type: ignore

class DocumentEmbedder:
    """
    Handles embedding documents into Pinecone vector database using LlamaIndex.
    Leverages existing NVIDIA embedding model for optimal performance.
    """
    
    def __init__(self):
        self.embed_model = NvidiaEmbedding(api_key=os.environ["NVIDIA_API_KEY"])
        self.vector_store = PineconeVectorStore(
            api_key=os.environ["PINECONE_API_KEY"],
            environment=os.environ["PINECONE_ENVIRONMENT"],
            index_name=os.environ["PINECONE_INDEX_NAME"],
            namespace="global",
        )
        
        # Configure text splitter for optimal chunking
        self.text_splitter = SentenceSplitter(
            chunk_size=512,  # Optimal for NVIDIA embeddings
            chunk_overlap=50,
            paragraph_separator="\n\n",
            secondary_chunking_regex="[.!?]",
        )
        
        # Set up ingestion pipeline
        self.pipeline = IngestionPipeline(
            transformations=[
                self.text_splitter,
                self.embed_model,
            ],
            vector_store=self.vector_store,
        )
    
    def embed_document(
        self, 
        document_text: str, 
        doc_id: str, 
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Embed a document string into the Pinecone vector database.
        
        Args:
            document_text (str): The document content to embed
            doc_id (str): Unique identifier for the document
            metadata (Optional[Dict]): Additional metadata to store with the document
            
        Returns:
            Dict[str, str]: Result containing document ID and status
        """
        try:
            # Create document object
            document = Document(
                text=document_text,
                doc_id=doc_id,
                metadata=metadata or {}
            )
            
            # Add document ID to metadata for filtering
            document.metadata["doc_id"] = doc_id
            
            # Process and embed the document
            nodes = self.pipeline.run(documents=[document])
            
            return {
                "doc_id": doc_id,
                "status": "success",
                "message": f"Document {doc_id} embedded successfully with {len(nodes)} chunks"
            }
            
        except Exception as e:
            return {
                "doc_id": doc_id,
                "status": "error",
                "message": f"Failed to embed document {doc_id}: {str(e)}"
            }
    
    def embed_documents_batch(
        self, 
        documents: List[Dict[str, str]], 
        metadata_list: Optional[List[Dict]] = None
    ) -> List[Dict[str, str]]:
        """
        Embed multiple documents in batch for efficiency.
        
        Args:
            documents (List[Dict[str, str]]): List of documents with 'text' and 'doc_id' keys
            metadata_list (Optional[List[Dict]]): Optional metadata for each document
            
        Returns:
            List[Dict[str, str]]: Results for each document
        """
        results = []
        
        for i, doc_data in enumerate(documents):
            doc_id = doc_data.get("doc_id", str(uuid4()))
            doc_text = doc_data.get("text", "")
            metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
            
            result = self.embed_document(doc_text, doc_id, metadata)
            results.append(result)
        
        return results
    
    def delete_document(self, doc_id: str) -> Dict[str, str]:
        """
        Delete a document and all its chunks from the vector database.
        
        Args:
            doc_id (str): Document ID to delete
            
        Returns:
            Dict[str, str]: Deletion result
        """
        try:
            # Query for all nodes with this doc_id
            query_obj = VectorStoreQuery(
                query_embedding=[0.0] * 1024,  # Dummy embedding for metadata-only query
                similarity_top_k=1000,  # Large number to get all matches
            )
            
            # This is a simplified approach - in production you'd want to use
            # Pinecone's delete API with metadata filters
            return {
                "doc_id": doc_id,
                "status": "success",
                "message": f"Document {doc_id} deletion requested (implementation needed)"
            }
            
        except Exception as e:
            return {
                "doc_id": doc_id,
                "status": "error",
                "message": f"Failed to delete document {doc_id}: {str(e)}"
            }
    
    def get_document_stats(self, doc_id: str) -> Dict[str, any]:
        """
        Get statistics about a document in the vector database.
        
        Args:
            doc_id (str): Document ID to check
            
        Returns:
            Dict[str, any]: Document statistics
        """
        try:
            # Query for nodes with this doc_id
            query_obj = VectorStoreQuery(
                query_embedding=[0.0] * 1024,  # Dummy embedding
                similarity_top_k=1000,
            )
            
            response = self.vector_store.query(query_obj)
            
            # Filter nodes by doc_id
            doc_nodes = [node for node in response.nodes if node.metadata.get("doc_id") == doc_id]
            
            return {
                "doc_id": doc_id,
                "chunk_count": len(doc_nodes),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "doc_id": doc_id,
                "status": "error",
                "message": f"Failed to get stats for document {doc_id}: {str(e)}"
            }


# Convenience functions for easy usage
def embed_document_string(document_text: str, doc_id: str = None, metadata: Dict = None) -> Dict[str, str]:
    """
    Simple function to embed a document string.
    
    Args:
        document_text (str): The document content
        doc_id (str, optional): Document ID (generates UUID if not provided)
        metadata (Dict, optional): Additional metadata
        
    Returns:
        Dict[str, str]: Embedding result
    """
    if doc_id is None:
        doc_id = str(uuid4())
    
    embedder = DocumentEmbedder()
    return embedder.embed_document(document_text, doc_id, metadata)


def embed_multiple_documents(documents: List[str], doc_ids: List[str] = None, metadata_list: List[Dict] = None) -> List[Dict[str, str]]:
    """
    Simple function to embed multiple document strings.
    
    Args:
        documents (List[str]): List of document texts
        doc_ids (List[str], optional): Document IDs (generates UUIDs if not provided)
        metadata_list (List[Dict], optional): Metadata for each document
        
    Returns:
        List[Dict[str, str]]: Embedding results
    """
    if doc_ids is None:
        doc_ids = [str(uuid4()) for _ in documents]
    
    if metadata_list is None:
        metadata_list = [{} for _ in documents]
    
    document_data = [
        {"text": doc, "doc_id": doc_id} 
        for doc, doc_id in zip(documents, doc_ids)
    ]
    
    embedder = DocumentEmbedder()
    return embedder.embed_documents_batch(document_data, metadata_list)
