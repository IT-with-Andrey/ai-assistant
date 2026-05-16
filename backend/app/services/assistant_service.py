
from backend.app.ai.provider import generate_response

from backend.app.ai.context_builder import build_context

from backend.app.database.repository import save_message , get_last_messages




def chat(user_input):
    # 1. сохраняем сообщение пользователя в БД
    save_message(role='user', content=user_input)
    # 2. берём историю из БД
    message_from_db = get_last_messages(limit=10)

    # 3. превращаем в формат для LLM
    history = [
        {
            'role': msg.role,
            'content': msg.content

        }
        for msg in message_from_db
    ]
    message = build_context(history,user_input)

    answer = generate_response(message)

    save_message(role='assistant' , content=answer)
    
    return answer