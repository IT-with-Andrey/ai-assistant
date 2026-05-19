

from backend.app.ai.provider import generate_response

from backend.app.ai.context_builder import build_context

from backend.app.database.repository import save_message , get_last_messages ,save_summary , get_lastest_summary

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
    # Get the last 10 messages from the DB (now including the one we just save
    message_from_db = get_last_messages(db,limit=MAX_HISTORY)
    if len(message_from_db) >= MAX_HISTORY:
        old_messages = message_from_db[:SUMMARY_TRIGGER]
        summary_prompt = [
            {'role':'system', 'content':  'Summarize the following conversation in Russian. Keep important details, decisions, user preferences.'
            ' Write concisely . Write concisely '},
             {"role": "user", "content": "\n".join([f"{m.role}: {m.content}" for m in old_messages])}
        ]

        # Generate a resume
        summary_text = generate_response(summary_prompt)

        # Saved summary in basedata
        save_summary(db,summary_text)

        stmt = delete(Message).where(Message.id.in_([m.id for m in old_messages]))
        db.execute(stmt)
        db.commit()

        message_from_db = get_last_messages(db , limit=MAX_HISTORY)


    #  Convert Message objects into a list of dicts for the AI
    history = [{'role': msg.role, 'content': msg.content} for msg in message_from_db]
    # Берём последнее резюме, если есть
    latest_summary = get_lastest_summary(db)
    context_message = build_context(history, user_input, summary=latest_summary.content if latest_summary else None)

    # 5. Получаем ответ
    answer = generate_response(context_message)

    # 6. Сохраняем ответ ассистента
    save_message(db, role='assistant', content=answer)

    return answer