
from sqlalchemy.orm import Session

from backend.app.database.repository import save_message, get_last_messages
from backend.app.ai.memory_orchestrator import memory_orchestrator
from backend.app.ai.context_builder import build_context
from backend.app.ai.provider import generate_response
from backend.app.ai.persona_manager import PersonaManager

def chat(user_input: str, db: Session, user_id: str = 'default_user') -> str:
    """
    Главная функция общения с ассистентом.
    Соединяет реляционную базу сообщений, память Mem0 и модель Ollama.
    """
    user_input = user_input.strip()

    # Обработка команды /role
    if user_input.startswith("/role"):
        parts = user_input.split(" ", 1)
        if len(parts) < 2 or not PersonaManager.validate_role(parts[1]):
            roles = "\n".join([f"- {r['id']} ({r['display_name']})" for r in PersonaManager.get_available_roles()])
            return f"Неверная роль. Доступные роли:\n{roles}"
        new_role = parts[1]
        memory_orchestrator.add_user_memory(user_id, text=f"assistant_role: {new_role}")
        return f"Роль успешно сменена на: {new_role}"

    # Обработка команды /help
    if user_input.startswith("/help"):
        return "Доступные команды:\n/role <название> - сменить роль\n/help - список команд"


    save_message(db, role='user', content=user_input)

    history = get_last_messages(db, limit=10)

    relevant_facts_string = memory_orchestrator.search_relevant_facts(user_id, query=user_input)


    context_messages = build_context(
        history, 
        user_input, 
        user_facts=relevant_facts_string, 
        user_id=user_id  
    )

    answer = generate_response(context_messages)

    save_message(db , role='assistant' , content=answer)

    memory_orchestrator.add_user_memory(user_id ,  text=user_input)

    return answer