"""
Менеджер долговременной памяти через ChromaDB + multilingual-e5-small.
Сохраняет факты о пользователе и ищет их по семантическому смыслу.
"""
import os
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer


class RAGManager:
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-small",
        persist_directory: str = "./chroma_db",
        collection_name: str = "user_facts",
    ):
        # Загружаем модель один раз при старте
        self.model = SentenceTransformer(model_name)

        # Персистентное хранилище ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # косинусное расстояние
        )

    def _text_for_embedding(self, key: str, value: str, is_query: bool = False) -> str:
        """
        Формирует текст с префиксом, необходимым для моделей E5.
        Для документов: passage: текст
        Для запросов:  query: текст
        """
        text = f"{key}: {value}" if key else value
        prefix = "query: " if is_query else "passage: "
        return prefix + text

    def add_fact(self, key: str, value: str) -> None:
        """
        Сохраняет (или обновляет) факт в векторной базе.
        ID документа = 'fact_<key>', что гарантирует уникальность.
        """
        passage = self._text_for_embedding(key, value, is_query=False)
        embedding = self.model.encode(passage).tolist()
        doc_id = f"fact_{key}"

        self.collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[{"key": key, "value": value}],
            documents=[passage],   # храним текстовое представление для отладки
        )

    def search_facts(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, str]]:
        """
        Ищет топ-K самых похожих фактов по запросу.
        Возвращает список словарей с ключами: key, value, distance.
        """
        query_text = self._text_for_embedding("", query, is_query=True)
        query_embedding = self.model.encode(query_text).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances"],
        )

        facts = []
        if results["metadatas"] and results["metadatas"][0]:
            for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
                facts.append(
                    {
                        "key": meta["key"],
                        "value": meta["value"],
                        "distance": dist,
                    }
                )
        return facts

    def format_facts_as_context(self, facts: List[Dict[str, str]]) -> str:
        """
        Преобразует список найденных фактов в текстовый блок для промпта.
        """
        if not facts:
            return "Нет сохранённых фактов о пользователе."

        lines = ["Факты о пользователе, которые могут быть полезны:"]
        for fact in facts:
            lines.append(f"- {fact['key']}: {fact['value']}")
        return "\n".join(lines)

    def delete_fact(self, key: str) -> None:
        """Удаляет факт по ключу из ChromaDB."""
        self.collection.delete(ids=[f"fact_{key}"])


# Синглтон, готовый к импорту в другие модули
rag_manager = RAGManager()