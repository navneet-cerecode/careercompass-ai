from services.embeddings.embedding_service import (
    EMBEDDING_MODEL_ID,
    EMBEDDING_MODEL_REVISION,
)


def test_embedding_model_is_namespaced_and_revision_pinned():
    assert EMBEDDING_MODEL_ID == "sentence-transformers/all-MiniLM-L6-v2"
    assert len(EMBEDDING_MODEL_REVISION) == 40
    assert all(character in "0123456789abcdef" for character in EMBEDDING_MODEL_REVISION)
