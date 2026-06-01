

# tests/test_memory_deepeval.py
from dotenv import load_dotenv
import os
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric
from backend.app.services.assistant_service import chat
from backend.app.database.models import Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ollama import AsyncClient, ChatResponse
from tenacity import retry, stop_after_attempt
from pydantic import BaseModel
from typing import Optional, Tuple, Union
import pytest
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


# DeepEval

# ---------- Кастомная модель с очисткой JSON ----------

class CleanOllamaModel(OllamaModel):
    @retry(stop=stop_after_attempt(3))
    async def a_generate(
        self, prompt: str, schema: Optional[BaseModel] = None
    ) -> Tuple[Union[str, BaseModel], float]:
        chat_model: AsyncClient = self.load_model(async_mode=True)

        # Всегда текстовый промпт, мультимодальность не нужна
        messages = [{"role": "user", "content": prompt}]

        response: ChatResponse = await chat_model.chat(
            model=self.name,
            messages=messages,
            format=schema.model_json_schema() if schema else None,
            options={
                **{"temperature": self.temperature},
                **self.generation_kwargs,
            },
        )

        raw = response.message.content

        if schema is not None:
            # Очищаем ```json ... ``` вокруг ответа
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '',
                             raw, flags=re.MULTILINE)
            cleaned = re.sub(r'\n?```\s*$', '', cleaned, flags=re.MULTILINE)
            parsed = schema.model_validate_json(cleaned)
            return parsed, 0
        else:
            return raw, 0


EVAL_MODEL = CleanOllamaModel(model="gemma4:31b-cloud")

# ---------- Фикстура с реальной БД ----------

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env")

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# ---------- Тест ----------


def test_memory_faithfulness(db_session):
    facts = [
        "Меня зовут Андрей",
        "Я живу в Германии",
        "Мой любимый язык — Python"
    ]
    for fact in facts:
        chat(fact, db_session)

    question = "Что ты знаешь обо мне?"
    answer = chat(question, db_session)

    retrieval_context = facts

    test_case = LLMTestCase(
        input=question,
        actual_output=answer,
        retrieval_context=retrieval_context,
        expected_output=answer
    )
    metric = FaithfulnessMetric(threshold=50.0, model=EVAL_MODEL)
    metric.measure(test_case)

    print(f"\nОтвет ассистента: {answer}")
    print(f"Memory IQ (Faithfulness): {metric.score:.1f} / 100")

    assert metric.score >= 0.5, f"Faithfulness слишком низкий: {metric.score}"
