import os 
from mem0 import Memory

MEM0_CONFIG = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": os.getenv("AI_MODEL", "gemma4:31b-cloud"),
            "ollama_base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434")
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
            "ollama_base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434")
        }
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "mem0_memory",
            "path": os.path.join(os.getcwd(), "chroma_db_mem0")
        }
    },
    "disable_telemetry": True
}

class MemoryOrchestrator:
    def __init__(self):
        self.memory = Memory.from_config(MEM0_CONFIG)

    def add_user_memory(self, user_id: str, text: str):
        """Сохраняет или обновляет важные жизненные факты пользователя из текста."""
        # В этой версии add принимает user_id как отдельный параметр
        return self.memory.add(text, user_id=user_id)

    def get_user_fact(self, user_id: str) -> list[str]:
        """Возвращает список всех структурированных фактов, которые ИИ запомнил о тебе."""
        # get_all также, вероятно, поддерживает прямой user_id (ошибок не было)
        memories = self.memory.get_all(user_id=user_id)
        facts = [m['text'] for m in memories if 'text' in m]
        return facts

    def search_relevant_facts(self, user_id: str, query: str, limit: int = 3) -> str:
        """
        Ищет факты, которые подходят под текущую тему разговора.
        search требует передачи user_id внутри filters
        """
        results = self.memory.search(query, filters={"user_id": user_id}, limit=limit)
        if not results:
            return ""
        relevant_facts = [r['text'] for r in results if 'text' in r]
        return "\n".join([f'-{fact}' for fact in relevant_facts])


memory_orchestrator = MemoryOrchestrator()