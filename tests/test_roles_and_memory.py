import requests
import time

BASE_URL = "http://localhost:8000/chat"

facts = [
    "Меня зовут Андрей",
    "Я живу в Германии",
    "Мой любимый язык программирования — Python",
    "Я работаю архитектором ПО",
    "Я люблю готовить пасту",
    "У меня есть собака по кличке Рекс",
    "Я изучаю немецкий язык",
    "Моё хобби — велоспорт",
    "Я предпочитаю чай кофе",
    "Мой любимый фильм — Матрица"
]

print("=== 1. Заполняем память 10 фактами ===")
for i, fact in enumerate(facts, 1):
    resp = requests.post(BASE_URL, json={"message": fact})
    print(f"{i}. Отправлено: '{fact}' | Статус: {resp.status_code}")
    time.sleep(0.5)

print("\n=== 2. Проверяем роль default ===")
resp = requests.post(BASE_URL, json={"message": "/role default"})
print(f"Статус: {resp.status_code}")
print(f"Ответ: {resp.json().get('response', '')}")

print("\n=== 3. Проверяем память ===")
resp = requests.post(BASE_URL, json={"message": "Расскажи, что ты обо мне знаешь"})
print(f"Статус: {resp.status_code}")
print(f"Ответ:\n{resp.json().get('response', '')}")

print("\n=== 4. Проверяем роль python_teacher ===")
resp = requests.post(BASE_URL, json={"message": "/role python_teacher"})
print(f"Статус: {resp.status_code}")
print(f"Ответ: {resp.json().get('response', '')}")

resp = requests.post(BASE_URL, json={"message": "Объясни мне, что такое декоратор в Python"})
print(f"Ответ на python_teacher:\n{resp.json().get('response', '')}")

print("\n=== 5. Проверяем роль english_tutor ===")
resp = requests.post(BASE_URL, json={"message": "/role english_tutor"})
print(f"Статус: {resp.status_code}")
print(f"Ответ: {resp.json().get('response', '')}")

resp = requests.post(BASE_URL, json={"message": "Объясни разницу между Present Perfect и Past Simple"})
print(f"Ответ на english_tutor:\n{resp.json().get('response', '')}")

print("\n=== 6. Проверяем роль fitness_coach ===")
resp = requests.post(BASE_URL, json={"message": "/role fitness_coach"})
print(f"Статус: {resp.status_code}")
print(f"Ответ: {resp.json().get('response', '')}")

resp = requests.post(BASE_URL, json={"message": "Составь программу тренировок на неделю"})
print(f"Ответ на fitness_coach:\n{resp.json().get('response', '')}")

print("\n=== 7. Проверяем невалидную роль ===")
resp = requests.post(BASE_URL, json={"message": "/role superhero"})
print(f"Ответ: {resp.json().get('response', '')}")

print("\n✅ Авто-тест завершён. Проверь ответы выше!")