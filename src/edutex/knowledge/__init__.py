"""EduTeX Knowledge public API."""
from edutex.knowledge.authoring import AuthoringReport, validate_authoring

from edutex.knowledge.loader import KnowledgeModelMeta, load_knowledge_model
from edutex.knowledge.models import ContentModel, ContentNode, TextBlock
from edutex.knowledge.query import ContentQuery, query_content
from edutex.knowledge.schema import CONTENT_MODEL_SCHEMA_VERSION, content_model_schema
from edutex.knowledge.service import KnowledgeService

__all__ = [
    "ContentModel",
    "AuthoringReport",
    "CONTENT_MODEL_SCHEMA_VERSION",
    "ContentQuery",
    "ContentNode",
    "KnowledgeModelMeta",
    "KnowledgeService",
    "TextBlock",
    "load_knowledge_model",
    "query_content",
    "validate_authoring",
    "content_model_schema",
]
