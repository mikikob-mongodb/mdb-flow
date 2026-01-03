"""Embedding generation using Voyage AI."""

from typing import List, Union
import voyageai

from shared.config import settings


class EmbeddingService:
    """Service for generating embeddings using Voyage AI."""

    def __init__(self, model: str = "voyage-3"):
        """
        Initialize the embedding service.

        Args:
            model: Voyage AI model to use (default: voyage-3)
        """
        self.client = voyageai.Client(api_key=settings.voyage_api_key)
        self.model = model

    def embed_text(self, text: str, input_type: str = "document") -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            input_type: Type of input - "document" or "query"

        Returns:
            Embedding vector as list of floats
        """
        result = self.client.embed(
            texts=[text],
            model=self.model,
            input_type=input_type
        )
        return result.embeddings[0]

    def embed_texts(
        self,
        texts: List[str],
        input_type: str = "document"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            input_type: Type of input - "document" or "query"

        Returns:
            List of embedding vectors
        """
        result = self.client.embed(
            texts=texts,
            model=self.model,
            input_type=input_type
        )
        return result.embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Query text to embed

        Returns:
            Embedding vector as list of floats
        """
        return self.embed_text(query, input_type="query")

    def embed_document(self, document: str) -> List[float]:
        """
        Generate embedding for a document.

        Args:
            document: Document text to embed

        Returns:
            Embedding vector as list of floats
        """
        return self.embed_text(document, input_type="document")


# Global embedding service instance
embedding_service = EmbeddingService()


def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a search query.

    Args:
        query: Query text to embed

    Returns:
        Embedding vector as list of floats
    """
    return embedding_service.embed_query(query)


def embed_document(document: str) -> List[float]:
    """
    Generate embedding for a document.

    Args:
        document: Document text to embed

    Returns:
        Embedding vector as list of floats
    """
    return embedding_service.embed_document(document)


def embed_documents(documents: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple documents.

    Args:
        documents: List of document texts to embed

    Returns:
        List of embedding vectors
    """
    return embedding_service.embed_texts(documents, input_type="document")
