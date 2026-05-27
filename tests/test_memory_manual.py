import requests
import time

BASE_URL = "http://localhost:8000/chat"
USER_ID = "benchmark_user"

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

print("=== Заполняем память 10 фактами ===")
for i, fact in enumerate(facts, 1):
    resp = requests.post(BASE_URL, json={"user_id": USER_ID, "message": fact})
    print(f"{i}. Отправлено: '{fact}' | Статус: {resp.status_code}")
    time.sleep(0.5)

print("\n=== Запрашиваем всё, что ассистент знает ===")
resp = requests.post(BASE_URL, json={"user_id": USER_ID, "message": "Расскажи, что ты обо мне знаешь"})
print(f"Статус: {resp.status_code}")
print(f"Ответ:\n{resp.json().get('response', '')}")