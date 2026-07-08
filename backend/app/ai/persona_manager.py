import asyncio
from backend.app.ai.personas import PERSONAS
# ИСПРАВЛЕНО: Убрали сломанный импорт memory_orchestrator, который вызывал падение.
# Теперь менеджер полностью независим и получает оркестратор через конструктор!

class PersonaManager:
    """Управление ролями ассистента с асинхронной загрузкой данных из памяти."""
    def __init__(self, memory_orchestrator):
        self.memory = memory_orchestrator

    async def get_persona_for_user(self, user_id: str) -> dict:
        facts = await self.memory.get_user_fact(user_id)
        role = 'default'
        for fact in facts:
            if isinstance(fact, str) and fact.startswith('assistant_role:'):
                role = fact.split(':', 1)[1].strip()
                break
        return PERSONAS.get(role, PERSONAS['default'])

    async def get_system_prompt(self, role_id: str) -> str:
         """Асинхронно возвращает системный промпт (в будущем может грузить из БД)."""
         return PERSONAS.get(role_id, PERSONAS['default'])['system_prompt']

    @staticmethod
    def validate_role(role_name: str) -> bool:
        return role_name in PERSONAS

    @staticmethod
    def get_available_roles() -> list[dict]:
        return [{'id': key, "display_name": val["display_name"]} for key, val in PERSONAS.items()]