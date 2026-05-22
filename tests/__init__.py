"""
. test_memory.py — ядро памяти (2 теста)
test_conversation_memory_flow
Симулирует диалог из 12 сообщений и проверяет:
✅ факты сохранились в user_facts
✅ старые 6 сообщений удалились
✅ осталось ровно 6 последних

test_extraction_with_new_keys_and_system_prompt
Проверяет новый формат фактов (name, goal, interest, preference, fact):
✅ все 5 ключей сохраняются
✅ SYSTEM_PROMPT попадает в контекст

2. test_context_injection.py — инжекция фактов (1 тест)
test_build_context_includes_all_facts
Напрямую кладёт 10 фактов в базу и вызывает build_context():
✅ все 10 фактов оказываются в итоговом промпте

3. test_benchmark.py — бенчмарк точности (1 тест)
test_memory_accuracy
Полный цикл: загружает 10 фактов, задаёт вопрос «Что ты знаешь обо мне?»:
✅ все 10 фактов сохранились в БД
✅ хотя бы часть фактов попала в ответ ассистента
✅ выводит метрику точности (X/10, Y%)

4. test_repository.py — кирпичики базы данных (5 тестов)
test_save_message — сохраняет сообщение и проверяет, что оно записалось.

test_get_last_messages — проверяет получение последних N сообщений и их порядок.

test_save_user_fact — сохраняет факт и проверяет запись.

test_get_all_user_facts — проверяет получение всех фактов.

test_save_summary — сохраняет резюме и проверяет запись.
"""