

from backend.app.ai.provider import generate_response

from backend.app.ai.context_builder import build_context

from backend.app.database.repository import save_message , get_last_messages , get_lastest_summary ,save_user_fact , get_all_user_facts ,save_summary 

from backend.app.database.models import Message

from sqlalchemy import delete


MAX_HISTORY = 10 

SUMMARY_TRIGGER =  6 


def chat(user_input, db):
    """
    Main function for processing a single user massage 
    Accepts:
            user_input - text enterd by the user
            db - ready SQLAlchemy session 
            Returns: 
                    answer = the assistant's response text 
    
    """
     # 1. Save the user's message to the database

    save_message(db , role='user', content=user_input)
    
    message_from_db = get_last_messages(db,limit=MAX_HISTORY)
    if len(message_from_db) >= MAX_HISTORY:
        old_messages = message_from_db[:SUMMARY_TRIGGER]
        extraction_prompt = [ { "role": "system", 
                    "content": ( "Ты — система извлечения пользовательской памяти. " 
                            "Твоя задача — извлечь ТОЛЬКО явные факты из диалога о пользователе: " 
                            "имя, цели, проекты, технологии, языки, интересы, предпочтения, опыт, планы, background. " 
                            "Не выдумывай ничего, чего нет в диалоге. " "Не используй догадки и не дополняй факты от себя. " 
                            "Не дублируй одинаковую информацию. " "Если один и тот же факт можно записать несколькими способами — выбери один короткий и консистентный вариант. " 
                            "Пиши value кратко, конкретно и без лишних пояснений. " 
                            "Верни СТРОГО JSON-массив объектов вида:\n" '[{"key":"...","value":"..."}, ...]\n' 
                            "Используй только lowercase key в едином стиле, например: name, goals, projects, languages, interests, preferences, background. " 
                            "Если фактов нет, верни []. " 
                            "Не добавляй markdown, комментарии, пояснения или любой другой текст вне JSON." ) }, 
                            { "role": "user", 
                            "content": ( "Диалог для анализа:\n" + "\n".join([f"{m.role}: {m.content}" for m in old_messages]) ) } 
                            ]

        raw_facts_json = generate_response(extraction_prompt)
        import json
        try:
            facts = json.loads(raw_facts_json)
            if isinstance(facts, list):  
                for fact in facts:
                    if isinstance(fact,dict ) and 'key' in fact and 'value' in fact:
                        save_user_fact(db , fact['key'], fact['value'])
        except json.JSONDecodeError:
            save_summary(db,raw_facts_json)

        stmt = delete(Message).where(Message.id.in_([m.id for m in old_messages]))
        db.execute(stmt)
        db.commit()

        message_from_db = get_last_messages(db , limit=MAX_HISTORY)


    #  Convert Message objects into a list of dicts for the AI
    history = [{'role': msg.role, 'content': msg.content} for msg in message_from_db]
     # Получаем все факты о пользователе
    latest_summary = get_lastest_summary(db)
    user_facts = get_all_user_facts(db)
    # Берём последнее резюме, если есть

    context_message = build_context(history, user_input, 
                                    user_facts=user_facts,
                                    summary=latest_summary.content if latest_summary else None)

    # 5. Получаем ответ
    answer = generate_response(context_message)

    # 6. Сохраняем ответ ассистента
    save_message(db, role='assistant', content=answer)

    return answer




"""
user_input
  │
  ├─> save_message(user)          # БД
  ├─> get_last_messages(10)       # БД
  ├─> if len >= 10:
  │     ├─> generate_response(...) # AI (суммаризация)
  │     ├─> save_message(...)      # БД
  │     └─> delete old messages    # БД
  ├─> get_last_messages(10)       # БД (обновлённые)
  ├─> build_context(history, user_input, summary)  # формирование контекста
  ├─> generate_response(context)  # AI (основной ответ)
  └─> save_message(assistant)     # БД
"""