import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import patch, MagicMock
from backend.app.ai.rag_manager import RAGManager
from backend.app.database.models import UserFact

FAKE_EMBEDDING = [0.0] * 384

def _fake_encode():
    mock = MagicMock()
    mock.tolist.return_value = FAKE_EMBEDDING
    return mock

def test_add_fact(db_session):
    with patch("backend.app.ai.rag_manager.SentenceTransformer") as mock_st:
        mock_st.return_value.encode.return_value = _fake_encode()
        rag = RAGManager(db_session)
        mock_collection = MagicMock()
        rag.collection = mock_collection
        rag.add_fact("name", "Алиса")
        mock_collection.upsert.assert_called_once()
        call_kwargs = mock_collection.upsert.call_args.kwargs
        assert call_kwargs["ids"] == ["fact_name"]

def test_search_fact(db_session):
    with patch("backend.app.ai.rag_manager.SentenceTransformer") as mock_st:
        mock_st.return_value.encode.return_value = _fake_encode()
        rag = RAGManager(db_session)
        with patch.object(rag.collection, "query") as mock_query:
            mock_query.return_value = {
                "ids": [["fact_name"]],
                "metadatas": [[{"key": "name", "value": "Алиса"}]],
                "distances": [[0.1]],
            }
            results = rag.search_facts("Алиса")
    assert len(results) > 0
    assert results[0]["key"] == "name"
    assert results[0]["value"] == "Алиса"

def test_delete_fact(db_session):
    fact = UserFact(key="name", value="Алиса")
    db_session.add(fact)
    db_session.commit()

    with patch("backend.app.ai.rag_manager.SentenceTransformer") as mock_st:
        mock_st.return_value.encode.return_value = _fake_encode()
        rag = RAGManager(db_session)
        mock_collection = MagicMock()
        rag.collection = mock_collection
        rag.delete_fact(fact.id)
        mock_collection.delete.assert_called_once_with(ids=[f"fact_{fact.id}"])

    # В текущей версии RAGManager не удаляет факт из SQL-базы, только из Chroma
    assert db_session.query(UserFact).count() == 1

def test_empty_search(db_session):
    with patch("backend.app.ai.rag_manager.SentenceTransformer") as mock_st:
        mock_st.return_value.encode.return_value = _fake_encode()
        rag = RAGManager(db_session)
        with patch.object(rag.collection, "query") as mock_query:
            mock_query.return_value = {"ids": [], "metadatas": [], "distances": []}
            results = rag.search_facts("несуществующее")
    assert results == []