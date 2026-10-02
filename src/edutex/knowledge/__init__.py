"""EduTeX Knowledge public API."""

from edutex.knowledge.loader import KnowledgeModelMeta, load_knowledge_model
from edutex.knowledge.models import ContentModel, ContentNode, TextBlock
from edutex.knowledge.query import ContentQuery, query_content
from edutex.knowledge.service import KnowledgeService

__all__ = [
    "ContentModel",
    "ContentQuery",
    "ContentNode",
    "KnowledgeModelMeta",
    "KnowledgeService",
    "TextBlock",
    "load_knowledge_model",
    "query_content",
]
