
from backend.app.database.connection import SessionLocal
from backend.app.services.assistant_service import chat


db = SessionLocal()

user_input = "Привет"

response = chat(user_input, db)

print("RESPONSE:", response)

db.close()