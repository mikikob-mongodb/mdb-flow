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


# =============================================================================
# TASK AND PROJECT EMBEDDING HELPERS
# =============================================================================

def build_task_embedding_text(task_doc: dict) -> str:
    """
    Build comprehensive searchable text for task embedding.

    Combines all relevant fields to enable semantic search across:
    - Title and description (what the task is)
    - Context (why/how)
    - Notes (discussions and decisions)
    - Blockers (what's preventing progress)
    - Assignee (who's responsible)

    Args:
        task_doc: Task document from MongoDB

    Returns:
        Combined text string for embedding
    """
    parts = []

    # Core fields
    if task_doc.get("title"):
        parts.append(task_doc["title"])

    if task_doc.get("description"):
        parts.append(task_doc["description"])

    # Context and notes
    if task_doc.get("context"):
        parts.append(task_doc["context"])

    if task_doc.get("notes"):
        # Join all notes with separator
        notes_text = " | ".join(task_doc["notes"])
        parts.append(notes_text)

    # Blockers (important for queries like "what's blocking progress")
    if task_doc.get("blockers"):
        blockers_text = "blockers: " + " | ".join(task_doc["blockers"])
        parts.append(blockers_text)

    # Assignee (enables queries like "show me Mike's tasks")
    if task_doc.get("assignee"):
        parts.append(f"assigned to {task_doc['assignee']}")

    # Priority for context
    if task_doc.get("priority"):
        parts.append(f"{task_doc['priority']} priority")

    return " ".join(parts)


def build_project_embedding_text(project_doc: dict) -> str:
    """
    Build comprehensive searchable text for project embedding.

    Combines all relevant fields to enable semantic search across:
    - Name and description (what the project is)
    - Context (why/how)
    - Notes (discussions and decisions)
    - Updates (status updates and progress)
    - Stakeholders (who's involved)
    - Methods and decisions

    Args:
        project_doc: Project document from MongoDB

    Returns:
        Combined text string for embedding
    """
    parts = []

    # Core fields
    if project_doc.get("name"):
        parts.append(project_doc["name"])

    if project_doc.get("description"):
        parts.append(project_doc["description"])

    # Context and notes
    if project_doc.get("context"):
        parts.append(project_doc["context"])

    if project_doc.get("notes"):
        # Join all notes with separator
        notes_text = " | ".join(project_doc["notes"])
        parts.append(notes_text)

    # Project updates (status updates over time)
    if project_doc.get("updates"):
        updates_texts = []
        for update in project_doc["updates"]:
            if isinstance(update, dict) and update.get("content"):
                updates_texts.append(update["content"])
            elif hasattr(update, "content"):
                # Handle ProjectUpdate object
                updates_texts.append(update.content)
        if updates_texts:
            updates_text = " | ".join(updates_texts)
            parts.append(f"updates: {updates_text}")

    # Stakeholders (enables queries like "show me projects Mike is involved in")
    if project_doc.get("stakeholders"):
        stakeholders_text = "stakeholders: " + " ".join(project_doc["stakeholders"])
        parts.append(stakeholders_text)

    # Methods/technologies
    if project_doc.get("methods"):
        methods_text = "methods: " + " ".join(project_doc["methods"])
        parts.append(methods_text)

    # Key decisions
    if project_doc.get("decisions"):
        decisions_text = " | ".join(project_doc["decisions"])
        parts.append(f"decisions: {decisions_text}")

    return " ".join(parts)
