import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from pydantic import ValidationError
from backend.app.ai.models import Fact


def test_valid_fact():
    fact = Fact(key="name", value="Алиса")
    assert fact.key == "name"
    assert fact.value == "Алиса"


def test_missing_key():
    with pytest.raises(ValidationError):
        Fact(value="Алиса")


def test_missing_value():
    with pytest.raises(ValidationError):
        Fact(key="name")


def test_key_not_string():
    with pytest.raises(ValidationError):
        Fact(key=123, value="Алиса")


def test_value_not_string():
    with pytest.raises(ValidationError):
        Fact(key="name", value=123)


def test_extra_fields_allowed():
    fact = Fact(key="name", value="Алиса", extra="лишнее")
    assert fact.key == "name"
    assert fact.value == "Алиса"