"""
Embedding Service.

Provides sentence embeddings for semantic
similarity computations.
"""

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Wrapper around SentenceTransformer.
    """

    def __init__(self):

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def encode(
        self,
        text: str,
    ):

        return self.model.encode(
            text,
            normalize_embeddings=True,
        )