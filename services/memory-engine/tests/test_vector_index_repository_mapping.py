from datetime import datetime, timezone

from memory_refactor.core.models import EmbeddingVector, MemoryEmbedding
from memory_refactor.db.repositories.vector_index import (
    memory_embedding_from_record,
    memory_embedding_to_record,
)


def test_memory_embedding_record_mapping_round_trips_contract_fields() -> None:
    captured_at = datetime(2026, 5, 3, tzinfo=timezone.utc)
    embedding = MemoryEmbedding(
        id="emb_test",
        memory_id="mem_test",
        embedding_model="text-embedding-test",
        vector=EmbeddingVector(values=[0.1, 0.2, 0.3]),
        content_hash="sha256:test",
        created_at=captured_at,
        updated_at=captured_at,
    )

    record = memory_embedding_to_record(embedding)
    mapped = memory_embedding_from_record(record)

    assert record.dimensions == 3
    assert record.embedding == [0.1, 0.2, 0.3]
    assert mapped == embedding
