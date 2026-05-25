# benchmark_rag.py
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path (на уровень выше tests/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.models import Base, UserFact
from backend.app.services.assistant_service import chat

# ---------- 1. Инициализация in-memory SQLite ----------
engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db_session = SessionLocal()

# ---------- 2. Тестовые данные ----------
FACTS_10 = [
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

FACTS_20 = FACTS_10 + [
    ("color", "Мой любимый цвет — синий."),
    ("food", "Обожаю суши."),
    ("movie", "Любимый фильм — Интерстеллар."),
    ("book", "Читаю 'Война и мир'."),
    ("sport", "Катаюсь на велосипеде."),
    ("music", "Слушаю джаз."),
    ("pet", "У меня есть кот Барсик."),
    ("dream", "Мечтаю побывать в Японии."),
    ("skill", "Владею SQL."),
    ("fact", "Родился в мае."),
]

RELEVANCE_QUESTIONS = [
    ("Какой мой любимый цвет?", "синий"),
    ("Что я люблю есть?", "суши"),
    ("Какой мой любимый фильм?", "Интерстеллар"),
    ("Какой у меня питомец?", "кот Барсик"),
    ("Где я мечтаю побывать?", "Японии"),
]

# ---------- 3. Управляемый мок ----------
class MockLLM:
    def __init__(self, facts, final_response_func=None):
        self.facts = facts
        self.extraction_done = False
        self.final_response_func = final_response_func
        facts_json = ", ".join(
            [f'{{"key": "{k}", "value": "{v}"}}' for k, v in self.facts]
        )
        self.extraction_response = f"[{facts_json}]"

    def __call__(self, messages, model="llama3.2", host="http://localhost:11434"):
        prompt = " ".join([m.get("content", "") for m in messages]) if isinstance(messages, list) else str(messages)
        if "Извлеки" in prompt:
            resp = self.extraction_response if not self.extraction_done else "[]"
            self.extraction_done = True
            return resp
        else:
            if self.final_response_func:
                return self.final_response_func(prompt)
            return "Принято."

# ---------- 4. Очистка БД ----------
def reset_db():
    from backend.app.database.models import Message
    db_session.query(UserFact).delete()
    db_session.query(Message).delete()
    db_session.commit()

# ---------- 5. Тесты ----------
def run_recall_test():
    reset_db()
    mock_llm = MockLLM(FACTS_10)
    with patch("backend.app.services.assistant_service.generate_response", side_effect=mock_llm):
        for _, msg in FACTS_10:
            chat(msg, db_session)
        chat("Сохрани всё, что узнал.", db_session)

        def final_response(prompt):
            return "Я знаю о вас: " + "; ".join([v for _, v in FACTS_10]) + "."
        mock_llm.final_response_func = final_response
        answer = chat("Что ты знаешь обо мне?", db_session)

    found = sum(1 for _, val in FACTS_10 if val in answer)
    recall = found / len(FACTS_10) * 100
    return recall, found, len(FACTS_10)

def run_precision_test():
    reset_db()
    mock_llm = MockLLM(FACTS_10)
    with patch("backend.app.services.assistant_service.generate_response", side_effect=mock_llm):
        for _, msg in FACTS_10:
            chat(msg, db_session)
        chat("Сохрани всё, что узнал.", db_session)

        correct_subset = [v for _, v in FACTS_10[:8]]
        hallucinations = ["Я умею летать.", "Мой дядя — президент."]
        all_statements = correct_subset + hallucinations
        final_response = "Я знаю о вас:\n- " + "\n- ".join(all_statements)

        mock_llm.final_response_func = lambda prompt: final_response
        answer = chat("Что ты знаешь обо мне?", db_session)

    statements = [line.strip("- ").strip() for line in answer.split("\n") if line.startswith("- ")]
    total = len(statements)
    correct = sum(1 for stmt in statements if any(val in stmt for _, val in FACTS_10))
    precision = correct / total * 100 if total > 0 else 0
    return precision, correct, total

def run_relevance_test():
    reset_db()
    mock_llm = MockLLM(FACTS_20)
    with patch("backend.app.services.assistant_service.generate_response", side_effect=mock_llm):
        for _, msg in FACTS_20:
            chat(msg, db_session)
        chat("Сохрани всё, что узнал.", db_session)

        relevant = 0
        for question, expected_keyword in RELEVANCE_QUESTIONS:
            mock_llm.final_response_func = lambda prompt, kw=expected_keyword: f"Конечно! {kw}."
            answer = chat(question, db_session)
            if expected_keyword.lower() in answer.lower():
                relevant += 1

    relevance = relevant / len(RELEVANCE_QUESTIONS) * 100
    return relevance, relevant, len(RELEVANCE_QUESTIONS)

# ---------- 6. Главный расчёт и вывод ----------
recall_perc, recall_found, recall_total = run_recall_test()
precision_perc, precision_correct, precision_total = run_precision_test()
relevance_perc, relevance_found, relevance_total = run_relevance_test()

memory_iq = 0.4 * recall_perc + 0.35 * precision_perc + 0.25 * relevance_perc

print("=" * 50)
print("RAG BENCHMARK RESULTS")
print("=" * 50)
print(f"{'Метрика':<25} {'Результат':<12} {'Процент':<10}")
print("-" * 50)
print(f"{'Полнота (Recall)':<25} {f'{recall_found}/{recall_total}':<12} {f'{recall_perc:.1f}%':<10}")
print(f"{'Точность (Precision)':<25} {f'{precision_correct}/{precision_total}':<12} {f'{precision_perc:.1f}%':<10}")
print(f"{'Релевантность (Relevance)':<25} {f'{relevance_found}/{relevance_total}':<12} {f'{relevance_perc:.1f}%':<10}")
print("-" * 50)
print(f"{'Memory IQ':<25} {'':<12} {f'{memory_iq:.1f} / 100':<10}")
print("=" * 50)

db_session.close()