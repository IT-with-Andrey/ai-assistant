from backend.app.ai.personas import PERSONAS
from backend.app.ai.memory_orchestrator import memory_orchestrator


class PersonaManager:
    @staticmethod
    def get_persona_for_user(user_id: str) -> dict:
        facts = memory_orchestrator.get_user_fact(user_id)
        role = 'default'
        for fact in facts:
            if isinstance(fact, str) and fact.startswith('assistant_role:'):
                role = fact.split(':', 1)[1].strip()
                break
        return PERSONAS.get(role, PERSONAS['default'])

    @staticmethod
    def validate_role(role_name: str) -> bool:
        return role_name in PERSONAS

    @staticmethod
    def get_system_prompt(role_id: str) -> str:
        """Возвращает системный промпт для указанной роли, либо default."""
        return PERSONAS.get(role_id, PERSONAS["default"])["system_prompt"]

    @staticmethod
    def get_available_roles() -> list[dict]:
        return [{'id': key, "display_name": val["display_name"]} for key, val in PERSONAS.items()]