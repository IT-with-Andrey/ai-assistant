import os
from mem0 import Memory
from backend.app.core.config import settings
# 1. Добавляем системную переменную для отключения телеметрии (самый надежный способ)
os.environ["MEM0_TELEMETRY_DISABLED"] = "true"

MEM0_CONFIG = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": settings.AI_MODEL, # Проверь модель, gemma4 еще не вышла
            "ollama_base_url": settings.OLLAMA_HOST
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
            "ollama_base_url": settings.OLLAMA_HOST
        }
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "mem0_memory",
            "path": os.path.join(os.getcwd(), "chroma_db_mem0")
        }
    }
}

class MemoryOrchestrator:
    def __init__(self):
        self.memory = Memory.from_config(MEM0_CONFIG)

    def add_user_memory(self, user_id: str, text: str):
        # Mem0 требует user_id в параметрах
        return self.memory.add(text, user_id=user_id)

    def get_user_fact(self, user_id: str) -> list[str]:
        # ИСПРАВЛЕНИЕ: используем filters вместо прямого аргумента
        memories = self.memory.get_all(filters={"user_id": user_id})
        
        # Защита: в зависимости от версии mem0, данные могут быть в разных полях
        facts = []
        for m in memories:
            if isinstance(m, dict):
                facts.append(m.get('text', ''))
        return facts

    def search_relevant_facts(self, user_id: str, query: str, limit: int = 3) -> str:
        """
        Ищет факты, которые подходят под текущую тему разговора.
        """
        results = self.memory.search(query, filters={"user_id": user_id}, limit=limit)
        
        if not results:
            return ""

        # Исправленная логика:
        relevant_facts = []
        for r in results:
            if isinstance(r, dict):
                # Если это словарь, берем поле 'text'
                fact = r.get('text', '')
            else:
                # Если это строка (или другой объект), берем её целиком
                fact = str(r)
            
            if fact:
                relevant_facts.append(fact)
                
        return "\n".join([f'- {fact}' for fact in relevant_facts])

memory_orchestrator = MemoryOrchestrator()