# Python stdlib
import re
import json

# Third-party
from sqlalchemy.orm import Session
from sqlalchemy import delete
from pydantic import TypeAdapter, ValidationError

# Project imports - AI layer
from backend.app.ai.provider import generate_response
from backend.app.ai.context_builder import build_context
from backend.app.ai.rag_manager import rag_manager
from backend.app.ai.models import Fact

# Project imports - DB layer
from backend.app.database.repository import (
    save_message,
    get_last_messages,
    get_lastest_summary,
    save_user_fact,
    get_all_user_facts,
    save_summary,
)
from backend.app.database.models import Message

# Core
from backend.app.core.logger import logger
from backend.app.core.logging_utils import log_execution_time


#Блок 2: Парсинг ответов модели (_extract_json)
def _extract_json(text: str | None) -> list | None:
    """Пытается извлечь JSON из текста, даже если он обёрнут в markdown-код."""
    if text is None:
        return None
    # Ищем JSON внутри markdown-кода
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        # Если нет markdown-кода, пытаемся найти JSON как есть
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            text = match.group(0)
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else None
    except json.JSONDecodeError:
        return None

MAX_HISTORY = 10

SUMMARY_TRIGGER = 6


@log_execution_time
def chat(user_input, db: Session) -> str:
    user_input = str(user_input)
    """
    Main function for processing a single user massage 
    Accepts:
            user_input - text enterd by the user
            db - ready SQLAlchemy session 
            Returns: 
                    answer = the assistant's response text 

    """
    # 1. Save the user's message to the database
    save_message(db, role='user', content=user_input)
    logger.info("Начало обработки сообщения: %s", user_input[:50])

    message_from_db = get_last_messages(db, limit=MAX_HISTORY)

    if len(message_from_db) >= MAX_HISTORY:
        logger.debug("Проверка истории: %d сообщений (порог %d)",
                     len(message_from_db), MAX_HISTORY)
        
        logger.info("Запущено извлечение фактов из %d сообщений", SUMMARY_TRIGGER)
        old_messages = message_from_db[:SUMMARY_TRIGGER]
        extraction_prompt = [{"role": "system",
                              "content": (
                                  "Ты — модуль извлечения фактов о пользователе из предоставленного диалога.\n"
                                  "Извлеки ТОЛЬКО те факты, которые пользователь явно сообщил в этом диалоге.\n"
                                  "Не добавляй ничего от себя, не домысливай, не используй внешние знания.\n"
                                  "Игнорируй общие фразы, вопросы и просьбы, не являющиеся информацией о самом пользователе.\n\n"
                                  "Твой ответ должен быть СТРОГО одним JSON-массивом. Никакого текста до или после массива. Никакой markdown-разметки (без ```json ... ```). Только чистый массив.\n\n"
                                  "Каждый элемент массива — это ОБЯЗАТЕЛЬНО объект ровно с двумя полями: \"key\" и \"value\".\n"
                                  "Оба значения ВСЕГДА строки.\n"
                                  "Использовать напрямую тип факта как ключ (например, {\"goal\": \"...\"}) ЗАПРЕЩЕНО.\n"
                                  "Пример НЕДОПУСТИМОГО формата: {\"goal\": \"выучить Python\"}\n"
                                  "Пример ДОПУСТИМОГО формата: {\"key\": \"goal\", \"value\": \"выучить Python\"}\n\n"
                                  "Даже если факт всего один, он должен быть внутри массива: [{\"key\": \"...\", \"value\": \"...\"}]\n\n"
                                  "Типы ключей (key) и правила их заполнения:\n"
                                  "- \"name\" — имя пользователя. Если назвал несколько имён — создавай отдельную запись для каждого.\n"
                                  "- \"goal\" — явно названная цель. Каждую цель оформляй отдельным объектом.\n"
                                  "- \"interest\" — хобби, увлечение, сфера интересов. Каждый интерес отдельной записью.\n"
                                  "- \"preference\" — конкретное предпочтение или пожелание. Значение записывай в формате \"характеристика: значение\" (например, \"стиль общения: дружелюбный\").\n"
                                  "- \"fact\" — любой другой явный факт о пользователе, не подходящий под категории выше.\n\n"
                                  "Если из сообщения не удалось извлечь ни одного факта, верни ПУСТОЙ массив: []\n\n"
                                  "Перед тем как выдать ответ, мысленно проверь каждый объект: содержит ли он строго два ключа — \"key\" и \"value\"? Если нет — исправь, чтобы содержал.\n\n"
                                  "Пример правильного полного ответа, если пользователь сказал: \"Меня зовут Алексей, хочу стать программистом и выучить Python, увлекаюсь фотографией, люблю дружелюбный стиль общения и работаю в банке\":\n"
                                  "[\n"
                                  "  {\"key\": \"name\", \"value\": \"Алексей\"},\n"
                                  "  {\"key\": \"goal\", \"value\": \"стать программистом\"},\n"
                                  "  {\"key\": \"goal\", \"value\": \"выучить Python\"},\n"
                                  "  {\"key\": \"interest\", \"value\": \"фотография\"},\n"
                                  "  {\"key\": \"preference\", \"value\": \"стиль общения: дружелюбный\"},\n"
                                  "  {\"key\": \"fact\", \"value\": \"работает в банке\"}\n"
                                  "]\n\n"
                                  "Ещё раз: никаких других форматов, никаких отклонений, только массив объектов {\"key\": \"...\", \"value\": \"...\"}."
                              )},
                             {"role": "user",
                              "content": ("Диалог для анализа:\n" + "\n".join([f"{m.role}: {m.content}" for m in old_messages]))}
                             ]
        try:
                
            raw_facts_json = generate_response(extraction_prompt)
            logger.debug("Сырой ответ модели (первые 300 символов): %s",
                        raw_facts_json[:300])
            logger.debug("raw_facts_json = %s", raw_facts_json)
            facts = _extract_json(raw_facts_json)

            logger.debug("facts = %s", facts)
            if facts is not None:

                try:
                    facts_adapter = TypeAdapter(list[Fact])
                    extracted_facts = facts_adapter.validate_python(facts)  # валидируем уже распарсенный список
                except (ValidationError, ValueError) as e:
                    logger.error(f"Fact validation failed: {e}")
                    extracted_facts = []

                for fact in extracted_facts:
                    save_user_fact(db, fact.key, fact.value)
                    rag_manager.add_fact(fact.key, fact.value)
                logger.info("Извлечено и сохранено %d фактов",
                            len(extracted_facts))
            else:
                # JSON не удалось извлечь — сохраняем сырой ответ как резюме
                logger.warning(
                    "Не удалось извлечь JSON из ответа модели, сохранено сырое резюме")
                save_summary(db, raw_facts_json)
             # Удаляем старые сообщения только после успешного сохранения фактов/резюме
            stmt = delete(Message).where(
                Message.id.in_([m.id for m in old_messages]))
            db.execute(stmt)
            db.commit()

            message_from_db = get_last_messages(db, limit=MAX_HISTORY)
        except Exception as e :
            db.rollback()
            logger.error("Ошибка при извлечении фактов и суммаризации, транзакция отменена: %s", e)
             # Продолжаем с текущим списком сообщений, история не пострадала
    #  Convert Message objects into a list of dicts for the AI
    history = [{'role': msg.role, 'content': msg.content}
               for msg in message_from_db]
    # Получаем все факты о пользователе
    latest_summary = get_lastest_summary(db)
    # Получаем все факты из краткосрочной памяти (SQLite)
    all_user_facts = get_all_user_facts(db)
    # Дополняем фактами из долговременной памяти (RAG)

    rag_facts = rag_manager.search_facts(user_input, top_k=5)
    # Конвертируем RAG-факты в строки для контекста
    rag_context = rag_manager.format_facts_as_context(rag_facts)
    # Объединяем всё в один блок (all_user_facts всё ещё можно использовать для билдера, если нужно)
    # Но для build_context мы по-прежнему передадим all_user_facts, а rag_context добавим отдельно

    # Берём последнее резюме, если есть

    context_message = build_context(history, user_input,
                                    user_facts=all_user_facts,
                                    summary=latest_summary.content if latest_summary else None)

    # 5. Получаем ответ
    if rag_context:
        context_message.insert(1, {'role': 'system', 'content': rag_context})
    # модель отвечает 
    answer = generate_response(context_message)

    # 6. Сохраняем ответ ассистента
    save_message(db, role='assistant', content=answer)
    logger.info("Завершена обработка сообщения, длина ответа: %d", len(answer))
    return answer


