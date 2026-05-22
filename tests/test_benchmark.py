# tests/test_benchmark.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from backend.app.database.models import UserFact
from backend.app.services.assistant_service import chat

# Используем общую фикстуру db_session из tests/conftest.py


def test_memory_accuracy(db_session: Session):
    # 10 фактов
    facts_to_load = [
        ("name", "Меня зовут Алиса."),
        ("goal", "Моя цель — выучить Python."),
        ("interest", "Я интересуюсь машинным обучением."),
        ("preference", "Я предпочитаю тёмную тему в редакторе."),
        ("fact", "Я работаю инженером в IT-компании."),
        ("name", "Моё второе имя — Боб."),
        ("goal", "Хочу пробежать марафон."),
        ("interest", "Увлекаюсь астрономией."),
        ("preference", "Люблю кофе по утрам."),
        ("fact", "Живу в городе Нск."),
    ]

    # Готовим JSON-массив для извлечения
    facts_json = ", ".join(
        [f'{{"key": "{key}", "value": "{value}"}}' for key, value in facts_to_load]
    )
    extraction_response = f"[{facts_json}]"

    # Мок, различающий вызовы: extraction prompt содержит русское "Извлеки"
    def mock_generate_response(prompt, *args, **kwargs):
        if "Извлеки" in str(prompt):
            return extraction_response
        return "Принято."

    with patch("backend.app.services.assistant_service.generate_response",
               side_effect=mock_generate_response):
        # Загружаем факты через 10 сообщений
        for _, msg in facts_to_load:
            chat(msg, db_session)
        # Дополнительное сообщение для превышения MAX_HISTORY
        chat("Сохрани всё, что узнал.", db_session)

    # Проверяем, что каждый факт присутствует в БД (без учёта дубликатов)
    saved_facts = db_session.query(UserFact).all()
    for key, value in facts_to_load:
        found = any(f.key == key and f.value == value for f in saved_facts)
        assert found, f"Факт ({key}, {value}) не найден в БД"

    # Финальный вопрос: мок возвращает ответ, перечисляя факты,
    # которые реально присутствуют в контексте
    def mock_final_answer(prompt, *args, **kwargs):
        present = []
        for _, value_text in facts_to_load:
            if value_text in str(prompt):
                present.append(value_text)
        if present:
            return "Я знаю: " + "; ".join(present) + "."
        return "Я ничего не знаю."

    with patch("backend.app.services.assistant_service.generate_response",
               side_effect=mock_final_answer):
        answer = chat("Что ты знаешь обо мне?", db_session)

    # Подсчитываем точность
    found_count = sum(1 for _, val in facts_to_load if val in answer)
    total = len(facts_to_load)
    accuracy = found_count / total * 100

    # Вывод метрики (pytest -s)
    print(f"\nТочность памяти: {found_count}/{total} ({accuracy:.0f}%)")

    # Минимальная гарантия – хотя бы часть фактов должна быть найдена
    assert found_count > 0, "Ни один факт не попал в ответ ассистента"