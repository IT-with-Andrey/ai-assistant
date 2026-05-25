import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from backend.app.services.assistant_service import _extract_json


def test_pure_json_array():
    result = _extract_json('[{"key": "a", "value": "b"}]')
    assert result == [{"key": "a", "value": "b"}]


def test_json_with_spaces():
    result = _extract_json('  [  {  "key" : "a" , "value" : "b" }  ]  ')
    assert result == [{"key": "a", "value": "b"}]


def test_json_in_markdown():
    text = '```json\n[{"key": "a", "value": "b"}]\n```'
    result = _extract_json(text)
    assert result == [{"key": "a", "value": "b"}]


def test_json_surrounded_by_text():
    text = 'Вот факты: [{"key": "a", "value": "b"}] конец.'
    result = _extract_json(text)
    assert result == [{"key": "a", "value": "b"}]


def test_empty_array():
    result = _extract_json('[]')
    assert result == []


def test_multiple_facts():
    text = '[{"key": "a", "value": "1"}, {"key": "b", "value": "2"}]'
    result = _extract_json(text)
    assert len(result) == 2
    assert result[0]["key"] == "a"
    assert result[1]["key"] == "b"


def test_broken_json_missing_bracket():
    result = _extract_json('[{"key": "a", "value": "b"')
    assert result is None


def test_empty_string():
    result = _extract_json("")
    assert result is None


def test_plain_text_no_json():
    result = _extract_json("Привет, как дела?")
    assert result is None


def test_none_input():
    result = _extract_json(None)
    assert result is None


def test_nested_array_in_value():
    text = '[{"key": "tags", "value": ["a", "b"]}]'
    result = _extract_json(text)
    assert result == [{"key": "tags", "value": ["a", "b"]}]


def test_json_object_not_array():
    # Функция ищет массив, объект не должен парситься
    result = _extract_json('{"key": "a"}')
    assert result is None


def test_array_with_numbers():
    result = _extract_json('[{"key": "age", "value": 30}]')
    assert result == [{"key": "age", "value": 30}]