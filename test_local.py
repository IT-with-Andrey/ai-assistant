from backend.app.ai.provider import generate_response
from backend.app.ai.context_builder import build_context

# простой тест
history = []

user_input = "Привет, ты локальная модель?"

message = build_context(history, user_input)

print("MESSAGE:", message)

response = generate_response(message)

print("RESPONSE:", response)