"""
CHAT PIPELINE / MAIN FLOW

user_input
  │
  ├─> str(user_input)
  │
  ├─> save_message(user)               # save user message to DB
  │
  ├─> get_last_messages(MAX_HISTORY)  # load recent history
  │
  ├─> if len(history) >= MAX_HISTORY:
  │      │
  │      ├─> old_messages = history[:SUMMARY_TRIGGER]
  │      │
  │      ├─> generate_response(extraction_prompt)
  │      │        # AI extracts facts from old dialogue
  │      │
  │      ├─> _extract_json(raw_facts_json)
  │      │        # try to parse JSON
  │      │
  │      ├─> validate_python(facts)
  │      │        # validate structure via Pydantic
  │      │
  │      ├─> save_user_fact(...)       # SQLite memory
  │      │
  │      ├─> rag_manager.add_fact(...) # RAG memory
  │      │
  │      ├─> save_summary(...)
  │      │        # fallback if JSON parsing failed
  │      │
  │      ├─> delete(old_messages)
  │      │
  │      └─> get_last_messages(...)
  │               # reload cleaned history
  │
  ├─> history = [...]
  │        # convert Message objects → dicts
  │
  ├─> get_latest_summary()
  │
  ├─> get_all_user_facts()
  │
  ├─> rag_manager.search_facts(user_input)
  │
  ├─> rag_manager.format_facts_as_context()
  │
  ├─> build_context(...)
  │        # combine:
  │        # - history
  │        # - summary
  │        # - user facts
  │        # - current message
  │
  ├─> if rag_context:
  │      └─> context_message.insert(...)
  │              # inject RAG facts into system prompt
  │
  ├─> generate_response(context_message)
  │        # main AI response
  │
  ├─> save_message(assistant)
  │        # save assistant reply
  │
  └─> return answer
"""
