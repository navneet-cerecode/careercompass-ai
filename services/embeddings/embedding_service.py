"""
Embedding Service.

Provides sentence embeddings for semantic
similarity computations.
"""

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


class EmbeddingService:
    """
    Wrapper around SentenceTransformer.
    """

    def __init__(self):

        self.model = SentenceTransformer(
            EMBEDDING_MODEL_ID,
            revision=EMBEDDING_MODEL_REVISION,
        )

    def encode(
        self,
        text: str,
    ):

        return self.model.encode(
            text,
            normalize_embeddings=True,
        )
