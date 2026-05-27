
from sqlalchemy.orm import Session

from backend.app.database.repository import save_message, get_last_messages
from backend.app.ai.memory_orchestrator import memory_orchestrator
from backend.app.ai.context_builder import build_context
from backend.app.ai.provider import generate_response


def chat(user_input: str, db: Session, user_id: str = 'default_user') -> str:
    """
    Главная функция общения с ассистентом.
    Соединяет реляционную базу сообщений, память Mem0 и модель Ollama.
    """

    save_message(db, role='user', content=user_input)

    history = get_last_messages(db, limit=10)

    relevant_facts_string = memory_orchestrator.search_relevant_facts(user_id, query=user_input)


    context_messages = build_context(history, user_input , user_facts=relevant_facts_string)

    answer = generate_response(context_messages)

    save_message(db , role='assistant' , content=answer)

    memory_orchestrator.add_user_memory(user_id ,  text=user_input)

    return answer